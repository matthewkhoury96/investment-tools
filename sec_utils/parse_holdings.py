import datetime
import itertools
import os
import pathlib
import re
import time
import typing
import xml.etree.ElementTree

import numpy as np
import requests

from sec_utils import sec_types


def _get_holding_type(
    put_call_tag: xml.etree.ElementTree.Element | None,
) -> sec_types.HoldingType:
    if put_call_tag is not None and put_call_tag.text:
        text_clean = put_call_tag.text.strip().upper()
        if "PUT" in text_clean:
            return sec_types.HoldingType.PUT
        elif "CALL" in text_clean:
            return sec_types.HoldingType.CALL

    return sec_types.HoldingType.SHARE


def parse_13f_xml(xml_path: str) -> list[sec_types.Holding]:
    """Parses an SEC 13F XML file into identifiers and values."""
    try:
        # Step 1: Read raw submission content
        with open(xml_path, "r", errors="ignore") as f:
            raw_content = f.read()

        # Step 2: Extract ALL embedded XML wrappers to isolate the info table from the cover page
        xml_blocks = re.findall(
            r"<XML>(.*?)</XML>", raw_content, re.DOTALL | re.IGNORECASE
        )

        root = None
        for block in xml_blocks:
            # Explicitly target the block containing infoTable matrix markers
            if "infoTable" in block:
                root = xml.etree.ElementTree.fromstring(block.strip())
                break

        if root is None:
            # Fallback for direct clean standalone XML files
            root = xml.etree.ElementTree.fromstring(raw_content)

    except Exception as e:
        print(f"XML Parsing failed for {xml_path}: {e}")
        return []

    # Look for infoTable elements regardless of what namespace URI prefix is attached
    holdings = []
    for table in root.findall(".//{*}infoTable"):
        cusip = table.find(".//{*}cusip")
        value = table.find(".//{*}value")
        put_call_tag = table.find(".//{*}putCall")
        if (
            cusip is not None
            and cusip.text
            and value is not None
            and value.text
        ):
            holdings.append(
                sec_types.Holding(
                    cusip=cusip.text.strip(),
                    value=float(value.text),
                    holding_type=_get_holding_type(put_call_tag),
                )
            )

    return holdings


def parse_nport_xml(
    xml_path: str, series_id: str, class_id: str = None
) -> list[sec_types.Holding]:
    """Parses an SEC N-PORT XML file into identifier and values."""
    try:
        # Step 1: Read raw submission content
        with open(xml_path, "r", errors="ignore") as f:
            raw_content = f.read()

        # Step 2: Extract embedded XML blocks wrapped in <XML> tags
        xml_blocks = re.findall(
            r"<XML>(.*?)</XML>", raw_content, re.DOTALL | re.IGNORECASE
        )

        root_blocks = []
        for block in xml_blocks:
            if "formData" in block or "invstSec" in block:
                root_blocks.append(
                    xml.etree.ElementTree.fromstring(block.strip())
                )

        if not root_blocks:
            root_blocks.append(xml.etree.ElementTree.fromstring(raw_content))

    except Exception as e:
        print(f"N-PORT File reading/loading failed for {xml_path}: {e}")
        return []

    # Find the root for the specific Series ID and Class ID.
    target_block = None
    for root in root_blocks:
        # Verify the Series ID matches
        series_tag = root.find(".//{*}seriesId")
        if series_tag is None or series_tag.text.strip() != series_id:
            continue

        # Verify the Class ID matches
        class_tags = root.findall(".//{*}classId")
        class_ids_in_block = [t.text.strip() for t in class_tags if t.text]

        if class_id in class_ids_in_block:
            # Both conditions are satisfied! Lock this XML block down.
            target_block = root
            break

    if target_block is None:
        print(
            "Could not find a matching combination of Series "
            f"'{series_id}' AND Class '{class_id}' inside {xml_path}."
        )
        return []

    # Extract individual holdings for the verified fund.
    holdings = []
    for security in target_block.findall(".//{*}invstOrSec"):
        cusip = security.find(".//{*}cusip")
        value = security.find(".//{*}valUSD")
        put_call_tag = security.find(".//{*}putCall")
        if (
            cusip is not None
            and cusip.text
            and value is not None
            and value.text
        ):
            holdings.append(
                sec_types.Holding(
                    cusip=cusip.text.strip(),
                    value=float(value.text),
                    holding_type=_get_holding_type(put_call_tag),
                )
            )

    return holdings


def _create_cusip_payload(code: str) -> dict[str, str]:
    """Converts CUSIP or CINS code to a json payload."""
    # Normalize the code to uppercase to match institutional CUSIP standards
    clean_code = code.upper().strip()

    if clean_code[0].isalpha():
        # Alphanumeric means CINS -> Search globally for international ADRs/assets
        return {
            "idType": "ID_CINS",
            "idValue": clean_code,
        }
    else:
        # Numeric means CUSIP -> Force lookups to stay inside the US market ecosystem
        return {
            "idType": "ID_CUSIP",
            "idValue": clean_code,
            "exchCode": "US",
        }


def _get_stock_ids_from_batch_cusips(
    batch_cusips: list[str],
) -> dict[str, sec_types.StockID]:
    """Gets StockIDs from a batch of CUSIP or CINS codes."""
    mapping = {}
    url = "https://api.openfigi.com/v3/mapping"
    headers = {
        "Content-Type": "application/json",
        "X-OPENFIGI-APIKEY": "bde60427-b70f-4c59-8418-289c99c1ee30",
    }
    payload = [_create_cusip_payload(code) for code in batch_cusips]

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)

        if response.status_code == 200:
            results = response.json()
            for idx, item in enumerate(results):
                original_code = batch_cusips[idx]
                data_block = item.get("data")

                if data_block:
                    # Extract the first matching record ticker
                    ticker = data_block[0].get("ticker")
                    name = data_block[0].get("name", "Unknown")
                    if ticker:
                        # Clean up market modifiers (e.g., "AAPL UW" -> "AAPL")
                        clean_ticker = ticker.split()[0].replace("/", ".")
                        mapping[original_code] = sec_types.StockID(
                            ticker=clean_ticker, name=name
                        )
        else:
            print(f"OpenFIGI API returned error status: {response.status_code}")
    except Exception as e:
        print(f"Network error connecting to OpenFIGI: {e}")

    return mapping


def convert_cusips_to_stock_ids(
    cusip_list: list[str],
    batch_size: int = 10,
) -> dict[str, sec_types.StockID]:
    """Maps SEC asset identifiers to StockIDs, dynamically choosing CUSIP or CINS."""
    if not cusip_list:
        return {}

    mapping = {}
    for i in range(0, len(cusip_list), batch_size):
        batch_cusips = cusip_list[i : i + batch_size]
        mapping.update(_get_stock_ids_from_batch_cusips(batch_cusips))
        time.sleep(0.4)

    return mapping


def find_13f_filename(
    download_dir: str, target_period: str, cik: str
) -> tuple[str, str]:
    directory = pathlib.Path(
        os.path.join(download_dir, "sec-edgar-filings", cik, "13F-HR")
    )

    # Keep track of valid files found and their extracted dates: (file_path, date)
    valid_files = []

    for file_path in directory.rglob("full-submission.txt"):
        try:
            with open(file_path, "r", errors="ignore") as f:
                file_head = f.read(15000)

                # Extract whatever date this file actually belongs to
                match = re.search(
                    r"CONFORMED\s+PERIOD\s+OF\s+REPORT:\s*(\d{8})",
                    file_head,
                    re.IGNORECASE,
                )
                if not match:
                    continue

                # If we found the file for the exact target period, return it.
                # Otherwise, store it in valid_files.
                date = match.group(1)
                if date == target_period:
                    return file_path, target_period

                valid_files.append((file_path, date))

        except Exception as e:
            print(f"Failed to read file {file_path} during date scan: {e}")

    # If we couldn't find a file with the given target period, return the
    # file with the most recent reporting date.
    valid_files.sort(key=lambda x: x[1])
    return valid_files[-1] if valid_files else ("", "")


def find_nport_filename(
    download_dir: str,
    target_period: str,
    cik: str,
    series_id: str,
) -> tuple[str, str]:
    directory = pathlib.Path(
        os.path.join(download_dir, "sec-edgar-filings", cik, "NPORT-P")
    )

    # Keep track of valid files found and their extracted dates: (file_path, date)
    valid_files = []

    for file_path in directory.rglob("full-submission.txt"):
        try:
            with open(file_path, "r", errors="ignore") as f:
                file_head = f.read(15000)

                # Skip files that don't have the correct series ID.
                if f"<SERIES-ID>{series_id}" not in file_head:
                    continue

                # Extract whatever date this file actually belongs to
                match = re.search(
                    r"CONFORMED\s+PERIOD\s+OF\s+REPORT:\s*(\d{8})",
                    file_head,
                    re.IGNORECASE,
                )
                if not match:
                    continue

                # If we found the file for the exact target period, return it.
                # Otherwise, store it in valid_files.
                date = match.group(1)
                if date == target_period:
                    return file_path, target_period

                valid_files.append((file_path, date))

        except Exception as e:
            print(f"Failed to read file {file_path} during date scan: {e}")

    # If we couldn't find a file with the given target period, return the
    # file with the most recent reporting date.
    valid_files.sort(key=lambda x: x[1])
    return valid_files[-1] if valid_files else ("", "")


def get_all_holdings_from_downloaded_files(
    download_dir: str,
    target_period: str,
    firms: typing.Mapping[str, sec_types.FirmID],
    etfs_and_mutual_funds: typing.Mapping[str, sec_types.ETFOrMutualFundID],
    cusip_patches: typing.Mapping[str, sec_types.StockID],
) -> dict[str, sec_types.HoldingList]:
    """Traverses downloaded filings to find matches for the quarter."""
    all_holdings: dict[str, sec_types.HoldingList] = {}
    all_detected_cusips = set()

    for name, firm_id in firms.items():
        file_path, date = find_13f_filename(
            download_dir, target_period, firm_id.cik
        )
        if not file_path:
            continue
        holding_list = sec_types.HoldingList(file_path=file_path, date=date)
        holding_list.holdings = parse_13f_xml(holding_list.file_path)
        if not holding_list.holdings:
            continue
        holding_list.calculate_weights_and_sort_holdings()
        all_detected_cusips.update(holding_list.get_all_cusips())
        all_holdings[name] = holding_list

    for name, etf_or_mutual_fund_id in etfs_and_mutual_funds.items():
        file_path, date = find_nport_filename(
            download_dir,
            target_period,
            etf_or_mutual_fund_id.cik,
            etf_or_mutual_fund_id.series_id,
        )
        if not file_path:
            continue
        holding_list = sec_types.HoldingList(file_path=file_path, date=date)
        holding_list.holdings = parse_nport_xml(
            holding_list.file_path,
            etf_or_mutual_fund_id.series_id,
            etf_or_mutual_fund_id.class_id,
        )
        if not holding_list.holdings:
            continue
        holding_list.calculate_weights_and_sort_holdings()
        all_detected_cusips.update(holding_list.get_all_cusips())
        all_holdings[name] = holding_list

    # Resolve CUSIP codes via bulk OpenFIGI mapping
    stock_id_lookup = convert_cusips_to_stock_ids(list(all_detected_cusips))
    stock_id_lookup.update(cusip_patches)
    for holding_list in all_holdings.values():
        for holding in holding_list.holdings:
            holding.stock_id = stock_id_lookup.get(
                holding.cusip,
                sec_types.StockID(
                    ticker=holding.cusip,
                    name="Unknown",
                ),
            )

    return all_holdings

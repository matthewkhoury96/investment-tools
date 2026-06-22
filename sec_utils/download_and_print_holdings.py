import csv
import pathlib
import sys
import tempfile
import types

from absl import app
from absl import flags

from sec_utils import csv_utils
from sec_utils import download_holdings
from sec_utils import parse_holdings
from sec_utils import sec_types

# Command line flags
_TOP_N = flags.DEFINE_integer(
    "top_n",
    10,
    "The top number of holdings to isolate.",
    lower_bound=1,
)
_PERIOD = flags.DEFINE_string(
    "period",
    "20251231",
    "Filing conformed period of report in YYYYMMDD format.",
)
_FIRM_NAMES = flags.DEFINE_multi_string(
    "firm_name",
    [],
    "Firm name(s) to filter by. Can be specified multiple times.",
)
_ETF_NAMES = flags.DEFINE_multi_string(
    "etf_name",
    [],
    "ETF name(s) to filter by. Can be specified multiple times.",
)
_MUTUAL_FUND_NAMES = flags.DEFINE_multi_string(
    "mutual_fund_name",
    [],
    "Mutual fund name(s) to filter by. Can be specified multiple times.",
)
_OUTPUT_FILE = flags.DEFINE_string(
    "output_file",
    "",
    "Output file to store the final CSV. If an output file is not specified, "
    "the CSV will be printed out",
)
_CSV_HOLDINGS_PER_ROW = flags.DEFINE_integer(
    "csv_holdings_per_row",
    5,
    "Number of holdings to put a row in the final CSV",
)

# Constants for generating the final CSV.
_CSV_BLANK_HEADER_ROWS = 1
_CSV_BLANK_COLUMNS_BETWEEN_HOLDINGS = 1
_CSV_BLANK_ROWS_INSIDE_HOLDING = 1
_CSV_BLANK_ROWS_AFTER_HOLDING = 2
_CSV_DELIMITER = ";"

# Firms file 13F reports every quarter.
# Maps {Name -> FirmID}
# CIK found from https://www.sec.gov/search-filings
_FIRMS = types.MappingProxyType(
    {
        "AKRE CAPITAL MANAGEMENT LLC": sec_types.FirmID(
            cik="0001112520",
        ),
        "WCM INVESTMENT MANAGEMENT, LLC": sec_types.FirmID(
            cik="0001061186",
        ),
        "BERKSHIRE HATHAWAY INC": sec_types.FirmID(
            cik="0001067983",
        ),
        "GATES FOUNDATION TRUST": sec_types.FirmID(
            cik="0001166559",
        ),
        "RUANE, CUNNIFF & GOLDFARB L.P.": sec_types.FirmID(
            cik="0001720792",
        ),
        "BAILLIE GIFFORD & CO": sec_types.FirmID(
            cik="0001088875",
        ),
        "TCI FUND MANAGEMENT LTD": sec_types.FirmID(
            cik="0001647251",
        ),
        "FUNDSMITH LLP": sec_types.FirmID(
            cik="0001569205",
        ),
        "AKO CAPITAL LLP": sec_types.FirmID(
            cik="0001376879",
        ),
        "DORSEY ASSET MANAGEMENT, LLC": sec_types.FirmID(
            cik="0001671657",
        ),
        "GARDNER RUSSO & QUINN LLC": sec_types.FirmID(
            cik="0000860643",
        ),
        "POLEN CAPITAL MANAGEMENT LLC": sec_types.FirmID(
            cik="0001034524",
        ),
        "D1 CAPITAL PARTNERS L.P.": sec_types.FirmID(
            cik="0001747057",
        ),
        "ALTAROCK PARTNERS LP": sec_types.FirmID(
            cik="0001631014",
        ),
        "LONE PINE CAPITAL LLC": sec_types.FirmID(
            cik="0001061165",
        ),
        "STRATEGY CAPITAL LLC": sec_types.FirmID(
            cik="0001592413",
        ),
        "GIVERNY CAPITAL INC.": sec_types.FirmID(
            cik="0001641864",
        ),
        "MARKEL GROUP INC.": sec_types.FirmID(
            cik="0001096343",
        ),
        "HIMALAYA CAPITAL MANAGEMENT LLC": sec_types.FirmID(
            cik="0001709323",
        ),
        "I.G.Y. LTD": sec_types.FirmID(
            cik="0001811472",
        ),
        "ALTIMETER CAPITAL MANAGEMENT, LP": sec_types.FirmID(
            cik="0001541617",
        ),
        "PERSHING SQUARE CAPITAL MANAGEMENT, L.P.": sec_types.FirmID(
            cik="0001336528",
        ),
        "SHAWSPRING PARTNERS LLC": sec_types.FirmID(
            cik="0001766908",
        ),
        "SOROBAN CAPITAL PARTNERS LP": sec_types.FirmID(
            cik="0001517857",
        ),
        "NZS CAPITAL, LLC": sec_types.FirmID(
            cik="0001816616",
        ),
        "EGERTON CAPITAL (UK) LLP": sec_types.FirmID(
            cik="0001581811",
        ),
        "THIRD POINT LLC": sec_types.FirmID(
            cik="0001040273",
        ),
        "DUQUESNE FAMILY OFFICE LLC": sec_types.FirmID(
            cik="0001536411",
        ),
        "MAR VISTA INVESTMENT PARTNERS LLC": sec_types.FirmID(
            cik="0001419999",
        ),
        "WEDGEWOOD PARTNERS INC": sec_types.FirmID(
            cik="0000859804",
        ),
        "APPALOOSA LP": sec_types.FirmID(
            cik="0001656456",
        ),
        "BENDER ROBERT & ASSOCIATES": sec_types.FirmID(
            cik="0000894300",
        ),
        "VULCAN VALUE PARTNERS, LLC": sec_types.FirmID(
            cik="0001556785",
        ),
        "VALLEY FORGE CAPITAL MANAGEMENT, LP": sec_types.FirmID(
            cik="0001697868",
        ),
        "GREENLEA LANE CAPITAL MANAGEMENT, LLC": sec_types.FirmID(
            cik="0001766504",
        ),
        "SITUATIONAL AWARENESS PARTNERS LP": sec_types.FirmID(
            cik="0002038540",
        ),
    }
)

# ETFs and Mutual Funds file NPORT files every month.
# Maps {name -> ETFOrMutualFundID}
# CIK, Series ID, Class ID found from https://www.sec.gov/search-filings
_ETFS_AND_MUTUAL_FUNDS = types.MappingProxyType(
    {
        # Filed under iShares Trust
        # https://www.sec.gov/edgar/browse/?CIK=1100663
        "ISHARES CORP S&P U.S. GROWTH ETF": sec_types.ETFOrMutualFundID(
            cik="0001100663",
            series_id="S000004340",
            class_id="C000012070",
        ),
        # Filed under Vanguard Specialized Funds
        # https://www.sec.gov/edgar/browse/?CIK=734383
        "VANGUARD DIVIDEND APPRECIATION INDEX FUND": sec_types.ETFOrMutualFundID(
            cik="0000734383",
            series_id="S000011322",
            class_id="C000031350",
        ),
        "VANGUARD DIVIDEND GROWTH FUND": sec_types.ETFOrMutualFundID(
            cik="0000734383",
            series_id="S000002920",
            class_id="C000008004",
        ),
        # Filed under Vanguard Index Funds
        # https://www.sec.gov/edgar/browse/?CIK=36405
        "VANGUARD GROWTH INDEX FUND": sec_types.ETFOrMutualFundID(
            cik="0000036405",
            series_id="S000002842",
            class_id="C000007786",
        ),
    }
)


_CUSIP_PATCHES = types.MappingProxyType(
    {
        # Acquired by IBM
        "20717M103": sec_types.StockID(
            ticker="CFLT",
            name="Confluent, Inc.",
        ),
    }
)


def main(argv):
    del argv  # Unused inside absl app context

    # Filter firms, etfs, and mutual funds if requested.
    filtered_firms = {}
    filtered_etfs_and_mutual_funds = {}
    if _FIRM_NAMES.value or _ETF_NAMES.value or _MUTUAL_FUND_NAMES.value:
        for name in _FIRM_NAMES.value:
            name = name.upper()
            if name not in _FIRMS:
                sys.exit(f"Error: '{name}' not found in mapping.")
            filtered_firms[name] = _FIRMS[name]
        for name in _ETF_NAMES.value + _MUTUAL_FUND_NAMES.value:
            name = name.upper()
            if name not in _ETFS_AND_MUTUAL_FUNDS:
                sys.exit(f"Error: '{name}' not found in mapping.")
            filtered_etfs_and_mutual_funds[name] = _ETFS_AND_MUTUAL_FUNDS[name]
    else:
        filtered_firms = _FIRMS
        filtered_etfs_and_mutual_funds = _ETFS_AND_MUTUAL_FUNDS

    with tempfile.TemporaryDirectory() as tmp_dir:
        print(
            "[*] Downloading files from SEC EDGAR",
            file=sys.stderr,
        )
        download_holdings.download_13f_filings(
            tmp_dir,
            filtered_firms,
            _PERIOD.value,
        )
        download_holdings.download_nport_filings(
            tmp_dir,
            filtered_etfs_and_mutual_funds,
            _PERIOD.value,
        )

        print(
            f"[*] Parsing data matching period [{_PERIOD.value}] ",
            file=sys.stderr,
        )
        all_holdings = parse_holdings.get_all_holdings_from_downloaded_files(
            tmp_dir,
            _PERIOD.value,
            filtered_firms,
            filtered_etfs_and_mutual_funds,
            _CUSIP_PATCHES,
        )

        print(
            f"[*] Creating CSV for top [{_TOP_N.value}] holdings",
            file=sys.stderr,
        )

        csv_output = csv_utils.create_top_n_holdings_csv(
            list(filtered_firms.keys())
            + list(filtered_etfs_and_mutual_funds.keys()),
            all_holdings,
            _TOP_N.value,
            _CSV_BLANK_HEADER_ROWS,
            _CSV_BLANK_COLUMNS_BETWEEN_HOLDINGS,
            _CSV_BLANK_ROWS_INSIDE_HOLDING,
            _CSV_BLANK_ROWS_AFTER_HOLDING,
            _CSV_HOLDINGS_PER_ROW.value,
        )

        if _OUTPUT_FILE.value:
            print(
                f"[*] Saving CSV file to [{_OUTPUT_FILE.value}]",
                file=sys.stderr,
            )
            file_path = pathlib.Path(_OUTPUT_FILE.value)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8", newline="") as file:
                writer = csv.writer(file, delimiter=_CSV_DELIMITER)
                writer.writerows(csv_output)
        else:
            print(
                f"[*] Printing CSV",
                file=sys.stderr,
            )
            writer = csv.writer(sys.stdout, delimiter=_CSV_DELIMITER)
            writer.writerows(csv_output)


if __name__ == "__main__":
    app.run(main)

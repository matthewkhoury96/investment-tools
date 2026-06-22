import datetime
import typing

import sec_edgar_downloader

from sec_utils import sec_types


def _download_filings(
    form_name: str,
    download_dir: str,
    ciks: set[str],
    target_period: str,
    days_before_target_period: int,
    days_after_target_period: int,
) -> None:
    target_period_date = datetime.datetime.strptime(
        target_period, "%Y%m%d"
    ).date()

    window_start = target_period_date - datetime.timedelta(
        days=days_before_target_period
    )
    window_end = target_period_date + datetime.timedelta(
        days=days_after_target_period
    )

    after_str = window_start.strftime("%Y-%m-%d")
    before_str = window_end.strftime("%Y-%m-%d")

    dl = sec_edgar_downloader.Downloader(
        "MyCompany", "yourname@example.com", download_dir
    )

    for cik in ciks:
        dl.get(form_name, cik, after=after_str, before=before_str)


def download_13f_filings(
    download_dir: str,
    firms: typing.Mapping[str, sec_types.FirmID],
    target_period: str,
) -> None:
    """Downloads 13F-HR filings restricted to the target quarter."""
    # Pad the beginning by 5 days to capture early filers
    ciks = set(firm_id.cik for firm_id in firms.values())
    _download_filings("13F-HR", download_dir, ciks, target_period, 5, 60)


def download_nport_filings(
    download_dir: str,
    etfs_and_mutual_funds: typing.Mapping[str, sec_types.ETFOrMutualFundID],
    target_period: str,
) -> None:
    """Downloads NPORT-P filings restricted to the target quarter."""
    # Pad the beginning by 5 days to capture early filers
    # Give it a 70-day window since funds have up to 60 days
    # post-period to file NPORT-P
    ciks = set(
        etf_or_mutual_fund_id.cik
        for etf_or_mutual_fund_id in etfs_and_mutual_funds.values()
    )
    _download_filings("NPORT-P", download_dir, ciks, target_period, 5, 70)

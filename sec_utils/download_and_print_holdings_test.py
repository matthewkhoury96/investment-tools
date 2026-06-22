import pathlib
import sys
from unittest import mock

from absl.testing import absltest
from absl.testing import flagsaver

from sec_utils import download_and_print_holdings


class DownloadAndPrintHoldingsTest(absltest.TestCase):
    @mock.patch(
        "sec_utils.download_and_print_holdings.tempfile.TemporaryDirectory"
    )
    @mock.patch("sec_utils.download_and_print_holdings.download_holdings")
    @mock.patch("sec_utils.download_and_print_holdings.parse_holdings")
    @mock.patch("sec_utils.download_and_print_holdings.csv_utils")
    def test_default_execution_flow(
        self, mock_csv, mock_parse, mock_download, mock_tempdir
    ):
        """Verifies full orchestration runs with all records if no flags are passed."""
        mock_tempdir.return_value.__enter__.return_value = (
            "/mocked/safe/temp/dir"
        )
        mock_parse.get_all_holdings_from_downloaded_files.return_value = []
        mock_csv.create_top_n_holdings_csv.return_value = [[]]

        with mock.patch("sys.stderr"), mock.patch("sys.stdout"):
            download_and_print_holdings.main([])

        # Clean assertions using your definitive mock directory string path
        mock_download.download_13f_filings.assert_called_once_with(
            "/mocked/safe/temp/dir",
            download_and_print_holdings._FIRMS,
            "20251231",
        )
        mock_download.download_nport_filings.assert_called_once_with(
            "/mocked/safe/temp/dir",
            download_and_print_holdings._ETFS_AND_MUTUAL_FUNDS,
            "20251231",
        )
        mock_parse.get_all_holdings_from_downloaded_files.assert_called_once_with(
            "/mocked/safe/temp/dir",
            "20251231",
            download_and_print_holdings._FIRMS,
            download_and_print_holdings._ETFS_AND_MUTUAL_FUNDS,
            mock.ANY,
        )
        mock_csv.create_top_n_holdings_csv.assert_called_once()

    @flagsaver.flagsaver(
        (
            download_and_print_holdings._FIRM_NAMES,
            ["AKRE CAPITAL MANAGEMENT LLC"],
        )
    )
    @mock.patch(
        "sec_utils.download_and_print_holdings.tempfile.TemporaryDirectory"
    )
    @mock.patch("sec_utils.download_and_print_holdings.download_holdings")
    @mock.patch("sec_utils.download_and_print_holdings.parse_holdings")
    @mock.patch("sec_utils.download_and_print_holdings.csv_utils")
    def test_valid_firm_filtering(
        self, mock_csv, mock_parse, mock_download, mock_tempdir
    ):
        """Verifies that flag filtering passes only specified firms downstream."""
        mock_tempdir.return_value.__enter__.return_value = (
            "/mocked/safe/temp/dir"
        )
        mock_parse.get_all_holdings_from_downloaded_files.return_value = []
        mock_csv.create_top_n_holdings_csv.return_value = [[]]

        with mock.patch("sys.stderr"), mock.patch("sys.stdout"):
            download_and_print_holdings.main([])

        expected_filtered_firms = {
            "AKRE CAPITAL MANAGEMENT LLC": download_and_print_holdings._FIRMS[
                "AKRE CAPITAL MANAGEMENT LLC"
            ]
        }
        expected_filtered_funds = {}
        mock_download.download_13f_filings.assert_called_once_with(
            "/mocked/safe/temp/dir", expected_filtered_firms, "20251231"
        )
        mock_download.download_nport_filings.assert_called_once_with(
            "/mocked/safe/temp/dir", expected_filtered_funds, "20251231"
        )
        mock_parse.get_all_holdings_from_downloaded_files.assert_called_once_with(
            "/mocked/safe/temp/dir",
            "20251231",
            expected_filtered_firms,
            expected_filtered_funds,
            mock.ANY,
        )
        mock_csv.create_top_n_holdings_csv.assert_called_once()

    @flagsaver.flagsaver(
        (
            download_and_print_holdings._MUTUAL_FUND_NAMES,
            ["VANGUARD DIVIDEND GROWTH FUND"],
        ),
        (
            download_and_print_holdings._ETF_NAMES,
            ["ISHARES CORP S&P U.S. GROWTH ETF"],
        ),
    )
    @mock.patch(
        "sec_utils.download_and_print_holdings.tempfile.TemporaryDirectory"
    )
    @mock.patch("sec_utils.download_and_print_holdings.download_holdings")
    @mock.patch("sec_utils.download_and_print_holdings.parse_holdings")
    @mock.patch("sec_utils.download_and_print_holdings.csv_utils")
    def test_valid_fund_filtering(
        self, mock_csv, mock_parse, mock_download, mock_tempdir
    ):
        """Verifies that flag filtering passes only specified ETFs and Funds downstream."""
        mock_tempdir.return_value.__enter__.return_value = (
            "/mocked/safe/temp/dir"
        )
        mock_parse.get_all_holdings_from_downloaded_files.return_value = []
        mock_csv.create_top_n_holdings_csv.return_value = [[]]

        with mock.patch("sys.stderr"), mock.patch("sys.stdout"):
            download_and_print_holdings.main([])

        expected_filtered_firms = {}
        expected_filtered_funds = {
            "ISHARES CORP S&P U.S. GROWTH ETF": download_and_print_holdings._ETFS_AND_MUTUAL_FUNDS[
                "ISHARES CORP S&P U.S. GROWTH ETF"
            ],
            "VANGUARD DIVIDEND GROWTH FUND": download_and_print_holdings._ETFS_AND_MUTUAL_FUNDS[
                "VANGUARD DIVIDEND GROWTH FUND"
            ],
        }
        mock_download.download_13f_filings.assert_called_once_with(
            "/mocked/safe/temp/dir", expected_filtered_firms, "20251231"
        )
        mock_download.download_nport_filings.assert_called_once_with(
            "/mocked/safe/temp/dir", expected_filtered_funds, "20251231"
        )
        mock_parse.get_all_holdings_from_downloaded_files.assert_called_once_with(
            "/mocked/safe/temp/dir",
            "20251231",
            expected_filtered_firms,
            expected_filtered_funds,
            mock.ANY,
        )
        mock_csv.create_top_n_holdings_csv.assert_called_once()

    @flagsaver.flagsaver(
        (
            download_and_print_holdings._FIRM_NAMES,
            ["AKRE CAPITAL MANAGEMENT LLC", "APPALOOSA LP"],
        ),
        (
            download_and_print_holdings._MUTUAL_FUND_NAMES,
            ["VANGUARD DIVIDEND GROWTH FUND"],
        ),
        (
            download_and_print_holdings._ETF_NAMES,
            ["ISHARES CORP S&P U.S. GROWTH ETF"],
        ),
    )
    @mock.patch(
        "sec_utils.download_and_print_holdings.tempfile.TemporaryDirectory"
    )
    @mock.patch("sec_utils.download_and_print_holdings.download_holdings")
    @mock.patch("sec_utils.download_and_print_holdings.parse_holdings")
    @mock.patch("sec_utils.download_and_print_holdings.csv_utils")
    def test_valid_fund_and_firm_filtering(
        self, mock_csv, mock_parse, mock_download, mock_tempdir
    ):
        """Verifies that flag filtering passes only specified ETFs and Funds downstream."""
        mock_tempdir.return_value.__enter__.return_value = (
            "/mocked/safe/temp/dir"
        )
        mock_parse.get_all_holdings_from_downloaded_files.return_value = []
        mock_csv.create_top_n_holdings_csv.return_value = [[]]

        with mock.patch("sys.stderr"), mock.patch("sys.stdout"):
            download_and_print_holdings.main([])

        expected_filtered_firms = {
            "AKRE CAPITAL MANAGEMENT LLC": download_and_print_holdings._FIRMS[
                "AKRE CAPITAL MANAGEMENT LLC"
            ],
            "APPALOOSA LP": download_and_print_holdings._FIRMS["APPALOOSA LP"],
        }
        expected_filtered_funds = {
            "ISHARES CORP S&P U.S. GROWTH ETF": download_and_print_holdings._ETFS_AND_MUTUAL_FUNDS[
                "ISHARES CORP S&P U.S. GROWTH ETF"
            ],
            "VANGUARD DIVIDEND GROWTH FUND": download_and_print_holdings._ETFS_AND_MUTUAL_FUNDS[
                "VANGUARD DIVIDEND GROWTH FUND"
            ],
        }
        mock_download.download_13f_filings.assert_called_once_with(
            "/mocked/safe/temp/dir", expected_filtered_firms, "20251231"
        )
        mock_download.download_nport_filings.assert_called_once_with(
            "/mocked/safe/temp/dir", expected_filtered_funds, "20251231"
        )
        mock_parse.get_all_holdings_from_downloaded_files.assert_called_once_with(
            "/mocked/safe/temp/dir",
            "20251231",
            expected_filtered_firms,
            expected_filtered_funds,
            mock.ANY,
        )
        mock_csv.create_top_n_holdings_csv.assert_called_once()

    @flagsaver.flagsaver(
        (download_and_print_holdings._FIRM_NAMES, ["NON_EXISTENT_HEDGE_FUND"])
    )
    def test_invalid_firm_terminates_gracefully(self):
        """Verifies that an unknown firm name triggers an immediate exit."""
        with self.assertRaises(SystemExit) as context:
            download_and_print_holdings.main([])

        self.assertIn(
            "Error: 'NON_EXISTENT_HEDGE_FUND' not found in mapping.",
            str(context.exception),
        )

    @flagsaver.flagsaver(
        (download_and_print_holdings._OUTPUT_FILE, "/fake/path/output.csv")
    )
    @mock.patch("sec_utils.download_and_print_holdings.download_holdings")
    @mock.patch("sec_utils.download_and_print_holdings.parse_holdings")
    @mock.patch("sec_utils.download_and_print_holdings.csv_utils")
    @mock.patch("pathlib.Path.mkdir")
    def test_saves_to_custom_file_path(
        self, mock_mkdir, mock_csv, mock_parse, mock_download
    ):
        """Verifies that if output_file is set, open() writes out to it."""
        mock_csv.create_top_n_holdings_csv.return_value = [["Data"]]

        m_open = mock.mock_open()
        with mock.patch("sys.stderr"), mock.patch("builtins.open", m_open):
            download_and_print_holdings.main([])

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        m_open.assert_called_once_with(
            pathlib.Path("/fake/path/output.csv"),
            "w",
            encoding="utf-8",
            newline="",
        )


if __name__ == "__main__":
    absltest.main()

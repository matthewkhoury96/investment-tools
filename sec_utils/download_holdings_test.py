from unittest import mock

from absl.testing import absltest

from sec_utils import download_holdings
from sec_utils import sec_types


class DownloadHoldingsTest(absltest.TestCase):
    @mock.patch("sec_edgar_downloader.Downloader")
    def test_download_13f_filings(self, mock_downloader_cls):
        # Setup the mock instance returned by the constructor
        mock_downloader_instance = mock.MagicMock()
        mock_downloader_cls.return_value = mock_downloader_instance

        # Test data using the real sec_types dataclasses/objects
        firms = {
            "firm_a": sec_types.FirmID(cik="0001111111"),
            "firm_b": sec_types.FirmID(cik="0002222222"),
        }

        # Execute the public function
        download_holdings.download_13f_filings(
            download_dir="/tmp/13f", firms=firms, target_period="20231231"
        )

        # Verify Downloader initialized with correct params
        mock_downloader_cls.assert_called_once_with(
            "MyCompany", "yourname@example.com", "/tmp/13f"
        )

        # Expected dates calculated by real internal logic:
        # 2023-12-31 minus 5 days and plus 60 days (2024 is a leap year)
        expected_after = "2023-12-26"
        expected_before = "2024-02-29"

        # Verify get was called for each CIK with the right date window
        self.assertEqual(mock_downloader_instance.get.call_count, 2)
        mock_downloader_instance.get.assert_any_call(
            "13F-HR", "0001111111", after=expected_after, before=expected_before
        )
        mock_downloader_instance.get.assert_any_call(
            "13F-HR", "0002222222", after=expected_after, before=expected_before
        )

    @mock.patch("sec_edgar_downloader.Downloader")
    def test_download_nport_filings(self, mock_downloader_cls):
        # Setup the mock instance returned by the constructor
        mock_downloader_instance = mock.MagicMock()
        mock_downloader_cls.return_value = mock_downloader_instance

        # Test data using the real sec_types dataclasses/objects
        # Note that fund_a and fund_b have the same CIK, so there
        # should only be one download command called for both funds.
        funds = {
            "fund_a": sec_types.ETFOrMutualFundID(
                cik="0003333333", series_id="S000003", class_id="C000003"
            ),
            "fund_b": sec_types.ETFOrMutualFundID(
                cik="0004444444", series_id="S000004", class_id="C000004"
            ),
            "fund_c": sec_types.ETFOrMutualFundID(
                cik="0003333333", series_id="S000004", class_id="C000004"
            ),
        }

        # Execute the public function
        download_holdings.download_nport_filings(
            download_dir="/tmp/nport",
            etfs_and_mutual_funds=funds,
            target_period="20230630",
        )

        # Verify Downloader initialized with correct params
        mock_downloader_cls.assert_called_once_with(
            "MyCompany", "yourname@example.com", "/tmp/nport"
        )

        # Expected dates calculated by real internal logic:
        # 2023-06-30 minus 5 days and plus 70 days
        expected_after = "2023-06-25"
        expected_before = "2023-09-08"

        # Verify get call parameters
        self.assertEqual(mock_downloader_instance.get.call_count, 2)
        mock_downloader_instance.get.assert_any_call(
            "NPORT-P",
            "0003333333",
            after=expected_after,
            before=expected_before,
        )
        mock_downloader_instance.get.assert_any_call(
            "NPORT-P",
            "0004444444",
            after=expected_after,
            before=expected_before,
        )


if __name__ == "__main__":
    absltest.main()

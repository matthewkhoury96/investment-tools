import contextlib
import io
import os
import pathlib
import textwrap
from unittest import mock

from absl.testing import absltest

from sec_utils import parse_holdings
from sec_utils import sec_types


def _cusip_post_handler(url, json=None, **kwargs):
    request_payload = json if json else []

    response_payload = []
    for item in request_payload:
        cusip = item.get("idValue", "None")
        response_payload.append(
            {
                "data": [
                    {
                        "ticker": f"TICKER_{cusip}",
                        "name": f"NAME_{cusip}",
                    }
                ]
            }
        )

    mock_response = mock.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = response_payload
    return mock_response


class ParseHoldingsTest(absltest.TestCase):
    @mock.patch("builtins.open", new_callable=mock.mock_open)
    def test_parse_13f_xml_embedded_blocks(self, mock_file):
        """Verifies regex extraction isolates embedded infoTable blocks."""
        mock_file.return_value.read.return_value = textwrap.dedent(
            """
        <SUBMISSION>
        <XML>
        <informationTable xmlns="http://sec.gov">
            <infoTable>
                <cusip>0000001</cusip>
                <value>5500.00</value>
                <putCall>PUT</putCall>
            </infoTable>
            <infoTable>
                <cusip>0000002</cusip>
                <value>7500.00</value>
                <putCall>CALL</putCall>
            </infoTable>
            <infoTable>
                <cusip>0000003</cusip>
                <value>8500.00</value>
            </infoTable>
          </informationTable>
        </XML>
        </SUBMISSION>
        """
        )
        results = parse_holdings.parse_13f_xml("mock_13f.txt")

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].cusip, "0000001")
        self.assertEqual(results[0].value, 5500.0)
        self.assertEqual(results[0].holding_type, sec_types.HoldingType.PUT)
        self.assertEqual(results[1].cusip, "0000002")
        self.assertEqual(results[1].value, 7500.0)
        self.assertEqual(results[1].holding_type, sec_types.HoldingType.CALL)
        self.assertEqual(results[2].cusip, "0000003")
        self.assertEqual(results[2].value, 8500.0)
        self.assertEqual(results[2].holding_type, sec_types.HoldingType.SHARE)

    def test_integration_parse_test_13f_file(self):
        """Verifies parsing and value extraction from a test 13F file."""
        # Locate your declared test data file inside the Bazel sandbox
        current_dir = pathlib.Path(__file__).parent
        fixture_path = os.path.join(current_dir, "testdata/test_13f.xml")

        # Act: Pass the local file path into your 13F parsing function
        holdings = parse_holdings.parse_13f_xml(fixture_path)

        # Assert: Confirm all three securities are perfectly extracted
        self.assertEqual(len(holdings), 3)

        # 1. Verify Alphabet Inc Class A position
        self.assertEqual(holdings[0].cusip, "02079K305")
        self.assertEqual(holdings[0].value, 51304869.0)
        self.assertEqual(holdings[0].holding_type, sec_types.HoldingType.SHARE)

        # 2. Verify Amazon Com Inc position
        self.assertEqual(holdings[1].cusip, "023135106")
        self.assertEqual(holdings[1].value, 13448958.0)
        self.assertEqual(holdings[1].holding_type, sec_types.HoldingType.SHARE)

        # 3. Verify Apple Inc position
        self.assertEqual(holdings[2].cusip, "037833100")
        self.assertEqual(holdings[2].value, 38854173.0)
        self.assertEqual(holdings[2].holding_type, sec_types.HoldingType.PUT)

    @mock.patch("builtins.open", new_callable=mock.mock_open)
    def test_parse_nport_xml_filtering(self, mock_file):
        """Verifies N-PORT structures parse correctly under ID filters."""
        mock_file.return_value.read.return_value = textwrap.dedent(
            """
        <XML>
        <formData>
            <seriesId>S000001</seriesId>
            <classId>C000002</classId>
            <invstOrSec>
                <cusip>0000005</cusip>
                <valUSD>10250.50</valUSD>
            </invstOrSec>
            <invstOrSec>
                <cusip>0000006</cusip>
                <valUSD>250.50</valUSD>
            </invstOrSec>
            <invstOrSec>
                <cusip>0000007</cusip>
                <valUSD>50.50</valUSD>
                <putCall>CALL</putCall>
            </invstOrSec>
            <invstOrSec>
                <cusip>0000008</cusip>
                <valUSD>133.33</valUSD>
                <putCall>PUT</putCall>
            </invstOrSec>
        </formData>
        </XML>
        """
        )
        results = parse_holdings.parse_nport_xml(
            "mock_nport.txt", series_id="S000001", class_id="C000002"
        )
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0].cusip, "0000005")
        self.assertEqual(results[0].value, 10250.50)
        self.assertEqual(results[0].holding_type, sec_types.HoldingType.SHARE)
        self.assertEqual(results[1].cusip, "0000006")
        self.assertEqual(results[1].value, 250.50)
        self.assertEqual(results[1].holding_type, sec_types.HoldingType.SHARE)
        self.assertEqual(results[2].cusip, "0000007")
        self.assertEqual(results[2].value, 50.50)
        self.assertEqual(results[2].holding_type, sec_types.HoldingType.CALL)
        self.assertEqual(results[3].cusip, "0000008")
        self.assertEqual(results[3].value, 133.33)
        self.assertEqual(results[3].holding_type, sec_types.HoldingType.PUT)

        # Confirm mismatch definitions drop outputs gracefully. Ignore
        # lines printed about failing to find a file.
        with contextlib.redirect_stdout(io.StringIO()):
            missed = parse_holdings.parse_nport_xml(
                "mock_nport.txt", series_id="WRONG_ID", class_id="C000002"
            )
            self.assertEqual(len(missed), 0)

    def test_integration_parse_test_nport_file(self):
        """Verifies parsing and value extraction from a test N-PORT file."""
        # Locate your declared test data file inside the Bazel sandbox
        current_dir = pathlib.Path(__file__).parent
        fixture_path = os.path.join(current_dir, "testdata/test_nport.xml")

        # Act: Run your production parsing module against the text file
        holdings = parse_holdings.parse_nport_xml(
            xml_path=fixture_path,
            series_id="S000002924",
            class_id="C000032424",
        )

        # Assert: Confirm all three records are perfectly extracted
        self.assertEqual(len(holdings), 3)

        # 1. Verify first asset (Prologis)
        self.assertEqual(holdings[0].cusip, "74340W103")
        self.assertEqual(holdings[0].value, 4850100200.50)
        self.assertEqual(holdings[0].holding_type, sec_types.HoldingType.SHARE)

        # 2. Verify second asset (American Tower)
        self.assertEqual(holdings[1].cusip, "03027X100")
        self.assertEqual(holdings[1].value, 3210450900.00)
        self.assertEqual(holdings[1].holding_type, sec_types.HoldingType.SHARE)

        # 3. Verify third asset (Equinix Call Option)
        self.assertEqual(holdings[2].cusip, "29444U109")
        self.assertEqual(holdings[2].value, 15400000.00)
        self.assertEqual(holdings[2].holding_type, sec_types.HoldingType.CALL)

    @mock.patch("requests.post")
    @mock.patch("time.sleep")
    def test_convert_cusips_to_stock_ids_batching(self, mock_sleep, mock_post):
        """Tests convert_cusips_to_stock_ids and verifies batching."""
        mock_post.side_effect = _cusip_post_handler

        test_cusips = [
            "0000001",
            "a000002",
            "  b000003  ",
            "0000004",
            "0000005",
        ]
        results = parse_holdings.convert_cusips_to_stock_ids(
            test_cusips, batch_size=2
        )

        # Check the results and the mock call counts.
        self.assertEqual(len(results), 5)
        self.assertEqual(mock_post.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 3)

        self.assertIn("0000001", results)
        self.assertEqual(
            results["0000001"],
            sec_types.StockID(ticker="TICKER_0000001", name="NAME_0000001"),
        )
        self.assertIn("a000002", results)
        self.assertEqual(
            results["a000002"],
            sec_types.StockID(ticker="TICKER_A000002", name="NAME_A000002"),
        )
        self.assertIn("  b000003  ", results)
        self.assertEqual(
            results["  b000003  "],
            sec_types.StockID(ticker="TICKER_B000003", name="NAME_B000003"),
        )
        self.assertIn("0000004", results)
        self.assertEqual(
            results["0000004"],
            sec_types.StockID(ticker="TICKER_0000004", name="NAME_0000004"),
        )
        self.assertIn("0000005", results)
        self.assertEqual(
            results["0000005"],
            sec_types.StockID(ticker="TICKER_0000005", name="NAME_0000005"),
        )

        # Check the payloads sent to requests.post
        posted_batches = [
            call.kwargs["json"] for call in mock_post.call_args_list
        ]
        self.assertEqual(len(posted_batches), 3)

        batch_0_payloads = posted_batches[0]
        self.assertEqual(len(batch_0_payloads), 2)
        self.assertEqual(batch_0_payloads[0]["idValue"], "0000001")
        self.assertEqual(batch_0_payloads[0]["idType"], "ID_CUSIP")
        self.assertEqual(batch_0_payloads[0]["exchCode"], "US")
        self.assertEqual(batch_0_payloads[1]["idValue"], "A000002")
        self.assertEqual(batch_0_payloads[1]["idType"], "ID_CINS")
        self.assertNotIn("exchCode", batch_0_payloads[1])

        batch_1_payloads = posted_batches[1]
        self.assertEqual(len(batch_1_payloads), 2)
        self.assertEqual(batch_1_payloads[0]["idValue"], "B000003")
        self.assertEqual(batch_1_payloads[0]["idType"], "ID_CINS")
        self.assertNotIn("exchCode", batch_1_payloads[0])
        self.assertEqual(batch_1_payloads[1]["idValue"], "0000004")
        self.assertEqual(batch_1_payloads[1]["idType"], "ID_CUSIP")
        self.assertEqual(batch_1_payloads[1]["exchCode"], "US")

        batch_2_payloads = posted_batches[2]
        self.assertEqual(len(batch_2_payloads), 1)
        self.assertEqual(batch_2_payloads[0]["idValue"], "0000005")
        self.assertEqual(batch_2_payloads[0]["idType"], "ID_CUSIP")
        self.assertEqual(batch_2_payloads[0]["exchCode"], "US")

    @mock.patch("pathlib.Path.rglob")
    @mock.patch("builtins.open", new_callable=mock.mock_open)
    def test_find_13f_filename_exact_and_fallback(self, mock_file, mock_rglob):
        """Verifies exact matches return instantly, fallbacks sort by date."""
        # Make rglob return 2 fake file paths
        mock_rglob.return_value = [
            "/tmp/sec/fake_file_0",
            "/tmp/sec/fake_file_1",
        ]

        # Case 1: Exact match found
        mock_file.return_value.read.side_effect = [
            "CONFORMED PERIOD OF REPORT: 20230930",
            "CONFORMED PERIOD OF REPORT: 20231231",
        ]
        file_path, date = parse_holdings.find_13f_filename(
            download_dir="/tmp/sec", target_period="20231231", cik="0001111111"
        )
        self.assertEqual(file_path, "/tmp/sec/fake_file_1")
        self.assertEqual(date, "20231231")

        # Case 2: Exact period missing, fall back to sorting by most recent date
        mock_file.return_value.read.side_effect = [
            "CONFORMED PERIOD OF REPORT: 20230930",
            "CONFORMED PERIOD OF REPORT: 20230630",
        ]
        file_path, date = parse_holdings.find_13f_filename(
            download_dir="/tmp/sec", target_period="20231231", cik="0001111111"
        )
        self.assertEqual(file_path, "/tmp/sec/fake_file_0")
        self.assertEqual(date, "20230930")

    @mock.patch("pathlib.Path.rglob")
    @mock.patch("builtins.open", new_callable=mock.mock_open)
    def test_find_nport_filename_filters_by_series_id(
        self, mock_file, mock_rglob
    ):
        """Verifies N-PORT file scans filter out non-matching Series IDs."""
        # Make rglob return 3 fake file paths
        mock_rglob.return_value = [
            "/tmp/sec/fake_file_0",
            "/tmp/sec/fake_file_1",
            "/tmp/sec/fake_file_2",
        ]

        # Case 1: Exact match found
        mock_file.return_value.read.side_effect = [
            "<SERIES-ID>S000000009\nCONFORMED PERIOD OF REPORT: 20231231",
            "<SERIES-ID>S000099999\nCONFORMED PERIOD OF REPORT: 20230831",
            "<SERIES-ID>S000099999\nCONFORMED PERIOD OF REPORT: 20231231",
        ]
        file_path, date = parse_holdings.find_nport_filename(
            download_dir="/tmp/sec",
            target_period="20231231",
            cik="0002222222",
            series_id="S000099999",
        )
        self.assertEqual(file_path, "/tmp/sec/fake_file_2")
        self.assertEqual(date, "20231231")

        # Case 2: Exact period missing, fall back to sorting by most recent date
        mock_file.return_value.read.side_effect = [
            "<SERIES-ID>S000000009\nCONFORMED PERIOD OF REPORT: 20230631",
            "<SERIES-ID>S000099999\nCONFORMED PERIOD OF REPORT: 20230831",
            "<SERIES-ID>S000099999\nCONFORMED PERIOD OF REPORT: 20230631",
        ]
        file_path, date = parse_holdings.find_nport_filename(
            download_dir="/tmp/sec",
            target_period="20231231",
            cik="0002222222",
            series_id="S000099999",
        )
        self.assertEqual(file_path, "/tmp/sec/fake_file_1")
        self.assertEqual(date, "20230831")

    @mock.patch("sec_utils.parse_holdings.convert_cusips_to_stock_ids")
    @mock.patch("sec_utils.parse_holdings.parse_nport_xml")
    @mock.patch("sec_utils.parse_holdings.find_nport_filename")
    @mock.patch("sec_utils.parse_holdings.parse_13f_xml")
    @mock.patch("sec_utils.parse_holdings.find_13f_filename")
    def test_get_all_holdings_from_downloaded_files_orchestration(
        self,
        mock_find_13f,
        mock_parse_13f,
        mock_find_nport,
        mock_parse_nport,
        mock_convert_cusips,
    ):
        """Verifies high-level pipeline loops, maps values, and applies patches."""
        mock_find_13f.return_value = ("/mock/path/13f.txt", "20231231")
        mock_find_nport.return_value = ("/mock/path/nport.txt", "20231231")

        mock_parse_13f.return_value = [
            sec_types.Holding(cusip="CUSIP111", value=100.0),
            sec_types.Holding(cusip="CUSIP112", value=50.0),
            sec_types.Holding(cusip="CUSIP113", value=125.0),
        ]
        mock_parse_nport.return_value = [
            sec_types.Holding(cusip="CUSIP211", value=200.0),
            sec_types.Holding(cusip="CUSIP212", value=600.0),
            sec_types.Holding(cusip="CUSIP211", value=200.0),
        ]

        mock_convert_cusips.return_value = {
            "CUSIP111": sec_types.StockID(ticker="MOCK111", name="Company 111"),
            "CUSIP112": sec_types.StockID(ticker="MOCK112", name="Company 112"),
            "CUSIP113": sec_types.StockID(ticker="MOCK113", name="Company 113"),
            "CUSIP212": sec_types.StockID(ticker="MOCK212", name="Company 212"),
        }

        firms = {"FirmA": sec_types.FirmID(cik="0001111111")}
        funds = {
            "FundB": sec_types.ETFOrMutualFundID(
                cik="0002222222", series_id="S1", class_id="C1"
            )
        }
        cusip_patches = {
            "CUSIP211": sec_types.StockID(ticker="PATCH211", name="Patch 211")
        }

        result = parse_holdings.get_all_holdings_from_downloaded_files(
            download_dir="/tmp/download",
            target_period="20231231",
            firms=firms,
            etfs_and_mutual_funds=funds,
            cusip_patches=cusip_patches,
        )

        # Holdings results should be combined and sorted.
        self.assertIn("FirmA", result)
        self.assertEqual(result["FirmA"].holdings[0].cusip, "CUSIP113")
        self.assertEqual(result["FirmA"].holdings[0].value, 125)
        self.assertEqual(
            result["FirmA"].holdings[0].holding_type,
            sec_types.HoldingType.SHARE,
        )
        self.assertEqual(result["FirmA"].holdings[0].weight, 125 / 275 * 100)
        self.assertEqual(result["FirmA"].holdings[0].stock_id.ticker, "MOCK113")
        self.assertEqual(
            result["FirmA"].holdings[0].stock_id.name, "Company 113"
        )
        self.assertEqual(result["FirmA"].holdings[1].cusip, "CUSIP111")
        self.assertEqual(result["FirmA"].holdings[1].value, 100)
        self.assertEqual(
            result["FirmA"].holdings[1].holding_type,
            sec_types.HoldingType.SHARE,
        )
        self.assertEqual(result["FirmA"].holdings[1].weight, 100 / 275 * 100)
        self.assertEqual(result["FirmA"].holdings[1].stock_id.ticker, "MOCK111")
        self.assertEqual(
            result["FirmA"].holdings[1].stock_id.name, "Company 111"
        )
        self.assertEqual(result["FirmA"].holdings[2].cusip, "CUSIP112")
        self.assertEqual(result["FirmA"].holdings[2].value, 50)
        self.assertEqual(
            result["FirmA"].holdings[2].holding_type,
            sec_types.HoldingType.SHARE,
        )
        self.assertEqual(result["FirmA"].holdings[2].weight, 50 / 275 * 100)
        self.assertEqual(result["FirmA"].holdings[2].stock_id.ticker, "MOCK112")
        self.assertEqual(
            result["FirmA"].holdings[2].stock_id.name, "Company 112"
        )

        self.assertIn("FundB", result)
        self.assertEqual(result["FundB"].holdings[0].cusip, "CUSIP212")
        self.assertEqual(result["FundB"].holdings[0].value, 600)
        self.assertEqual(
            result["FundB"].holdings[0].holding_type,
            sec_types.HoldingType.SHARE,
        )
        self.assertEqual(result["FundB"].holdings[0].weight, 600 / 1000 * 100)
        self.assertEqual(result["FundB"].holdings[0].stock_id.ticker, "MOCK212")
        self.assertEqual(
            result["FundB"].holdings[0].stock_id.name, "Company 212"
        )
        self.assertEqual(result["FundB"].holdings[1].cusip, "CUSIP211")
        self.assertEqual(result["FundB"].holdings[1].value, 400)
        self.assertEqual(
            result["FundB"].holdings[1].holding_type,
            sec_types.HoldingType.SHARE,
        )
        self.assertEqual(result["FundB"].holdings[1].weight, 400 / 1000 * 100)
        self.assertEqual(
            result["FundB"].holdings[1].stock_id.ticker, "PATCH211"
        )
        self.assertEqual(result["FundB"].holdings[1].stock_id.name, "Patch 211")


if __name__ == "__main__":
    absltest.main()

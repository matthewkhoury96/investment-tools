from absl.testing import absltest

from sec_utils import csv_utils
from sec_utils import sec_types


class CsvUtilsTest(absltest.TestCase):
    def test_create_top_n_holdings_csv(self):
        """Checks output CSV size and values."""
        # 4 holding files configured to pack 3 items per row max
        # This forces 2 block rows (Row 1: 2 items, Row 2: 1 item)
        holdings_names = ["FundA", "FundB", "FundC", "FundD", "FundE"]

        # Skip holdings data for FundD, it should just be blank in the final CSV.
        all_holdings = {
            "FundA": sec_types.HoldingList(
                file_path="a.xml",
                date="20231231",
                holdings=[
                    sec_types.Holding(
                        cusip="a1",
                        value=10,
                        weight=10,
                        stock_id=sec_types.StockID(
                            ticker="A1", name="Stock A1"
                        ),
                    ),
                    sec_types.Holding(
                        cusip="a2",
                        value=90,
                        weight=90,
                        stock_id=sec_types.StockID(
                            ticker="A2", name="Stock A2"
                        ),
                    ),
                ],
            ),
            "FundB": sec_types.HoldingList(
                file_path="b.xml",
                date="20230831",
                holdings=[
                    sec_types.Holding(
                        cusip="b1",
                        value=100,
                        weight=100,
                        stock_id=sec_types.StockID(
                            ticker="B1", name="Stock B1"
                        ),
                    ),
                ],
            ),
            "FundC": sec_types.HoldingList(
                file_path="c.xml",
                date="20231231",
                holdings=[
                    sec_types.Holding(
                        cusip="c1",
                        value=20,
                        weight=20,
                        stock_id=sec_types.StockID(
                            ticker="C1", name="Stock C1"
                        ),
                        holding_type=sec_types.HoldingType.PUT,
                    ),
                    sec_types.Holding(
                        cusip="c2",
                        value=18,
                        weight=18,
                        stock_id=sec_types.StockID(
                            ticker="C2", name="Stock C2"
                        ),
                        holding_type=sec_types.HoldingType.CALL,
                    ),
                    sec_types.Holding(
                        cusip="c3",
                        value=12,
                        weight=12,
                        stock_id=sec_types.StockID(
                            ticker="C3", name="Stock C3"
                        ),
                    ),
                ],
            ),
            "FundE": sec_types.HoldingList(
                file_path="e.xml",
                date="20231231",
                holdings=[
                    sec_types.Holding(
                        cusip="e1",
                        value=15.15,
                        weight=15.15,
                        stock_id=sec_types.StockID(
                            ticker="E1", name="Stock E1"
                        ),
                    ),
                    sec_types.Holding(
                        cusip="e2",
                        value=14.14,
                        weight=14.14,
                        stock_id=sec_types.StockID(
                            ticker="E2", name="Stock E2"
                        ),
                    ),
                    sec_types.Holding(
                        cusip="e3",
                        value=13,
                        weight=13,
                        stock_id=sec_types.StockID(
                            ticker="E3", name="Stock E3"
                        ),
                    ),
                ],
            ),
        }

        # Calculations:
        # rows_per_holding = 4 + top_n(2) + blank_inside(1) = 7 rows
        # block_rows = ceil(5 / 3) = 2 blocks
        # total_rows = header(2) + (7 * 2) + after_holding(2) = 18 rows
        # total_columns = (3 * 3) + column_spacing(1 * 2) = 11 columns
        matrix = csv_utils.create_top_n_holdings_csv(
            holdings_names=holdings_names,
            all_holdings=all_holdings,
            top_n=2,
            csv_blank_header_rows=2,
            csv_blank_columns_between_holdings=1,
            csv_blank_rows_inside_holding=1,
            csv_blank_rows_after_holding=2,
            csv_holdings_per_row=3,
        )

        self.assertEqual(len(matrix), 18)  # Total expected rows
        self.assertEqual(len(matrix[0]), 11)  # Total expected columns

        # Check the contents. Use a helper function so we can keep track
        # of which cells we check. At the end we will make sure all the
        # remaining cells are empty.
        cells_checked = set()

        def _check_cell(i: int, j: int, val: str) -> None:
            cells_checked.add((i, j))
            self.assertEqual(matrix[i][j], val)

        # FundA should start at [2][0]
        _check_cell(2, 0, "FundA")
        _check_cell(3, 0, "(December 31, 2023)")
        _check_cell(4, 0, "Ticker")
        _check_cell(4, 1, "Name")
        _check_cell(4, 2, "Weight")
        _check_cell(5, 0, "A1")
        _check_cell(5, 1, "Stock A1")
        _check_cell(5, 2, "10.00%")
        _check_cell(6, 0, "A2")
        _check_cell(6, 1, "Stock A2")
        _check_cell(6, 2, "90.00%")
        _check_cell(8, 1, "Top 2 Total %")
        _check_cell(8, 2, "100.00%")

        # FundB should start at [2][4]
        # FundB only has 1 stock
        _check_cell(2, 4, "FundB")
        _check_cell(3, 4, "(August 31, 2023)")
        _check_cell(4, 4, "Ticker")
        _check_cell(4, 5, "Name")
        _check_cell(4, 6, "Weight")
        _check_cell(5, 4, "B1")
        _check_cell(5, 5, "Stock B1")
        _check_cell(5, 6, "100.00%")
        _check_cell(8, 5, "Top 2 Total %")
        _check_cell(8, 6, "100.00%")

        # FundC should start at [2][8]
        _check_cell(2, 8, "FundC")
        _check_cell(3, 8, "(December 31, 2023)")
        _check_cell(4, 8, "Ticker")
        _check_cell(4, 9, "Name")
        _check_cell(4, 10, "Weight")
        _check_cell(5, 8, "C1 (PUT)")
        _check_cell(5, 9, "Stock C1")
        _check_cell(5, 10, "20.00%")
        _check_cell(6, 8, "C2 (CALL)")
        _check_cell(6, 9, "Stock C2")
        _check_cell(6, 10, "18.00%")
        _check_cell(8, 9, "Top 2 Total %")
        _check_cell(8, 10, "38.00%")

        # FundD should start at [11][0]
        _check_cell(11, 0, "FundD")
        _check_cell(12, 0, "N/A")

        # FundE should start at [11][4]
        _check_cell(11, 4, "FundE")
        _check_cell(12, 4, "(December 31, 2023)")
        _check_cell(13, 4, "Ticker")
        _check_cell(13, 5, "Name")
        _check_cell(13, 6, "Weight")
        _check_cell(14, 4, "E1")
        _check_cell(14, 5, "Stock E1")
        _check_cell(14, 6, "15.15%")
        _check_cell(15, 4, "E2")
        _check_cell(15, 5, "Stock E2")
        _check_cell(15, 6, "14.14%")
        _check_cell(17, 5, "Top 2 Total %")
        _check_cell(17, 6, "29.29%")

        # Remaining cells should be empty
        for i in range(18):
            for j in range(11):
                if (i, j) not in cells_checked:
                    self.assertEqual(matrix[i][j], "")


if __name__ == "__main__":
    absltest.main()

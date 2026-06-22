import datetime
import math
import typing

from sec_utils import sec_types


def _add_holding_to_output_csv(
    name: str,
    holding_list: sec_types.HoldingList,
    output_csv: list[list[str]],
    i: int,
    j: int,
    top_n: int,
    csv_blank_rows_inside_holding: int,
) -> None:
    # Add the name in the first row, first column.
    output_csv[i][j] = name

    # If the holding_list is empty, add N/A for the date and return early.
    if not holding_list.holdings:
        output_csv[i + 1][j] = "N/A"
        return

    # Add the formatted date in the second row, first column.
    date_obj = datetime.datetime.strptime(holding_list.date, "%Y%m%d")
    formatted_date = date_obj.strftime("%B %d, %Y")
    output_csv[i + 1][j] = f"({formatted_date})"

    # Add the Ticker, Name, Weight titles to the third row.
    output_csv[i + 2][j] = "Ticker"
    output_csv[i + 2][j + 1] = "Name"
    output_csv[i + 2][j + 2] = "Weight"

    # Add the top_n holdings, computing the top_n total percent.
    # The actual holdings start on the fourth row.
    top_n_total_percent = 0
    for holding_index, holding in enumerate(holding_list.holdings[:top_n]):
        ticker = holding.stock_id.ticker
        if holding.holding_type != sec_types.HoldingType.SHARE:
            ticker += f" ({holding.holding_type.name})"
        output_csv[i + 3 + holding_index][j] = ticker
        output_csv[i + 3 + holding_index][j + 1] = holding.stock_id.name
        output_csv[i + 3 + holding_index][j + 2] = f"{holding.weight:.2f}%"
        top_n_total_percent += holding.weight

    # At the very bottom, add the top_n total percentage. The last row is
    # at index i + 3 + top_n + csv_blank_rows_inside_holding because.
    last_row_index = i + 3 + top_n + csv_blank_rows_inside_holding
    output_csv[last_row_index][j + 1] = f"Top {top_n} Total %"
    output_csv[last_row_index][j + 2] = f"{top_n_total_percent:.2f}%"


def create_top_n_holdings_csv(
    holdings_names: list[str],
    all_holdings: typing.Mapping[str, sec_types.HoldingList],
    top_n: int,
    csv_blank_header_rows: int,
    csv_blank_columns_between_holdings: int,
    csv_blank_rows_inside_holding: int,
    csv_blank_rows_after_holding: int,
    csv_holdings_per_row: int,
) -> list[list[str]]:
    # Create an empty CSV (using a list[list[str]]) of the appropriate size

    # Each holding has
    #   * 1 row for the name
    #   * 1 row for the date
    #   * 1 row for the headers "Ticker, Name, Weight"
    #   * top_n rows for the top n holdings
    #   * csv_blank_rows_inside_holding blank rows
    #   * 1 row at the bottom for the top_n total percentage
    rows_per_holding = 4 + top_n + csv_blank_rows_inside_holding

    # The CSV is divided up into 'block rows' each containing
    # csv_holdings_per_row holdings.
    block_rows = math.ceil(len(holdings_names) / csv_holdings_per_row)

    # Total number of rows is the addition of all these
    #  * csv_blank_header_rows
    #  * rows_per_holding * block_rows
    #  * csv_blank_rows_after_holding * (block_rows - 1)
    total_rows = (
        csv_blank_header_rows
        + (rows_per_holding * block_rows)
        + (csv_blank_rows_after_holding * (block_rows - 1))
    )

    # Each holding takes up 3 colums. So the total number of columns is
    # the addition of all of these
    #  * (3 * csv_holdings_per_row)
    #  * csv_blank_columns_between_holdings * (csv_holdings_per_row- 1)
    total_columns = (3 * csv_holdings_per_row) + (
        csv_blank_columns_between_holdings * (csv_holdings_per_row - 1)
    )

    output_csv = [["" for j in range(total_columns)] for i in range(total_rows)]

    # Use i and j to track the top left corner index of each holding. We update
    # both i and j after adding each holding to the output_csv.
    i = csv_blank_header_rows
    j = 0
    for name in holdings_names:
        holding_list = all_holdings.get(
            name, sec_types.HoldingList(file_path="", date="")
        )
        _add_holding_to_output_csv(
            name,
            holding_list,
            output_csv,
            i,
            j,
            top_n,
            csv_blank_rows_inside_holding,
        )

        # Try to keep moving (i, j) to the right after each holding.
        # If we go too far out of bounds, move (i, j) down to the next 'block row'.
        j += 3 + csv_blank_columns_between_holdings
        if j >= total_columns:
            i += rows_per_holding + csv_blank_rows_after_holding
            j = 0

    return output_csv

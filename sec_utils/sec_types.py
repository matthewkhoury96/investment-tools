import dataclasses
import enum


@dataclasses.dataclass(frozen=True)
class FirmID:
    cik: str


@dataclasses.dataclass(frozen=True)
class ETFOrMutualFundID:
    cik: str
    series_id: str
    class_id: str


@dataclasses.dataclass(frozen=True)
class StockID:
    ticker: str = ""
    name: str = ""


class HoldingType(enum.Enum):
    SHARE = 1
    PUT = 2
    CALL = 3


@dataclasses.dataclass
class Holding:
    cusip: str
    value: float
    holding_type: HoldingType = HoldingType.SHARE
    weight: float = 0.0
    stock_id: StockID = StockID()


@dataclasses.dataclass
class HoldingList:
    file_path: str
    date: str
    holdings: list[Holding] = dataclasses.field(default_factory=list)

    def _combine_duplicate_holdings(self) -> None:
        combined_holdings = dict()

        for holding in self.holdings:
            key = (holding.cusip, holding.holding_type)
            if key in combined_holdings:
                combined_holdings[key].value += holding.value
            else:
                combined_holdings[key] = dataclasses.replace(holding)

        self.holdings = list(combined_holdings.values())

    def calculate_weights_and_sort_holdings(self) -> None:
        self._combine_duplicate_holdings()
        total_value = sum(holding.value for holding in self.holdings)
        for holding in self.holdings:
            holding.weight = (holding.value / total_value) * 100
        self.holdings.sort(key=lambda holding: holding.weight, reverse=True)

    def get_all_cusips(self) -> set[str]:
        return set(holding.cusip for holding in self.holdings)

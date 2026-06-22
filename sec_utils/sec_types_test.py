from absl.testing import absltest

from sec_utils import sec_types


class SecTypesTest(absltest.TestCase):
    def test_calculate_weights_and_sort_holdings(self):
        holding_1 = sec_types.Holding(
            cusip="CUSIP111",
            value=100.0,
            holding_type=sec_types.HoldingType.CALL,
        )
        holding_2 = sec_types.Holding(
            cusip="CUSIP111",
            value=50.0,
            holding_type=sec_types.HoldingType.CALL,
        )
        holding_3 = sec_types.Holding(
            cusip="CUSIP111",
            value=30.0,
            holding_type=sec_types.HoldingType.PUT,
        )
        holding_4 = sec_types.Holding(
            cusip="CUSIP222",
            value=20.0,
            holding_type=sec_types.HoldingType.SHARE,
        )
        holding_5 = sec_types.Holding(
            cusip="CUSIP333",
            value=1000.0,
            holding_type=sec_types.HoldingType.SHARE,
        )
        holding_6 = sec_types.Holding(
            cusip="CUSIP222",
            value=40.0,
            holding_type=sec_types.HoldingType.SHARE,
        )

        holding_list = sec_types.HoldingList(
            file_path="test.xml",
            date="20231231",
            holdings=[
                holding_1,
                holding_2,
                holding_3,
                holding_4,
                holding_5,
                holding_6,
            ],
        )

        holding_list.calculate_weights_and_sort_holdings()

        # Should combine 6 elements down to 4
        self.assertEqual(len(holding_list.holdings), 4)

        self.assertEqual(holding_list.holdings[0].cusip, "CUSIP333")
        self.assertEqual(holding_list.holdings[0].value, 1000)
        self.assertEqual(
            holding_list.holdings[0].holding_type, sec_types.HoldingType.SHARE
        )
        self.assertEqual(holding_list.holdings[0].weight, 1000 / 1240 * 100)

        self.assertEqual(holding_list.holdings[1].cusip, "CUSIP111")
        self.assertEqual(holding_list.holdings[1].value, 150)
        self.assertEqual(
            holding_list.holdings[1].holding_type, sec_types.HoldingType.CALL
        )
        self.assertEqual(holding_list.holdings[1].weight, 150 / 1240 * 100)

        self.assertEqual(holding_list.holdings[2].cusip, "CUSIP222")
        self.assertEqual(holding_list.holdings[2].value, 60)
        self.assertEqual(
            holding_list.holdings[2].holding_type, sec_types.HoldingType.SHARE
        )
        self.assertEqual(holding_list.holdings[2].weight, 60 / 1240 * 100)

        self.assertEqual(holding_list.holdings[3].cusip, "CUSIP111")
        self.assertEqual(holding_list.holdings[3].value, 30)
        self.assertEqual(
            holding_list.holdings[3].holding_type, sec_types.HoldingType.PUT
        )
        self.assertEqual(holding_list.holdings[3].weight, 30 / 1240 * 100)

    def test_get_all_cusips(self):
        holdings = [
            sec_types.Holding(cusip="CUSIP_A", value=10.0),
            sec_types.Holding(cusip="CUSIP_B", value=20.0),
            sec_types.Holding(cusip="CUSIP_A", value=30.0),
            sec_types.Holding(cusip="CUSIP_C", value=50.0),
            sec_types.Holding(cusip="CUSIP_C", value=40.0),
            sec_types.Holding(cusip="CUSIP_D", value=60.0),
        ]
        holding_list = sec_types.HoldingList(
            file_path="test.xml", date="20231231", holdings=holdings
        )

        cusips = holding_list.get_all_cusips()
        self.assertEqual(cusips, {"CUSIP_A", "CUSIP_B", "CUSIP_C", "CUSIP_D"})


if __name__ == "__main__":
    absltest.main()

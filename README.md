# Investment Tools

## Download, Build, and Test

Download with

```sh
git clone https://github.com/matthewkhoury96/investment-tools.git
```

The files in this repository are intended to be built, tested, and run with [bazel](https://bazel.build/).
It is recommended to simply install [bazelisk](https://bazel.build/install/bazelisk) and use that to run bazel (as it will pick up the version from the `.bazelversion` file).

All code can be built and tested with

```sh
bazel build //...
bazel test //...
```

## Tool to Download, Parse, and Print Holdings

The main runfile to download, parse, and print holdings is `sec_utils/download_and_print_holdings.py`. By default, it will download, parse, and print the top 10 holdings for all of the firms, mutual funds, and ETFs defined in the file.

Flags

- `--firm_name` (repeatable) filters the firms defined in `sec_utils/download_and_print_holdings.py`.
- `--etf_name` (repeatable) filters the ETFs defined in `sec_utils/download_and_print_holdings.py`.
- `--mutual_fund_name` (repeatable) filters the mutual funds defined in `sec_utils/download_and_print_holdings.py`.
- `--period` specifies the end-of-quarter date in format `YYYYMMDD`.
- `--top_n` specifies top number of holdings to print for each firm, ETF, and mutual fund (default value is 10).
- `--output_file` specifies the file where results will be saved. If not provided, the results will be printed directly to the terminal.

Note that if `--firm_name`, `--etf_name`, and/or `--mutual_fund_name` are specified, all the output results will be filtered.

Example usage:

```sh
bazel run //sec_utils:download_and_print_holdings -- \
  --period=20260331 \
  --output_file=$HOME/Downloads/holdings.csv
```

```sh
bazel run //sec_utils:download_and_print_holdings -- \
  --period=20260331 \
  --etf_name="VANGUARD DIVIDEND GROWTH FUND" \
  --firm_name="WCM INVESTMENT MANAGEMENT, LLC" \
  --firm_name="DUQUESNE FAMILY OFFICE LLC" \
  --firm_name="SITUATIONAL AWARENESS PARTNERS LP"
```

```sh
bazel run //sec_utils:download_and_print_holdings -- \
  --period=20260331 \
  --firm_name="WCM INVESTMENT MANAGEMENT, LLC" \
  --top_n=200
```

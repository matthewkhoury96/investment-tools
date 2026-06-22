# Investment Tools

## Download, Build, and Test

Download with

```
git clone https://github.com/matthewkhoury96/investment-tools.git
```

This files in this repository are intended to be built, tested, and run with [bazel](https://bazel.build/).
It is recommended to simply install [bazelisk](https://bazel.build/install/bazelisk) and use that to run bazel (as it will pick up the version from the `.bazelversion` file).

All code can be built and tested with

```
bazel build //...
bazel test //...
```

## Tool to Download, Parse, and Print Holdings

The main runfile to download, parse, and print holdings is `sec_utils/download_and_print_holdings.py`. By default, it will download, parse, and print data for all of the firms, mutual funds, and ETFs defined in the file. By default, the top 10 holdings will be printed.

Firms, mutual funds, and ETFs can be filtered with the `--firm_name` , `--etf_name`, and `mutual_fund_name` flags. You can print more or less than 10 holdings by changing the `--top_n` flag.

Specify the end-of-quarter date with the `--period` flag in format `YYYYMMDD`.

If an output file is specified with the `--output_file` flag, the results will be saved to that file. Otherwise, results will be printed directly to the terminal.

Example usage:

```
bazel run //sec_utils:download_and_print_holdings -- \
  --period=20260331 \
  --output_file=$HOME/Downloads/holdings.csv
```

```
bazel run //sec_utils:download_and_print_holdings -- \
  --period=20260331 \
  --etf_name="VANGUARD DIVIDEND GROWTH FUND" \
  --firm_name="WCM INVESTMENT MANAGEMENT, LLC" \
  --firm_name="DUQUESNE FAMILY OFFICE LLC" \
  --firm_name="SITUATIONAL AWARENESS PARTNERS LP"
```

```
blaze run //sec_utils:download_and_print_holdings -- \
  --period=20260331
  --firm_name="WCM INVESTMENT MANAGEMENT, LLC"
  --top_n=200
```

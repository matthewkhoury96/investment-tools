load("@rules_python//python:defs.bzl", "py_binary", "py_library", "py_test")
load("@pip_deps//:requirements.bzl", "requirement")

py_library(
    name = "sec_types",
    srcs = ["sec_types.py"],
)

py_test(
    name = "sec_types_test",
    srcs = ["sec_types_test.py"],
    deps = [
        ":sec_types",
        requirement("absl-py"),
    ],
)

py_library(
    name = "download_holdings",
    srcs = ["download_holdings.py"],
    deps = [
        ":sec_types",
        requirement("sec-edgar-downloader"),
    ],
)

py_test(
    name = "download_holdings_test",
    srcs = ["download_holdings_test.py"],
    deps = [
        ":download_holdings",
        ":sec_types",
        requirement("absl-py"),
    ],
)

py_library(
    name = "parse_holdings",
    srcs = ["parse_holdings.py"],
    deps = [
        ":sec_types",
        requirement("numpy"),
        requirement("requests"),
    ],
)

py_test(
    name = "parse_holdings_test",
    srcs = ["parse_holdings_test.py"],
    data = ["//sec_utils/testdata"],
    deps = [
        ":parse_holdings",
        ":sec_types",
        requirement("absl-py"),
    ],
)

py_library(
    name = "csv_utils",
    srcs = ["csv_utils.py"],
    deps = [
        ":sec_types",
    ],
)

py_test(
    name = "csv_utils_test",
    srcs = ["csv_utils_test.py"],
    deps = [
        ":csv_utils",
        ":sec_types",
        requirement("absl-py"),
    ],
)

py_binary(
    name = "download_and_print_holdings",
    srcs = ["download_and_print_holdings.py"],
    deps = [
        ":csv_utils",
        ":download_holdings",
        ":parse_holdings",
        ":sec_types",
        requirement("absl-py"),
    ],
)

py_test(
    name = "download_and_print_holdings_test",
    srcs = ["download_and_print_holdings_test.py"],
    deps = [
        ":download_and_print_holdings",
        requirement("absl-py"),
    ],
)

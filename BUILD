load("@rules_python//python:pip.bzl", "compile_pip_requirements")

# This target auto-generates your lockfile for Bazel
compile_pip_requirements(
    name = "requirements",
    src = "requirements.in",
    requirements_txt = "requirements.txt",
)

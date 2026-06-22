import hashlib
import os
import subprocess


_HOME_DIR = os.environ["HOME"]
_USER_NAME = os.environ["USER"]
_THIS_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
_BAZEL_OS_PREFIX = {
    "Darwin": f"{_HOME_DIR}/Library/Caches/bazel",
    "Linux": f"{_HOME_DIR}/.cache/bazel",
}


def get_os():
    # Run uname and try to find an OS In _BAZEL_OS_PREFIX.
    process = subprocess.run(["uname"], capture_output=True)
    for os_name in _BAZEL_OS_PREFIX:
        if os_name in str(process.stdout):
            return os_name

    raise RuntimeError("Did not find a supported OS")


def get_bazel_external_path():
    # See (https://bazel.build/remote/output-directories#layout)
    # for more information about bazel output directory layout.
    bazel_prefix = _BAZEL_OS_PREFIX.get(get_os(), None)
    if bazel_prefix is None:
        raise RuntimeError("Unable to determine bazel prefix")

    project_dir_md5_hash = hashlib.md5(_THIS_FILE_DIR.encode("utf-8")).hexdigest()

    bazel_external_path = [
        bazel_prefix,
        f"_bazel_{_USER_NAME}",
        project_dir_md5_hash,
        "external",
    ]

    return os.path.join(*bazel_external_path)


def get_bazel_python_interpreter_path():
    bazel_external_path = get_bazel_external_path()

    # Look for the modern rules_python hermetic toolchain interpreter
    for dirpath, _, filenames in os.walk(bazel_external_path, followlinks=True):
        dirname = os.path.basename(dirpath)
        if dirname == "bin" and "python3" in filenames and "rules_python" in dirpath:
            return os.path.join(dirpath, "python3")

    raise RuntimeError("Could not find Python interpreter path")


def get_bazel_python_deps_paths():
    bazel_external_path = get_bazel_external_path()

    # Get all site-packages directories that are installed by pip.
    python_deps_paths = []
    for dirpath, _, _ in os.walk(bazel_external_path, followlinks=True):
        dirname = os.path.basename(dirpath)

        # Skip bazel-out and bazel-bin artifacts
        if "bazel-out" in dirpath or "bazel-bin" in dirpath:
            continue

        if dirname == "site-packages" and "pip_deps" in dirpath:
            python_deps_paths.append(dirpath)

    return python_deps_paths


def Settings(**kwargs):
    return {
        "interpreter_path": get_bazel_python_interpreter_path(),
        "sys_path": get_bazel_python_deps_paths(),
    }

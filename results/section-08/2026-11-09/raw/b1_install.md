# B1: how each library is installed for iOS and macOS, 2026-11-09

**Source and Measured.**
- **Measured:** PyPI's files and the kivy-mobile-wheels index were read on 2026-11-09 at 23:29 UTC by [`pypi_files.py`](../../../../tests/section-08/pypi_files.py), into `b1_pypi.json`. The builds are this section's own, for M1.
- **Source:** kivy-ios at `fd363d4` and KivyForge at the baseline's `a36c2cc`.
- **Author's projects:** KivyForge and kivy-mobile-wheels are the comparison author's.

## Summary

| | pyobjus | Rubicon |
|---|---|---|
| Needs compiling | Yes: a Cython extension, built for each Python version and platform, linked against libffi (Section 5, claim 16) | No: pure Python, one wheel |
| Latest release on PyPI | 1.2.4, 29 December 2025: an sdist and 11 wheels | 0.5.7, 30 September 2026: an sdist and 1 wheel, `py3-none-any`, for Python 3.11 and later |
| macOS wheels on PyPI | Python 3.10 to 3.14, `universal2` | The one wheel |
| iOS wheels on PyPI | Python 3.13 and 3.14: `arm64` device, `arm64` and `x86_64` simulator | The one wheel |
| Python 3.15, or free-threaded builds | No wheel on PyPI. kivy-mobile-wheels has `cp315` iOS wheels for 1.2.4 and `1.2.5.dev202610250845`; macOS 3.15 needs a source build | The one wheel |
| kivy-ios | Its [`pyobjus` recipe](https://github.com/kivy/kivy-ios/blob/fd363d49eddb5ac06766348738bd89c7d46007f8/kivy_ios/recipes/pyobjus/__init__.py) compiles `master` from GitHub with Cython, on kivy-ios's Python 3.11.6, as a static library. The `kivy` and `plyer` recipes depend on it (M3) | No recipe needed. kivy-ios installs pure-Python packages with [`toolchain pip install`](https://github.com/kivy/kivy-ios/blob/fd363d49eddb5ac06766348738bd89c7d46007f8/README.md#L115). Not tested here for Rubicon |
| KivyForge, `a36c2cc` | Installed from wheels, like any dependency. With its default Python, 3.15.0, there's no pyobjus wheel on PyPI. `kivyforge init` writes the kivy-mobile-wheels index into a new project's `extra_index_urls`, commented as "first-party iOS wheels for kivy and pyobjus". If a lock fails without that index, the error suggests adding it for kivy or pyobjus | Installed from PyPI's wheel, like any pure-Python dependency |

## This section's own builds

- **Mac:** both pyobjus versions were built from source with Cython 3.3.1, `pip install --no-build-isolation .`, into Python 3.14.7. Rubicon 0.5.7 was installed from PyPI, and `main` from its source with `pip install`.
- **iPhone, Python 3.15:**
  - **pyobjus:** both versions were compiled by Section 2's [`build_wheels.sh`](../../../../tests/section-02/ios/build_wheels.sh). That script builds libffi 3.5.2 from pyobjus's own script and reruns `xcodebuild` with a 16.0 target, because Xcode 27 refuses the libffi project's iOS 8.0 target. It then runs Cython and compiles and links one wheel for the device and one for the simulator.
  - **Rubicon:** 0.5.7 came from PyPI unchanged, and `main` was built as a pure wheel with `uv build`.
  - **KivyForge:** it locked and installed all four from those wheels. Its install step rejects a percent-encoded `+` in a version, so Rubicon `main` was built as `0.5.8.dev21`, with no local version segment.
- **kivy-mobile-wheels:** M1's apps didn't use its wheels.

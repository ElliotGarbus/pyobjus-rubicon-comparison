# Section 3 tests

Each case runs in its own process, so a crash or hang is recorded and doesn't stop the run. Each library has its own file of cases, written with that library's public API as its docs show, so the same case can look different in each.

- `cases.py`: every case, its F row, what it checks and its expected value
- `cases_pyobjus.py`, `cases_rubicon.py`: the cases for each library
- `cases_pyobjc.py`: the PyObjC control, on the Mac only
- `s3fixture.m`: the Objective-C fixture, compiled with ARC
- `s3extra.m`: a dylib that F1.6 loads at runtime
- `S3Swift.swift`: the Swift library for F7
- `run_one.py`, `run_all.py`: run cases, 5 times each by default
- `headers.py`: A1, A2 and A4, the count of each SDK's public Objective-C API
- `reach.py`: matches each declaration's kinds to the measured cases
- `crosscheck.py`: A3, the comparison with BridgeSupport on macOS
- `ios/`: the iPhone build and runner

A case ID ending in `__ctypes` or `__helper` is the workaround for the case without the suffix, written only where the library can't do that case itself.

## Results

Each run gives one of these outcomes:

| Outcome | Meaning |
|---|---|
| correct | The case returned the expected value |
| wrong value | It returned something else, shown in the detail |
| python exception | Python raised, shown in the detail |
| not expressible | The library has no public way to write the case, with the reason |
| not applicable | The case tests something this library doesn't need to do |
| crash, hang, exited | The process died, ran past 30 seconds, or exited without a result |

The outcome is compared strictly: `False` doesn't match `0`.

## Rerun on a Mac

Use the Python environments from [Section 2's tests](../section-02/README.md), at the versions in [the baseline](../../results/baseline/2026-11-04.md). `BUILD` is an empty folder. From the repository root:

```bash
xcrun --sdk macosx clang -dynamiclib -arch arm64 -fobjc-arc -framework Foundation -framework CoreGraphics tests/section-03/s3fixture.m -o BUILD/libs3fixture.dylib
```

```bash
xcrun --sdk macosx clang -dynamiclib -arch arm64 -fobjc-arc -framework Foundation tests/section-03/s3extra.m -o BUILD/libs3extra.dylib
```

```bash
xcrun --sdk macosx swiftc -emit-library -module-name S3Swift -target arm64-apple-macos13 tests/section-03/S3Swift.swift -o BUILD/libS3Swift.dylib
```

```bash
python tests/section-03/run_all.py mac.json BUILD pyobjus-main=pyobjus=PATH/TO/python rubicon-main=rubicon=PATH/TO/python pyobjc-13.0=pyobjc=PATH/TO/python
```

Set `S3_ONLY` to a comma-separated list of case prefixes to run only those, and `S3_RUNS` to change the number of runs. A rerun skips cases already in the output file unless `S3_ONLY` is set.

## Count the SDK headers

```bash
python tests/section-03/headers.py macosx arm64-apple-macos26.6 macos 26.6.2 headers_mac.json
```

```bash
python tests/section-03/headers.py iphoneos arm64-apple-ios27.0 ios 27.0.1 headers_ios.json
```

Add framework names at the end to read only those. Each declaration is listed with the kinds of value its signature needs. A framework without an umbrella header is read by importing each of its headers.

`reach.py` then matches the kinds to the case results, using the Mac results for macOS and the iPhone results for iOS, with Section 2's results for the kinds Section 2 tested. The table at the top of the script lists which cases decide each kind:

```bash
python tests/section-03/reach.py headers_mac.json mac.json results/section-02/2026-11-04/raw/mac.json reach_mac.json
```

```bash
python tests/section-03/crosscheck.py headers_mac.json crosscheck_mac.json
```

## Rerun on an iPhone

You need what [Section 2's iPhone steps](../section-02/README.md#rerun-on-an-iphone) need, and the iOS wheels they build. `WORK` is an empty folder and `WHEELS` is Section 2's `WORK/wheels`.

```bash
tests/section-03/ios/build_frameworks.sh WORK
```

Then, for `release` and `main`:

```bash
python tests/section-03/ios/make_project.py WORK WHEELS release
```

```bash
cd WORK/apps/release && kivyforge lock -p ios && KIVYFORGE_TEAM_ID=YOUR_TEAM kivyforge build -p ios --device
```

```bash
xcrun devicectl device install app --device DEVICE WORK/apps/release/s3-release-ios/build/DerivedData/Build/Products/Debug-iphoneos/s3-release.app
```

Finally, from the repository root:

```bash
python tests/section-03/ios/run_device.py iphone.json DEVICE pyobjus-main=pyobjus=org.comparison.s3-main rubicon-main=rubicon=org.comparison.s3-main pyobjus-1.2.4=pyobjus=org.comparison.s3-release rubicon-0.5.7=rubicon=org.comparison.s3-release
```

The Swift library is built by KivyForge as a local package. The F1.6 library is embedded in the app but not linked, so it isn't loaded until the case loads it. A rerun skips cases already in the output file.

# Section 2 tests

Each scenario runs in its own process, so a crash or hang is recorded and doesn't stop the run. The same scenarios run against every library, through one small adapter per library.

- `s2fixture.m`: the shared Objective-C fixture, compiled without ARC
- `adapters.py`: how each library expresses the shared operations, using public APIs
- `scenarios.py`: the scenarios and their expected results
- `run_one.py`, `run_all.py`: run scenarios, 5 times each by default
- `gil_status.py`: TH5, whether importing a library enables the GIL
- `t5_select.py`, `t5_one.py`, `t5_run.py`: the BridgeSupport sample and its check
- `t5_calls.py`, `t5_call_run.py`: T5's calling step. `t5_truth.m` makes the less obvious calls in Objective-C for the expected values
- `ios/`: the iPhone build and runner

## Rerun on a Mac

Create one Python 3.14 environment per library, with the versions in [the baseline](../../results/baseline/2026-11-04.md). Then, from the repository root:

```bash
xcrun --sdk macosx clang -dynamiclib -arch arm64 -fno-objc-arc -fobjc-weak -framework Foundation -framework CoreGraphics tests/section-02/s2fixture.m -o libs2fixture.dylib
```

```bash
python tests/section-02/run_all.py mac.json libs2fixture.dylib pyobjus-main=pyobjus=PATH/TO/python rubicon-main=rubicon=PATH/TO/python pyobjc-13.0=pyobjc=PATH/TO/python
```

Set `S2_ONLY` to a comma-separated list of scenario prefixes to run only those, and `S2_RUNS` to change the number of runs.

To run T5's calling step:

```bash
python tests/section-02/t5_call_run.py results/section-02/2026-11-04/raw/t5_sample.json t5_calls.json pyobjus-main=pyobjus=PATH/TO/python rubicon-main=rubicon=PATH/TO/python pyobjc-13.0=pyobjc=PATH/TO/python
```

The PyObjC environment needs `pyobjc-framework-Cocoa`, `pyobjc-framework-CoreLocation` and `pyobjc-framework-UserNotifications`.

## Rerun on an iPhone

You need Xcode, a paired phone with Auto-Lock set to Never, [KivyForge](https://github.com/ElliotGarbus/kivyforge), and your own Apple team ID. `WORK` is an empty folder, and `PYOBJUS` and `RUBICON` are clones at the baseline commits.

```bash
tests/section-02/ios/build_wheels.sh WORK PYOBJUS RUBICON
```

```bash
tests/section-02/ios/build_fixture.sh WORK
```

Then, for `release` and `main`:

```bash
python tests/section-02/ios/make_project.py WORK release
```

```bash
cd WORK/apps/release && kivyforge lock -p ios && KIVYFORGE_TEAM_ID=YOUR_TEAM kivyforge build -p ios --device
```

```bash
xcrun devicectl device install app --device DEVICE WORK/apps/release/s2-release-ios/build/DerivedData/Build/Products/Debug-iphoneos/s2-release.app
```

Finally, from the repository root:

```bash
python tests/section-02/ios/run_device.py iphone.json DEVICE pyobjus-main=pyobjus=org.comparison.s2-main rubicon-main=rubicon=org.comparison.s2-main pyobjus-1.2.4=pyobjus=org.comparison.s2-release rubicon-0.5.7=rubicon=org.comparison.s2-release
```

A rerun skips scenarios already in the output file, so it resumes after a dropped connection.

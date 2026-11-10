# Section 8 results, 2026-11-09

The scripts are in [`tests/section-08`](../../../tests/section-08), and each one's docstring gives its usage. Metric IDs refer to the [approved definitions](../../../metrics/08-compatibility-and-migration.md). Each part's detail is in its file under `raw/`, linked below.

## Status

| Part | Status |
|---|---|
| U0 sample, U1 catalog, U2 patterns | Done: `raw/sample.json`, `raw/catalog.json`, `raw/patterns.json`, and [`raw/hand_notes.md`](raw/hand_notes.md) |
| M1 translations, Mac and iPhone | Done: [`raw/m1_translations.md`](raw/m1_translations.md), from `raw/m1_mac.json` and `raw/m1_iphone.json` |
| M2 Kivy and Plyer, file by file | Done: [`raw/m2_inventory.md`](raw/m2_inventory.md) |
| M3 changes outside the code | Done: [`raw/m3_build.md`](raw/m3_build.md) |
| B1 installing each library | Done: [`raw/b1_install.md`](raw/b1_install.md) |
| Claims 17 and 18 | Done: [`raw/claims17_18_kivy.md`](raw/claims17_18_kivy.md) |
| Claim 19 | Done: [`raw/claim19_plyer.md`](raw/claim19_plyer.md) |
| Section text | Draft: [`sections/08-compatibility-and-migration.md`](../../../sections/08-compatibility-and-migration.md) |

## Conditions

| | |
|---|---|
| Sample collected | 2026-11-09 18:02 UTC. Each repository was cloned at its default branch, and the commits are in `raw/sample.json` |
| Libraries | At [the baseline](../../baseline/2026-11-04.md): pyobjus 1.2.4 and `master` (`0c204ad`), built from source with Cython 3.3.1. Rubicon 0.5.7 from PyPI, and `main` (`6bf0639`) |
| Mac | macOS 26.6.2, Python 3.14.7 |
| iPhone | iPhone 18 Pro Max, iOS 27.0.1, Python 3.15.0. Apps built with KivyForge `a36c2cc`, the comparison author's project. pyobjus's iOS wheels were built by Section 2's `build_wheels.sh` |
| Runs | Each M1 case ran 5 times for each of the 4 library versions: in its own process on the Mac, one app launch per run on the iPhone |
| PyPI, GitHub and indexes | B1 was read at 2026-11-09 23:29 UTC, and claim 19 at 2026-11-10 00:48 UTC, still 9 November in US time zones |

## U0 and U1: the sample and where it uses pyobjus

U0 is the 10 repositories Section 7 counted as importing pyobjus with 50 or more stars, without gistable/gistable, which its hand check listed as a possible copy. Calls are counted in the files' iOS and macOS code. In files that also hold other platforms' code, that's the line ranges in [`regions.json`](../../../tests/section-08/regions.json).

| Repository | Stars | Files using pyobjus | pyobjus calls | Flat-form method calls | Platforms |
|---|---:|---:|---:|---:|---|
| [kivy/kivy](https://github.com/kivy/kivy) | 19,025 | 2 | 8 | 6 | iOS and macOS |
| [renpy/renpy](https://github.com/renpy/renpy) | 6,998 | 7 | 22 | 18 | iOS and macOS |
| [kivymd/KivyMD](https://github.com/kivymd/KivyMD) | 2,468 | 1 | 1 | 0 | iOS |
| [kivy/plyer](https://github.com/kivy/plyer) | 1,805 | 28 | 104 | 82 | iOS and macOS |
| [kivy/kivy-ios](https://github.com/kivy/kivy-ios) | 856 | 2 | 6 | 3 | iOS |
| [renpy/renpy-build](https://github.com/renpy/renpy-build) | 123 | 1 | 4 | 3 | iOS |
| [oskros/MF_run_counter](https://github.com/oskros/MF_run_counter) | 102 | 1 | 2 | 1 | macOS |
| [Carvera-Community/Carvera_Controller](https://github.com/Carvera-Community/Carvera_Controller) | 94 | 2 | 3 | 2 | iOS |
| [Dirk-Sandberg/Friendly-Fitness-App](https://github.com/Dirk-Sandberg/Friendly-Fitness-App) | 70 | 1 | 1 | 0 | iOS |
| [teticio/kivy-tensorflow-helloworld](https://github.com/teticio/kivy-tensorflow-helloworld) | 53 | 1 | 6 | 18 | iOS |
| **Total** | | **46** | **157** | **133** | |

"pyobjus calls" are calls of pyobjus's own API, such as `autoclass`, `load_framework` and `objc_str`. "Flat-form method calls" are Objective-C methods called with pyobjus's underscore names, such as `setObject_forKey_(...)`.

Classes that aren't Apple's, and the workarounds the code uses, are in [`raw/hand_notes.md`](raw/hand_notes.md). Plyer's six motion sensors use the `bridge` class from kivy-ios's Xcode template. Ren'Py's `IAPHelper`, `Log` and `Age` come from renpy-build.

## U2: use patterns

23 patterns, from `raw/patterns.json`, with each file that uses them.

| Feature | Pattern: repositories using it |
|---|---|
| Classes | load-class: 10. load-framework: 5 |
| Objects | alloc-init: 6 |
| Methods | selector-call: 8. property-or-method: 3 |
| Strings | objc-str: 3. utf8string: 3. bytes-check: 2 |
| Collections | nsarray-index: 4. objc-arr: 1. python-container-arg: 1 |
| Delegates | protocol-method: 3. delegate-self: 2. observer-self, protocol-register, selector, bool-return: 1 each |
| Blocks | completion-nil: 3 |
| Errors | error-arg: 3 |
| Structs | struct-field: 2 |
| Constants | enum: 1 |
| Memory | retain-release, raw-pointer: 1 each |

## M1: the Rubicon way to do each pattern

The full table, with the code on each side, is in [`raw/m1_translations.md`](raw/m1_translations.md). On the Mac, 18 cases ran, plus `m2_names`, which checks names for M2. On the iPhone, 13 portable cases ran, plus 5 iOS ones. Each case gave the same result in all 5 runs, except two, both pyobjus 1.2.4: `zero_arg` crashed in 2 of 5 Mac runs (1 of 5 on a rerun), and `observer_ios` read a keyboard height of 0.0 in 1 of 5 iPhone runs.

- **Unchanged:** the 133 flat-form method calls. Rubicon accepts pyobjus's underscore names.
- **Renamed:** `autoclass` becomes `ObjCClass`, and `load_framework` becomes `load_library`.
- **No longer needed:** `objc_str`, `objc_arr`, `enum`, hand-registered protocol encodings, and `ObjcBOOL` returns. Python values and type annotations take their place.
- **Properties:** 70 call sites in 8 repositories call, with `()`, a name that Rubicon reads as a property, which raises `TypeError` there. Of those, 39 are `UTF8String`, which gives `bytes` in Rubicon, so it's replaced with `str(...)`. 5 more call `NSArray.count()`, which becomes `len()`.
- **Delegates and observers:** they become `NSObject` subclasses with `@objc_method`, which Python must keep a reference to.
- **Errors:** passing `NSError.alloc()` for an `NSError **` argument crashed pyobjus (SIGSEGV) whenever an error was written. Rubicon's form, `byref(objc_id())`, read the error. Plyer's macOS audio and kivy-tensorflow-helloworld use the `NSError.alloc()` form, and Plyer's VoIP passes an `NSError` object the same way.
- **Blocks:** Rubicon took a Python function as a block. pyobjus aborted (SIGABRT). The sample passes `None` or uses an Objective-C helper.
- **Results that differ:** pyobjus returned `str` from `UTF8String` where Rubicon returns `bytes`. pyobjus 1.2.4 lost a dictionary's value, as Section 3 found.

## M2: Kivy and Plyer, file by file

From [`raw/m2_inventory.md`](raw/m2_inventory.md), which lists each file's changes by line.

| | Files | pyobjus calls | Flat-form calls, unchanged | Changes, most common first |
|---|---:|---:|---:|---|
| Kivy | 2 | 8 | 6 | `autoclass` 5, `load_framework` 2, `init_utf8` 2, `protocol` 1, `delegate_self` 1, `property_parens` 1, `utf8string` 1 |
| Plyer | 28 | 104 | 82 | `autoclass` 60, `utf8string` 29, `load_framework` 23, `property_parens` 16, `objc_str` 13, `protocol` 6, `delegate_self` 4, `nsarray_index` 3, and 8 others with 1 or 2 each |

14 Plyer files and both Kivy files were also read by hand, for the motion sensors' `bridge`, the file chooser's `NativeImagePicker`, the bundled `Voip.framework`, `NSError.alloc()`, constants, GPS parsing and `UUIDString`.

## M3: changes outside the code

From [`raw/m3_build.md`](raw/m3_build.md).

- **Declared:** only Plyer declares pyobjus as a dependency, as an `ios` and `macosx` extra. Its install instructions and macOS CI use pyobjus `master` from GitHub.
- **kivy-ios:** its pyobjus recipe builds `master`, and its `kivy` and `plyer` recipes depend on it. Kivy, KivyMD, Carvera Controller and kivy-tensorflow-helloworld get pyobjus that way on iOS without naming it.
- **renpy-build:** it compiles pyobjus at `b61d65f`, with two patches, into Ren'Py's Python for iOS and macOS. Ren'Py's docs offer pyobjus to game creators.
- **Carvera Controller:** its Xcode project also links `libpyobjus.xcframework` directly.

## B1: installing each library

From [`raw/b1_install.md`](raw/b1_install.md).

| | pyobjus | Rubicon |
|---|---|---|
| Needs compiling | Yes, a Cython extension linked against libffi | No |
| On PyPI | 1.2.4: macOS wheels for Python 3.10 to 3.14, iOS wheels for 3.13 and 3.14 | 0.5.7: one `py3-none-any` wheel |
| Python 3.15 | No PyPI wheel. kivy-mobile-wheels, the comparison author's project, has `cp315` iOS wheels | The one wheel |
| kivy-ios | A recipe that builds `master` | No recipe needed. kivy-ios installs pure-Python packages with `toolchain pip install`. Not tested here for Rubicon |
| KivyForge, the author's project | From wheels, with kivy-mobile-wheels added to new projects' indexes | From PyPI's wheel |

## Claims

| Claim ([register](../../../CLAIMS.md)) | Result |
|---|---|
| 13. Both libraries work side by side on Python 3.15 | Not tested: running both in one process is excluded by the definitions |
| 17. Kivy doesn't require pyobjus by design | Kivy declares no dependency on pyobjus. Its two pyobjus files are providers that Kivy skips when the import fails, falling back to other audio and clipboard providers. On iOS, kivy-ios's `kivy` recipe always includes pyobjus. "By design" is about intent and isn't measured |
| 18. Kivy already depends on pyobjus alone | Kivy also imports PyObjC, in its optional macOS spelling provider. It also calls the Objective-C runtime through ctypes in `kivy.mobile` on iOS, the comparison author's module, and compiles four Objective-C++ files for macOS and iOS, one of them only with the ANGLE backend. It doesn't use Rubicon |
| 19. Plyer's last release was 2.1.0 in November 2022, and it has 69 open PRs, most more than five years old | Holds. 2.1.0 was uploaded on 12 November 2022. There were 69 open PRs on the claim's date, 54 of them more than five years old. One more was opened before collection, making 70 |

## Limits

- **Not checked:**
  - `UIApplication.keyWindow` and `rootViewController` (Plyer's iOS file chooser), because the test app has no window.
  - Rubicon's `load_library` with a framework folder path (Plyer's `Voip.framework`).
  - Reading the `coordinate` struct (Plyer's GPS), and `identifierForVendor`.
- **Intermittent results:** pyobjus 1.2.4's `zero_arg` crashes and its `observer_ios` reading of 0.0 weren't investigated further.
- **The sample is 10 repositories.** Projects that use pyobjus through Plyer or Kivy, and Ren'Py games, aren't in it, as in Section 7.
- **Hand reading:** platforms, helper classes and workarounds were read by hand, and are listed in [`raw/hand_notes.md`](raw/hand_notes.md).

## Files

| File | Contents |
|---|---|
| `raw/sample.json` | The 10 repositories, their stars and pinned commits |
| `raw/catalog.json` | U1: every using file, its imports, pyobjus calls, flat-form calls, classes, frameworks and protocols, and the files that only mention pyobjus |
| `raw/patterns.json` | U2: each pattern's files and match counts, and the SDK check of the classes used |
| `raw/hand_notes.md` | What was read by hand |
| `raw/m1_mac.json`, `raw/m1_iphone.json` | Every M1 run's output, for each library version |
| `raw/m1_iphone_first_attempt.json` | The first iPhone run, before the test fixes |
| `raw/m1_translations.md` | M1's translation table and zero-argument names |
| `raw/m2_inventory.json`, `raw/m2_inventory.md` | M2 |
| `raw/m3_build.json`, `raw/m3_build.md` | M3 |
| `raw/b1_pypi.json`, `raw/b1_install.md` | B1 |
| `raw/claims17_18_kivy.md` | Claims 17 and 18 |
| `raw/claim19_plyer.json`, `raw/claim19_plyer.md` | Claim 19 |

To rerun the catalog and M2 from fresh clones at the pinned commits (`CLONES` holds one folder per repository, named `owner__repo`):

```bash
python tests/section-08/catalog.py CLONES results/section-08/2026-11-09/raw/sample.json catalog.json
```

```bash
python tests/section-08/inventory.py CLONES catalog.json results/section-08/2026-11-09/raw/m1_mac.json results/section-08/2026-11-09/raw/m1_iphone.json m2_inventory.json m2_inventory.md
```

M1 needs the four library builds, and for the iPhone the apps built by `m1/ios/make_project.py`. B1 and claim 19 read live services, so a rerun gives that day's values.

# 8. Compatibility and migration

**Status: draft for factual review.** Neither project has reviewed this section. Metric IDs refer to the [approved definitions](../metrics/08-compatibility-and-migration.md), which also list every change made after approval.

This section documents what it takes to move code from pyobjus to Rubicon. It catalogs how the ten most-starred public projects that import pyobjus use it, gives the Rubicon way to do each thing they do, tested with both libraries, and lists what Kivy and Plyer would change. It doesn't design or test a compatibility layer, estimate hours of work, or plan when or whether any project moves.

## Summary of findings

The ten projects use pyobjus in 46 files. They make 157 calls to pyobjus's own API, such as `autoclass` and `objc_str`, and 133 Objective-C method calls in pyobjus's underscore form, such as `setObject_forKey_(...)`. Rubicon accepts that underscore form, so those 133 calls run unchanged. Of the pyobjus API calls, most are renamed or dropped: `autoclass` becomes `ObjCClass`, `load_framework` becomes `load_library`, and `objc_str`, `objc_arr` and `enum` aren't needed, because Rubicon converts Python values.

The changes that need more than a rename fall in four places:
- **Properties:** 70 calls in 8 projects call, with `()`, a name that Rubicon reads as a declared property, which raises `TypeError` there. 39 of them are `UTF8String`, which gives `bytes` in Rubicon, so it becomes `str(...)`. Another 5 call `NSArray.count()`, which becomes `len()`.
- **Delegates and observers:** in pyobjus, any Python object can be a delegate. Kivy's AVPlayer audio sets the `Sound` object itself as the player's delegate and marks its callback with `@protocol("AVAudioPlayerDelegate")`. Kivy, Plyer and kivy-ios do this in 9 callbacks. In Rubicon, the delegate must be an Objective-C class, defined in Python. The move changes four things:
  - **A new class:** each callback moves to a class that subclasses `NSObject` and names the protocol, as in `class PlayerDelegate(NSObject, protocols=[ObjCProtocol("AVAudioPlayerDelegate")])`. `@protocol(...)` becomes `@objc_method`.
  - **Types from annotations:** Rubicon builds each callback's Objective-C signature from its type annotations, so non-object arguments are annotated, such as `flag: bool`, and the return type is given, such as `-> None`. A callback that returned `ObjcBOOL(True)` returns `True` with `-> bool`.
  - **A reference kept in Python:** the delegate is created with `PlayerDelegate.alloc().init()` and set as the delegate. Delegate properties are weak references, so the owning Python object, here the `Sound`, keeps the delegate in an attribute, and the delegate reaches the `Sound` through an attribute of its own.
  - **No hand-registered protocols:** kivy-ios's keyboard observer writes a protocol's method signatures into pyobjus's `protocols` table and names the method with `selector("keyboardWillShow")`. In Rubicon, the method's annotations give its signature, and `SEL("keyboardWillShow:")` names it, with the trailing colon of its Objective-C name.
- **Error arguments:** many Cocoa methods take an `NSError **` argument, where the method writes an error object when it fails. The sample passes one in 23 calls in 3 projects, in two forms:
  - **`None`,** as in Kivy's AVPlayer audio, which ignores the error. These calls don't change.
  - **An object from `NSError.alloc()`,** as in Plyer's macOS audio and VoIP and in kivy-tensorflow-helloworld. These calls must change: Rubicon rejects the object with `ctypes.ArgumentError` before the method runs, on every call. In Rubicon, the code creates `err = objc_id()`, passes `byref(err)`, and reads the error afterwards with `ObjCInstance(err)`. In pyobjus, this form never delivered an error either: it crashed the process (SIGSEGV) whenever the method wrote one. After the move, these calls can read the errors they were written to read.
- **Workarounds that can go:** the sample works around pyobjus with Objective-C helpers for blocks and C functions, struct values read in Objective-C and passed in environment variables, strings parsed out of `description`, and checks for whether a name is a property or a method. Rubicon took a Python function as a block, where pyobjus crashed, and both libraries read the `UIScreen` structs that Carvera Controller reads in Objective-C.

**Kivy** uses pyobjus in 2 files, its AVPlayer audio and macOS clipboard, with 8 calls. Both are optional providers that Kivy skips when pyobjus is missing. Kivy also reaches Objective-C through PyObjC, ctypes and compiled Objective-C++. **Plyer** uses pyobjus in 28 files, 21 for iOS and 7 for macOS, with 104 calls and 82 underscore-form calls. Six of its iOS sensors read a `bridge` class from kivy-ios's Xcode template, which Rubicon can call unchanged.

**Outside the code:** only Plyer declares pyobjus as a dependency. kivy-ios builds pyobjus `master` and makes its `kivy` and `plyer` recipes depend on it, which is how Kivy, KivyMD, Carvera Controller and kivy-tensorflow-helloworld get it on iOS. renpy-build compiles a pinned, patched pyobjus into Ren'Py. pyobjus is a compiled extension with wheels on PyPI for Python 3.10 to 3.14, and Rubicon is one pure-Python wheel. Rubicon needs no kivy-ios recipe: kivy-ios installs pure-Python packages with [`toolchain pip install`](https://github.com/kivy/kivy-ios/blob/fd363d49eddb5ac06766348738bd89c7d46007f8/README.md#L115).

All figures are **Measured** at the commits pinned on 2026-11-09, unless labeled otherwise. This section makes no recommendation.

| Measure | Figure |
|---|---|
| [Projects in the sample](#u0-and-u1-the-sample-and-where-it-uses-pyobjus) | 10 |
| [Files that use pyobjus](#u0-and-u1-the-sample-and-where-it-uses-pyobjus) | 46 |
| [Calls to pyobjus's own API](#u0-and-u1-the-sample-and-where-it-uses-pyobjus) | 157 |
| [Method calls in underscore form, unchanged in Rubicon](#m1-the-rubicon-way-to-do-each-pattern) | 133 |
| [Use patterns](#u2-use-patterns) | 23 |
| [Calls with `()` of a name Rubicon reads as a property](#zero-argument-names) | 70, in 8 projects |
| [Kivy: files, pyobjus calls](#kivy) | 2, 8 |
| [Plyer: files, pyobjus calls](#plyer) | 28, 104 |
| [Projects that declare pyobjus as a dependency](#m3-changes-outside-the-code) | 1, Plyer |
| [Translations where pyobjus crashed](#m1-the-rubicon-way-to-do-each-pattern) | 2: an `NSError` object passed for `NSError **`, and a Python function passed as a block |

## Claims from the discussion

| Claim ([register](../CLAIMS.md)) | Finding |
|---|---|
| 13. Both libraries work side by side on Python 3.15 | **Not tested.** The definitions exclude running both libraries in one process. Each worked on its own on Python 3.15 on the iPhone, here and in Section 2 |
| 17. Kivy doesn't require pyobjus by design | Kivy declares no dependency on pyobjus in any of its 19 metadata, requirements and CI files. Its two pyobjus files are [providers](#kivy) that Kivy skips when the import fails, falling back to other audio and clipboard providers. On iOS, kivy-ios's Kivy recipe [depends on pyobjus](https://github.com/kivy/kivy-ios/blob/fd363d49eddb5ac06766348738bd89c7d46007f8/kivy_ios/recipes/kivy/__init__.py#L21), so a kivy-ios build always includes it. Whether this is by design is about intent, which isn't measured |
| 18. Kivy already depends on pyobjus alone | Kivy also imports [PyObjC](#kivy), in its optional macOS spelling provider. It calls the Objective-C runtime through `ctypes` in `kivy.mobile` on iOS, a module by this comparison's author. It also compiles four Objective-C++ files for macOS and iOS: camera, video, ImageIO and, when the ANGLE backend is on, ANGLE's Metal backend. It doesn't use Rubicon |
| 19. Plyer's last release was 2.1.0 in November 2022, and it has 69 open PRs, most more than five years old | **Confirmed.** 2.1.0 was uploaded to PyPI on 12 November 2022. On the claim's date, 30 October 2026, there were 69 open PRs, 54 of them more than five years old, the oldest from March 2014. One more was opened on 6 November |

## Supporting facts

Raw results, conditions and the full tables are in [`results/section-08/2026-11-09`](../results/section-08/2026-11-09/README.md). The scripts and test cases are in [`tests/section-08`](../tests/section-08).

**How it was measured:** each project was cloned at its default branch on 2026-11-09, and the commits are recorded. [`catalog.py`](../tests/section-08/catalog.py) searched each full checkout for every import of pyobjus and every call, and [`patterns.py`](../tests/section-08/patterns.py) matched 23 use patterns. Platforms, helper classes and workarounds were read by hand. For M1, each pattern was written both ways and run with pyobjus 1.2.4 and `master` and Rubicon 0.5.7 and `main`, 5 times each, on the Mac (macOS 26.6.2, Python 3.14.7) and on an iPhone 18 Pro Max (iOS 27.0.1, Python 3.15.0). The iPhone apps were built with KivyForge, by this comparison's author.

### U0 and U1. The sample and where it uses pyobjus

U0 is every repository Section 7 counted as importing pyobjus with 50 or more stars, without gistable/gistable, which Section 7 listed as a possible copy. In files that also hold Android or desktop code, only the iOS and macOS code is counted.

| Repository | Stars | Files | pyobjus API calls | Underscore-form method calls | Platforms |
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

Several classes the sample loads aren't Apple's, and come from elsewhere (**Source**):
- **`bridge`:** Plyer's six motion sensors use it. It comes from kivy-ios's Xcode project template, which runs CoreMotion's block-based updates in Objective-C.
- **`NativeImagePicker`:** Plyer's iOS file chooser uses it, from kivy-ios's `ios` recipe, to call the C function `UIImagePNGRepresentation`.
- **`Voip`:** from Plyer's own bundled framework.
- **`IAPHelper`, `Log` and `Age`:** Ren'Py uses them, from renpy-build. `Age` is a Swift class.
- **TensorFlow Lite's classes:** kivy-tensorflow-helloworld gets them from CocoaPods.

### U2. Use patterns

Each pattern with the number of projects and matches, and one example.

| Feature | Pattern | Projects | Matches | Example |
|---|---|---:|---:|---|
| Classes | `load-class`: `autoclass(...)` loads an Objective-C class | 10 | 91 | [kivy, `audio_avplayer.py`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/core/audio_output/audio_avplayer.py#L13) |
| Classes | `load-framework`: `load_framework(...)` loads a framework before its classes | 5 | 28 | [kivy, `audio_avplayer.py`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/core/audio_output/audio_avplayer.py#L12) |
| Objects | `alloc-init`: `.alloc()` then an init method creates an object | 6 | 41 | [kivy, `audio_avplayer.py`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/core/audio_output/audio_avplayer.py#L33) |
| Methods | `selector-call`: a method with arguments, in underscore form, such as `setObject_forKey_(...)` | 8 | 133 | [kivy, `audio_avplayer.py`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/core/audio_output/audio_avplayer.py#L33) |
| Methods | `property-or-method`: code that tries a name both as a property and as a method | 3 | 4 | [renpy, `renpy.py`](https://github.com/renpy/renpy/blob/1b79387539ed04c7123492967e2736789859d925/renpy.py#L156) |
| Strings | `objc-str`: `objc_str(...)` turns a Python `str` into an `NSString` | 3 | 21 | [renpy, `00iap.rpy`](https://github.com/renpy/renpy/blob/1b79387539ed04c7123492967e2736789859d925/renpy/common/00iap.rpy#L223) |
| Strings | `utf8string`: `.UTF8String()` turns an `NSString` into Python | 3 | 39 | [kivy, `clipboard_nspaste.py`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/core/clipboard/clipboard_nspaste.py#L35) |
| Strings | `bytes-check`: a check for `bytes` after `UTF8String()` | 2 | 9 | [renpy, `renpy.py`](https://github.com/renpy/renpy/blob/1b79387539ed04c7123492967e2736789859d925/renpy.py#L161) |
| Collections | `nsarray-index`: `objectAtIndex_(i)` reads an `NSArray` element by element | 4 | 8 | [renpy, `tts.py`](https://github.com/renpy/renpy/blob/1b79387539ed04c7123492967e2736789859d925/renpy/display/tts.py#L540) |
| Collections | `objc-arr`: `objc_arr(...)` builds an `NSArray` | 1 | 1 | [plyer, `filechooser.py`](https://github.com/kivy/plyer/blob/4853b3a92a786237af966b86d07fa8242eee9aec/plyer/platforms/macosx/filechooser.py#L92) |
| Collections | `python-container-arg`: a Python `{}` or `[]` passed straight to a method | 1 | 1 | [renpy-build, `iossupport.py`](https://github.com/renpy/renpy-build/blob/e01af78cc04de8d991b4617f58ef0718c27b1d0b/runtime/iossupport.py#L36) |
| Delegates | `delegate-self`: a Python object set as an Objective-C object's delegate | 2 | 5 | [kivy, `audio_avplayer.py`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/core/audio_output/audio_avplayer.py#L45) |
| Delegates | `observer-self`: a Python object registered with `NSNotificationCenter` | 1 | 2 | [kivy-ios, `ios.pyx`](https://github.com/kivy/kivy-ios/blob/fd363d49eddb5ac06766348738bd89c7d46007f8/kivy_ios/recipes/ios/src/ios.pyx#L239) |
| Delegates | `protocol-method`: `@protocol(...)` marks a method that Objective-C calls back | 3 | 9 | [kivy, `audio_avplayer.py`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/core/audio_output/audio_avplayer.py#L79) |
| Delegates | `protocol-register`: a protocol's method signatures written out by hand | 1 | 1 | [kivy-ios, `ios.pyx`](https://github.com/kivy/kivy-ios/blob/fd363d49eddb5ac06766348738bd89c7d46007f8/kivy_ios/recipes/ios/src/ios.pyx#L226) |
| Delegates | `selector`: `selector(...)` names a method for a target-action API | 1 | 2 | [kivy-ios, `ios.pyx`](https://github.com/kivy/kivy-ios/blob/fd363d49eddb5ac06766348738bd89c7d46007f8/kivy_ios/recipes/ios/src/ios.pyx#L239) |
| Delegates | `bool-return`: `ObjcBOOL(...)` returns a `BOOL` from a callback | 1 | 1 | [plyer, `notification.py`](https://github.com/kivy/plyer/blob/4853b3a92a786237af966b86d07fa8242eee9aec/plyer/platforms/macosx/notification.py#L44) |
| Blocks | `completion-nil`: a method that takes a completion block, called with `None` | 3 | 4 | [plyer, `filechooser.py`](https://github.com/kivy/plyer/blob/4853b3a92a786237af966b86d07fa8242eee9aec/plyer/platforms/ios/filechooser.py#L60) |
| Errors | `error-arg`: a method with an `NSError **` argument | 3 | 23 | [kivy, `audio_avplayer.py`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/core/audio_output/audio_avplayer.py#L35) |
| Structs | `struct-field`: a field of a returned struct, such as `frame.size.width` | 2 | 6 | [kivy-ios, `ios.pyx`](https://github.com/kivy/kivy-ios/blob/fd363d49eddb5ac06766348738bd89c7d46007f8/kivy_ios/recipes/ios/src/ios.pyx#L245) |
| Constants | `enum`: pyobjus's `enum(...)` declares enum values by hand | 1 | 4 | [renpy, `renpy.py`](https://github.com/renpy/renpy/blob/1b79387539ed04c7123492967e2736789859d925/renpy.py#L145) |
| Memory | `retain-release`: reference counts managed by hand | 1 | 2 | [kivy-tensorflow-helloworld, `model.py`](https://github.com/teticio/kivy-tensorflow-helloworld/blob/4785a4f0cca844aee6022041ce9d49f3ccd224ac/model.py#L155) |
| Memory | `raw-pointer`: a raw pointer read or passed through `ctypes` | 1 | 2 | [kivy-tensorflow-helloworld, `model.py`](https://github.com/teticio/kivy-tensorflow-helloworld/blob/4785a4f0cca844aee6022041ce9d49f3ccd224ac/model.py#L145) |

### M1. The Rubicon way to do each pattern

Each translation ran with both libraries against the same Apple API, checking the same result: 18 cases on the Mac, and 13 portable cases plus 5 iOS ones on the iPhone. Every case gave the same result in all 5 runs, except two, both pyobjus 1.2.4. `zero_arg` crashed in 2 of 5 Mac runs, and 1 of 5 on a rerun, and `observer_ios` read a keyboard height of 0.0 instead of 216.0 in 1 of 5 iPhone runs. The full table, with the code on each side, is in [`m1_translations.md`](../results/section-08/2026-11-09/raw/m1_translations.md).

| pyobjus, as the sample writes it | Rubicon | Result |
|---|---|---|
| `autoclass("NSString")` | `ObjCClass("NSString")` | Same |
| `load_framework(INCLUDE.AppKit)` | `load_library("AppKit")` | Same |
| `pb.setString_forType_(x, t)` | Unchanged. Rubicon's own form is `pb.setString(x, forType=t)` | Same |
| `objc_str("token")`, `objc_arr(...)`, `{}` for an `NSDictionary` | A `str`, `list` or `dict` | Same, except that pyobjus 1.2.4 lost the dictionary's value, as Section 3 found |
| `s.UTF8String()`, then decode if `bytes` | `str(s)` | pyobjus returned `str`, and Rubicon's `UTF8String` gives `bytes` |
| `for i in range(a.count()): a.objectAtIndex_(i)` | `len(a)`, `a[i]`, `for x in a` | Same |
| `enum("NSSearchPathDirectory", NSDocumentDirectory=9)` | Plain integers | Same |
| `"vide"` for `AVMediaTypeVideo` | `objc_const(load_library("AVFoundation"), "AVMediaTypeVideo")` | Same value |
| `obj.delegate = self`, with `@protocol(...)` methods | An `NSObject` subclass with `protocols=[ObjCProtocol(...)]` and `@objc_method` methods, kept alive by Python because delegates are weak references | Same |
| `protocols["Name"] = {...}` encodings, and `selector("keyboardWillShow")` | An annotated `@objc_method`, and `SEL("keyboardWillShow:")`. No encodings | Same, except pyobjus 1.2.4's one reading of 0.0 |
| `frame.size.width`, `UIScreen.mainScreen().bounds` | The same field names | Same. Both read `UIScreen`'s bounds and scale, the values Carvera Controller reads in Objective-C because "pyobjus can't reliably read UIScreen struct properties" |
| `NSError.alloc()` for an `NSError **` argument | `byref(objc_id())`, then `ObjCInstance(err)` | With `None`, both gave nil. When the call wrote an error, pyobjus crashed (SIGSEGV) in every run, and Rubicon read the error |
| `None` for a completion block | A Python function with type annotations | pyobjus aborted (SIGABRT) when given a function, and Rubicon called it |
| `ctypes.cast(...)`, `.bytes().arg_ref`, `release()` until `retainCount()` is 1 | Pass `bytes`. Rubicon manages reference counts | Same bytes and length |
| `return ObjcBOOL(True)` | Annotate `-> bool` | Not rerun: Section 3 found both return the value, and pyobjus 1.2.4 returned nothing |
| `load_dylib(path)`, then the app's own class | `load_library(path)`, `ObjCClass(...)` | Same, on the Mac. Swift `@objc` classes are in Section 3 |

#### Zero-argument names

A declared property in Rubicon is read without `()`, and calling it raises `TypeError`. pyobjus treats most of these names as methods. Checked on the Mac, and on the iPhone for iOS classes (**Measured**):

| Name | Calls with `()` in the sample |
|---|---:|
| `NSString.UTF8String` | 39 |
| `UIApplication.sharedApplication` | 6 |
| `UIDevice.currentDevice` | 5 |
| `NSFileManager.defaultManager` | 4 |
| `NSUserDefaults.standardUserDefaults`, `NSNotificationCenter.defaultCenter`, `NSNumber.intValue` | 2 each |
| `UIScreen.mainScreen`, `NSValue.CGRectValue`, `NSPasteboard.generalPasteboard`, `NSLocale.preferredLanguages`, `NSRunLoop.currentRunLoop`, `description`, `NSUserNotificationCenter.defaultUserNotificationCenter`, `NSScreen.screens`, `NSData.bytes`, `NSNotification.userInfo` | 1 each |
| **Total** | **70** |

`NSArray.count()`, with 5 calls, raises in Rubicon too, because `count` is Python's `list.count`, so it becomes `len()`. `UUIDString` is a property in both libraries, so Plyer's `UUIDString()` would raise in either. Names that are methods in both, such as `lastObject`, `sharedInstance` and `openPanel`, are unchanged.

### M2. Kivy and Plyer, file by file

The changes each file needs, by line, are in [`m2_inventory.md`](../results/section-08/2026-11-09/raw/m2_inventory.md).

#### Kivy

| File | Platform | How Kivy loads it | pyobjus calls | Underscore-form calls | Changes |
|---|---|---|---:|---:|---|
| [`audio_avplayer.py`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/core/audio_output/audio_avplayer.py) | iOS and macOS | First audio provider on both. If the import fails, Kivy moves on to gstplayer, ffpyplayer and SDL3 | 5 | 3 | 3 `autoclass`, 1 `load_framework`, 1 `initWithUTF8String_`. The `Sound` subclass is its own delegate, so the delegate becomes an `NSObject` subclass the `Sound` keeps |
| [`clipboard_nspaste.py`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/core/clipboard/clipboard_nspaste.py) | macOS | The macOS clipboard provider. If pyobjus is missing it raises `SystemError` with `pip install --user pyobjus`, and Kivy moves on to SDL3, then a dummy clipboard | 3 | 3 | 2 `autoclass`, 1 `load_framework`, 1 `UTF8String`, 1 `initWithUTF8String_`, 1 `generalPasteboard()` |

Kivy's other routes to Objective-C (**Source**):
- **PyObjC:** [`spelling_osxappkit.py`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/core/spelling/spelling_osxappkit.py#L16) imports PyObjC's `AppKit`. It's an optional spelling provider on macOS, and no metadata file names PyObjC.
- **ctypes:** [`kivy/mobile/_platform/ios.py`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/mobile/_platform/ios.py) calls `objc_msgSend` through `ctypes` for safe areas, keyboard height and screen scale. It's by this comparison's author.
- **Objective-C++:** four `.mm` files are compiled into Cython extensions for camera, video, ImageIO and ANGLE's Metal backend.

#### Plyer

Plyer's 28 files make 104 pyobjus calls and 82 underscore-form calls. By count, the changes are `autoclass` 60, `UTF8String` 29, `load_framework` 23, other zero-argument names 16 and `objc_str` 13. Then come `@protocol` methods 6 and delegates 4, and 3 or fewer each of `objectAtIndex_` loops, completion blocks, `NSError.alloc()`, `count()`, `objc_arr`, `ObjcBOOL` and a property-or-method check. Files that need more than these:
- **Motion sensors:** accelerometer, barometer, compass, gravity, gyroscope and spatial orientation poll kivy-ios's `bridge` class. Rubicon calls the class unchanged, or can pass Python functions to CoreMotion directly, as Section 4 does for the barometer.
- **iOS file chooser:** it calls kivy-ios's `NativeImagePicker`, which Rubicon calls unchanged, or the C function through `ctypes`.
- **iOS VoIP:** it loads Plyer's bundled `Voip.framework` by its folder path, and passes an `NSError` object for `NSError **`, the form that crashed pyobjus.
- **macOS audio:** it passes `NSError.alloc()` for `NSError **`, the same form.
- **iOS flash:** it writes `AVMediaTypeVideo` as `"vide"`, which Rubicon can read with `objc_const`.
- **GPS, iOS and macOS:** they parse latitude, longitude and accuracy out of `location.description` instead of reading the `coordinate` struct.

### M3. Changes outside the code

Every non-code file that names pyobjus, and each project's package metadata and build files (**Source**). Details are in [`m3_build.md`](../results/section-08/2026-11-09/raw/m3_build.md).

| Project | Where pyobjus is declared, built or linked |
|---|---|
| Plyer | [`setup.py`](https://github.com/kivy/plyer/blob/4853b3a92a786237af966b86d07fa8242eee9aec/setup.py#L26) gives `pyobjus` as an extra for `ios` and `macosx`. Its install notes and macOS CI install pyobjus `master` from GitHub |
| kivy-ios | Its [pyobjus recipe](https://github.com/kivy/kivy-ios/blob/fd363d49eddb5ac06766348738bd89c7d46007f8/kivy_ios/recipes/pyobjus/__init__.py#L4) compiles `master` from GitHub. Its `kivy` and `plyer` recipes depend on it |
| Kivy, KivyMD, kivy-tensorflow-helloworld | Not named in any metadata. They get pyobjus on iOS through kivy-ios's `kivy` recipe. Kivy's README lists pyobjus as a sister project |
| Carvera Controller | Built through kivy-ios, and its Xcode project also [links `libpyobjus.xcframework`](https://github.com/Carvera-Community/Carvera_Controller/blob/e5623ece10309597d43a708dde35ae41c7854cb8/assets/packaging/ios/carveracontroller-ios/CarveraController.xcodeproj/project.pbxproj#L22) |
| renpy-build | [`tasks/pyobjus.py`](https://github.com/renpy/renpy-build/blob/e01af78cc04de8d991b4617f58ef0718c27b1d0b/tasks/pyobjus.py#L19) clones pyobjus at `b61d65f`, from June 2025, applies two patches and compiles it into Ren'Py's Python for iOS and macOS |
| Ren'Py | Not named in metadata. Its [iOS docs](https://github.com/renpy/renpy/blob/1b79387539ed04c7123492967e2736789859d925/sphinx/source/ios.rst#L146) offer pyobjus to game creators |
| MF_run_counter, Friendly-Fitness-App | Nothing in the repository |

### B1. Getting each library into an app

From PyPI and the kivy-mobile-wheels index on 2026-11-09 (**Measured**), and kivy-ios and KivyForge at their pinned commits (**Source**). Details are in [`b1_install.md`](../results/section-08/2026-11-09/raw/b1_install.md).

| | pyobjus | Rubicon |
|---|---|---|
| Needs compiling | Yes, a Cython extension linked against libffi, built for each Python version and platform (Section 5) | No |
| Latest on PyPI | 1.2.4, 29 December 2025: macOS wheels for Python 3.10 to 3.14, iOS wheels for 3.13 and 3.14 | 0.5.7, 30 September 2026: one `py3-none-any` wheel, for Python 3.11 and later |
| Python 3.15 | No wheel on PyPI. kivy-mobile-wheels, by this comparison's author, has `cp315` iOS wheels | The same wheel |
| kivy-ios | A recipe that compiles `master` | No recipe needed. kivy-ios installs pure-Python packages with `toolchain pip install`. Not tested here for Rubicon |
| KivyForge, by this comparison's author | From wheels. New projects add the kivy-mobile-wheels index, for pyobjus on Python 3.15 | From PyPI's wheel |

For this section's iPhone tests, pyobjus had to be compiled for iOS, including libffi, whose project needed its iOS 8.0 target raised for Xcode 27. Rubicon 0.5.7 was installed from PyPI unchanged.

## Limits of this section

- **The sample is ten projects,** chosen by stars from Section 7's count. Apps that use pyobjus only through Kivy or Plyer, and Ren'Py games, aren't in it.
- **The changes are counted, not timed.** Hours of work depend on the developer and aren't estimated.
- **Not tested:**
  - `UIApplication.keyWindow` and `rootViewController`, used by Plyer's iOS file chooser, because the test app has no window.
  - Rubicon's `load_library` with a framework folder path, as Plyer's VoIP needs.
  - Reading CoreLocation's `coordinate` struct, and `identifierForVendor`.
  - Running both libraries in one process.
- **pyobjus 1.2.4's intermittent results,** its `zero_arg` crashes and one 0.0 keyboard height, weren't investigated further.
- **Translations are tested on the sample's calls,** with the versions at the baseline. Other apps may use APIs or patterns this sample doesn't.
- **This comparison's author** wrote `kivy.mobile`'s iOS module, one of Kivy's other routes to Objective-C, and owns KivyForge and kivy-mobile-wheels, which built and supplied this section's iPhone apps and wheels and appear in B1.

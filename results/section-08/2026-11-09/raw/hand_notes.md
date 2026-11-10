# Section 8 hand notes, 2026-11-09

Read by hand at the commits in `sample.json`. Links are to those commits.

## Platforms (U1)

- **iOS:** Plyer's `plyer/platforms/ios/` files, KivyMD's `uix/behaviors/ios/native_behavior.py`, kivy-ios's `ios.pyx` and its test app, renpy-build's `runtime/iossupport.py`, Carvera Controller's two files, and the `renpy.ios` or `platform == 'ios'` branches in Ren'Py (`renpy.py`, `bootstrap.py`, `main.py`, `00iap.rpy`, `platformexports.py`), Friendly-Fitness-App and kivy-tensorflow-helloworld.
- **macOS:** Plyer's `plyer/platforms/macosx/` files, Kivy's `clipboard_nspaste.py` (raises on other platforms), MF_run_counter's `osx.py` enumerator.
- **Both:** Kivy's `audio_avplayer.py` (its docstring says iOS and OSX), Ren'Py's `translation/__init__.py` (`renpy.ios or renpy.macintosh`) and `display/tts.py` (AppleTTS is chosen for both).

## Classes that aren't Apple's (U2)

No `@interface` for these in the iPhoneOS 27.0 or MacOSX 27.0 SDK headers.

| Class | Used by | Supplied by |
|---|---|---|
| `bridge` | Plyer: accelerometer, barometer, compass, gravity, gyroscope, spatialorientation | kivy-ios's Xcode project template, `kivy_ios/tools/templates/{{ cookiecutter.project_name }}-ios/bridge.m`. Plyer doesn't ship it. Carvera Controller carries its own copy in `assets/packaging/ios/carveracontroller-ios/bridge.h` |
| `NativeImagePicker` | Plyer: iOS filechooser | kivy-ios: `kivy_ios/recipes/ios/src/ios_filechooser.m`. Plyer's comment: there's "no way to call a non-class function via pyobjus", here `UIImagePNGRepresentation` |
| `Voip` | Plyer: iOS voip | Plyer's bundled `plyer/platforms/ios/frameworks/Voip.framework`, loaded with `load_framework` through `load_plyer_framework` |
| `IAPHelper`, `Log` | Ren'Py `00iap.rpy`; renpy-build `runtime/iossupport.py` | renpy-build: `renios/prototype/IAPHelper.m`, `renios/prototype/Log.m` |
| `Age` | Ren'Py `platformexports.py` | renpy-build: `renios/prototype/Age.swift`, a Swift class exposed with `@objc(Age)` |
| `adSwitch` | Friendly-Fitness-App | Not in the repository: the app's Xcode project |
| `TFLInterpreter`, `TFLInterpreterOptions` | kivy-tensorflow-helloworld | TensorFlow Lite's Objective-C pod, installed with `pod install` per its README |

## Workarounds seen

- **Blocks:** Plyer's six motion sensors poll the `bridge` class from kivy-ios's template, which runs CoreMotion's block-based updates in Objective-C. `presentViewController_animated_completion_`, `dismissViewControllerAnimated_completion_` (Plyer) and `openURL_options_completionHandler_` (renpy-build, Carvera) are called with `None` for the block.
- **C functions:** Plyer calls `UIImagePNGRepresentation` through kivy-ios's `NativeImagePicker`. Plyer's iOS vibrator calls `AudioServicesPlaySystemSound` through `ctypes` and doesn't import pyobjus.
- **Structs:** Carvera Controller reads `UIScreen` bounds and scale in `main.m` and passes them in environment variables, with the comment "pyobjus can't reliably read UIScreen struct properties". Plyer's iOS and macOS GPS parse latitude, longitude and accuracy from `location.description` instead of reading the `coordinate` struct.
- **Objective-C runtime through ctypes:** Carvera Controller's `ios_helpers.py` imports pyobjus but calls `objc_getClass`, `sel_registerName` and `objc_msgSend` through `ctypes` to reach its `DocumentPickerHelper` class.
- **Constants:** Plyer's iOS flash recreates `AVMediaTypeVideo` as the string `"vide"`. Plyer's storagepath and Ren'Py write `NSSearchPathDirectory` values as numbers, Ren'Py through pyobjus's `enum`.
- **Property or method:** Ren'Py (`url.path`), MF_run_counter (`frame`) and Plyer's macOS GPS (`description`) try a name both as a method and as a property. Ren'Py's comment: "url.path seems to change type based on iOS version".
- **Strings:** Ren'Py and Plyer's storagepath check whether `UTF8String()` returned bytes and decode them.
- **Arrays:** kivy-tensorflow-helloworld fills an `NSMutableArray` by hand, with the comment "objc_arr doesn't work as expected on iPhone".
- **Memory:** kivy-tensorflow-helloworld calls `release()` until `retainCount()` is 1 "to avoid memory leaks", and reads the output buffer through `.arg_ref`.
- **Errors:** kivy-tensorflow-helloworld and Plyer's macOS audio pass an object from `NSError.alloc()` where the method takes `NSError **`. Kivy and Plyer's flash pass `None`.

## Kivy (claims 17 and 18)

- **pyobjus imports:** `kivy/core/audio_output/audio_avplayer.py` (module level; Kivy's audio provider list tries it on iOS and macOS) and `kivy/core/clipboard/clipboard_nspaste.py` (inside `try`, raising `SystemError` with an install hint; tried on macOS only).
- **Declared dependency:** `pyproject.toml` doesn't list pyobjus in any dependency or extra. kivy-ios's Kivy recipe lists `pyobjus` and `ios` in `_base_depends`.
- **kivy-ios's `ios` module**, also in that recipe's dependencies, uses pyobjus in `ios.pyx` for a keyboard-height observer (`NSNotificationCenter`, `selector`, a hand-registered protocol).
- **Other Objective-C bridges in Kivy:** `kivy/core/spelling/spelling_osxappkit.py` imports PyObjC's `AppKit`. `kivy/mobile/_platform/ios.py` calls the Objective-C runtime through `ctypes` for keyboard height, safe area and screen scale. That module was added and changed by the comparison's author: kivy/kivy#9331, #9345 and #9444, and two other commits, June to October 2026.

## Build and packaging (M3, B1)

- **Plyer** `setup.py`: `extras_require` gives `pyobjus` for `ios` and `macosx`; its docstring says to install pyobjus from GitHub's master zipball.
- **kivy-ios:** `recipes/pyobjus` builds pyobjus `master` from GitHub's zip as a Cython recipe; the `kivy` and `plyer` recipes depend on it.
- **renpy-build:** `tasks/pyobjus.py` clones pyobjus at commit `b61d65f` (10 June 2025), applies `pyobjus-ffi-h.diff` (include path for `ffi.h`) and `pyobjus-ios-foundation.diff` (iOS Foundation path), and compiles it into Ren'Py's runtime.
- **Carvera Controller:** its Xcode project links `libpyobjus.xcframework` from kivy-ios's `dist/xcframework` in its Frameworks build phase. `main.m` mentions pyobjus only in comments and a disabled `PYOBJUS_DEBUG` line.

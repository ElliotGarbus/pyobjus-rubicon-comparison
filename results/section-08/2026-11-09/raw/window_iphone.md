# Window test: `keyWindow`, `rootViewController` and Plyer's iOS file chooser, 2026-11-10

**Measured.** M1's iPhone app runs each case before a `UIApplication` exists, so it couldn't check the two names Plyer's iOS file chooser reads from the app's window. This test runs them in a Kivy app with a window, on the same iPhone 18 Pro Max (iOS 27.0.1, Python 3.15.0), built with KivyForge `a36c2cc`. It also runs Plyer's own file chooser, unchanged.

- **Code:** [`tests/section-08/window`](../../../../tests/section-08/window). `main.py` is the app, `make_project.py` writes its KivyForge project, and `run_window.py` launches it with M1's launcher.
- **Versions:**
  - **release:** pyobjus 1.2.4 and Rubicon 0.5.7.
  - **main:** pyobjus `master` (`0c204ad`, which reports 1.2.4) and Rubicon `main` (`6bf0639`, built as 0.5.8.dev21).
  - **Both apps:** the same pyobjus wheels as M1, Plyer 2.1.0 from PyPI, and Kivy `3.0.0.dev202610251128` from kivy-mobile-wheels, the comparison author's index, with the pins of KivyForge's `hello-kivy` example. Plyer's iOS file chooser is the same in 2.1.0 and `master` (`4853b3a`).
- **Runs:** each library ran 5 times for each version, one app launch per run, starting 1 second after Kivy's `on_start`. All 5 runs gave the same result in every case. Data: `window_iphone.json`, collected 2026-11-10 21:58 UTC, with app container paths removed.

## Results

| | pyobjus 1.2.4 and `master` | Rubicon 0.5.7 and `main` |
|---|---|---|
| `UIApplication.sharedApplication` | method | property |
| `keyWindow` | property, not nil | property, not nil |
| `rootViewController` | property | property |
| Plyer's expression, `UIApplication.sharedApplication().keyWindow.rootViewController()` | `TypeError: 'SDL_uikitviewcontroller' object is not callable` | `TypeError: 'ObjCInstance' object is not callable`, in Rubicon's form `...sharedApplication.keyWindow.rootViewController()` |
| A plain `UIViewController`, presented and dismissed without animation (control) | Presented and dismissed | Presented and dismissed |
| `UIImagePickerController`, photo library, presented with animation as Plyer does, read without `()` | Presented, seen 3.25 s after the call | Presented, seen 3.25 s after the call, with a delegate defined in Rubicon (`UIImagePickerControllerDelegate` found) |
| `load_library("Photos")` | | Loaded |
| `load_library("/System/Library/Frameworks/Photos.framework")`, the path Plyer passes to `load_framework` | | `ValueError` |
| `load_library("/System/Library/Frameworks/Photos.framework/Photos")` | | Loaded |

**Plyer 2.1.0, unchanged, on pyobjus 1.2.4 and `master`:** its iOS platform was found, and `plyer.platforms.ios.filechooser` imported, including its `load_framework` of the Photos folder path. `filechooser.open_file()` then raised `TypeError: 'SDL_uikitviewcontroller' object is not callable` at line 59, and no picker was presented, in all 10 runs.

## What this shows

- **Plyer's iOS file chooser doesn't open today.** `rootViewController` is a property in pyobjus, so Plyer's `rootViewController()` calls the view controller and raises. It's the same in Rubicon, so this is a `()` to remove in either library, not a change the move brings. Read without `()`, the picker opens in both.
- **In Rubicon,** `sharedApplication`, `keyWindow` and `rootViewController` are all properties, and the picker can have a delegate defined in Rubicon.
- **Framework paths:** Rubicon's `load_library` takes a framework's name, or the path of the binary inside it, not the `.framework` folder that pyobjus's `load_framework` takes.

## Test fixes

The first versions of the test read `presentedViewController` 1.5 seconds after presenting the picker, and found nothing in both libraries. A step-by-step probe showed that the picker appears asynchronously here, more than 1.5 seconds after the call, so the test now polls every 0.25 seconds for up to 5 seconds. An earlier version also presented the picker while the control's dismissal was still finishing, which UIKit refused in both libraries; each step now waits for the one before. pyobjus's `isKindOfClass_` didn't match the picker when given pyobjus's class wrapper, so both libraries now compare the presented controller with the picker itself, with `isEqual_`.

## Not tested

- What happens after an image is picked. That needs a person to choose one, and Plyer's delegate then calls kivy-ios's `NativeImagePicker`, which a KivyForge app doesn't have.
- Plyer's bundled `Voip.framework`. The Photos result suggests passing the binary inside it, `Voip.framework/Voip`.

## Plyer's platform check (Source)

Plyer finds iOS only from the environment variable `KIVY_BUILD == "ios"` ([`plyer/utils.py`](https://github.com/kivy/plyer/blob/4853b3a92a786237af966b86d07fa8242eee9aec/plyer/utils.py#L52)). It doesn't check `sys.platform == "ios"`, which Python 3.13 and later report on iOS. kivy-ios's `main.m` and KivyForge's bootstrap both set `KIVY_BUILD`, so this test's app found iOS. In an app that doesn't set it, Plyer reports the platform as `'unknown'` and uses its facade, which raises `NotImplementedError`. That case isn't tested here.

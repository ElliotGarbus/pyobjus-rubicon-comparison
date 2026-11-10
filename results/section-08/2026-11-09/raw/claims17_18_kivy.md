# Claims 17 and 18: how Kivy uses pyobjus, and what else it uses to reach Objective-C

**Source and Measured.** Kivy at `0f23a55`, the commit in `sample.json`. The full checkout was searched for imports of PyObjC (`objc`, `AppKit`, `Foundation`, `Cocoa`, `Quartz`, `CoreFoundation`, `UIKit`, `PyObjCTools`) and Rubicon, for ctypes calls into the Objective-C runtime (`objc_msgSend`, `objc_getClass`, `sel_registerName`, `libobjc`), and for Objective-C source files (`.m`, `.mm`). The provider loading code was then read by hand. The pyobjus files and their call counts come from U1 (`catalog.json`), and the metadata check from M3 (`m3_build.json`).

**Author's work:** `kivy.mobile`'s iOS module, listed below, is the comparison author's.

## Claim 17: Kivy doesn't require pyobjus by design

Claim 17 in the [register](../../../../CLAIMS.md), with a link to where it was made.

**What's measured:**

- **Not declared:** none of Kivy's 19 metadata, requirements and CI files names pyobjus (M3).
- **Two files use pyobjus.** Both are providers: modules Kivy tries in order, moving to the next when one fails to import.

| File | Platform | How it's loaded | Without pyobjus |
|---|---|---|---|
| [`audio_avplayer.py`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/core/audio_output/audio_avplayer.py#L9) | macOS and iOS | It's first in the audio list on macOS and iOS ([`audio_output/__init__.py`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/core/audio_output/__init__.py#L338)). The list is then registered with `core_register_libs` | `core_register_libs` catches the `ImportError`. The next providers in the list are `gstplayer`, if it imports, then `ffpyplayer`, and `sdl3` when Kivy is built with SDL3 |
| [`clipboard_nspaste.py`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/core/clipboard/clipboard_nspaste.py#L12) | macOS | It's the macOS entry in the clipboard list ([`clipboard/__init__.py`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/core/clipboard/__init__.py#L119)). The list is passed to [`core_select_lib`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/core/__init__.py#L283) | The file turns the `ImportError` into a `SystemError` that says `pip install --user pyobjus`. `core_select_lib` catches it and moves on to `sdl3` when Kivy is built with SDL3, then to `dummy` |

- **On iOS, kivy-ios always includes pyobjus.** Its `kivy` recipe depends on `pyobjus` (M3), so a Kivy app built with kivy-ios has pyobjus whether or not the app uses it.
- **Not measured:** "by design" is about intent. This file records only what the code and metadata do.

## Claim 18: Kivy already depends on pyobjus alone

Claim 18 in the [register](../../../../CLAIMS.md), with a link to where it was made.

**What's measured:** Kivy reaches Objective-C four ways besides pyobjus.

| Route | Where | Platform | How it's loaded |
|---|---|---|---|
| PyObjC | [`spelling_osxappkit.py`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/core/spelling/spelling_osxappkit.py#L16) imports `NSSpellChecker` and `NSMakeRange` from PyObjC's `AppKit`. Its docstring says to install `pyobjc` | macOS | It's a spelling provider: second after `enchant`, added when `sys.platform == 'darwin'` ([`spelling/__init__.py`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/core/spelling/__init__.py#L139)). No metadata file names PyObjC |
| ctypes calls into the Objective-C runtime | [`kivy/mobile/_platform/ios.py`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/mobile/_platform/ios.py#L1) wraps `objc_msgSend`, `objc_getClass` and `sel_registerName` to read UIKit geometry, "without adding any compiled extension dependency". The comparison author wrote it | iOS | `kivy.mobile` imports it on iOS. `kivy.metrics` and the window's safe area use it |
| Objective-C++ compiled into Cython extensions | [`camera_avfoundation_implem.mm`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/core/camera/camera_avfoundation_implem.mm), [`video_avfoundation_implem.mm`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/core/video/video_avfoundation_implem.mm) and [`img_imageio_implem.mm`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/core/image/img_imageio_implem.mm) | macOS and iOS | Built by `setup.py` for `darwin` and `ios` ([L331](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/setup.py#L331), [L1452](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/setup.py#L1452)) |
| The same, for ANGLE's Metal backend | [`egl_angle_metal_implem.mm`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/graphics/egl_backend/egl_angle_metal_implem.mm) | macOS and iOS | Built when the ANGLE backend is on, on `darwin` and `ios` ([L1558](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/setup.py#L1558)) |

- **No Rubicon:** nothing in the checkout imports it.
- **No kivy-ios `ios` module:** Kivy's own code doesn't import it. That module imports pyobjus (U1), but it belongs to kivy-ios.
- **Among Python-level Objective-C bridges,** Kivy imports two: pyobjus, in the two providers above, and PyObjC, in the spelling provider. The ctypes module and the Objective-C++ files call Apple's APIs without either bridge.

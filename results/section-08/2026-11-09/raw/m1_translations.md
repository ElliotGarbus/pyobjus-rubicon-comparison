# M1: the Rubicon way to do each pattern, 2026-11-09

Versions are at [the baseline](../../../baseline/2026-11-04.md): pyobjus 1.2.4 and `master` (built from source with Cython 3.3.1), Rubicon 0.5.7 and `main`.

- **Mac:** macOS 26.6.2, Python 3.14.7. Each of the 18 cases ran 5 times in its own process for each version: `m1_mac.json`.
- **iPhone:** iPhone 18 Pro Max, iOS 27.0.1, Python 3.15.0, apps built with KivyForge `a36c2cc`, with the iOS wheels rebuilt by Section 2's `build_wheels.sh`. 13 of the Mac cases that don't need AppKit, CoreWLAN or a dylib, plus 5 iOS cases, ran 5 times each, one app launch per run: `m1_iphone.json`. App-container paths and device IDs were removed from the saved output. The code is in [`tests/section-08/m1`](../../../../tests/section-08/m1), with the pyobjus side written as the sampled code writes it. [`mapping.json`](../../../../tests/section-08/m1/mapping.json) maps each U2 pattern to its cases. Every case gave the same result in all 5 runs, with two exceptions, both pyobjus 1.2.4:

- On the Mac, it crashed in 2 of 5 runs of `zero_arg` (SIGSEGV, SIGTRAP), and in 1 of 5 when that case was rerun with four CoreWLAN names added. Its runs that finished agreed with `master`.
- On the iPhone, kivy-ios's keyboard observer read a height of 0.0 instead of 216.0 in 1 of 5 runs (`observer_ios`).

**Test fixes.** The first iPhone run is kept in `m1_iphone_first_attempt.json`. Every Rubicon case failed there, because the iOS case file defined a second Objective-C class with the name of one in the Mac file it imports. `search_path` also compared paths without resolving the `/private/var` symlink. Both are fixed. The Rubicon cases and `search_path` were rerun, and `search_path` was rerun on the Mac too. A third fix read `CGRectValue` as the property it is in Rubicon on iOS; `observer_ios` was rerun for Rubicon. pyobjus's other iPhone results are from the first run, whose pyobjus code didn't change.

Rubicon docs are at commit `6bf0639`: [type mapping](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/topics/type-mapping.md), [protocols](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/topics/protocols.md), [C functions and constants](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/topics/c-functions.md), [memory management](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/topics/memory-management.md), and the [method-name syntax](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/api.py#L1038) in `ObjCInstance.__getattr__`.

## Translations

| Pattern (U2) | pyobjus, as the sample writes it | Rubicon | Result, Mac and iPhone |
|---|---|---|---|
| load-class | `autoclass("NSString")` | `ObjCClass("NSString")` | Same in all cases |
| load-framework | `load_framework(INCLUDE.AppKit)` or a framework path | `load_library("AppKit")` | Same |
| alloc-init | `NSString.alloc().initWithUTF8String_(s)` | Unchanged, but `initWithUTF8String_` takes `bytes`: `s.encode()`. Or pass the `str` where a method takes an `NSString` | Same text (`strings`) |
| selector-call | `pb.setString_forType_(x, t)` | Unchanged: Rubicon accepts the same flat names. Its preferred form is `pb.setString(x, forType=t)` | Same (`pasteboard` and `observer` on the Mac only, `defaults`, `observer_ios`) |
| property-or-method | `url.path()` or `url.path`, `count()`, `frame()` | Declared properties are read without `()`. Of 27 zero-argument names checked on the Mac, the sample's or their Mac equivalents, 13 are properties in Rubicon and methods in pyobjus, and calling them with `()` raises `TypeError` (table below). `NSArray.count()` raises `TypeError`, because `count` is Python's `list.count`; use `len()` | Same values once read the Rubicon way |
| objc-str | `objc_str("token")` | Not needed: a `str` argument is converted | Same (`defaults`) |
| utf8string, bytes-check | `s.UTF8String()`, then decode if `bytes` | `str(s)`. `UTF8String` is a property giving `bytes` | pyobjus 1.2.4 and `master` returned `str` here; Rubicon `bytes` |
| nsarray-index | `for i in range(a.count()): a.objectAtIndex_(i)` | `len(a)`, `a[i]`, `for x in a` | Same (`languages`, `voices`) |
| objc-arr, python-container-arg | `objc_arr(objc_str("png"), ...)`; `{}` passed for an `NSDictionary` | Pass a `list` or `dict` | Same, except pyobjus 1.2.4 lost the dictionary's value (`collections`), as Section 3 F2.5 and F7.2 found |
| delegate-self, protocol-method | `obj.delegate = self` on a Python object, with `@protocol("AVAudioPlayerDelegate")` methods | A class `PlayerDelegate(NSObject, protocols=[ObjCProtocol("AVAudioPlayerDelegate")])` with `@objc_method` methods, kept alive by Python because delegates are weak references | Same (`delegate`) |
| observer-self, selector, protocol-register | `protocols["Name"] = {encodings}`, `selector("keyboardWillShow")`, `@protocol("Name")` | An `NSObject` subclass with an annotated `@objc_method`, and `SEL("keyboardWillShow:")`. No encodings | Same (`observer` on the Mac, `observer_ios` on the iPhone), except that pyobjus 1.2.4 read 0.0 in 1 of 5 iPhone runs |
| struct-field | `frame.size.width`, `CGRectValue().size.height`, `UIScreen.mainScreen().bounds` | Same field names. On the Mac `rectValue()` stays a method; on iOS `CGRectValue` is a property | Same (`screens`, `observer`, `observer_ios`, `screen`). Both read `UIScreen`'s bounds and scale correctly, the values Carvera Controller reads in `main.m` because "pyobjus can't reliably read UIScreen struct properties" |
| enum | `enum("NSSearchPathDirectory", NSDocumentDirectory=9)` | Plain integers | Same (`search_path`) |
| error-arg | `None`, or `NSError.alloc()` | `None`, or `byref(objc_id())`, then `ObjCInstance(err)` | Both gave nil with `None`. Passing `NSError.alloc()` to a call that fails crashed pyobjus (SIGSEGV) in every run; Rubicon read the error (code 260) (`nserror_out`). Checked by hand on 2026-11-10, 3 runs each with Rubicon 0.5.7 and `main` on the Mac: passing `NSError.alloc()` to Rubicon raises `ctypes.ArgumentError` ("expected LP_objc_id instance instead of objc_id") before the method runs |
| retain-release, raw-pointer | `ctypes.cast(...)` to pass bytes, `.bytes().arg_ref`, `release()` until `retainCount()` is 1 | Pass `bytes`; `data.bytes` is a `c_void_p`. Rubicon manages reference counts ([memory management](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/topics/memory-management.md)) | Same bytes and length (`nsdata`) |
| completion-nil | `None` for the block | A Python function with type annotations | pyobjus aborted (SIGABRT) when given a function; Rubicon called it (`block`). Section 3 F4.1 and Section 4 E3 show completion handlers and CoreMotion's block-based updates, the API behind Plyer's `bridge` class |
| bool-return | `return ObjcBOOL(True)` | Annotate `-> bool` | Not rerun: Section 3 F3.7 found that both pyobjus `master` and Rubicon return the value, and pyobjus 1.2.4 returned nothing |
| App's own classes | `load_dylib(path, abs_path=True)`, `autoclass("S8Helper")` | `load_library(path)`, `ObjCClass("S8Helper")` | Same (`app_class`, Mac only). Swift `@objc` classes such as Ren'Py's `Age`: Section 3 F7.1 |
| Constants | Plyer writes `AVMediaTypeVideo` as `"vide"` | `objc_const(load_library("AVFoundation"), "AVMediaTypeVideo")` | Same value (`constant`) |
| UIKit calls (Ren'Py's idiom, KivyMD's haptics) | `UIDevice.currentDevice().userInterfaceIdiom`; `UISelectionFeedbackGenerator.alloc().init()`, `prepare()`, `selectionChanged()` | `UIDevice.currentDevice.userInterfaceIdiom`; the haptic calls unchanged | Same (`idiom`, `haptic`, iPhone) |
| C functions | `ctypes`, or an Objective-C helper such as kivy-ios's `NativeImagePicker` | `ctypes`, as Rubicon's C functions guide shows | Not rerun: Section 3 F1.5 |

## Zero-argument names (`zero_arg`, `zero_arg_ios`)

The receiver is an object of the class the sample uses, or on the Mac the Mac class with the same method. "Property" means the attribute is already the value, so `()` raises `TypeError`. The portable names gave the same answer on the Mac and the iPhone.

| Name | pyobjus 1.2.4 and `master` | Rubicon 0.5.7 and `main` | Sample calls with `()` |
|---|---|---|---:|
| `NSString.UTF8String` | method | property | 39 (Plyer 29, Ren'Py 9, Kivy 1) |
| `UIApplication.sharedApplication` (iPhone) | method | property | 6 (Plyer 4, renpy-build 1, Carvera 1) |
| `UIDevice.currentDevice` (iPhone) | method | property | 5 (Plyer 4, Ren'Py 1) |
| `NSFileManager.defaultManager` | method | property | 4 |
| `NSUserDefaults.standardUserDefaults` | method | property | 2 |
| `NSNotificationCenter.defaultCenter` | method | property | 2 (kivy-ios) |
| `NSNumber.intValue` | method | property | 2 |
| `UIScreen.mainScreen` (iPhone) | method | property | 1 (Plyer) |
| `NSValue.CGRectValue` (iPhone) | method | property | 1 (kivy-ios) |
| `NSPasteboard.generalPasteboard` (Mac) | method | property | 1 (Kivy) |
| `NSLocale.preferredLanguages` | method | property | 1 |
| `NSRunLoop.currentRunLoop` | method | property | 1 |
| `NSObject.description` | method | property | 1 |
| `NSUserNotificationCenter.defaultUserNotificationCenter` (Mac) | method | property | 1 |
| `NSScreen.screens` (Mac) | method | property | 1 |
| `NSData.bytes` | method | property | 1 |
| `NSNotification.userInfo` (from `observer`) | method | property | 1 (kivy-ios) |
| `NSScreen.mainScreen` (Mac) | method | property | 0 |
| `NSArray.count` | method | Python's `list.count`: `()` raises `TypeError` | 5 |
| `count` of `preferredLanguages` | property | Python's `list.count` | 0 |
| `NSUUID.UUIDString`, `UIDevice.userInterfaceIdiom`, `UIScreen.bounds`, `UIScreen.scale` | property | property | Unchanged |
| `NSArray.firstObject`, `lastObject`, `NSValue.rectValue` (Mac), `NSHost.currentHost`, `NSOpenPanel.openPanel`, `AVSpeechSynthesisVoice.speechVoices`, `AVSpeechSynthesizer.isSpeaking`, `AVAudioSession.sharedInstance`, `UISelectionFeedbackGenerator.prepare`, `CWWiFiClient.sharedWiFiClient`, `interface`, `CWInterface.powerOn`, `ssid` | method | method | Unchanged |

So 70 call sites in 8 repositories call a name with `()` that Rubicon reads as a property, 57 of them checked on the Mac and 13 on the iPhone, and 5 call `count()` on an array. Calls are counted in the sampled files' iOS and macOS code, as for U2.

**Not checked:** `UIApplication.keyWindow` and `rootViewController` (1 call each, Plyer's iOS filechooser). The test app runs each case before a `UIApplication` exists, so `sharedApplication` returned nil in both libraries.

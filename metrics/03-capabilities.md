# Section 3 metric definitions

**Status: approved 2026-11-07.** These definitions were written before the Section 3 data was collected. Changes made after that are recorded at the end of this document with their reasons.

Section 3 records what each library can do through its public API, what it can't, and what a developer has to do instead. Section 2 explained how features work. Section 3 asks whether a feature exists, whether it's documented, and whether it works in a minimal test.

## What was seen before these were written

| Seen before writing (2026-11-07) | Where | Effect on the rules |
|---|---|---|
| All of Section 2's results, including that pyobjus has no public way to write blocks, function pointers or subclasses, and that Rubicon blocks need a patch to return structs | [Section 2](../sections/02-architecture.md) | Rows that Section 2 already tested cite its result instead of rerunning it. The feature list is drawn from both libraries' docs and APIs, not from Section 2's failures |
| The public API and doc headings of both libraries at the pinned commits | Baseline commits | The feature list below comes from this survey. A feature either library documents is a row, so each library's distinctive features appear |
| pyobjus can register protocol encodings at runtime, so `@protocol` works for protocols missing from `protocols.py` | [akshayaurora's comment](https://github.com/kivy/kivy/issues/9469#issuecomment-6517712158) | Tested as a row, using the pattern from that comment |
| BridgeSupport files list only declarations that need more type information than the runtime gives: Foundation's lists 46 NSString methods, and the runtime reports 303 instance methods | `Foundation.bridgesupport` and the runtime, on this Mac | BridgeSupport can't be the count of Apple's API, so A1 and A2 use the SDK headers, and BridgeSupport is only a cross-check (A3) |
| A trial parse of UIKit's iOS 27.0 headers with clang found 8,732 method declarations, 103 C functions and 4 variadic methods, with full block signatures. Duplicates and availability weren't filtered | iOS 27.0 SDK, this Mac. No library was run | The header method was chosen for A. No library's support was mapped to these counts |
| The author's KivyForge guide to calling Swift, and its pyobjus findings. They report pyobjus defects with a `dict` argument, delegate return values, exceptions in delegates and nested lists, and Rubicon behavior with completion-handler arguments and `Bool` values in collections. Its pyobjus results came from a development build, `1.2.5.dev202610250845`, that is neither tested version, and the test app wasn't kept | [Call Swift from Python](https://github.com/ElliotGarbus/kivyforge/blob/edaa3aa8c4eb2f1a4f9f1b42a7c7b7350ae55012/docs/guides/guides/ios/swift.md) and [its findings](https://github.com/ElliotGarbus/kivyforge/blob/edaa3aa8c4eb2f1a4f9f1b42a7c7b7350ae55012/docs/design/dev/swift-bridge-spike-findings.md), both written by the author | F7 was added for Swift. The guide's findings aren't cited as results. Each one is retested at both versions of each library |
| pyobjus's docs list bit fields and unions by value as missing, citing libffi | [Remarks](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/remarks.rst) | Both are rows for both libraries |
| The author wrote several pyobjus changes now on `master`, including `None` as `NULL` for pointer arguments, `CArray` type codes, nested struct types and delegate return values | pyobjus merge history | pyobjus is tested at its release and its default branch, so this work is credited where it applies |

## Scope and common rules

- **Versions and platforms:** the same as Section 2: [the 2026-11-04 baseline](../results/baseline/2026-11-04.md), on the Apple Silicon Mac (Python 3.14) and the iPhone (Python 3.15). A result is shown once if both versions of a library match, and separately if they differ.
- **Public API:** a feature counts as supported only if it's reachable through what the library exports. Rubicon's `rubicon.objc.runtime` module is exported and documented, so it counts. Using `ctypes` directly beside either library is a workaround, not support.
- **Three checks per row:**
  - **API (Source):** a public way to do it exists, linked at the pinned commit.
  - **Docs (Source):** the library's docs at the pin describe it. A feature that works but isn't described is "undocumented".
  - **Works (Measured):** a minimal test, run 5 times, each in its own process, on both platforms. A row Section 2 already tested cites that scenario.
- **Results:** each cell is one of: supported; supported with a stated limit; undocumented; workaround with `ctypes`; workaround with an Objective-C helper compiled into the app; not supported. The workaround named is the simplest one known, with its code published.
- **Tests:** in `tests/section-03/`, reusing Section 2's fixture where it fits. PyObjC 13.0 runs as a control on the Mac, reported separately, to help separate a library's limit from a faulty test.
- **Outside rows:** anyone can propose a feature with code, especially something one library can do and the other can't. Rows proposed before results are written are added and tested. Results are published whichever library they favor.
- **No scoring:** rows aren't counted as wins, weighted or combined.

## F. Feature matrix

Each row is tested as defined. The examples given are the ones the tests use.

### F1. Calling Objective-C and C

| ID | Feature | Definition |
|---|---|---|
| F1.1 | Classes and methods | Look up a class by name, call class and instance methods, including multi-part selectors |
| F1.2 | Properties | Read and write a declared property, such as `NSURLComponents.host` |
| F1.3 | Variadic methods | Call `+[NSString stringWithFormat:]` and `+[NSArray arrayWithObjects:]` |
| F1.4 | Global constants | Read an object constant (`NSLocaleCountryCode`) and a scalar constant (`NSFoundationVersionNumber`) |
| F1.5 | C functions | Call a plain C function (`NSStringFromClass`) and one returning a struct (`NSMakeRange`) |
| F1.6 | Loading code | Load a system framework, and a dylib built by the app |
| F1.7 | Introspection | List a class's methods and properties from Python, for example through `dir()` |

### F2. Types

| ID | Feature | Definition |
|---|---|---|
| F2.1 | Structs | Built-in structs, a struct the user defines, a nested struct and a pointer to a struct |
| F2.2 | Unions and bit fields | A union passed and returned by value, and a struct with bit fields |
| F2.3 | C arrays | A fixed-size array, and an array with a separate count argument |
| F2.4 | Out parameters | A scalar out parameter, and an object out parameter (`NSError **`) |
| F2.5 | Collections | Converting `list` and `dict` to and from `NSArray` and `NSDictionary`, automatically and by an explicit call, including a `BOOL` stored as an `NSNumber` |
| F2.6 | Python behavior on Objective-C objects | `len()`, indexing, iteration and `in` on `NSArray` and `NSDictionary`, and string operations on `NSString` |
| F2.7 | Enums and constants | Defining or importing named integer constants |

### F3. Defining Objective-C behavior in Python

| ID | Feature | Definition |
|---|---|---|
| F3.1 | New class | Define a class that subclasses `NSObject`, with instance and class methods |
| F3.2 | Subclass an Apple class | Subclass an existing class, override a method and call the superclass's version |
| F3.3 | Instance state | Instance variables and properties on a class defined in Python |
| F3.4 | Apple protocol | Implement a protocol Apple declares, and receive a delegate call |
| F3.5 | Protocol not known in advance | Implement a protocol the library doesn't ship metadata for, including one declared only by the app. pyobjus uses the runtime registration pattern from claim 11 |
| F3.6 | Selector targets | Register a method as a target for `NSNotificationCenter` and a timer |
| F3.7 | Delegate values | A delegate method receiving and returning an object, a scalar, a struct, a union and a C array |
| F3.8 | Removing a delegate | A public way to release a Python-defined object the library is holding |

### F4. Blocks and function pointers

| ID | Feature | Definition |
|---|---|---|
| F4.1 | Completion handlers | Create a block in Python and pass it as a completion handler |
| F4.2 | Received blocks | Call a block received from Objective-C, such as an enumeration block's `stop` handling |
| F4.3 | GCD | Run Python code on the main queue with `dispatch_async` |
| F4.4 | Function pointers | Pass a Python function where a C function pointer is expected |

### F5. Runtime services

| ID | Feature | Definition |
|---|---|---|
| F5.1 | Memory management | Whether management is automatic, plus public retain, release, autorelease pool and weak reference APIs. Behavior is cited from Section 2 |
| F5.2 | Objective-C exceptions | Whether an exception can be caught in Python. Behavior is cited from Section 2 |
| F5.3 | Event loops | Integrating `asyncio` with the Core Foundation run loop, `NSApplication` and `UIApplication` |
| F5.4 | Main thread | A public way to run Python code on the main thread |

### F6. Platforms (Source)

| ID | Feature | Definition |
|---|---|---|
| F6.1 | Declared platforms | The operating systems and architectures each library's metadata, docs and published artifacts cover. Only the Mac and the iPhone are tested |

### F7. Swift

Neither library calls Swift directly. Both reach Swift code through classes marked `@objc`, which appear in the Objective-C runtime. These rows use a small Swift test library, built with `swiftc` as a dylib on the Mac and as a KivyForge local package on the iPhone. Swift behavior that depends on another row, such as blocks or out parameters, is tested here because Swift exports it in its own form.

| ID | Feature | Definition |
|---|---|---|
| F7.1 | Finding Swift classes | Look up a class by its explicit `@objc` name, and by the name Swift generates when there isn't one |
| F7.2 | Swift values | `String`, `Int`, `Double`, `Bool` and optional returns. Nested `[String]`, `[Int]` and `[String: Any]` containing a `Bool`. A Python `list` and `dict` passed as arguments |
| F7.3 | Throwing methods | The value on success, the result on failure, and reading the `NSError` |
| F7.4 | `async` methods | The completion handler Swift generates, including the two-argument handler of an `async throws` method, called from one of Swift's threads |
| F7.5 | Swift protocols in Python | Implement a Swift `@objc` protocol: receive arguments, return a `Bool`, an `Int` and an object, raise an exception, and be called from the main thread and a background thread |
| F7.6 | Swift-only APIs (Source) | Structs, generics, enums with associated values and functions not marked `@objc`: whether either library has any route to them |

## A. Reach into Apple's API

| ID | Metric | Definition | Source | Label |
|---|---|---|---|---|
| A1 | macOS API reach | The public Objective-C API in the macOS SDK headers, classified by the kinds of value each declaration needs. Each kind is matched to the F results, giving the share of declarations each library can express, per framework and kind | SDK headers, F results | Inferred |
| A2 | iOS API reach | The same count from the iOS SDK headers | SDK headers, F results | Inferred |
| A3 | Cross-check | On macOS, the kinds A1 assigns compared with BridgeSupport's annotations, for every declaration both list. Each disagreement is published with how it was resolved | SDK headers, BridgeSupport | Source |
| A4 | Swift-only frameworks | The frameworks in each SDK that have a Swift interface (`.swiftinterface`) and no Objective-C headers, which neither library can reach without a shim. Frameworks with both are counted separately | SDKs | Source |

**Reading the headers:** Xcode 27.0's clang parses each framework's umbrella header for the platform and dumps its syntax tree. The script and the compiler version are published. Apple's BridgeSupport generator isn't used.

**What's counted:** class methods, instance methods and properties, C functions and constants, each declared once. Category methods count with their class. A property counts once, not as a getter and setter.

**Filtered to the tested systems:** both SDKs are version 27.0, newer than macOS 26.6.2 on the Mac. A declaration is left out if its availability marking says it was introduced after the tested version (macOS 26.6.2, iOS 27.0.1) or is unavailable on that platform. Deprecated declarations are kept and counted separately.

**Calling and implementing are counted separately:**
- **To call:** methods of classes, C functions and constants. A block parameter needs F4.1, and a block that's returned needs F4.2.
- **To implement:** protocol methods, which the app writes and Objective-C calls. A struct parameter needs F3.7. A block parameter, such as a completion handler passed to a delegate, needs F4.2.

**Kinds of value:** objects and scalars only; struct by value; union by value; C array; out parameter or other pointer; block; function pointer; variadic. Each kind maps to an F row. A declaration with several kinds is expressible only if the library supports all of them, and it's listed under the first kind it can't express.

**Frameworks:** totals across all Objective-C frameworks in each SDK, and a table per framework:
- **macOS:** Foundation, AppKit, AVFoundation, CoreBluetooth, CoreLocation, StoreKit and UserNotifications.
- **iOS:** UIKit, Foundation, AVFoundation, CoreBluetooth, CoreLocation, Photos, StoreKit and UserNotifications.

**Limits of A:** these counts show what can be written, not what apps use. A declaration's kinds come from its header, not from calling it, and Section 2's T5 is the sample that was called. APIs that exist only in Swift aren't in these headers. A4 counts the Swift-only frameworks, and F7.6 covers Swift-only APIs. A4 describes a limit both libraries share. PySwiftKit, which takes a different approach, gets a short note, as [METHODOLOGY.md](../METHODOLOGY.md) provides for other bridges.

## L. Stated limits and open gaps

| ID | Metric | Definition | Source | Label |
|---|---|---|---|---|
| L1 | Documented limits | What each library's docs say it can't do, quoted and linked at the pin | Docs | Source |
| L2 | Open capability issues | Open issues at Section 1's snapshot that report a missing feature or a feature that doesn't work, each matched to an F row. The list and how each was classified are published | GitHub | Reported |

## Deliberately excluded

| Measure | Why |
|---|---|
| How a feature works internally | Section 2 covers this |
| How much code a task takes, and how readable it is | Section 4 covers this with side-by-side examples |
| Python versions in CI and test coverage | Section 5 covers this |
| Speed and memory amounts | Section 6 covers this |
| Which features Kivy and its projects use | Sections 7 and 8 cover this |
| "Easier", "more Pythonic" or "more complete" | These are judgments, so the section reports the rows behind them |

## Claims this section reports on

| Claim ([register](../CLAIMS.md)) | Evidence |
|---|---|
| 8. Each library can do things the other can't | The F rows where only one library is supported, and any rows proposed under the outside-rows rule |
| 9. pyobjus can't create blocks, so APIs with completion handlers need Objective-C helper code | F4.1 and F4.2, the block counts in A1 and A2 for both calling and implementing, and the simplest workaround for F4.1 |
| 10. pyobjus can't subclass Objective-C classes from Python | F3.1 and F3.2 |
| 11. pyobjus delegates can register protocols at runtime, but can't pass struct, union or array values | F3.5 and F3.7 |

## Changes after approval

| Metric | Change | Reason |
|---|---|---|
| F1.5 | The C function that returns a struct is `NSRangeFromString`, not `NSMakeRange` | `NSMakeRange` is an inline function, so there's no symbol for either library to call. Found while writing the tests, before any run |
| A1, A2 | Shares are of the declarations the cases cover. Inline functions and declarations needing a kind no case tested are counted separately | Both groups are the same for both libraries. Counting them in the share showed a gap for Rubicon that no case measured. Changed after the results were in, before the section was published, at the author's request. `reach_mac.json` and `reach_ios.json` hold the counts for either way of reporting |

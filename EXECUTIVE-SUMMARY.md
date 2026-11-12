# pyobjus and Rubicon: executive summary

**Status: draft for review.** This summarizes the eight sections of the [pyobjus and Rubicon comparison](README.md) for [kivy/kivy#9469](https://github.com/kivy/kivy/issues/9469). Each section is measured, with its tests and raw data published. The sections make no recommendation; the recommendation at the end is mine, as the comparison's author.

## Key findings

1. **[History and maintenance](sections/01-history-and-maintenance.md):** Rubicon has had steadier activity from more people: commits in nearly every month since 2023, a median of 107 days between stable releases against 502, and 9 contributors in the last 12 months against 3. Most of pyobjus's recent work came in October 2026, largely from me, and none of it is in a PyPI release yet.
2. **[Architecture](sections/02-architecture.md):** Rubicon frees the objects and delegates it creates, releases the GIL during calls, and got all 73 sampled Apple methods right. pyobjus doesn't free delegates, or objects from `alloc`, `new` or `copy` unless the code releases them by hand, holds the GIL during calls, and couldn't express 45 of the 73 Apple methods.
3. **[Capabilities](sections/03-capabilities.md):** Rubicon can create and call blocks, pass function pointers, subclass Objective-C classes, and call C functions and constants. pyobjus can do none of these. Applying those test results to every declaration in Apple's SDK headers, pyobjus can express about half of the API the tests cover, 50% on macOS and 56% on iOS, against all of it for Rubicon.
4. **[Examples](sections/04-examples.md):** where an API delivers results only through a block, as Core Motion's barometer does, pyobjus needs 31 lines of compiled Objective-C and Rubicon needs none. Where both can do a task directly, the code is about the same size.
5. **[Testing and CI](sections/05-testing-and-ci.md):** Rubicon's testing is more complete where it reaches users: its full suite runs on macOS and the iOS simulator, against the exact wheel it publishes, with 89.7% coverage at its release. pyobjus has no iOS tests, only import-tests the macOS wheels it publishes, and its release has no coverage measure or memory tests, which its unreleased `master` adds.
6. **[Performance](sections/06-performance.md):** Rubicon is faster for every call measured: a delegate call takes 0.9 µs against 128 µs on the iPhone, and returning an object is 10 to 20 times faster. pyobjus's memory grows with use, while Rubicon's stays flat.
7. **[Ecosystem](sections/07-ecosystem.md):** the two have similar breadth of direct public use: 84 public repositories import pyobjus and 78 import Rubicon. pyobjus's most-starred users are Kivy, Ren'Py, KivyMD and Plyer, while most of Rubicon's are outside BeeWare.
8. **[Compatibility and migration](sections/08-compatibility-and-migration.md):** code written for pyobjus maps concept for concept onto Rubicon. Method calls in pyobjus's underscore form run unchanged, and the main work is reading properties without `()`, moving delegates into `NSObject` subclasses, and swapping a compiled dependency for a pure-Python one. Some of Plyer's code doesn't work on pyobjus today: its iOS file chooser fails before opening.

## Recommendation

**This is my recommendation, as the comparison's author: Kivy's own code and packaging should standardize on Rubicon, with Rubicon as the only bridge Kivy itself uses from Kivy 3.0.**

On the evidence above, Rubicon is the more effective bridge for Kivy's needs. It's maintained more consistently by more people. It reaches all of the Apple API the tests cover, against about half for pyobjus, including the roughly 1,500 macOS and 1,900 iOS methods and properties that take or return a block, such as a completion handler. It frees the memory pyobjus keeps, is faster for every call measured, and runs its test suite on the iOS simulator in CI. It installs as one pure-Python wheel on every Python version, with no recipe, compiler or patches. The move is a translation, not a rewrite.

**Scope:**
- **Kivy core:** the AVPlayer audio and macOS clipboard providers, 2 files with 8 calls.
- **kivy-ios:** the `ios` module's keyboard observer, and the `kivy` recipe, which makes pyobjus part of every kivy-ios build. Rubicon needs no recipe, because kivy-ios installs pure-Python packages with `toolchain pip install`.
- **Docs:** Rubicon as the bridge Kivy's docs use for iOS and macOS, linking to the [migration guide](guides/migrate-from-pyobjus-to-rubicon.md).

**Timing:** one cutover, in Kivy 3.0, which is where Kivy's iOS support is being modernized. Kivy 2.x stays on pyobjus, and 3.0 moves to Rubicon.

**pyobjus stays available.** Apps can keep using pyobjus, or any other bridge, and anyone can keep maintaining it. What changes is that Kivy itself stops depending on it, so the project's own effort goes into one bridge. The cost is the porting work, and one change for apps: those that call pyobjus directly add it to their own build, because Kivy no longer brings it in.

**Plyer** is a separate effort. Its last release was in 2022 and some of its iOS code doesn't work today, so its move belongs with work to revitalize it.

**The decisions I'm asking for:**
1. **Kivy:** that Kivy's maintainers agree on this direction and the 3.0 target. With that agreement, I'll open the pull requests, starting with Kivy core and kivy-ios's `ios` module.
2. **pyobjus:** that pyobjus's README opens with a note recommending Rubicon, and that a guide to migrating from pyobjus to Rubicon is published in the pyobjus repository, so its existing users find both where they already look.

**My role:** I opened the proposal in kivy/kivy#9469 and was pyobjus's most active recent contributor before stopping. All of the comparison's tests and data are public, so anyone can check these findings independently.

# Migrate from pyobjus to Rubicon

This guide shows you how to move Python code that calls Objective-C APIs on
macOS and iOS from [pyobjus](https://github.com/kivy/pyobjus) to
[Rubicon](https://rubicon-objc.beeware.org/en/stable/) (the `rubicon-objc`
package). It covers the patterns that Kivy, Plyer, and other projects that
use pyobjus rely on most: loading classes, calling methods, reading
properties, converting strings and collections, implementing delegates,
passing blocks, and handling errors.

Each section shows the pyobjus code you have and the Rubicon code that
replaces it. The complete examples were run on macOS with pyobjus 1.2.4 and
Rubicon 0.5.7. The iOS property names in this guide were checked on an
iPhone. The short iOS snippets and the Kivy example show the shape of the
change and weren't run as written. To rerun the complete examples, use
[`check_examples.py`](check_examples.py), which runs each one and compares
its output with the guide.

## Before you begin

- Use Python 3.11 or later. Rubicon 0.5.7 requires Python 3.11 or later.
- Find every file that imports pyobjus. Search for `pyobjus` in your
  project, including imports inside functions.
- Read Rubicon's [Your first bridge](https://rubicon-objc.beeware.org/en/stable/tutorial/tutorial-1/)
  tutorial. It introduces the names this guide uses.

## Summary of changes

Most pyobjus code moves to Rubicon with small, local changes. The following
table lists them. Each row links to the section that explains it.

| pyobjus | Rubicon |
|---|---|
| `autoclass("NSString")` | [`ObjCClass("NSString")`](#load-classes-and-frameworks) |
| `load_framework(INCLUDE.AVFoundation)` | [`load_library("AVFoundation")`](#load-classes-and-frameworks) |
| `obj.setObject_forKey_(value, key)` | [Unchanged](#call-methods) |
| `NSFileManager.defaultManager()` | [`NSFileManager.defaultManager`](#read-properties-without-parentheses), without `()` |
| `s.UTF8String()` | [`str(s)`](#convert-strings) |
| `objc_str("text")` | [`"text"`](#convert-strings) |
| `objc_arr(a, b)`, `array.count()`, `array.objectAtIndex_(i)` | [`[a, b]`, `len(array)`, `array[i]`](#work-with-arrays-and-dictionaries) |
| `enum(...)` values, string copies of constants | [Plain integers, `objc_const(...)`](#use-enums-and-constants) |
| `@protocol("...")` on a Python object | [An `NSObject` subclass with `@objc_method`](#implement-a-delegate) |
| `protocols["Name"] = {...}`, `selector("name")` | [`SEL("name:")`](#receive-notifications-and-target-action-calls) |
| `return ObjcBOOL(True)` | [`return True`, with `-> bool`](#return-values-from-callbacks) |
| `None` for a completion block | [A Python function](#pass-blocks) |
| `NSError.alloc()` for an `NSError **` argument | [`byref(objc_id())`](#handle-nserror-output-arguments) |
| `ctypes.cast(...)`, `release()`, `retainCount()` | [Python `bytes`, and automatic reference counting](#work-with-bytes-and-memory) |
| `load_dylib(path)` | [`load_library(path)`](#load-your-apps-own-classes) |

## Install Rubicon

Rubicon is pure Python, so you install it the same way on every platform and
Python version, with no compiler.

1.  Add `rubicon-objc` to your project's dependencies and remove `pyobjus`:

    ```bash
    pip install rubicon-objc
    ```

2.  Remove pyobjus from your build configuration. Check these places:
    - Package metadata, such as `extras_require` in `setup.py` or
      `optional-dependencies` in `pyproject.toml`.
    - `requirements` in `buildozer.spec`.
    - kivy-ios recipe dependencies that name `pyobjus`.
    - Xcode projects that link `libpyobjus`.

3.  For iOS, install the `rubicon-objc` wheel into your app the way your
    build tool installs other pure-Python packages. With kivy-ios, pure-Python
    packages are installed with `toolchain pip install`.

    Rubicon needs no kivy-ios recipe. kivy-ios installs pure-Python packages
    with `toolchain pip install`:

    ```bash
    toolchain pip install rubicon-objc
    ```

    **Note:** This command isn't verified for this guide.

## Update imports

Replace pyobjus imports with their Rubicon equivalents:

| pyobjus | Rubicon |
|---|---|
| `from pyobjus import autoclass` | `from rubicon.objc import ObjCClass` |
| `from pyobjus.dylib_manager import load_framework, INCLUDE` | `from rubicon.objc.runtime import load_library` |
| `from pyobjus.dylib_manager import load_dylib` | `from rubicon.objc.runtime import load_library` |
| `from pyobjus import protocol` | `from rubicon.objc import NSObject, ObjCProtocol, objc_method` |
| `from pyobjus import selector` | `from rubicon.objc import SEL` |
| `from pyobjus import objc_str, objc_arr, objc_dict` | Not needed |
| `from pyobjus import ObjcBOOL` | Not needed |
| `from pyobjus import enum` | Not needed |

## Load classes and frameworks

pyobjus loads a class with `autoclass()` and a framework with
`load_framework()`. Rubicon uses `ObjCClass()` and `load_library()`.

pyobjus:

<!-- run: pyobjus -->
```python
from pyobjus import autoclass, objc_str
from pyobjus.dylib_manager import load_framework, INCLUDE

load_framework(INCLUDE.AVFoundation)
AVSpeechSynthesisVoice = autoclass("AVSpeechSynthesisVoice")
voice = AVSpeechSynthesisVoice.voiceWithLanguage_(objc_str("en-US"))
print(voice is not None)
# Prints: True
```

Rubicon:

<!-- run: rubicon -->
```python
from rubicon.objc import ObjCClass
from rubicon.objc.runtime import load_library

avfoundation = load_library("AVFoundation")
AVSpeechSynthesisVoice = ObjCClass("AVSpeechSynthesisVoice")
voice = AVSpeechSynthesisVoice.voiceWithLanguage_("en-US")
print(voice is not None)
# Prints: True
```

`load_library()` takes the framework's name and returns the loaded library.
Keep the returned value if you need the framework's
[constants](#use-enums-and-constants) or [C functions](#call-c-functions).
Foundation is loaded with Rubicon, so you don't need to load it yourself.

If `ObjCClass()` raises `NameError: ObjC Class ... couldn't be found`, load
the framework that defines the class first.

For more information, see
[`ObjCClass`](https://rubicon-objc.beeware.org/en/stable/reference/rubicon-objc-api/#rubicon.objc.api.ObjCClass)
and
[`load_library`](https://rubicon-objc.beeware.org/en/stable/reference/rubicon-objc-runtime/#rubicon.objc.runtime.load_library).

## Call methods

pyobjus names a method with arguments by replacing each colon in its
Objective-C name with an underscore, such as `setObject_forKey_(...)`.
Rubicon accepts the same form, so these calls don't change.

Rubicon also accepts an *interleaved* form, which reads like Objective-C: the
first part of the name is the attribute, and each later part is a keyword
argument. The following example uses both forms:

<!-- run: rubicon -->
```python
from rubicon.objc import ObjCClass

NSUserDefaults = ObjCClass("NSUserDefaults")
defaults = NSUserDefaults.alloc().initWithSuiteName_("org.example.migration")

# The pyobjus form works unchanged.
defaults.setObject_forKey_("blue", "theme")

# The interleaved form calls the same method.
defaults.setObject("large", forKey="size")

print(defaults.stringForKey_("theme"), defaults.stringForKey("size"))
# Prints: blue large

defaults.removePersistentDomainForName_("org.example.migration")
```

You don't need to rename methods when you migrate. You can move to the
interleaved form later, one call at a time.

For more information, see
[`ObjCInstance`](https://rubicon-objc.beeware.org/en/stable/reference/rubicon-objc-api/#rubicon.objc.api.ObjCInstance)
and [Invoking Objective-C methods](https://rubicon-objc.beeware.org/en/stable/topics/type-mapping/#invoking-objective-c-methods).

## Read properties without parentheses

Property reads need the most care, because the pyobjus code still looks
valid and fails only when it runs. Rubicon reads an Objective-C declared
property as a Python attribute, so you don't call it.
pyobjus treats most of these names as methods, so pyobjus code calls them
with `()`.

pyobjus:

<!-- run: pyobjus -->
```python
from pyobjus import autoclass

NSFileManager = autoclass("NSFileManager")
manager = NSFileManager.defaultManager()
print(manager.fileExistsAtPath_("/"))
# Prints: True
```

Rubicon:

<!-- run: rubicon -->
```python
from rubicon.objc import ObjCClass

NSFileManager = ObjCClass("NSFileManager")
manager = NSFileManager.defaultManager
print(manager.fileExistsAtPath_("/"))
# Prints: True
```

If you call a property with `()` in Rubicon, Python calls the value it
returned and raises an error such as `TypeError: 'ObjCInstance' object is
not callable`.

The following names are properties in Rubicon and are commonly called with
`()` in pyobjus code:

| Class | Properties |
|---|---|
| `NSString` | `UTF8String` (see [Convert strings](#convert-strings)) |
| `NSObject` | `description` |
| `NSFileManager` | `defaultManager` |
| `NSUserDefaults` | `standardUserDefaults` |
| `NSNotificationCenter` | `defaultCenter` |
| `NSNotification` | `userInfo` |
| `NSLocale` | `preferredLanguages` |
| `NSRunLoop` | `currentRunLoop` |
| `NSNumber` | `intValue` |
| `NSData` | `bytes` |
| `NSScreen` (macOS) | `screens`, `mainScreen` |
| `NSPasteboard` (macOS) | `generalPasteboard` |
| `NSUserNotificationCenter` (macOS) | `defaultUserNotificationCenter` |
| `UIApplication` (iOS) | `sharedApplication` |
| `UIDevice` (iOS) | `currentDevice` |
| `UIScreen` (iOS) | `mainScreen` |
| `UIApplication` (iOS) | `keyWindow` |
| `UIWindow` (iOS) | `rootViewController` |
| `UIViewController` (iOS) | `presentedViewController` |
| `NSValue` (iOS) | `CGRectValue` |

To check a name that isn't listed, open the class in
[Apple's developer documentation](https://developer.apple.com/documentation/)
and look at the Objective-C declaration. A declaration that starts with
`@property` is a property, so you read it without `()`. A declaration that
starts with `-` or `+` is a method, so you call it. For example,
`lastObject` on `NSArray` and `sharedInstance` on `AVAudioSession` are
methods in both libraries.

You set properties the same way in both libraries, for example
`player.volume = 0.5`.

**Caution:** `UUIDString` on `NSUUID` and `rootViewController` on
`UIWindow` are properties in pyobjus too. If your pyobjus code calls
`UUIDString()` or `rootViewController()`, it raises an error in either
library. Read them without `()`. For example, Plyer's iOS file chooser calls
`keyWindow.rootViewController()`, so it raises `TypeError` with pyobjus as
well as with Rubicon.

For more information, see
[Objective-C properties](https://rubicon-objc.beeware.org/en/stable/tutorial/tutorial-2/#objective-c-properties)
and
[`ObjCInstance`](https://rubicon-objc.beeware.org/en/stable/reference/rubicon-objc-api/#rubicon.objc.api.ObjCInstance),
which describes how Rubicon decides that a name is a property.

## Convert strings

pyobjus code converts strings in both directions by hand. Rubicon converts
them for you.

- **Python to Objective-C:** pass a `str` wherever a method takes an
  `NSString`. Remove `objc_str()` and `NSString.alloc().initWithUTF8String_()`
  calls that exist only to make an `NSString`.
- **Objective-C to Python:** call `str()` on the `NSString`. In Rubicon,
  `UTF8String` is a property that returns `bytes`, so replace
  `s.UTF8String()` with `str(s)`.
- **Bytes checks:** remove code that checks whether `UTF8String()` returned
  `bytes` and decodes it. `str()` always returns a `str`.

pyobjus:

<!-- run: pyobjus -->
```python
from pyobjus import autoclass, objc_str

NSString = autoclass("NSString")
NSUserDefaults = autoclass("NSUserDefaults")

defaults = NSUserDefaults.alloc().initWithSuiteName_(objc_str("org.example.migration"))
defaults.setObject_forKey_(objc_str("Grüße"), objc_str("greeting"))
value = defaults.stringForKey_(objc_str("greeting")).UTF8String()
if isinstance(value, bytes):
    value = value.decode("utf-8")
print(value)
# Prints: Grüße

defaults.removePersistentDomainForName_(objc_str("org.example.migration"))
```

Rubicon:

<!-- run: rubicon -->
```python
from rubicon.objc import ObjCClass

NSUserDefaults = ObjCClass("NSUserDefaults")

defaults = NSUserDefaults.alloc().initWithSuiteName_("org.example.migration")
defaults.setObject_forKey_("Grüße", "greeting")
value = str(defaults.stringForKey_("greeting"))
print(value)
# Prints: Grüße

defaults.removePersistentDomainForName_("org.example.migration")
```

An `NSString` returned by Rubicon already behaves like a `str` for most
operations, such as comparison, slicing, and `split()`. Use `str()` when you
pass the value to Python code that checks for `str`, or when you store it.

If you keep a call to `initWithUTF8String_()`, pass `bytes`, such as
`text.encode("utf-8")`. That method takes a C string, and passing a `str`
raises `ArgumentError`.

For more information, see
[Strings](https://rubicon-objc.beeware.org/en/stable/topics/type-mapping/#strings).

## Work with arrays and dictionaries

Rubicon converts Python lists and dictionaries to `NSArray` and
`NSDictionary` when you pass them to a method. It also gives `NSArray` and
`NSDictionary` Python behavior, so you can use `len()`, indexing, and
iteration.

pyobjus:

<!-- run: pyobjus -->
```python
from pyobjus import autoclass, objc_arr, objc_str

NSArray = autoclass("NSArray")
types = NSArray.arrayWithArray_(objc_arr(objc_str("png"), objc_str("jpg")))
names = []
for i in range(types.count()):
    name = types.objectAtIndex_(i).UTF8String()
    if isinstance(name, bytes):
        name = name.decode("utf-8")
    names.append(name)
print(names)
# Prints: ['png', 'jpg']
```

Rubicon:

<!-- run: rubicon -->
```python
from rubicon.objc import ObjCClass

NSArray = ObjCClass("NSArray")
types = NSArray.arrayWithArray_(["png", "jpg"])
names = [str(t) for t in types]
print(names, len(types), types[0])
# Prints: ['png', 'jpg'] 2 png
```

**Caution:** Don't call `count()` on an `NSArray` in Rubicon. Rubicon gives
`NSArray` the methods of a Python list, so `count` is the list method
`count(value)`, and calling it with no argument raises `TypeError`. Use
`len()` instead.

For more information, see
[Lists](https://rubicon-objc.beeware.org/en/stable/topics/type-mapping/#lists)
and
[Dictionaries](https://rubicon-objc.beeware.org/en/stable/topics/type-mapping/#dictionaries).

## Use enums and constants

Pass enum values as plain integers. You don't need to declare them with
pyobjus's `enum()`.

<!-- run: rubicon -->
```python
from rubicon.objc import ObjCClass

NSDocumentDirectory = 9
NSUserDomainMask = 1

manager = ObjCClass("NSFileManager").defaultManager
urls = manager.URLsForDirectory_inDomains_(NSDocumentDirectory, NSUserDomainMask)
print(str(urls.lastObject().lastPathComponent))
# Prints: Documents
```

pyobjus can't read exported Objective-C constants, so pyobjus code often
copies their values, such as `"vide"` for `AVMediaTypeVideo`. In Rubicon,
read the constant from its framework with `objc_const()`:

<!-- run: rubicon -->
```python
from rubicon.objc import objc_const
from rubicon.objc.runtime import load_library

avfoundation = load_library("AVFoundation")
AVMediaTypeVideo = objc_const(avfoundation, "AVMediaTypeVideo")
print(AVMediaTypeVideo)
# Prints: vide
```

For more information, see
[Objective-C object constants](https://rubicon-objc.beeware.org/en/stable/topics/c-functions/#objective-c-object-constants).

## Read structs

Struct fields have the same names in both libraries, such as
`frame.size.width`. When a method takes a struct, you can pass a tuple, and
Rubicon converts it.

<!-- run: rubicon -->
```python
from rubicon.objc import NSMakeRect, ObjCClass

NSValue = ObjCClass("NSValue")
value = NSValue.valueWithRect_(NSMakeRect(0, 0, 390, 216))
print(value.rectValue().size.height)
# Prints: 216.0
```

Some struct getters are properties in Rubicon. For example, on iOS,
`NSValue.CGRectValue` is a property, so you read
`value.CGRectValue.size.height`. `UIScreen.mainScreen.bounds` and
`UIScreen.mainScreen.scale` read correctly in Rubicon, so you don't need to
read them in Objective-C and pass them to Python.

For more information, see
[Argument conversion](https://rubicon-objc.beeware.org/en/stable/topics/type-mapping/#argument-conversion).

## Implement a delegate

In pyobjus, you set a Python object as a delegate and mark its callback
methods with `@protocol`. In Rubicon, a delegate is an Objective-C class that
you define in Python: subclass `NSObject`, list the protocol, and mark each
callback method with `@objc_method`.

The following example parses XML with `NSXMLParser`, which calls its delegate
while `parse()` runs:

<!-- run: rubicon -->
```python
from rubicon.objc import NSObject, ObjCClass, ObjCProtocol, objc_method


class ElementCounter(NSObject, protocols=[ObjCProtocol("NSXMLParserDelegate")]):
    @objc_method
    def parser_didStartElement_namespaceURI_qualifiedName_attributes_(
        self, parser, name, namespace, qualified_name, attributes
    ) -> None:
        self.names.append(str(name))


NSXMLParser = ObjCClass("NSXMLParser")
xml = b"<items><item/><item/></items>"
parser = NSXMLParser.alloc().initWithData_(xml)

counter = ElementCounter.alloc().init()
counter.names = []
parser.delegate = counter
parser.parse()
print(counter.names)
# Prints: ['items', 'item', 'item']
```

Keep these rules in mind when you write a delegate:

- **Keep a reference.** Most delegate properties in Apple's frameworks are
  weak, so Objective-C doesn't keep your delegate alive. Store the delegate
  on a Python object that lives as long as you need callbacks, such as
  `self._delegate`. If you don't, the delegate can be freed and its methods
  are never called.
- **Annotate non-object arguments.** Rubicon builds the method's Objective-C
  signature from its type annotations. Arguments without annotations are
  objects. Annotate `BOOL` arguments as `bool`, numbers as `int` or `float`,
  and set the return type, such as `-> None`.
- **Use unique class names.** Each class you define becomes an Objective-C
  class with the same name, and Objective-C class names are global. Define
  each class once, at module level, with a name that other code is unlikely
  to use. Defining a second class with the same name raises
  `RuntimeError: An Objective-C class named ... already exists`.
- **Store Python state on the delegate or its owner.** You can set Python
  attributes on an instance of your class, such as `counter.names` above, or
  a reference back to the object that owns it.

**Note:** `ObjCProtocol("Name")` finds a protocol only if code loaded into
the process references it, and raises `NameError` otherwise. For example,
`NSUserNotificationCenterDelegate` isn't found even with AppKit loaded. If
that happens, leave out `protocols=[...]`. Objective-C finds delegate methods
by name, so the delegate still works.

For more information, see
[Writing your own class](https://rubicon-objc.beeware.org/en/stable/tutorial/tutorial-2/),
[Implementing a protocol](https://rubicon-objc.beeware.org/en/stable/topics/protocols/#implementing-a-protocol),
and
[Weak references in Objective-C](https://rubicon-objc.beeware.org/en/stable/topics/memory-management/#weak-references-in-objective-c).

### Example: Kivy's AVAudioPlayer sound

Kivy's `audio_avplayer.py` sets the `Sound` object itself as the player's
delegate. The following shows the parts that change.

pyobjus:

```python
from pyobjus import autoclass, protocol
from pyobjus.dylib_manager import load_framework, INCLUDE

load_framework(INCLUDE.AVFoundation)
AVAudioPlayer = autoclass("AVAudioPlayer")
NSURL = autoclass("NSURL")
NSString = autoclass("NSString")


class SoundAvplayer(Sound):
    def load(self):
        self.unload()
        fn = NSString.alloc().initWithUTF8String_(self.source)
        url = NSURL.alloc().initFileURLWithPath_(fn)
        self._avplayer = AVAudioPlayer.alloc().initWithContentsOfURL_error_(
            url, None)

    def play(self):
        if not self._avplayer:
            return
        self._avplayer.delegate = self
        self._avplayer.play()
        super(SoundAvplayer, self).play()

    @protocol("AVAudioPlayerDelegate")
    def audioPlayerDidFinishPlaying_successfully_(self, player, flag):
        self.stop()
```

Rubicon:

```python
from rubicon.objc import NSObject, ObjCClass, ObjCProtocol, objc_method
from rubicon.objc.runtime import load_library

load_library("AVFoundation")
AVAudioPlayer = ObjCClass("AVAudioPlayer")
NSURL = ObjCClass("NSURL")


class KivyAVAudioPlayerDelegate(
    NSObject, protocols=[ObjCProtocol("AVAudioPlayerDelegate")]
):
    @objc_method
    def audioPlayerDidFinishPlaying_successfully_(
        self, player, flag: bool
    ) -> None:
        self.sound.stop()


class SoundAvplayer(Sound):
    def load(self):
        self.unload()
        url = NSURL.alloc().initFileURLWithPath_(self.source)
        self._avplayer = AVAudioPlayer.alloc().initWithContentsOfURL_error_(
            url, None)
        # The player's delegate is a weak reference, so the Sound keeps it.
        self._delegate = KivyAVAudioPlayerDelegate.alloc().init()
        self._delegate.sound = self

    def play(self):
        if not self._avplayer:
            return
        self._avplayer.delegate = self._delegate
        self._avplayer.play()
        super(SoundAvplayer, self).play()
```

The changes are:

1.  The imports and class loading move to Rubicon.
2.  `initFileURLWithPath_()` takes the `str` path directly, so the
    `NSString` conversion goes.
3.  The callback moves from the `Sound` to a new `NSObject` subclass, and the
    `Sound` keeps a reference to it.
4.  The callback's `flag` argument is annotated as `bool`.

The rest of the file, including `stop()`, `seek()`, and the `currentTime`,
`volume`, and `duration` properties, doesn't change.

## Receive notifications and target-action calls

pyobjus needs a protocol's method signatures before it can receive a call
from `NSNotificationCenter` or another target-action API. Code such as
kivy-ios's keyboard observer registers them by hand in pyobjus's
`protocols` dictionary and names the method with `selector()`.

In Rubicon, define the method on an `NSObject` subclass. The type
annotations give its signature, so you don't register anything. Name the
method with `SEL()`, using its full Objective-C name, including the trailing
colon.

<!-- run: rubicon -->
```python
from rubicon.objc import NSMakeRect, NSObject, ObjCClass, SEL, objc_method

NSNotificationCenter = ObjCClass("NSNotificationCenter")


class KeyboardObserver(NSObject):
    @objc_method
    def keyboardWillShow_(self, notification) -> None:
        frame = notification.userInfo.objectForKey_("frame").rectValue()
        self.height = frame.size.height


observer = KeyboardObserver.alloc().init()
center = NSNotificationCenter.defaultCenter
center.addObserver_selector_name_object_(
    observer, SEL("keyboardWillShow:"), "ExampleKeyboardWillShow", None
)

# Post a notification to call the observer.
value = ObjCClass("NSValue").valueWithRect_(NSMakeRect(0, 0, 390, 216))
info = ObjCClass("NSDictionary").dictionaryWithObject_forKey_(value, "frame")
center.postNotificationName_object_userInfo_("ExampleKeyboardWillShow", None, info)
print(observer.height)
# Prints: 216.0

center.removeObserver_(observer)
```

On iOS, the keyboard frame is under the `"UIKeyboardFrameEndUserInfoKey"`
key, and `CGRectValue` is a property:
`notification.userInfo.objectForKey_("UIKeyboardFrameEndUserInfoKey").CGRectValue.size.height`.

## Return values from callbacks

pyobjus code returns `ObjcBOOL(True)` from a callback that returns a `BOOL`.
In Rubicon, return a Python value and annotate the method's return type.

pyobjus:

```python
@protocol("NSUserNotificationCenterDelegate")
def userNotificationCenter_shouldPresentNotification_(self, center, notification):
    return ObjcBOOL(True)
```

Rubicon:

<!-- run: rubicon -->
```python
from rubicon.objc import NSObject, objc_method


class NotificationDelegate(NSObject):
    @objc_method
    def userNotificationCenter_shouldPresentNotification_(
        self, center, notification
    ) -> bool:
        return True


delegate = NotificationDelegate.alloc().init()
print(delegate.userNotificationCenter_shouldPresentNotification_(None, None))
# Prints: True
```

This class leaves out `protocols=[...]` because
`NSUserNotificationCenterDelegate` isn't found at run time, as described in
[Implement a delegate](#implement-a-delegate).

For more information, see
[Parameter and return types](https://rubicon-objc.beeware.org/en/stable/reference/rubicon-objc-api/#custom-classes-and-protocols).

## Pass blocks

pyobjus can't create Objective-C blocks. pyobjus code passes `None` for a
completion handler, or moves the work into Objective-C helper code. In
Rubicon, pass a Python function. Annotate its arguments and return type, so
that Rubicon can give the block the right signature.

The following example sorts an array with a comparator block:

<!-- run: rubicon -->
```python
from rubicon.objc import ObjCClass, ObjCInstance, objc_id

NSArray = ObjCClass("NSArray")
words = NSArray.arrayWithArray_(["pear", "fig", "banana"])


def by_length(a: objc_id, b: objc_id) -> int:
    length_a = len(str(ObjCInstance(a)))
    length_b = len(str(ObjCInstance(b)))
    return (length_a > length_b) - (length_a < length_b)


print([str(w) for w in words.sortedArrayUsingComparator_(by_length)])
# Prints: ['fig', 'pear', 'banana']
```

A completion handler works the same way. For example, on iOS:

```python
def opened(success: bool) -> None:
    print("Opened:", success)


app = ObjCClass("UIApplication").sharedApplication
app.openURL_options_completionHandler_(url, {}, opened)
```

Block arguments that are objects arrive as `objc_id` values. Wrap them in
`ObjCInstance()` to use them.

**Caution:** Don't pass a Python function where a pyobjus method expects a
block. pyobjus aborts the process.

Objective-C helper code that exists only to call a block-based API, such as
the `bridge` class Plyer's motion sensors use to run CoreMotion's updates,
can stay. Rubicon calls the helper class the same way, so you can replace it
later.

For more information, see
[Objective-C blocks](https://rubicon-objc.beeware.org/en/stable/reference/rubicon-objc-api/#objc_blocks).

## Handle NSError output arguments

Many Cocoa methods report failures through an `NSError **` argument. You can
pass `None` in both libraries if you don't need the error. To read the
error in Rubicon, pass `byref(objc_id())`, and then wrap the result in
`ObjCInstance()`.

<!-- run: rubicon -->
```python
from ctypes import byref

from rubicon.objc import ObjCClass, ObjCInstance, objc_id

NSString = ObjCClass("NSString")
NSUTF8StringEncoding = 4

error = objc_id()
text = NSString.stringWithContentsOfFile_encoding_error_(
    "/no/such/file", NSUTF8StringEncoding, byref(error)
)
if text is None and error.value:
    print(ObjCInstance(error).code)
# Prints: 260
```

**Caution:** Some pyobjus code passes `NSError.alloc()` for an `NSError **`
argument. Rubicon rejects that argument with `ctypes.ArgumentError` on every
call, so replace it with `byref(objc_id())`, or with `None`. In pyobjus, that
form crashes the process when the method writes an error, so the migrated
code can read errors that the pyobjus code couldn't.

## Work with bytes and memory

Pass Python `bytes` where a method takes a pointer to bytes or an `NSData`
object, and Rubicon converts them. `NSData.bytes` is a pointer that you can
read with `ctypes`:

<!-- run: rubicon -->
```python
import ctypes

from rubicon.objc import ObjCClass

NSData = ObjCClass("NSData")
payload = (ctypes.c_float * 3)(1.5, 2.5, 3.5)
data = NSData.dataWithBytes_length_(bytes(payload), ctypes.sizeof(payload))

values = (ctypes.c_float * 3).from_address(data.bytes.value)
print(list(values), data.length)
# Prints: [1.5, 2.5, 3.5] 12
```

Rubicon manages reference counts for the objects it returns. Remove code
that calls `release()` until `retainCount()` reaches a value, and code that
uses pyobjus's `.arg_ref`.

For more information, see
[Memory management for Objective-C instances](https://rubicon-objc.beeware.org/en/stable/topics/memory-management/).

## Call C functions

Neither library calls C functions directly. pyobjus code calls them through
`ctypes` or through an Objective-C helper class. In Rubicon, use `ctypes` on
the library that `load_library()` returns:

<!-- run: rubicon -->
```python
from rubicon.objc import ObjCInstance, objc_id
from rubicon.objc.runtime import load_library

foundation = load_library("Foundation")
foundation.NSHomeDirectory.restype = objc_id
foundation.NSHomeDirectory.argtypes = []

home = str(ObjCInstance(foundation.NSHomeDirectory()))
print(home.startswith("/"))
# Prints: True
```

Set `restype` and `argtypes` for each function before you call it. A
function that returns an Objective-C object returns an `objc_id`, which you
wrap in `ObjCInstance()`.

For more information, see
[Calling plain C functions from Python](https://rubicon-objc.beeware.org/en/stable/topics/c-functions/).

## Load your app's own classes

Classes compiled into your app, such as the `bridge` class in kivy-ios's
Xcode template, are already loaded. Use `ObjCClass("bridge")` as you used
`autoclass("bridge")`.

For a class in a separate dynamic library, replace `load_dylib()` with
`load_library()`, passing the library's path:

```python
from rubicon.objc import ObjCClass
from rubicon.objc.runtime import load_library

load_library("/path/to/libhelper.dylib")
Helper = ObjCClass("Helper")
```

`load_library()` doesn't accept a `.framework` folder, which pyobjus's
`load_framework()` does. Pass the framework's name, or the path of the binary
inside the folder:

<!-- run: rubicon -->
```python
from rubicon.objc.runtime import load_library

# pyobjus: load_framework("/System/Library/Frameworks/Photos.framework")
load_library("Photos")
# Or: load_library("/System/Library/Frameworks/Photos.framework/Photos")
```

Passing the folder path raises `ValueError`.

**Note:** Plyer's bundled `Voip.framework` isn't verified for this guide. By
the same rule, pass the binary inside it, such as `Voip.framework/Voip`.

## Troubleshoot common errors

| Error | Cause | Fix |
|---|---|---|
| `TypeError: 'ObjCInstance' object is not callable` | A property is called with `()` | [Remove the `()`](#read-properties-without-parentheses) |
| `TypeError: 'bytes' object is not callable` | `UTF8String()` is called | Use [`str(s)`](#convert-strings) |
| `TypeError: ObjCListInstance.count() missing 1 required positional argument: 'value'` | `count()` is called on an `NSArray` | Use [`len()`](#work-with-arrays-and-dictionaries) |
| `ArgumentError: initWithUTF8String: ... 'str' object cannot be interpreted as ctypes.c_char_p` | A `str` is passed for a C string | Pass `bytes`, or pass the `str` straight to the method that needs the `NSString` |
| `ArgumentError: ... expected LP_objc_id instance instead of objc_id` | An object, such as `NSError.alloc()`, is passed for an `NSError **` argument | [Pass `byref(objc_id())` or `None`](#handle-nserror-output-arguments) |
| `ValueError` from `load_library()` | A `.framework` folder path is passed | [Pass the framework's name, or its binary's path](#load-your-apps-own-classes) |
| `NameError: ObjC Class ... couldn't be found` | The framework isn't loaded, or the class name is wrong | [Load the framework](#load-classes-and-frameworks) first |
| `NameError: Objective-C protocol ... not found` | No loaded code references the protocol | [Leave out `protocols=[...]`](#implement-a-delegate) |
| `RuntimeError: An Objective-C class named ... already exists` | Two classes have the same name, or a class is defined more than once | [Define each class once, with a unique name](#implement-a-delegate) |
| `AttributeError` for a method name | The name is misspelled, or has the wrong number of underscores | Check the Objective-C name. Each colon is one underscore |
| A delegate's methods are never called | The delegate was freed, because the delegate property is weak | [Keep a reference](#implement-a-delegate) to the delegate |

## Migration checklist

Use this list to track a migration, file by file:

- [ ] Replace pyobjus imports.
- [ ] Replace `autoclass()` with `ObjCClass()` and `load_framework()` with
      `load_library()`.
- [ ] Remove `()` from property reads.
- [ ] Replace `UTF8String()` with `str()`, and remove `objc_str()`,
      `objc_arr()`, and bytes checks.
- [ ] Replace `count()` and `objectAtIndex_()` loops with `len()`, indexing,
      or iteration.
- [ ] Move `@protocol` methods to `NSObject` subclasses, and keep a reference
      to each delegate.
- [ ] Replace hand-registered protocols and `selector()` with `SEL()`.
- [ ] Replace `ObjcBOOL` returns with annotations.
- [ ] Replace `NSError.alloc()` arguments with `byref(objc_id())` or `None`.
- [ ] Replace copied constant values with `objc_const()`.
- [ ] Remove pyobjus from dependencies and build files.
- [ ] Test each changed file on macOS and iOS.

## What's next

- Work through Rubicon's
  [tutorials](https://rubicon-objc.beeware.org/en/stable/tutorial/tutorial-0/).
- Read the [topic guides](https://rubicon-objc.beeware.org/en/stable/topics/)
  on type mapping, protocols, memory management, C functions, and
  [asyncio integration](https://rubicon-objc.beeware.org/en/stable/topics/async/).
- Look up names in the
  [`rubicon.objc` API reference](https://rubicon-objc.beeware.org/en/stable/reference/rubicon-objc-api/).

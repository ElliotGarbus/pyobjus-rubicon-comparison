"""M1 cases, pyobjus side, written the way the sampled code writes them.

Each case returns plain Python values. cases_rubicon.py has a case of the
same name doing the same thing with Rubicon. The comment above each case
names the U2 patterns it covers and the sampled code it follows.
"""
import ctypes
import os
import sys

from pyobjus import autoclass, objc_arr, objc_str, protocol, selector
from pyobjus.dylib_manager import INCLUDE, load_dylib, load_framework
from pyobjus.objc_py_types import NSPoint, NSRect, NSSize, enum
from pyobjus.protocols import protocols

from common import (FLOATS, same_path, SUITE, TEXT, documents_dir, float_bytes, private, silent_wav, to_str,
                    wait)

load_framework(INCLUDE.AVFoundation)
if sys.platform == "darwin":  # Mac-only frameworks; cases_ios_pyobjus.py reuses the rest
    load_framework(INCLUDE.AppKit)
    load_framework(INCLUDE.CoreWLAN)


# alloc-init, selector-call, utf8string, bytes-check. Kivy's audio_avplayer.py and clipboard_nspaste.py.
def strings():
    NSString = autoclass("NSString")
    s = NSString.alloc().initWithUTF8String_(TEXT)
    raw = s.UTF8String()
    return {"text": to_str(raw), "utf8string_type": type(raw).__name__}


# load-framework, selector-call. Kivy's clipboard_nspaste.py, on a named pasteboard
# so the Mac's clipboard isn't touched.
def pasteboard():
    NSPasteboard = autoclass("NSPasteboard")
    NSString = autoclass("NSString")
    pb = NSPasteboard.pasteboardWithName_(SUITE)
    pb.clearContents()
    pb.setString_forType_(NSString.alloc().initWithUTF8String_(TEXT), "public.utf8-plain-text")
    data = pb.stringForType_("public.utf8-plain-text")
    text = to_str(data.UTF8String()) if data else ""
    pb.releaseGlobally()
    return {"text": text}


# objc-str, selector-call. Plyer's ios/keystore.py, in a separate defaults suite.
def defaults():
    NSUserDefaults = autoclass("NSUserDefaults")
    d = NSUserDefaults.alloc().initWithSuiteName_(objc_str(SUITE))
    key, value = objc_str("token"), objc_str(TEXT)
    d.setObject_forKey_(value, key)
    ret = d.stringForKey_(objc_str("token"))
    text = to_str(ret.UTF8String()) if ret is not None else None
    d.removePersistentDomainForName_(objc_str(SUITE))
    return {"text": text}


# enum, property-or-method, utf8string. Ren'Py's renpy.py and bootstrap.py.
def search_path():
    NSSearchPathDirectory = enum("NSSearchPathDirectory", NSDocumentDirectory=9)
    NSSearchPathDomainMask = enum("NSSearchPathDomainMask", NSUserDomainMask=1)
    manager = autoclass("NSFileManager").defaultManager()
    url = manager.URLsForDirectory_inDomains_(
        NSSearchPathDirectory.NSDocumentDirectory, NSSearchPathDomainMask.NSUserDomainMask).lastObject()
    try:
        path, read_as = url.path().UTF8String(), "method"
    except Exception:
        path, read_as = url.path.UTF8String(), "property"
    return {"is_documents": same_path(to_str(path), documents_dir()), "path_read_as": read_as}


# nsarray-index, utf8string. Ren'Py's translation/__init__.py.
def languages():
    languages = autoclass("NSLocale").preferredLanguages()
    first = to_str(languages.objectAtIndex_(0).UTF8String())
    count = languages.count
    count = count() if callable(count) else count
    return {"count": count, "first": private(first)}


# nsarray-index, property reads. Ren'Py's display/tts.py and Plyer's ios/tts.py.
def voices():
    voices = autoclass("AVSpeechSynthesisVoice").speechVoices()
    count = voices.count
    count = count() if callable(count) else count
    ids = sorted(to_str(voices.objectAtIndex_(i).identifier.UTF8String()) for i in range(count))
    return {"count": count, "identifiers": private(ids)}


# struct-field, property-or-method. MF_run_counter's screeninfo/enumerators/osx.py.
def screens():
    screens = autoclass("NSScreen").screens()
    f = screens.objectAtIndex_(0).frame
    read_as = "property"
    if callable(f):
        f, read_as = f(), "method"
    return {"size": [int(f.size.width), int(f.size.height)], "frame_read_as": read_as}


# objc-arr, python-container-arg. Plyer's macosx/filechooser.py; renpy-build's iossupport.py
# passes {} for an NSDictionary.
def collections():
    arr = objc_arr(objc_str("png"), objc_str("jpg"))
    items = [to_str(arr.objectAtIndex_(i).UTF8String()) for i in range(arr.count())]
    d = autoclass("NSDictionary").dictionaryWithDictionary_({"key": "value"})
    v = d.objectForKey_("key")
    empty = autoclass("NSDictionary").dictionaryWithDictionary_({})
    return {"array": items, "dict_value": to_str(v.UTF8String()) if v is not None else None,
            "empty_count": empty.count()}


# delegate-self, protocol-method, alloc-init, error-arg (None). Kivy's audio_avplayer.py.
class Player:
    finished = None

    def play(self, path):
        NSString = autoclass("NSString")
        NSURL = autoclass("NSURL")
        AVAudioPlayer = autoclass("AVAudioPlayer")
        fn = NSString.alloc().initWithUTF8String_(path)
        url = NSURL.alloc().initFileURLWithPath_(fn)
        self._avplayer = AVAudioPlayer.alloc().initWithContentsOfURL_error_(url, None)
        self._avplayer.delegate = self
        self._avplayer.volume = 0.0
        self._avplayer.play()

    @protocol("AVAudioPlayerDelegate")
    def audioPlayerDidFinishPlaying_successfully_(self, player, flag):
        self.finished = bool(flag)


def delegate():
    p = Player()
    p.play(silent_wav())
    wait(lambda: p.finished is not None)
    return {"finished": p.finished, "volume": round(float(p._avplayer.volume), 3)}


# observer-self, selector, protocol-register, protocol-method, struct-field.
# kivy-ios's ios.pyx keyboard observer, with the Mac's NSValue rect instead of CGRectValue.
protocols["S8Observer"] = {"keyboardWillShow": ("v16@0:4@8", "v32@0:8@16")}


class Observer:
    height = None

    def __init__(self):
        autoclass("NSNotificationCenter").defaultCenter().addObserver_selector_name_object_(
            self, selector("keyboardWillShow"), "S8KeyboardWillShow", None)

    @protocol("S8Observer")
    def keyboardWillShow(self, notification):
        self.height = notification.userInfo().objectForKey_("frame").rectValue().size.height


def observer():
    o = Observer()
    value = autoclass("NSValue").valueWithRect_(NSRect(NSPoint(0, 0), NSSize(390, 216)))
    info = autoclass("NSDictionary").dictionaryWithObject_forKey_(value, "frame")
    autoclass("NSNotificationCenter").defaultCenter().postNotificationName_object_userInfo_(
        "S8KeyboardWillShow", None, info)
    return {"height": o.height}


# A constant. Plyer's ios/flash.py writes AVMediaTypeVideo's value by hand, as pyobjus
# has no API for constants (Section 3, F1).
def constant():
    return {"AVMediaTypeVideo": "vide", "how": "hard-coded"}


# error-arg. Kivy and Plyer's flash pass None for an NSError ** argument.
def nserror_none():
    r = autoclass("NSString").stringWithContentsOfFile_encoding_error_("/nonexistent-s8", 4, None)
    return {"result_is_nil": r is None}


# error-arg. kivy-tensorflow-helloworld and Plyer's macosx/audio.py pass NSError.alloc(),
# here to a call that fails and writes an error.
def nserror_out():
    err = autoclass("NSError").alloc()
    r = autoclass("NSString").stringWithContentsOfFile_encoding_error_("/nonexistent-s8", 4, err)
    return {"result_is_nil": r is None, "error_code": err.code}


# raw-pointer, retain-release. kivy-tensorflow-helloworld's model.py.
def nsdata():
    NSData = autoclass("NSData")
    bytestr = float_bytes()
    floatbuf = ctypes.cast(bytestr, ctypes.POINTER(ctypes.c_float)).contents
    data = NSData.dataWithBytes_length_(floatbuf, len(bytestr))
    out = (ctypes.c_float * len(FLOATS)).from_address(data.bytes().arg_ref)
    retain_before = data.retainCount()
    return {"floats": list(out), "length": data.length(), "retain_count": retain_before}


# property-or-method: a zero-argument property called as a method, and read as an attribute.
def property_call():
    arr = objc_arr(objc_str("a"), objc_str("b"))
    out = {}
    for form in ("call", "attribute"):
        try:
            v = arr.count() if form == "call" else arr.count
            out[form] = v if isinstance(v, int) else type(v).__name__
        except Exception as e:
            out[form] = "raised " + type(e).__name__
    return out


# property-or-method: zero-argument names the sample calls, on the Mac classes that have
# them. ZERO_ARG in common.py lists them. "property" means the attribute is already the value;
# "method" means it's callable and calling it with no arguments worked.
def zero_arg():
    from common import ZERO_ARG, get
    return {key: kind(eval(expr, {"get": get, "autoclass": autoclass, "objc_arr": objc_arr, "objc_str": objc_str,
                                  "NSRect": NSRect, "NSPoint": NSPoint, "NSSize": NSSize}), name)
            for key, (expr, name) in ZERO_ARG.items()}


def kind(obj, name):
    try:
        v = getattr(obj, name)
    except Exception as e:
        return "raised " + type(e).__name__
    if not callable(v):
        return "property"
    try:
        v()
    except Exception as e:
        return "method, but () raised " + type(e).__name__
    return "method"


# An app's own class (Plyer's bridge, Ren'Py's IAPHelper). Built by run_mac.py.
def app_class():
    load_dylib(os.environ["S8_HELPER"], abs_path=True)
    S8Helper = autoclass("S8Helper")
    h = S8Helper.alloc().init()
    h.bump()
    h.bump()
    return {"greet": to_str(S8Helper.greet_(objc_str("Kivy")).UTF8String()), "level": h.level}


# completion-nil. pyobjus can't create blocks (Section 3, F4.1), so the sample passes None.
def block():
    called = []
    queue = autoclass("NSOperationQueue").mainQueue()
    try:
        queue.addOperationWithBlock_(lambda: called.append(True))
    except Exception as e:
        return {"called": False, "how": "raised " + type(e).__name__}
    wait(lambda: called, timeout=2.0)
    return {"called": bool(called), "how": "passed a Python function"}


# M2: names Kivy and Plyer call that M1 didn't check, looked up without calling them.
def m2_names():
    from common import NAMES_M2, get, lookup_kind, scratch_path
    load_framework(INCLUDE.CoreLocation)
    env = {"silent_wav": silent_wav, "scratch_path": scratch_path, "get": get, "autoclass": autoclass, "objc_arr": objc_arr, "objc_str": objc_str}
    out = {}
    for key, (expr, name) in NAMES_M2.items():
        try:
            obj = eval(expr, env)
        except Exception as e:
            out[key] = "receiver raised " + type(e).__name__
            continue
        out[key] = "receiver is nil" if obj is None else lookup_kind(obj, name)
    return out


CASES = {f.__name__: f for f in (strings, pasteboard, defaults, search_path, languages, voices, screens,
                                  collections, delegate, observer, constant, nserror_none, nserror_out, nsdata,
                                  property_call, zero_arg, app_class, block, m2_names)}

"""M1 cases, Rubicon side: the same work as cases_pyobjus.py.

Method calls keep pyobjus's flat names, such as setObject_forKey_(...),
which Rubicon also accepts, so each case shows the smallest change from the
sampled code. Where Rubicon needs something different, the comment says so.
"""
import ctypes
import os
import sys
from ctypes import byref

from rubicon.objc import (NSMakeRect, NSObject, ObjCClass, ObjCProtocol, SEL, objc_const, objc_id,
                          objc_method)
from rubicon.objc.api import ObjCInstance
from rubicon.objc.runtime import load_library

from common import FLOATS, same_path, SUITE, TEXT, documents_dir, float_bytes, private, silent_wav, wait

avfoundation = load_library("AVFoundation")
if sys.platform == "darwin":  # Mac-only frameworks; cases_ios_rubicon.py reuses the rest
    load_library("AppKit")
    load_library("CoreWLAN")


# initWithUTF8String: takes a C string, so Rubicon needs bytes. UTF8String is a property, read
# without (), and gives bytes. str() turns an NSString into Python.
def strings():
    NSString = ObjCClass("NSString")
    s = NSString.alloc().initWithUTF8String_(TEXT.encode("utf-8"))
    raw = s.UTF8String
    return {"text": str(s), "utf8string_type": type(raw).__name__}


# A Python str can be passed where a method takes an NSString.
def pasteboard():
    NSPasteboard = ObjCClass("NSPasteboard")
    pb = NSPasteboard.pasteboardWithName_(SUITE)
    pb.clearContents()
    pb.setString_forType_(TEXT, "public.utf8-plain-text")
    data = pb.stringForType_("public.utf8-plain-text")
    text = str(data) if data else ""
    pb.releaseGlobally()
    return {"text": text}


# objc_str(...) isn't needed: Rubicon converts str arguments.
def defaults():
    NSUserDefaults = ObjCClass("NSUserDefaults")
    d = NSUserDefaults.alloc().initWithSuiteName_(SUITE)
    d.setObject_forKey_(TEXT, "token")
    ret = d.stringForKey_("token")
    text = str(ret) if ret is not None else None
    d.removePersistentDomainForName_(SUITE)
    return {"text": text}


# Enum values are plain integers. path is a property, read without (). lastObject stays a method.
def search_path():
    NSDocumentDirectory, NSUserDomainMask = 9, 1
    manager = ObjCClass("NSFileManager").defaultManager
    url = manager.URLsForDirectory_inDomains_(NSDocumentDirectory, NSUserDomainMask).lastObject()
    return {"is_documents": same_path(str(url.path), documents_dir()), "path_read_as": "property"}


# NSArray supports len() and indexing.
def languages():
    languages = ObjCClass("NSLocale").preferredLanguages
    return {"count": len(languages), "first": private(str(languages[0]))}


def voices():
    voices = ObjCClass("AVSpeechSynthesisVoice").speechVoices()
    ids = sorted(str(v.identifier) for v in voices)
    return {"count": len(voices), "identifiers": private(ids)}


# frame is a property and returns an NSRect with the same field names.
def screens():
    f = ObjCClass("NSScreen").screens[0].frame
    return {"size": [int(f.size.width), int(f.size.height)], "frame_read_as": "property"}


# Python lists and dicts are converted to NSArray and NSDictionary.
def collections():
    arr = ObjCClass("NSArray").arrayWithArray_(["png", "jpg"])
    d = ObjCClass("NSDictionary").dictionaryWithDictionary_({"key": "value"})
    v = d.objectForKey_("key")
    empty = ObjCClass("NSDictionary").dictionaryWithDictionary_({})
    return {"array": [str(x) for x in arr], "dict_value": str(v) if v is not None else None,
            "empty_count": len(empty)}


# A delegate is an Objective-C class defined in Python, declaring the protocol.
# Delegate properties are weak references, so Python keeps the delegate alive.
class PlayerDelegate(NSObject, protocols=[ObjCProtocol("AVAudioPlayerDelegate")]):
    @objc_method
    def audioPlayerDidFinishPlaying_successfully_(self, player, flag: bool) -> None:
        self.owner.finished = bool(flag)


class Player:
    finished = None

    def play(self, path):
        NSURL = ObjCClass("NSURL")
        AVAudioPlayer = ObjCClass("AVAudioPlayer")
        url = NSURL.alloc().initFileURLWithPath_(path)
        self._avplayer = AVAudioPlayer.alloc().initWithContentsOfURL_error_(url, None)
        self._delegate = PlayerDelegate.alloc().init()
        self._delegate.owner = self
        self._avplayer.delegate = self._delegate
        self._avplayer.volume = 0.0
        self._avplayer.play()


def delegate():
    p = Player()
    p.play(silent_wav())
    wait(lambda: p.finished is not None)
    return {"finished": p.finished, "volume": round(float(p._avplayer.volume), 3)}


# No protocol registration: the method's types come from its annotations, and SEL names it.
class ObserverTarget(NSObject):
    @objc_method
    def keyboardWillShow_(self, notification) -> None:
        self.owner.height = notification.userInfo.objectForKey_("frame").rectValue().size.height


class Observer:
    height = None

    def __init__(self):
        self._target = ObserverTarget.alloc().init()
        self._target.owner = self
        ObjCClass("NSNotificationCenter").defaultCenter.addObserver_selector_name_object_(
            self._target, SEL("keyboardWillShow:"), "S8KeyboardWillShow", None)


def observer():
    o = Observer()
    value = ObjCClass("NSValue").valueWithRect_(NSMakeRect(0, 0, 390, 216))
    info = ObjCClass("NSDictionary").dictionaryWithObject_forKey_(value, "frame")
    ObjCClass("NSNotificationCenter").defaultCenter.postNotificationName_object_userInfo_(
        "S8KeyboardWillShow", None, info)
    return {"height": o.height}


# objc_const reads an exported constant (Rubicon's docs, topics/c-functions.md).
def constant():
    return {"AVMediaTypeVideo": str(objc_const(avfoundation, "AVMediaTypeVideo")), "how": "objc_const"}


def nserror_none():
    r = ObjCClass("NSString").stringWithContentsOfFile_encoding_error_("/nonexistent-s8", 4, None)
    return {"result_is_nil": r is None}


# An NSError ** argument takes byref(objc_id()), and the error is read afterwards.
def nserror_out():
    err = objc_id()
    r = ObjCClass("NSString").stringWithContentsOfFile_encoding_error_("/nonexistent-s8", 4, byref(err))
    return {"result_is_nil": r is None, "error_code": ObjCInstance(err).code if err.value else None}


# Bytes pass through ctypes; data.bytes is a pointer. Rubicon manages the reference count.
def nsdata():
    NSData = ObjCClass("NSData")
    bytestr = float_bytes()
    data = NSData.dataWithBytes_length_(bytestr, len(bytestr))
    out = (ctypes.c_float * len(FLOATS)).from_address(data.bytes.value)
    return {"floats": list(out), "length": data.length, "retain_count": data.retainCount()}


def property_call():
    arr = ObjCClass("NSArray").arrayWithArray_(["a", "b"])
    out = {}
    for form in ("call", "attribute"):
        try:
            v = arr.count() if form == "call" else arr.count
            out[form] = v if isinstance(v, int) else type(v).__name__
        except Exception as e:
            out[form] = "raised " + type(e).__name__
    return out


def zero_arg():
    from common import ZERO_ARG, get
    env = {"get": get, "autoclass": ObjCClass, "objc_arr": lambda *a: ObjCClass("NSArray").arrayWithArray_(list(a)),
           "objc_str": lambda x: x, "NSRect": lambda p, s: NSMakeRect(p[0], p[1], s[0], s[1]),
           "NSPoint": lambda x, y: (x, y), "NSSize": lambda w, h: (w, h)}
    return {key: kind(eval(expr, env), name) for key, (expr, name) in ZERO_ARG.items()}


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


def app_class():
    load_library(os.environ["S8_HELPER"])
    S8Helper = ObjCClass("S8Helper")
    h = S8Helper.alloc().init()
    h.bump()
    h.bump()
    return {"greet": str(S8Helper.greet_("Kivy")), "level": h.level}


# A Python function annotated with its types is passed as a block.
def block():
    called = []

    def handler() -> None:
        called.append(True)

    ObjCClass("NSOperationQueue").mainQueue.addOperationWithBlock_(handler)
    wait(lambda: called, timeout=2.0)
    return {"called": bool(called), "how": "passed a Python function"}


# M2: names Kivy and Plyer call that M1 didn't check, looked up without calling them.
def m2_names():
    from common import NAMES_M2, get, lookup_kind, scratch_path
    load_library("CoreLocation")
    env = {"silent_wav": silent_wav, "scratch_path": scratch_path, "get": get, "autoclass": ObjCClass, "objc_arr": lambda *a: ObjCClass("NSArray").arrayWithArray_(list(a)), "objc_str": lambda x: x}
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

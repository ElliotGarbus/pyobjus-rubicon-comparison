"""M1 cases on the iPhone, pyobjus side.

The portable cases come from cases_pyobjus.py unchanged. The iOS cases
follow the sampled code that needs UIKit, written as that code writes it.
"""
from pyobjus import autoclass, objc_arr, objc_str, protocol, selector
from pyobjus.dylib_manager import load_framework
from pyobjus.objc_py_types import NSPoint, NSRect, NSSize
from pyobjus.protocols import protocols

import cases_pyobjus as mac
from common import ZERO_ARG_IOS, get

load_framework("/System/Library/Frameworks/UIKit.framework")

PORTABLE = ("strings", "defaults", "search_path", "languages", "voices", "collections", "delegate", "constant",
            "nserror_none", "nserror_out", "nsdata", "property_call", "block")


# Ren'Py's main.py: userInterfaceIdiom read as an attribute.
def idiom():
    return {"idiom": int(autoclass("UIDevice").currentDevice().userInterfaceIdiom)}


# KivyMD's uix/behaviors/ios/native_behavior.py.
def haptic():
    g = autoclass("UISelectionFeedbackGenerator").alloc().init()
    g.prepare()
    g.selectionChanged()
    return {"ran": True}


# Carvera Controller reads these in main.m because "pyobjus can't reliably read UIScreen struct
# properties". Here pyobjus reads them, as its other code reads properties.
def screen():
    s = autoclass("UIScreen").mainScreen()
    b = s.bounds
    b = b() if callable(b) else b
    scale = s.scale
    scale = scale() if callable(scale) else scale
    return {"size": [float(b.size.width), float(b.size.height)], "scale": float(scale)}


# kivy-ios's ios.pyx keyboard observer, as written there, with an NSValue holding a CGRect.
protocols["S8KeyboardDelegates"] = {"keyboardWillShow": ("v16@0:4@8", "v32@0:8@16")}


class Observer:
    height = None

    def __init__(self):
        autoclass("NSNotificationCenter").defaultCenter().addObserver_selector_name_object_(
            self, selector("keyboardWillShow"), "S8KeyboardWillShow", None)

    @protocol("S8KeyboardDelegates")
    def keyboardWillShow(self, notification):
        self.height = notification.userInfo().objectForKey_("UIKeyboardFrameEndUserInfoKey").CGRectValue().size.height


def observer_ios():
    o = Observer()
    value = autoclass("NSValue").valueWithCGRect_(NSRect(NSPoint(0, 0), NSSize(390, 216)))
    info = autoclass("NSDictionary").dictionaryWithObject_forKey_(value, "UIKeyboardFrameEndUserInfoKey")
    autoclass("NSNotificationCenter").defaultCenter().postNotificationName_object_userInfo_(
        "S8KeyboardWillShow", None, info)
    return {"height": o.height}


def zero_arg_ios():
    env = {"get": get, "autoclass": autoclass, "objc_arr": objc_arr, "objc_str": objc_str,
           "NSRect": NSRect, "NSPoint": NSPoint, "NSSize": NSSize}
    out = {}
    for key, (expr, name) in ZERO_ARG_IOS.items():
        try:
            obj = eval(expr, env)
        except Exception as e:
            out[key] = "receiver raised " + type(e).__name__
            continue
        out[key] = "receiver is nil" if obj is None else mac.kind(obj, name)
    return out


CASES = {name: mac.CASES[name] for name in PORTABLE}
CASES.update({f.__name__: f for f in (idiom, haptic, screen, observer_ios, zero_arg_ios)})

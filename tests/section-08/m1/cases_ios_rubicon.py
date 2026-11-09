"""M1 cases on the iPhone, Rubicon side: the same work as cases_ios_pyobjus.py."""
from rubicon.objc import NSMakeRect, NSObject, ObjCClass, SEL, objc_method
from rubicon.objc.runtime import load_library

import cases_rubicon as mac
from cases_ios_pyobjus import PORTABLE
from common import ZERO_ARG_IOS, get

load_library("UIKit")


# userInterfaceIdiom is a property; currentDevice is a class property.
def idiom():
    return {"idiom": int(ObjCClass("UIDevice").currentDevice.userInterfaceIdiom)}


def haptic():
    g = ObjCClass("UISelectionFeedbackGenerator").alloc().init()
    g.prepare()
    g.selectionChanged()
    return {"ran": True}


def screen():
    s = ObjCClass("UIScreen").mainScreen
    b = s.bounds
    return {"size": [float(b.size.width), float(b.size.height)], "scale": float(s.scale)}


# CGRectValue is a property on iOS, read without (). Objective-C class names are global, hence IOS.
class ObserverTargetIOS(NSObject):
    @objc_method
    def keyboardWillShow_(self, notification) -> None:
        self.owner.height = notification.userInfo.objectForKey_("UIKeyboardFrameEndUserInfoKey").CGRectValue.size.height


class Observer:
    height = None

    def __init__(self):
        self._target = ObserverTargetIOS.alloc().init()
        self._target.owner = self
        ObjCClass("NSNotificationCenter").defaultCenter.addObserver_selector_name_object_(
            self._target, SEL("keyboardWillShow:"), "S8KeyboardWillShow", None)


def observer_ios():
    o = Observer()
    value = ObjCClass("NSValue").valueWithCGRect_(NSMakeRect(0, 0, 390, 216))
    info = ObjCClass("NSDictionary").dictionaryWithObject_forKey_(value, "UIKeyboardFrameEndUserInfoKey")
    ObjCClass("NSNotificationCenter").defaultCenter.postNotificationName_object_userInfo_(
        "S8KeyboardWillShow", None, info)
    return {"height": o.height}


def zero_arg_ios():
    env = {"get": get, "autoclass": ObjCClass,
           "objc_arr": lambda *a: ObjCClass("NSArray").arrayWithArray_(list(a)), "objc_str": lambda x: x,
           "NSRect": lambda p, s: NSMakeRect(p[0], p[1], s[0], s[1]), "NSPoint": lambda x, y: (x, y),
           "NSSize": lambda w, h: (w, h)}
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

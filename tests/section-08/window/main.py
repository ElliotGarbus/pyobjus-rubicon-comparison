"""Section 8 window test: UIApplication.keyWindow and rootViewController, and
Plyer's iOS file chooser, in a running Kivy app that has a window.

S8_LIB picks one library per launch:
- plyer: Plyer's own iOS file chooser, unchanged, on pyobjus.
- pyobjus: how pyobjus reads keyWindow and rootViewController, Plyer's line, and the
  image picker presented with the corrected read.
- rubicon: the same reads in Rubicon, Photos loaded as Plyer loads it, and the
  image picker presented as Plyer presents it, with a Rubicon delegate.
The result is printed as one S8RESULT line, then the app exits.
"""
import json
import os
import traceback

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.label import Label

LIB = os.environ.get("S8_LIB", "")
result = {}


def finish(outcome="ran"):
    os.write(1, ("S8RESULT " + json.dumps({"outcome": outcome, "value": result}, default=repr) + "\n").encode())
    os._exit(0)


def guarded(f):
    def run(*args):
        try:
            f(*args)
        except Exception as e:
            result["error"] = type(e).__name__ + ": " + str(e)[:300]
            result["traceback"] = traceback.format_exc()[-1500:]
            finish("raised")
    return run


def kind(obj, name):
    """'property' if the attribute is already the value, 'method' if it must be called."""
    try:
        value = getattr(obj, name)
    except Exception as e:
        return "raised " + type(e).__name__
    return "method" if callable(value) else "property"


def value(obj, name):
    v = getattr(obj, name)
    return v() if callable(v) else v


def present_and_check(vc, Picker, ViewController, picker=None):
    """Present a plain view controller (a control), dismiss it, then present the
    image picker as Plyer does, animated. UIKit finishes a presentation or
    dismissal on a later turn of the run loop, so each step waits for the last,
    and the picker is polled for up to 5 s.
    Same steps in both libraries."""
    result["view_in_window"] = value(value(vc, "view"), "window") is not None
    result["photo_library_available"] = bool(Picker.isSourceTypeAvailable_(0))
    plain = ViewController.alloc().init()
    vc.presentViewController_animated_completion_(plain, False, None)

    def control_shown(dt):
        result["control_presented"] = value(vc, "presentedViewController") is not None
        vc.dismissViewControllerAnimated_completion_(False, None)
        Clock.schedule_once(guarded(control_gone), 1.0)

    def control_gone(dt):
        result["control_dismissed"] = value(vc, "presentedViewController") is None
        nonlocal picker
        if picker is None:
            picker = Picker.alloc().init()
            picker.sourceType = 0
        vc.presentViewController_animated_completion_(picker, True, None)
        poll(0.0)

    # The picker appears asynchronously, after its remote view loads, so poll for it.
    def poll(waited):
        shown = value(vc, "presentedViewController")
        if shown is None and waited < 5.0:
            Clock.schedule_once(guarded(lambda dt: poll(waited + 0.25)), 0.25)
            return
        # isEqual_ compares with the very picker presented, with an object argument
        # in both libraries; isKindOfClass_ would need each library's class object.
        result["presented"] = None if shown is None else \
            ("the picker" if shown.isEqual_(picker) else "other")
        result["presented_within_s"] = waited if shown is not None else None
        vc.dismissViewControllerAnimated_completion_(False, None)
        Clock.schedule_once(lambda dt: finish(), 0.5)

    Clock.schedule_once(guarded(control_shown), 0.5)


# Plyer: its own module, imported and called as an app would.
def check_plyer(dt):
    import plyer
    from plyer.utils import platform
    from pyobjus import autoclass
    result["plyer_version"] = plyer.__version__
    result["plyer_platform"] = str(platform)
    try:
        __import__("plyer.platforms.ios.filechooser")
        result["module_import"] = "ok"
    except Exception as e:
        result["module_import"] = "raised " + type(e).__name__ + ": " + str(e)[:300]
    from plyer import filechooser
    result["implementation"] = type(object.__getattribute__(filechooser, "_ensure_obj")()).__name__
    filechooser.open_file(on_selection=lambda selection: None)
    result["open_file"] = "returned"

    vc = value(value(value(autoclass("UIApplication"), "sharedApplication"), "keyWindow"), "rootViewController")

    def poll(waited):
        shown = value(vc, "presentedViewController")
        if shown is None and waited < 5.0:
            Clock.schedule_once(guarded(lambda dt: poll(waited + 0.25)), 0.25)
            return
        result["presented"] = None if shown is None else \
            ("UIImagePickerController" if shown.isKindOfClass_(autoclass("UIImagePickerController")) else "other")
        vc.dismissViewControllerAnimated_completion_(False, None)
        Clock.schedule_once(lambda dt: finish(), 0.5)

    poll(0.0)


# pyobjus: the reads Plyer's file chooser makes, and its exact expression.
def check_pyobjus(dt):
    import pyobjus
    from pyobjus import autoclass
    result["pyobjus_version"] = getattr(pyobjus, "__version__", "unknown")
    UIApplication = autoclass("UIApplication")
    result["sharedApplication"] = kind(UIApplication, "sharedApplication")
    app = value(UIApplication, "sharedApplication")
    result["keyWindow"] = kind(app, "keyWindow")
    window = value(app, "keyWindow")
    result["keyWindow_is_nil"] = window is None
    result["rootViewController"] = kind(window, "rootViewController")
    try:
        vc = UIApplication.sharedApplication().keyWindow.rootViewController()  # Plyer's line 59
        result["plyer_expression"] = "nil" if vc is None else "ok"
        result["is_view_controller"] = bool(vc.isKindOfClass_(autoclass("UIViewController")))
    except Exception as e:
        result["plyer_expression"] = "raised " + type(e).__name__ + ": " + str(e)[:200]
    vc = value(value(value(UIApplication, "sharedApplication"), "keyWindow"), "rootViewController")
    present_and_check(vc, autoclass("UIImagePickerController"), autoclass("UIViewController"))


# Rubicon: the same reads, Photos loaded as Plyer loads it, and the picker presented.
def check_rubicon(dt):
    import rubicon.objc
    from rubicon.objc import NSObject, ObjCClass, ObjCProtocol, objc_method
    from rubicon.objc.runtime import load_library
    result["rubicon_version"] = rubicon.objc.__version__
    UIApplication = ObjCClass("UIApplication")
    result["sharedApplication"] = kind(UIApplication, "sharedApplication")
    app = UIApplication.sharedApplication
    result["keyWindow"] = kind(app, "keyWindow")
    window = app.keyWindow
    result["keyWindow_is_nil"] = window is None
    result["rootViewController"] = kind(window, "rootViewController")
    vc = UIApplication.sharedApplication.keyWindow.rootViewController
    result["is_view_controller"] = bool(vc.isKindOfClass_(ObjCClass("UIViewController")))
    try:
        UIApplication.sharedApplication.keyWindow.rootViewController()
        result["plyer_form"] = "ok"
    except Exception as e:
        result["plyer_form"] = "raised " + type(e).__name__ + ": " + str(e)[:120]

    for name in ("Photos", "/System/Library/Frameworks/Photos.framework",
                 "/System/Library/Frameworks/Photos.framework/Photos"):
        try:
            load_library(name)
            result["load_library " + name] = "ok"
        except Exception as e:
            result["load_library " + name] = "raised " + type(e).__name__

    try:
        protocols = [ObjCProtocol("UIImagePickerControllerDelegate")]
        result["delegate_protocol"] = "found"
    except NameError:
        protocols = []
        result["delegate_protocol"] = "not found"

    class S8WindowPickerDelegate(NSObject, protocols=protocols):
        @objc_method
        def imagePickerController_didFinishPickingMediaWithInfo_(self, picker, info) -> None:
            picker.dismissViewControllerAnimated_completion_(True, None)

    global _delegate  # the picker's delegate is a weak reference
    _delegate = S8WindowPickerDelegate.alloc().init()
    picker = ObjCClass("UIImagePickerController").alloc().init()
    picker.sourceType = 0
    picker.delegate = _delegate
    result["delegate_set"] = picker.delegate is not None
    present_and_check(vc, ObjCClass("UIImagePickerController"), ObjCClass("UIViewController"), picker)


# probe: which presentations UIKit accepts here, step by step (Rubicon only).
def check_probe(dt):
    from rubicon.objc import ObjCClass
    UIViewController = ObjCClass("UIViewController")
    Picker = ObjCClass("UIImagePickerController")
    vc = ObjCClass("UIApplication").sharedApplication.keyWindow.rootViewController

    def picker():
        p = Picker.alloc().init()
        p.sourceType = 0
        return p

    steps = [("plain_animated", lambda: UIViewController.alloc().init(), True),
             ("picker_not_animated", picker, False),
             ("picker_animated", picker, True)]

    def run(i):
        if i == len(steps):
            finish()
            return
        name, make, animated = steps[i]
        child = make()
        vc.presentViewController_animated_completion_(child, animated, None)
        result[name + "_now"] = vc.presentedViewController is not None

        def later(dt):
            result[name + "_after_2s"] = vc.presentedViewController is not None
            vc.dismissViewControllerAnimated_completion_(False, None)
            Clock.schedule_once(guarded(lambda dt: run(i + 1)), 1.0)

        Clock.schedule_once(guarded(later), 2.0)

    run(0)


CHECKS = {"plyer": check_plyer, "pyobjus": check_pyobjus, "rubicon": check_rubicon, "probe": check_probe}


class WindowTest(App):
    def build(self):
        return Label(text="Section 8 window test: " + LIB)

    def on_start(self):
        if LIB not in CHECKS:
            result["error"] = "S8_LIB must be one of " + ", ".join(CHECKS)
            finish("raised")
        Clock.schedule_once(guarded(CHECKS[LIB]), 1.0)


WindowTest().run()

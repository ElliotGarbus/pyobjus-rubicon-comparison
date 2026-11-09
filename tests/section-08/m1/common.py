"""What both libraries' M1 cases share.

`wait` spins the Core Foundation run loop through ctypes, the same way for
both libraries, so delegate and block callbacks on the main thread arrive.
`private` replaces a value about the Mac's user, such as their preferred
language, with a short hash, so that the two libraries can be compared
without saving the value.
"""
import ctypes
import hashlib
import math
import os
import struct
import tempfile
import time
import wave

_cf = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
_cf.CFRunLoopRunInMode.restype = ctypes.c_int32
_cf.CFRunLoopRunInMode.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_bool]
_default_mode = ctypes.c_void_p.in_dll(_cf, "kCFRunLoopDefaultMode")

TEXT = "héllo, Kivy"
SUITE = "org.comparison.s8"
FLOATS = (1.5, -2.25, 3.0, 4.125)


def wait(done, timeout=10.0):
    end = time.monotonic() + timeout
    while not done() and time.monotonic() < end:
        _cf.CFRunLoopRunInMode(_default_mode, 0.05, False)
    return done()


def private(value):
    return "sha256:" + hashlib.sha256(repr(value).encode()).hexdigest()[:12]


def to_str(value):
    """UTF8String() returns bytes in some versions and str in others."""
    return value.decode("utf-8") if isinstance(value, bytes) else value


def silent_wav():
    """A 0.2 second silent WAV file, for AVAudioPlayer."""
    path = os.path.join(tempfile.mkdtemp(), "silence.wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(b"\0\0" * 1600)
    return path


def scratch_path(name):
    return os.path.join(tempfile.mkdtemp(), name)


def float_bytes():
    return struct.pack("<4f", *FLOATS)


def documents_dir():
    return os.path.expanduser("~/Documents")


def same_path(a, b):
    """iOS can give the same folder under /var and /private/var."""
    return os.path.realpath(a) == os.path.realpath(b)


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-9)


def get(obj, name):
    """Read a zero-argument name either way: as a property or by calling it."""
    v = getattr(obj, name)
    return v() if callable(v) else v


# Zero-argument names the sample calls with (), on a Mac object of the class the sample calls them
# on, or the Mac equivalent: name -> (expression giving the receiver, attribute).
ZERO_ARG = {
    "NSString.UTF8String": ('autoclass("NSString").stringWithString_(objc_str("x"))', "UTF8String"),
    "NSObject.description": ('autoclass("NSString").stringWithString_(objc_str("x"))', "description"),
    "NSArray.count": ('objc_arr(objc_str("a"), objc_str("b"))', "count"),
    "NSArray.firstObject": ('objc_arr(objc_str("a"), objc_str("b"))', "firstObject"),
    "NSArray.lastObject": ('objc_arr(objc_str("a"), objc_str("b"))', "lastObject"),
    "NSLocale.preferredLanguages": ('autoclass("NSLocale")', "preferredLanguages"),
    "preferredLanguages.count": ('get(autoclass("NSLocale"), "preferredLanguages")', "count"),
    "NSFileManager.defaultManager": ('autoclass("NSFileManager")', "defaultManager"),
    "NSUserDefaults.standardUserDefaults": ('autoclass("NSUserDefaults")', "standardUserDefaults"),
    "NSNotificationCenter.defaultCenter": ('autoclass("NSNotificationCenter")', "defaultCenter"),
    "NSPasteboard.generalPasteboard": ('autoclass("NSPasteboard")', "generalPasteboard"),
    "NSScreen.screens": ('autoclass("NSScreen")', "screens"),
    "NSScreen.mainScreen": ('autoclass("NSScreen")', "mainScreen"),
    "NSHost.currentHost": ('autoclass("NSHost")', "currentHost"),
    "NSRunLoop.currentRunLoop": ('autoclass("NSRunLoop")', "currentRunLoop"),
    "NSUUID.UUIDString": ('autoclass("NSUUID").UUID()', "UUIDString"),
    "NSNumber.intValue": ('autoclass("NSNumber").numberWithInt_(3)', "intValue"),
    "NSData.bytes": ('autoclass("NSData").data()', "bytes"),
    "NSValue.rectValue": ('autoclass("NSValue").valueWithRect_(NSRect(NSPoint(0, 0), NSSize(1, 2)))', "rectValue"),
    "AVSpeechSynthesisVoice.speechVoices": ('autoclass("AVSpeechSynthesisVoice")', "speechVoices"),
    "AVSpeechSynthesizer.isSpeaking": ('autoclass("AVSpeechSynthesizer").alloc().init()', "isSpeaking"),
    "NSOpenPanel.openPanel": ('autoclass("NSOpenPanel")', "openPanel"),
    "NSUserNotificationCenter.defaultUserNotificationCenter": ('autoclass("NSUserNotificationCenter")',
                                                               "defaultUserNotificationCenter"),
    "CWWiFiClient.sharedWiFiClient": ('autoclass("CWWiFiClient")', "sharedWiFiClient"),
    "CWWiFiClient.interface": ('get(autoclass("CWWiFiClient"), "sharedWiFiClient")', "interface"),
    "CWInterface.powerOn": ('get(get(autoclass("CWWiFiClient"), "sharedWiFiClient"), "interface")', "powerOn"),
    "CWInterface.ssid": ('get(get(autoclass("CWWiFiClient"), "sharedWiFiClient"), "interface")', "ssid"),
}


# The same check on the iPhone: the portable names above, and the iOS names the sample calls.
ZERO_ARG_IOS = {k: v for k, v in ZERO_ARG.items() if k.split(".")[0] in (
    "NSString", "NSObject", "NSArray", "NSLocale", "preferredLanguages", "NSFileManager", "NSUserDefaults",
    "NSNotificationCenter", "NSRunLoop", "NSUUID", "NSNumber", "NSData", "AVSpeechSynthesisVoice",
    "AVSpeechSynthesizer")}
ZERO_ARG_IOS.update({
    "UIDevice.currentDevice": ('autoclass("UIDevice")', "currentDevice"),
    "UIDevice.userInterfaceIdiom": ('get(autoclass("UIDevice"), "currentDevice")', "userInterfaceIdiom"),
    "UIApplication.sharedApplication": ('autoclass("UIApplication")', "sharedApplication"),
    "UIApplication.keyWindow": ('get(autoclass("UIApplication"), "sharedApplication")', "keyWindow"),
    "UIWindow.rootViewController": ('get(get(autoclass("UIApplication"), "sharedApplication"), "keyWindow")',
                                    "rootViewController"),
    "UIScreen.mainScreen": ('autoclass("UIScreen")', "mainScreen"),
    "UIScreen.bounds": ('get(autoclass("UIScreen"), "mainScreen")', "bounds"),
    "UIScreen.scale": ('get(autoclass("UIScreen"), "mainScreen")', "scale"),
    "AVAudioSession.sharedInstance": ('autoclass("AVAudioSession")', "sharedInstance"),
    "NSValue.CGRectValue": ('autoclass("NSValue").valueWithCGRect_(NSRect(NSPoint(0, 0), NSSize(1, 2)))',
                            "CGRectValue"),
    "UISelectionFeedbackGenerator.prepare": ('autoclass("UISelectionFeedbackGenerator").alloc().init()', "prepare"),
})


# M2: further zero-argument names Kivy and Plyer call, looked up without calling them, on the Mac.
NAMES_M2 = {
    "AVAudioEngine.stop": ('autoclass("AVAudioEngine").alloc().init()', "stop"),
    "AVAudioEngine.prepare": ('autoclass("AVAudioEngine").alloc().init()', "prepare"),
    "AVAudioPlayerNode.play": ('autoclass("AVAudioPlayerNode").alloc().init()', "play"),
    "AVAudioPlayerNode.stop": ('autoclass("AVAudioPlayerNode").alloc().init()', "stop"),
    "AVAudioPlayer.play": ('autoclass("AVAudioPlayer").alloc().initWithContentsOfURL_error_(autoclass("NSURL").fileURLWithPath_(objc_str(silent_wav())), None)', "play"),
    "AVAudioPlayer.stop": ('autoclass("AVAudioPlayer").alloc().initWithContentsOfURL_error_(autoclass("NSURL").fileURLWithPath_(objc_str(silent_wav())), None)', "stop"),
    "AVAudioRecorder.record": ('autoclass("AVAudioRecorder").alloc().initWithURL_settings_error_(autoclass("NSURL").fileURLWithPath_(objc_str(scratch_path("s8.caf"))), {}, None)', "record"),
    "AVAudioRecorder.stop": ('autoclass("AVAudioRecorder").alloc().initWithURL_settings_error_(autoclass("NSURL").fileURLWithPath_(objc_str(scratch_path("s8.caf"))), {}, None)', "stop"),
    "AVCaptureDevice.unlockForConfiguration": ('autoclass("AVCaptureDevice").alloc()', "unlockForConfiguration"),
    "CLLocationManager.requestWhenInUseAuthorization": ('autoclass("CLLocationManager").alloc().init()',
                                                        "requestWhenInUseAuthorization"),
    "CLLocationManager.requestAlwaysAuthorization": ('autoclass("CLLocationManager").alloc().init()',
                                                     "requestAlwaysAuthorization"),
    "CLLocationManager.startUpdatingLocation": ('autoclass("CLLocationManager").alloc().init()',
                                                "startUpdatingLocation"),
    "CLLocationManager.stopUpdatingLocation": ('autoclass("CLLocationManager").alloc().init()',
                                               "stopUpdatingLocation"),
    "NSSet.allObjects": ('autoclass("NSSet").setWithArray_(objc_arr(objc_str("a")))', "allObjects"),
    "NSOpenPanel.filename": ('get(autoclass("NSOpenPanel"), "openPanel")', "filename"),
    "NSOpenPanel.filenames": ('get(autoclass("NSOpenPanel"), "openPanel")', "filenames"),
    "NSOpenPanel.runModal": ('get(autoclass("NSOpenPanel"), "openPanel")', "runModal"),
    "NSSavePanel.savePanel": ('autoclass("NSSavePanel")', "savePanel"),
    "NSPasteboard.clearContents": ('autoclass("NSPasteboard").pasteboardWithName_(objc_str("org.comparison.s8"))',
                                   "clearContents"),
    "CWInterface.interface": ('autoclass("CWInterface")', "interface"),
    "CWInterface.disassociate": ('get(get(autoclass("CWWiFiClient"), "sharedWiFiClient"), "interface")',
                                 "disassociate"),
}


def lookup_kind(obj, name):
    """Like kind(), but never calls the name: a property's getter runs, a method doesn't."""
    try:
        v = getattr(obj, name)
    except Exception as e:
        return "raised " + type(e).__name__
    return "method" if callable(v) else "property"

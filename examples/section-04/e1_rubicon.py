"""E1, clipboard, with Rubicon. Written from Rubicon's docs."""
from rubicon.objc import ObjCClass
from rubicon.objc.runtime import load_library

load_library("AppKit")
NSPasteboard = ObjCClass("NSPasteboard")


class Clipboard:
    def __init__(self):
        # A private pasteboard keeps the test from replacing what the user has
        # copied. An app would use generalPasteboard().
        self._clipboard = NSPasteboard.pasteboardWithUniqueName()

    def get(self):
        data = self._clipboard.stringForType("public.utf8-plain-text")
        return str(data) if data else ""

    def put(self, data):
        self._clipboard.clearContents()
        self._clipboard.setString(data, forType="public.utf8-plain-text")

    def get_types(self):
        return [str(t) for t in self._clipboard.types]


def run(wait):
    clipboard = Clipboard()
    clipboard.put("héllo, Kivy")
    text = clipboard.get()
    clipboard.put("Kivy")
    return {"text": text, "short_text": clipboard.get(), "types": clipboard.get_types()}

"""E1, clipboard, with pyobjus. From Kivy's clipboard_nspaste.py."""
from pyobjus import autoclass
from pyobjus.dylib_manager import INCLUDE, load_framework

load_framework(INCLUDE.AppKit)
NSPasteboard = autoclass("NSPasteboard")


class Clipboard:
    def __init__(self):
        # Kivy uses generalPasteboard(). A private pasteboard keeps the test
        # from replacing what the user has copied.
        self._clipboard = NSPasteboard.pasteboardWithUniqueName()

    def get(self):
        data = self._clipboard.stringForType_("public.utf8-plain-text")
        if not data:
            return ""
        return data.UTF8String()

    def put(self, data):
        self._clipboard.clearContents()
        self._clipboard.setString_forType_(data, "public.utf8-plain-text")

    def get_types(self):
        types = self._clipboard.types
        return [types.objectAtIndex_(i).UTF8String() for i in range(types.count())]


def run(wait):
    clipboard = Clipboard()
    clipboard.put("héllo, Kivy")
    text = clipboard.get()
    clipboard.put("Kivy")
    return {"text": text, "short_text": clipboard.get(), "types": clipboard.get_types()}

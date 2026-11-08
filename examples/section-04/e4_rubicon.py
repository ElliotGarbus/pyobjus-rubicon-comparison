"""E4, a Swift async method, with Rubicon. From the KivyForge guide."""
import threading

from rubicon.objc import NSInteger, ObjCClass

Work = ObjCClass("S4Work")


class NotificationStatus:
    def __init__(self):
        self.value = None

    def start(self):
        def done(status: NSInteger) -> None:
            self.on_main = threading.current_thread() is threading.main_thread()  # measure
            self.value = status

        Work.notificationStatusWithCompletionHandler(done)


def run(wait):
    status = NotificationStatus()
    status.start()
    wait(lambda: status.value is not None)
    return {"status": status.value, "on_main": getattr(status, "on_main", None)}  # measure

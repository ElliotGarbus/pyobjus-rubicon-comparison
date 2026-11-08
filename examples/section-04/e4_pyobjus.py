"""E4, a Swift async method, with pyobjus, which can't pass a completion
handler, so Swift keeps the result for Python to poll."""
from pyobjus import autoclass

PolledWork = autoclass("S4PolledWork")


class NotificationStatus:
    def __init__(self):
        self.value = None
        self.job = None

    def start(self):
        self.job = PolledWork.notificationStatus()

    def poll(self):
        result = self.job.result
        if result is None:
            return False
        self.value = result.integerValue()
        return True


def run(wait):
    status = NotificationStatus()
    status.start()
    wait(status.poll)
    # Swift sets the result on the main thread, and Python polls.
    return {"status": status.value, "on_main": None}  # measure

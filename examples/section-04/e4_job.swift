// E4's Swift for pyobjus, which can't pass a completion handler: the same work,
// started on the main actor, with its one result for Python to poll.
import Foundation
import UserNotifications

@objc(S4PolledWork)
public final class PolledWork: NSObject {
    @objc public private(set) var result: NSNumber?

    @objc public static func notificationStatus() -> PolledWork {
        let work = PolledWork()
        Task { @MainActor in
            let settings =
                await UNUserNotificationCenter.current().notificationSettings()
            work.result = NSNumber(
                value: settings.authorizationStatus.rawValue
            )
        }
        return work
    }
}

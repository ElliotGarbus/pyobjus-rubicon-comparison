// E4's Swift for Rubicon: an async method, which Objective-C sees as
// notificationStatusWithCompletionHandler:. From the KivyForge swift-bridge
// example's notificationSettings, trimmed to the authorization status.
import Foundation
import UserNotifications

@objc(S4Work)
public final class Work: NSObject {
    @objc public static func notificationStatus() async -> Int {
        let settings = await UNUserNotificationCenter.current().notificationSettings()
        return settings.authorizationStatus.rawValue
    }
}

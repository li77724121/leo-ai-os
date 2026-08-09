import AppKit

@objc class ServiceProvider: NSObject {
    @objc func translateSelection(_ pboard: NSPasteboard, userData: String, error: AutoreleasingUnsafeMutablePointer<NSString?>) {
        guard let selected = pboard.string(forType: .string) else {
            error.pointee = "没有选中的文本" as NSString
            return
        }

        // Copy text to clipboard for the app
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(selected, forType: .string)

        // Show translation via notification
        let notification = NSUserNotification()
        notification.title = "Leo 翻译助手"
        notification.informativeText = "正在翻译: \(selected.prefix(50))..."
        notification.soundName = nil
        NSUserNotificationCenter.default.deliver(notification)

        // Do translation in background
        translateAndNotify(selected)
    }

    private func translateAndNotify(_ text: String) {
        TranslationService.shared.translate(text: text, provider: .openrouter) { result in
            DispatchQueue.main.async {
                guard let translated = result else { return }

                // Show result in notification
                let notification = NSUserNotification()
                notification.title = "翻译结果"
                notification.informativeText = translated
                notification.soundName = nil
                NSUserNotificationCenter.default.deliver(notification)

                // Copy result to clipboard
                NSPasteboard.general.clearContents()
                NSPasteboard.general.setString(translated, forType: .string)
            }
        }
    }
}

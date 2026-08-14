// SPDX-FileCopyrightText: 2026 MrDouZheng and contributors
// SPDX-License-Identifier: GPL-3.0-only

import SwiftUI
import WebKit

struct GameWebView: UIViewRepresentable {
    func makeCoordinator() -> Coordinator {
        Coordinator()
    }

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.defaultWebpagePreferences.allowsContentJavaScript = true
        configuration.preferences.javaScriptCanOpenWindowsAutomatically = false
        configuration.websiteDataStore = .nonPersistent()

        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.navigationDelegate = context.coordinator
        webView.isOpaque = false
        webView.backgroundColor = UIColor(red: 16 / 255, green: 20 / 255, blue: 22 / 255, alpha: 1)
        webView.scrollView.backgroundColor = webView.backgroundColor
        webView.scrollView.bounces = false
        webView.scrollView.contentInsetAdjustmentBehavior = .never
        webView.allowsBackForwardNavigationGestures = false

        #if DEBUG
        if #available(iOS 16.4, *) {
            webView.isInspectable = true
        }
        #endif

        loadGame(in: webView)
        return webView
    }

    func updateUIView(_ webView: WKWebView, context: Context) {}

    private func loadGame(in webView: WKWebView) {
        guard
            let indexURL = Bundle.main.url(forResource: "index", withExtension: "html", subdirectory: "Web")
        else {
            webView.loadHTMLString(errorPage("离线游戏资源未打包。"), baseURL: nil)
            return
        }

        let webDirectory = indexURL.deletingLastPathComponent()
        webView.loadFileURL(indexURL, allowingReadAccessTo: webDirectory)
    }

    private func errorPage(_ message: String) -> String {
        """
        <!doctype html><meta name="viewport" content="width=device-width,initial-scale=1">
        <style>body{background:#101416;color:#f4f0e8;font:16px -apple-system;padding:48px 24px}</style>
        <h1>斗弈</h1><p>\(message)</p>
        """
    }

    final class Coordinator: NSObject, WKNavigationDelegate {
        func webView(
            _ webView: WKWebView,
            decidePolicyFor navigationAction: WKNavigationAction,
            decisionHandler: @escaping (WKNavigationActionPolicy) -> Void
        ) {
            guard let url = navigationAction.request.url else {
                decisionHandler(.cancel)
                return
            }

            // The iPhone app is intentionally offline: only bundled files and
            // WebKit's blank document are allowed to load.
            decisionHandler(url.isFileURL || url.scheme == "about" ? .allow : .cancel)
        }
    }
}

// SPDX-FileCopyrightText: 2026 MrDouZheng and contributors
// SPDX-License-Identifier: GPL-3.0-only

import SwiftUI

@main
struct DouYiApp: App {
    var body: some Scene {
        WindowGroup {
            GameWebView()
                .background(Color(red: 16 / 255, green: 20 / 255, blue: 22 / 255))
                .ignoresSafeArea()
        }
    }
}

// SPDX-FileCopyrightText: 2026 MrDouZheng and contributors
// SPDX-License-Identifier: GPL-3.0-only

package com.mrdouzheng.rapfigomoku;

import android.app.Activity;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.io.IOException;
import java.io.InputStream;
import java.util.Locale;

public final class MainActivity extends Activity {
    private static final String APP_HOST = "appassets.androidplatform.net";
    private WebView webView;

    @Override
    @SuppressWarnings("SetJavaScriptEnabled")
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        webView = new WebView(this);
        webView.setBackgroundColor(Color.rgb(16, 20, 22));
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setCacheMode(WebSettings.LOAD_NO_CACHE);

        webView.setWebViewClient(new LocalAssetClient());
        setContentView(webView);
        webView.loadUrl("https://" + APP_HOST + "/assets/index.html");
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.loadUrl("about:blank");
            webView.destroy();
        }
        super.onDestroy();
    }

    private final class LocalAssetClient extends WebViewClient {
        @Override
        public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
            Uri uri = request.getUrl();
            if (!APP_HOST.equals(uri.getHost())) {
                return super.shouldInterceptRequest(view, request);
            }

            String path = uri.getPath();
            if (path == null || !path.startsWith("/assets/")) {
                return new WebResourceResponse("text/plain", "UTF-8", 404, "Not Found", null, null);
            }

            String assetPath = path.substring("/assets/".length());
            try {
                InputStream stream = getAssets().open(assetPath);
                return new WebResourceResponse(mimeType(assetPath), encoding(assetPath), stream);
            } catch (IOException exception) {
                return new WebResourceResponse("text/plain", "UTF-8", 404, "Not Found", null, null);
            }
        }

        private String mimeType(String path) {
            String lower = path.toLowerCase(Locale.ROOT);
            if (lower.endsWith(".html")) return "text/html";
            if (lower.endsWith(".css")) return "text/css";
            if (lower.endsWith(".js")) return "application/javascript";
            if (lower.endsWith(".wasm")) return "application/wasm";
            if (lower.endsWith(".json")) return "application/json";
            if (lower.endsWith(".svg")) return "image/svg+xml";
            if (lower.endsWith(".png")) return "image/png";
            return "application/octet-stream";
        }

        private String encoding(String path) {
            String lower = path.toLowerCase(Locale.ROOT);
            return lower.endsWith(".wasm") || lower.endsWith(".data") ? null : "UTF-8";
        }
    }
}

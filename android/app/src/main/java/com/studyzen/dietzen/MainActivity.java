package com.studyzen.dietzen;

import android.annotation.SuppressLint;
import android.os.Bundle;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.webkit.WebViewAssetLoader;
import androidx.webkit.WebViewClientCompat;

/**
 * DietZen 的 Android 外殼。
 *
 * 網頁不是用 file:// 載入，而是透過 WebViewAssetLoader 以
 * https://appassets.androidplatform.net/ 提供 —— file:// 在 WebView 裡不是安全來源，
 * localStorage 的行為會不穩；換成正常的 https 來源後，App 的資料儲存就跟在瀏覽器裡一樣可靠。
 */
public class MainActivity extends AppCompatActivity {

    private static final String BASE = "https://appassets.androidplatform.net";
    private WebView webView;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        webView = findViewById(R.id.webview);

        final WebViewAssetLoader assetLoader = new WebViewAssetLoader.Builder()
                .setDomain("appassets.androidplatform.net")
                .addPathHandler("/", new WebViewAssetLoader.AssetsPathHandler(this))
                .build();

        webView.setWebViewClient(new WebViewClientCompat() {
            @Override
            public WebResourceResponse shouldInterceptRequest(@NonNull WebView view,
                                                              @NonNull WebResourceRequest request) {
                return assetLoader.shouldInterceptRequest(request.getUrl());
            }
        });

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);   // localStorage：所有紀錄都存在這裡
        settings.setSupportZoom(false);
        settings.setMediaPlaybackRequiresUserGesture(false);

        webView.setOverScrollMode(WebView.OVER_SCROLL_NEVER);

        if (savedInstanceState == null) {
            webView.loadUrl(BASE + "/index.html");
        } else {
            webView.restoreState(savedInstanceState);
        }
    }

    @Override
    protected void onSaveInstanceState(@NonNull Bundle outState) {
        super.onSaveInstanceState(outState);
        webView.saveState(outState);
    }

    /** 返回鍵：底部彈出面板開著時先關掉它，否則才離開 App。 */
    @Override
    public void onBackPressed() {
        webView.evaluateJavascript(
                "(function(){var s=document.getElementById('sheet');"
                        + "if(s&&s.classList.contains('open')){"
                        + "document.getElementById('scrim').click();return 'handled';}"
                        + "return 'exit';})()",
                value -> {
                    if (value == null || value.contains("exit")) {
                        finish();
                    }
                });
    }
}

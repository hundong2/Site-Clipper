package com.siteclipper.app.ui

import android.webkit.CookieManager
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import com.siteclipper.app.data.CookieItem

@Composable
fun CookieWebViewScreen(
    url: String,
    onCookiesExtracted: (List<CookieItem>) -> Unit,
    onDismiss: () -> Unit,
) {
    var currentUrl by remember { mutableStateOf(url) }

    Column(modifier = Modifier.fillMaxSize()) {
        TopAppBar(
            title = { Text("Login to site", maxLines = 1) },
            actions = {
                TextButton(onClick = {
                    val cookies = extractCookies(currentUrl)
                    onCookiesExtracted(cookies)
                }) {
                    Text("Done")
                }
                TextButton(onClick = onDismiss) {
                    Text("Cancel")
                }
            }
        )

        Text(
            text = currentUrl,
            style = MaterialTheme.typography.bodySmall,
            maxLines = 1,
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp)
        )

        AndroidView(
            factory = { ctx ->
                WebView(ctx).apply {
                    settings.javaScriptEnabled = true
                    settings.domStorageEnabled = true
                    CookieManager.getInstance().setAcceptCookie(true)
                    CookieManager.getInstance().setAcceptThirdPartyCookies(this, true)

                    webViewClient = object : WebViewClient() {
                        override fun onPageFinished(view: WebView?, pageUrl: String?) {
                            pageUrl?.let { currentUrl = it }
                        }
                    }
                    loadUrl(url)
                }
            },
            modifier = Modifier.fillMaxSize()
        )
    }
}

private fun extractCookies(url: String): List<CookieItem> {
    val cookieManager = CookieManager.getInstance()
    val cookieString = cookieManager.getCookie(url) ?: return emptyList()
    val domain = try {
        java.net.URI(url).host ?: ""
    } catch (_: Exception) {
        ""
    }

    return cookieString.split(";").mapNotNull { raw ->
        val parts = raw.trim().split("=", limit = 2)
        if (parts.size == 2) {
            CookieItem(
                name = parts[0].trim(),
                value = parts[1].trim(),
                domain = domain,
            )
        } else null
    }
}

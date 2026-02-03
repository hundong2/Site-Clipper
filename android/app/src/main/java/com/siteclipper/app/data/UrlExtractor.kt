package com.siteclipper.app.data

object UrlExtractor {
    private val URL_REGEX = Regex(
        """https?://[^\s<>"{}|\\^`\[\]]+"""
    )

    fun extract(text: String): String? {
        return URL_REGEX.find(text)?.value
    }
}

package com.siteclipper.app.data

import android.content.ContentValues
import android.content.Context
import android.net.Uri
import android.os.Environment
import android.provider.MediaStore

object FileManager {

    fun saveMarkdown(context: Context, filename: String, content: String): Uri? {
        val values = ContentValues().apply {
            put(MediaStore.MediaColumns.DISPLAY_NAME, filename)
            put(MediaStore.MediaColumns.MIME_TYPE, "text/markdown")
            put(
                MediaStore.MediaColumns.RELATIVE_PATH,
                "${Environment.DIRECTORY_DOCUMENTS}/SiteClipper"
            )
        }

        val resolver = context.contentResolver
        val uri = resolver.insert(MediaStore.Files.getContentUri("external"), values)
            ?: return null

        resolver.openOutputStream(uri)?.use { stream ->
            stream.write(content.toByteArray())
        }

        return uri
    }
}

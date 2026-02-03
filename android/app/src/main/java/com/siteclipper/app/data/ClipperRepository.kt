package com.siteclipper.app.data

import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow

class ClipperRepository(
    private val api: ApiService = ApiClient.service
) {
    suspend fun submitUrl(
        url: String,
        sitemap: Boolean = false,
        cookies: List<CookieItem> = emptyList(),
    ): CrawlResponse {
        return api.createCrawl(CrawlRequest(url, sitemap, cookies))
    }

    fun streamTask(taskId: String): Flow<SseEvent> {
        return SseClient.streamTask(taskId)
    }

    suspend fun uploadToDrive(
        taskId: String,
        accessToken: String,
        filename: String? = null,
    ): DriveUploadResponse {
        return api.uploadToDrive(DriveUploadRequest(taskId, accessToken, filename))
    }

    suspend fun pollUntilDone(
        taskId: String,
        intervalMs: Long = 2000,
        onProgress: (Int) -> Unit = {},
    ): TaskResult {
        while (true) {
            val task = api.getTask(taskId)
            onProgress(task.progress)
            when (task.status) {
                "completed", "failed" -> return task
                else -> delay(intervalMs)
            }
        }
    }
}

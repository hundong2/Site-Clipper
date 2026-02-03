package com.siteclipper.app.data

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

data class CookieItem(
    val name: String,
    val value: String,
    val domain: String = "",
    val path: String = "/"
)

data class CrawlRequest(
    val url: String,
    val sitemap: Boolean = false,
    val cookies: List<CookieItem> = emptyList()
)
data class CrawlResponse(val task_id: String, val status: String)
data class TaskResult(
    val id: String,
    val url: String,
    val status: String,
    val progress: Int = 0,
    val total_pages: Int = 0,
    val processed_pages: Int = 0,
    val result: String?,
    val error: String?
)
data class DriveUploadRequest(
    val task_id: String,
    val access_token: String,
    val filename: String? = null,
)

data class DriveUploadResponse(
    val file_id: String,
    val name: String,
    val web_link: String,
)

data class HealthResponse(val status: String)

interface ApiService {
    @POST("/api/v1/crawl")
    suspend fun createCrawl(@Body request: CrawlRequest): CrawlResponse

    @GET("/api/v1/tasks/{taskId}")
    suspend fun getTask(@Path("taskId") taskId: String): TaskResult

    @POST("/api/v1/drive/upload")
    suspend fun uploadToDrive(@Body request: DriveUploadRequest): DriveUploadResponse

    @GET("/api/v1/health")
    suspend fun health(): HealthResponse
}

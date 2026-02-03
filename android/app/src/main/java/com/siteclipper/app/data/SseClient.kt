package com.siteclipper.app.data

import com.siteclipper.app.BuildConfig
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import okhttp3.*
import okhttp3.sse.EventSource
import okhttp3.sse.EventSourceListener
import okhttp3.sse.EventSources
import org.json.JSONObject

data class SseEvent(
    val event: String,
    val status: String,
    val progress: Int,
    val result: String? = null,
    val error: String? = null,
)

object SseClient {
    private val client = OkHttpClient.Builder().build()

    fun streamTask(taskId: String): Flow<SseEvent> = callbackFlow {
        val request = Request.Builder()
            .url("${BuildConfig.API_BASE_URL}/api/v1/tasks/$taskId/stream")
            .header("Accept", "text/event-stream")
            .build()

        val factory = EventSources.createFactory(client)

        val listener = object : EventSourceListener() {
            override fun onEvent(
                eventSource: EventSource,
                id: String?,
                type: String?,
                data: String
            ) {
                try {
                    val json = JSONObject(data)
                    val event = SseEvent(
                        event = type ?: "progress",
                        status = json.optString("status", ""),
                        progress = json.optInt("progress", 0),
                        result = json.optString("result", null),
                        error = json.optString("error", null),
                    )
                    trySend(event)

                    if (type == "done") {
                        close()
                    }
                } catch (_: Exception) {}
            }

            override fun onFailure(
                eventSource: EventSource,
                t: Throwable?,
                response: Response?
            ) {
                close(t)
            }

            override fun onClosed(eventSource: EventSource) {
                close()
            }
        }

        val eventSource = factory.newEventSource(request, listener)

        awaitClose {
            eventSource.cancel()
        }
    }
}

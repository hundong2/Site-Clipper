package com.siteclipper.app.ui

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.siteclipper.app.data.ClipperRepository
import com.siteclipper.app.data.CookieItem
import com.siteclipper.app.data.FileManager
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.launch

sealed interface UiState {
    data object Idle : UiState
    data object Submitting : UiState
    data class Processing(val taskId: String, val progress: Int = 0) : UiState
    data class Completed(
        val markdown: String,
        val url: String,
        val taskId: String = "",
        val savedPath: String? = null,
        val driveLink: String? = null,
    ) : UiState
    data class Error(val message: String) : UiState
}

class ClipperViewModel(
    private val repo: ClipperRepository = ClipperRepository()
) : ViewModel() {

    private val _uiState = MutableStateFlow<UiState>(UiState.Idle)
    val uiState: StateFlow<UiState> = _uiState

    private var pendingCookies: List<CookieItem> = emptyList()

    fun setCookies(cookies: List<CookieItem>) {
        pendingCookies = cookies
    }

    fun submit(url: String) {
        viewModelScope.launch {
            try {
                _uiState.value = UiState.Submitting
                val response = repo.submitUrl(url, cookies = pendingCookies)
                _uiState.value = UiState.Processing(response.task_id)

                var sseSucceeded = false
                try {
                    repo.streamTask(response.task_id)
                        .catch { /* SSE failed, will fallback to polling */ }
                        .collect { event ->
                            _uiState.value = UiState.Processing(response.task_id, event.progress)
                            if (event.event == "done") {
                                sseSucceeded = true
                                if (event.status == "completed" && event.result != null) {
                                    _uiState.value = UiState.Completed(
                                        markdown = event.result,
                                        url = url,
                                        taskId = response.task_id,
                                    )
                                } else {
                                    _uiState.value = UiState.Error(event.error ?: "Unknown error")
                                }
                            }
                        }
                } catch (_: Exception) {}

                // Fallback to polling if SSE didn't complete
                if (!sseSucceeded) {
                    val result = repo.pollUntilDone(response.task_id) { progress ->
                        _uiState.value = UiState.Processing(response.task_id, progress)
                    }
                    if (result.status == "completed" && result.result != null) {
                        _uiState.value = UiState.Completed(
                            markdown = result.result,
                            url = url,
                            taskId = response.task_id,
                        )
                    } else {
                        _uiState.value = UiState.Error(result.error ?: "Unknown error")
                    }
                }
            } catch (e: Exception) {
                _uiState.value = UiState.Error(e.message ?: "Connection failed")
            }
        }
    }

    fun uploadToDrive(accessToken: String) {
        val state = _uiState.value
        if (state !is UiState.Completed) return

        viewModelScope.launch {
            try {
                val response = repo.uploadToDrive(
                    taskId = state.taskId,
                    accessToken = accessToken,
                )
                _uiState.value = state.copy(driveLink = response.web_link)
            } catch (e: Exception) {
                // Don't replace state, just log silently
                // User can retry
            }
        }
    }

    fun saveToFile(context: Context) {
        val state = _uiState.value
        if (state !is UiState.Completed) return

        val filename = state.url
            .removePrefix("https://")
            .removePrefix("http://")
            .replace(Regex("[^a-zA-Z0-9.-]"), "_")
            .take(80) + ".md"

        val uri = FileManager.saveMarkdown(context, filename, state.markdown)
        if (uri != null) {
            _uiState.value = state.copy(savedPath = uri.toString())
        }
    }
}

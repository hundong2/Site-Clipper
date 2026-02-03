package com.siteclipper.app.ui

import android.app.Activity
import android.content.Intent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.google.android.gms.auth.api.signin.GoogleSignIn
import com.google.android.gms.common.api.ApiException
import com.siteclipper.app.data.GoogleSignInHelper

@Composable
fun ShareReceiverScreen(
    sharedUrl: String?,
    viewModel: ClipperViewModel = viewModel()
) {
    val state by viewModel.uiState.collectAsState()
    val context = LocalContext.current
    var showCookieLogin by remember { mutableStateOf(false) }

    val signInLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            try {
                val account = GoogleSignIn.getSignedInAccountFromIntent(result.data)
                    .getResult(ApiException::class.java)
                account.serverAuthCode?.let { authCode ->
                    viewModel.uploadToDrive(authCode)
                }
            } catch (_: ApiException) {}
        }
    }

    LaunchedEffect(sharedUrl) {
        if (sharedUrl != null && state is UiState.Idle) {
            viewModel.submit(sharedUrl)
        }
    }

    if (showCookieLogin && sharedUrl != null) {
        CookieWebViewScreen(
            url = sharedUrl,
            onCookiesExtracted = { cookies ->
                viewModel.setCookies(cookies)
                showCookieLogin = false
                viewModel.submit(sharedUrl)
            },
            onDismiss = { showCookieLogin = false }
        )
        return
    }

    Surface(
        modifier = Modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.background
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text = "Site Clipper",
                style = MaterialTheme.typography.headlineMedium
            )

            Spacer(modifier = Modifier.height(32.dp))

            when (val s = state) {
                is UiState.Idle -> {
                    Text("Share a URL from any app to convert it to markdown.")
                }
                is UiState.Submitting -> {
                    CircularProgressIndicator()
                    Spacer(modifier = Modifier.height(16.dp))
                    Text("Submitting...")
                }
                is UiState.Processing -> {
                    if (s.progress > 0) {
                        LinearProgressIndicator(
                            progress = { s.progress / 100f },
                            modifier = Modifier.fillMaxWidth()
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text("Converting... ${s.progress}%")
                    } else {
                        CircularProgressIndicator()
                        Spacer(modifier = Modifier.height(16.dp))
                        Text("Converting to markdown...")
                    }
                }
                is UiState.Completed -> {
                    Text("Conversion complete!", style = MaterialTheme.typography.titleMedium)
                    Spacer(modifier = Modifier.height(16.dp))

                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        Button(onClick = { viewModel.saveToFile(context) }) {
                            Text("Save File")
                        }
                        OutlinedButton(onClick = {
                            val intent = Intent(Intent.ACTION_SEND).apply {
                                type = "text/plain"
                                putExtra(Intent.EXTRA_TEXT, s.markdown)
                            }
                            context.startActivity(Intent.createChooser(intent, "Share markdown"))
                        }) {
                            Text("Share")
                        }
                    }

                    Spacer(modifier = Modifier.height(8.dp))

                    OutlinedButton(onClick = {
                        val account = GoogleSignInHelper.getLastSignedInAccount(context)
                        if (account?.serverAuthCode != null) {
                            viewModel.uploadToDrive(account.serverAuthCode!!)
                        } else {
                            val intent = GoogleSignInHelper.getSignInIntent(
                                context,
                                serverClientId = "" // TODO: Set your Google OAuth client ID
                            )
                            signInLauncher.launch(intent)
                        }
                    }) {
                        Text("Upload to Google Drive")
                    }

                    if (s.savedPath != null) {
                        Spacer(modifier = Modifier.height(12.dp))
                        Text(
                            text = "Saved to Documents/SiteClipper/",
                            style = MaterialTheme.typography.bodySmall,
                            textAlign = TextAlign.Center
                        )
                    }

                    if (s.driveLink != null) {
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "Uploaded to Google Drive",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.primary,
                            textAlign = TextAlign.Center
                        )
                    }
                }
                is UiState.Error -> {
                    Text(
                        text = "Error: ${s.message}",
                        color = MaterialTheme.colorScheme.error,
                        textAlign = TextAlign.Center
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        Button(onClick = {
                            sharedUrl?.let { viewModel.submit(it) }
                        }) {
                            Text("Retry")
                        }
                        OutlinedButton(onClick = {
                            showCookieLogin = true
                        }) {
                            Text("Login & Retry")
                        }
                    }
                }
            }
        }
    }
}

package com.siteclipper.app.data

import android.content.Context
import android.content.Intent
import com.google.android.gms.auth.api.signin.GoogleSignIn
import com.google.android.gms.auth.api.signin.GoogleSignInAccount
import com.google.android.gms.auth.api.signin.GoogleSignInClient
import com.google.android.gms.auth.api.signin.GoogleSignInOptions
import com.google.android.gms.common.api.Scope

object GoogleSignInHelper {

    private const val DRIVE_FILE_SCOPE = "https://www.googleapis.com/auth/drive.file"

    fun getClient(context: Context, serverClientId: String): GoogleSignInClient {
        val gso = GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
            .requestEmail()
            .requestScopes(Scope(DRIVE_FILE_SCOPE))
            .requestServerAuthCode(serverClientId)
            .build()
        return GoogleSignIn.getClient(context, gso)
    }

    fun getSignInIntent(context: Context, serverClientId: String): Intent {
        return getClient(context, serverClientId).signInIntent
    }

    fun getLastSignedInAccount(context: Context): GoogleSignInAccount? {
        return GoogleSignIn.getLastSignedInAccount(context)
    }
}

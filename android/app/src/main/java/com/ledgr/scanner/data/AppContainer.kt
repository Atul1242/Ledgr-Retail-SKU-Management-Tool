package com.ledgr.scanner.data

import android.content.Context
import com.ledgr.scanner.data.api.ApiHolder
import com.ledgr.scanner.data.db.AppDatabase
import com.ledgr.scanner.data.prefs.AppPrefs

/** Tiny manual-DI container. Avoids dragging in Hilt for an app this small. */
class AppContainer(context: Context) {
    val prefs: AppPrefs = AppPrefs(context.applicationContext)
    val db: AppDatabase = AppDatabase.get(context.applicationContext)
    val apiHolder: ApiHolder = ApiHolder(prefs)
}

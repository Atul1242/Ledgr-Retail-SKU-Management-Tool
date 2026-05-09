package com.ledgr.scanner

import android.app.Application
import com.ledgr.scanner.data.AppContainer

class LedgrApp : Application() {
    lateinit var container: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        container = AppContainer(this)
    }
}

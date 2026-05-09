package com.ledgr.scanner.data.db

import androidx.room.Dao
import androidx.room.Database
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.Room
import androidx.room.RoomDatabase
import android.content.Context
import kotlinx.coroutines.flow.Flow

@Entity(tableName = "scan_queue")
data class ScanRow(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val sku_code: String,
    val product_name: String? = null,
    val qty_received: Int = 1,
    val batch_expiry: String? = null,
    val scanned_at: Long = System.currentTimeMillis(),
    val synced: Boolean = false,
    val error: String? = null,
)

@Dao
interface ScanQueueDao {
    @Insert suspend fun insert(row: ScanRow): Long
    @Query("SELECT * FROM scan_queue WHERE synced = 0 ORDER BY scanned_at ASC") suspend fun pending(): List<ScanRow>
    @Query("SELECT * FROM scan_queue ORDER BY scanned_at DESC LIMIT 50") fun recent(): Flow<List<ScanRow>>
    @Query("UPDATE scan_queue SET synced = 1, error = NULL WHERE id = :id") suspend fun markSynced(id: Long)
    @Query("UPDATE scan_queue SET error = :err WHERE id = :id") suspend fun markError(id: Long, err: String)
    @Query("SELECT COUNT(*) FROM scan_queue WHERE synced = 0") fun pendingCount(): Flow<Int>
    @Query("DELETE FROM scan_queue WHERE synced = 1 AND scanned_at < :cutoff") suspend fun pruneOld(cutoff: Long)
}

@Database(entities = [ScanRow::class], version = 1, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {
    abstract fun scanQueue(): ScanQueueDao

    companion object {
        @Volatile private var INSTANCE: AppDatabase? = null
        fun get(context: Context): AppDatabase = INSTANCE ?: synchronized(this) {
            INSTANCE ?: Room.databaseBuilder(context.applicationContext, AppDatabase::class.java, "ledgr.db")
                .fallbackToDestructiveMigration()
                .build()
                .also { INSTANCE = it }
        }
    }
}

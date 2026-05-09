package com.ledgr.scanner.data

import com.ledgr.scanner.data.api.ApiHolder
import com.ledgr.scanner.data.api.ScanRequest
import com.ledgr.scanner.data.db.AppDatabase
import com.ledgr.scanner.data.db.ScanRow
import com.ledgr.scanner.data.prefs.AppPrefs
import kotlinx.coroutines.flow.Flow
import okhttp3.ResponseBody
import retrofit2.Response

/** Captures a scan + handles best-effort sync. Falls back to a Room queue
 *  when the server is unreachable; the queue is drained on Sync Now or the
 *  next successful scan. */
class ScanRepository(
    private val db: AppDatabase,
    private val prefs: AppPrefs,
    private val apiHolder: ApiHolder,
) {
    private val dao = db.scanQueue()

    fun recent(): Flow<List<ScanRow>> = dao.recent()
    fun pendingCount(): Flow<Int> = dao.pendingCount()

    /** Local-first: insert a row, then attempt to sync. Returns the row id
     *  and whether the immediate sync attempt succeeded. */
    suspend fun captureScan(req: ScanRequest): Pair<Long, Boolean> {
        val row = ScanRow(
            sku_code = req.sku_code,
            product_name = req.product_name,
            qty_received = req.qty_received,
            batch_expiry = req.batch_expiry,
        )
        val id = dao.insert(row)
        val ok = tryUpload(id, req)
        return id to ok
    }

    /** Drain all pending rows. Returns (succeeded, failed). */
    suspend fun drainQueue(): Pair<Int, Int> {
        var ok = 0; var fail = 0
        for (row in dao.pending()) {
            val req = ScanRequest(
                sku_code = row.sku_code,
                product_name = row.product_name,
                qty_received = row.qty_received,
                batch_expiry = row.batch_expiry,
                scanned_at = row.scanned_at.toString(),
            )
            if (tryUpload(row.id, req)) ok++ else fail++
        }
        return ok to fail
    }

    private suspend fun tryUpload(id: Long, req: ScanRequest): Boolean {
        val api = apiHolder.api ?: return false
        return try {
            val r = api.scan(req)
            if (r.isSuccessful && r.body()?.status == "success") {
                dao.markSynced(id); true
            } else {
                val msg = r.body()?.message ?: "HTTP ${r.code()}"
                dao.markError(id, msg); false
            }
        } catch (e: Exception) {
            dao.markError(id, e.message ?: e::class.java.simpleName)
            false
        }
    }

    /** Convenience: refresh CSRF token by hitting the home page and parsing
     *  the meta tag. Stored in prefs; the OkHttp interceptor reads it. */
    suspend fun refreshCsrf(): Boolean {
        val api = apiHolder.api ?: return false
        val resp: Response<ResponseBody> = try { api.home() } catch (e: Exception) { return false }
        if (!resp.isSuccessful) return false
        val html = resp.body()?.string() ?: return false
        val match = Regex("""name="csrf-token" content="([^"]+)"""").find(html) ?: return false
        prefs.saveCsrf(match.groupValues[1])
        return true
    }
}

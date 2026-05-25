# Kintsugi-DAM: System Overview & Architecture

Welcome to the Kintsugi-DAM wiki! Kintsugi-DAM is a highly opinionated traffic controller and Digital Asset Management system designed to seamlessly manage, quarantine, and remediate digital media files.

## Architecture Summary
Kintsugi-DAM is built to run safely and efficiently on low-resource home servers. We affectionately refer to this as our "Toaster Philosophy." Operations are stateless, idempotent, and highly memory-efficient.

The backend stack is powered by:
- **FastAPI (Python):** Serves as the high-performance async web framework.
- **SQLite (via Async SQLAlchemy):** Provides robust, local storage without heavy infrastructure overhead (though PostgreSQL and MySQL are fully supported).
- **Rust (`kintsugi_rs`):** A custom core hashing module that uses `blake3` to stream files in small chunks, minimizing RAM usage dramatically.

## The "Dumb" Pipeline
The core application acts as a traffic controller routing files between Detection Algorithms, Triage systems, and Backup Providers.
**Kintsugi-DAM does not analyze the files itself.** Instead, it monitors physical directories, pipes files through external/plugin logic, and reacts to the results.

## The Recycle Bin Rule
Kintsugi-DAM enforces a strict safety mechanism: **Files are never permanently deleted from the live library.**
When a file is flagged as corrupted or requires replacement, it is quarantined and moved to a Recycle Bin directory subject to a strict grace period (Time-To-Live). This ensures that accidental false positives never result in permanent data loss.

## Manual vs. Automatic Remediation
- **Manual Intervention:** By default, remediation requires explicit user consent via the WebUI (Triage). Corrupted files will sit in quarantine until approved.
- **Auto-Restore:** Live files can be automatically replaced if the user explicitly enables the `auto_restore` setting in the system.

## Continuous Monitoring
Real-time file monitoring is handled by a `WatcherService` leveraging the `watchdog` library. It implements a settling/debounce queue (waiting for file size stability) before introducing new files to the async scanning semaphore. Out-of-band background scanning is scheduled via APScheduler.

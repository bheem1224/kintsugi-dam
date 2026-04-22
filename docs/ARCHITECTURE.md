# Kintsugi-DAM: Core Architecture & AI System Instructions

## 1. Core Philosophy & Non-Negotiables
* **The "Dumb" Pipeline:** The core application is a highly opinionated traffic controller. It routes files between Detection Algorithms and Backup Providers. It does not analyze files itself.
* **Strict Manual Intervention:** The system must NEVER automatically delete or replace a live file. Detection runs automatically; remediation requires explicit user consent via the WebUI.
* **The Recycle Bin Rule:** Files are never permanently deleted from the live library. When quarantined or replaced, the original corrupted file is moved to a dedicated Recycle Bin directory. The system enforces a strict grace period (e.g., 30/90 days) before actual file deletion is permitted.
* **The "Toaster" Philosophy:** The app must run safely on low-resource home servers. Heavy processes (like ImageMagick) must be strictly throttled using `asyncio.Semaphore` to prevent CPU/RAM exhaustion.

## 2. The Abstraction Layer (Plugins)
All external logic is handled via two strict Abstract Base Classes (ABCs).
* **`DetectorProvider`:** Read-only algorithms (e.g., ImageMagick, jpeginfo) that return a boolean (Healthy/Corrupted) and a message.
* **`RemediationProvider`:** Storage interfaces (e.g., ZFS, BTRFS, S3, Storj) that locate clean snapshots and handle the transfer of files to the core app's quarantine zone.

### 2a. Internal Sandboxing & AST Validation
Before loading any plugin dynamically, the core app runs an AST (Abstract Syntax Tree) scan on the Python file. 
* **Rule:** If a `DetectorProvider` plugin contains AST nodes for file modification (`open(..., 'w')`, `os.remove`, `shutil.move`), the plugin is rejected and fails to load.
* **Rule:** Algorithms only receive read-only file access (or byte streams) from the core.

## 3. The Scanning Engine & Concurrency
Processing a massive (2TB+) library requires bypassing Python's GIL and minimizing disk I/O.
* **The Fast Sweep:** Uses `os.scandir` to rapidly check `mtime` and file size. Only hashes files if the `mtime` has changed (catching intentional user edits).
* **The Deep Path (Bit-Rot Catch):** Periodically selects a subset of older files and recalculates their SHA-256 hashes even if `mtime` hasn't changed, verifying physical disk integrity.
* **Multiprocessing:** Native Python hashing uses `concurrent.futures.ProcessPoolExecutor` to utilize multiple CPU cores. CLI tools (like ImageMagick) are called via `asyncio.create_subprocess_exec` to offload work to the OS.

## 4. Tech Stack & State Management
* **Frontend:** Next.js (App Router), Tailwind CSS, shadcn/ui.
* **Backend:** Python + FastAPI.
* **Database:** SQLite running in `WAL` (Write-Ahead Logging) mode to allow concurrent API reads while the background scanner writes.
* **ORM:** SQLAlchemy 2.0 (using asynchronous `aiosqlite`).

## 5. Timeboxed Execution & Smart Scheduling
To accommodate massive libraries (e.g., 10TB+) without bogging down the host server during waking hours, the scanning engine strictly operates within user-defined Maintenance Windows.
* **The Timebox Rule:** The scanner loop must check the current time after every file (or small batch). If `datetime.now()` exceeds the configured end time (e.g., 2:00 AM), the scanner gracefully pauses, commits the current progress to the database, and sleeps until the next scheduled window.
* **Continuous Cycling:** Combined with the "Deep Path" hash check (prioritizing the oldest `last_hashed_date`), the application continuously and seamlessly cycles through the entire library across multiple days or weeks.
* **Predictive Retention Analytics:** The core app must track "Scan Velocity" (GB processed per hour). It calculates the Total Library Size divided by the Scan Velocity to determine the "Full Cycle Time." The WebUI must expose this metric to warn the user about their external backup retention policies (e.g., "Your library takes 14 days to fully scan. Ensure your ZFS snapshots or Cloud backups are configured for at least a 15-day retention period, or corrupted files may fall out of your backup window before detection").
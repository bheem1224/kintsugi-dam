***

### 2. `Guide.md`

```markdown
# 🏺 Kintsugi-DAM: The Official Guide

Welcome to the Kintsugi-DAM wiki. This document contains deep-dive explanations of our architecture, obscure settings, and advanced workflows for Pro and Studio users.

## 📑 Index
1. [The Consensus Detection Engine](#1-the-consensus-detection-engine)
2. [Configuring Local Snapshot Remediation](#2-configuring-local-snapshot-remediation)
3. [The "Toaster Philosophy" (Concurrency Limits)](#3-the-toaster-philosophy)
4. [Advanced: The Kintsugi AI Protocol (Pro/Studio)](#4-advanced-the-kintsugi-ai-protocol)
5. [Security: The Serverless Cloud Gateway](#5-security-the-serverless-cloud-gateway)

---

### 1. The Consensus Detection Engine
Kintsugi does not rely on a single point of failure. When a file is scanned, it passes through multiple plugins:
* **Stage 1 (Fast Boundary Scan):** The `jpeginfo` plugin runs a high-speed Huffman boundary check. If it fails, the file is marked **CORRUPTED**.
* **Stage 2 (Deep Scan Fallback):** If `jpeginfo` passes, the file is handed to the `PillowDeepScanDetector`. This loads the file entirely into RAM to check for subtle rendering failures and truncated bytes. 
* *Note:* Video files (Pro) pass through an `ffprobe` frame-drop consensus pipeline.

### 2. Configuring Local Snapshot Remediation
Kintsugi-DAM's free tier can automatically heal your library using your OS-level snapshots.
1. Ensure your host machine is actively taking snapshots (e.g., via `sanoid` for ZFS).
2. In the Kintsugi Settings UI, set your snapshot directory suffix (e.g., `.zfs/snapshot` or `.snapshots`).
3. When Kintsugi finds a corrupted file, it will reverse-traverse the hidden snapshot folders, comparing `mtime` (Modification Time) to find the most recent healthy version of the file, and gracefully copy it over the corrupted version.

### 3. The "Toaster Philosophy"
We know homelabs. We know you are running 40 other Docker containers on an old Intel CPU. 
Kintsugi utilizes strict `asyncio.Semaphore` limits (defaulting to 4 concurrent heavy processes). This prevents the deep-scan algorithms from eating your RAM and crashing your host OS. You can adjust this limit in the `System Settings` tab if you are running on enterprise hardware.

---

### 4. Advanced: The Kintsugi AI Protocol
*(Available in Kintsugi Pro & Studio)*

When local snapshots are unavailable and cloud backups have already been overwritten with corrupted data, Kintsugi Pro utilizes the **AI Repair Protocol**.

Instead of a generic AI "guess," Kintsugi uses localized context to rebuild the photo cleanly. To do this, it requires a "Reference Image."

#### Reference Image Selection Guidelines (The Penalty Matrix)
When Kintsugi attempts to automatically select a reference image to send to the AI, it uses an EXIF-based penalty scoring system. It scans surrounding photos in the directory and applies penalties:
* **Timestamp Penalty:** +10 points for every hour of difference between the corrupted photo and the reference photo.
* **Location Penalty:** +50 points if the GPS coordinates differ by more than 100 meters.
* **Device Penalty:** +100 points if the `Make/Model` EXIF data does not match.

*Selection Rule:* The system chooses the photo with the lowest penalty score. If the lowest score exceeds 200 points, Kintsugi aborts the auto-repair and sends the photo to the Triage Dashboard, asking the user to manually upload a reference file.

#### The Computational Post-Process
Once the Cloud AI (Nano Banana) returns the repaired image, Kintsugi runs a local algorithmic de-blur and sharpening routine. This strips away the "plastic AI feel" and restores natural photographic grain.

---

### 5. Security: The Serverless Cloud Gateway
*(Architecture Note for Security Auditors)*

If you are using Cloud Credits to repair photos, you may wonder how your credits are secured. 
Kintsugi-DAM **never** allows the local Docker binary to communicate directly with AI providers (like Google or Nano Banana). Doing so would risk API key extraction.

Instead, your local instance securely communicates with the **Kintsugi Serverless Gateway** (built on Cloudflare Workers). 
1. Your app sends the image and your License Key to the Gateway.
2. The Gateway verifies your Pro/Studio tier and deducts the credit.
3. The Gateway handles the upstream API communication securely. 

This guarantees zero-trust security and prevents Pi-hole network spoofing.
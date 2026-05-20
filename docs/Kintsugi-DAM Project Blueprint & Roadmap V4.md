# **Kintsugi-DAM Project Blueprint & Roadmap**

This document serves as the master blueprint and progress tracker for Kintsugi-DAM. It outlines the core architecture, tracks development milestones, and strictly delineates Free vs. Pro features to ensure the open-source repository remains pure. It also acts as the master backlog to capture feature ideas and prevent scope creep during active sprints.

## **1\. Executive Summary**

Kintsugi-DAM is a bespoke, self-hosted Digital Asset Management (DAM) integrity scanner. It is designed to identify, quarantine, and remediate "silent" ingest corruption (bit-rot, truncated files, gray-band artifacts) across massive media libraries.

Instead of blindly deleting files or requiring dangerous host-level privileges, it uses a multi-engine consensus scoring system to flag corruption with near-zero false positives. It then utilizes natively exposed, read-only local snapshots or targeted cloud backups to securely and automatically restore clean versions of corrupted files without interrupting the live environment.

## **2\. Current Status (As of Phase 12\)**

* **Core Application:** The core infrastructure is highly mature. The application has transitioned from a theoretical router to a functional scanner armed with real Python forensic tools.  
* **Backend:** Python/FastAPI pipeline is stable. SQLite (WAL mode) state management, dynamic setup wizards, and AST-validated plugin sandboxing are fully operational.  
* **Detection Engines:** jpeginfo (fast scan) and Pillow (deep scan) are wired and functioning safely within asyncio.Semaphore limits.  
* **Deployment:** Secure, multi-stage, single-container Docker monolith with strict Unraid runner permissions.

## **3\. Feature List & Licensing Strategy**

### **License Structure**

* **For the Pro Tier ($20): Lifetime License \+ 1 Year of Updates.** "Your $20 purchase grants you a perpetual, lifetime license to Kintsugi Pro. The software is yours forever and will never be disabled. This includes one full year of major feature updates and new remediation engines. After 12 months, you can continue using your current version forever, or purchase an optional 'Maintenance Pass' at a discount to access the newest features."  
* **For the Studio Tier ($100/yr): Active Subscription.** "Billed annually. Includes all Pro features, plus Priority Support, Enterprise SSO/RBAC, and day-one access to the newest SOTA AI repair models. Active subscriptions receive all updates continuously."

### **Feature Breakdown**

This section strictly tracks which features belong in the public open-source repository versus the private Pro repository.

| Feature | Tier | Description | Status |
| :---- | :---- | :---- | :---- |
| Basic Hashing & Fast Scanners | Free (Open-Source) | SHA-256 hashing, jpeginfo, and Pillow consensus engine. | Completed |
| Local Snapshot Remediation | Free (Open-Source) | Auto-restoration using natively exposed hidden directories (ZFS, BTRFS). | Complete |
| Dashboard & Glass UI Theme | Free (Open-Source) | Modern glassmorphism landing page with live system stats and routing. | Complete |
| Single Directory Monitoring | Free (Open-Source) | Configuration to monitor one root /media path. | Complete |
| Active Watch Directory (Hot Folder) | Free (Open-Source) | Real-time folder monitoring via watchdog. Instantly scans new files upon arrival. | Complete |
| Multi-Directory Monitoring | Pro ($20 Lifetime) | Monitor unlimited custom paths and network shares with per-folder rules. | Planned Backlog |
| User Authentication & Setup | Core System | Local accounts with setup wizard and OIDC support. | Complete |
| In-App File Browser | Pro ($20 Lifetime) | Live filesystem browser to manually target specific folders/files for scanning. | Planned Backlog |
| Cloud Backend Remediation | Pro ($20 Lifetime) | S3-compatible (AWS, Backblaze, Storj) targeted single-file downloads. | Planned Backlog |
| Video File Scanning | Pro ($20 Lifetime) | ffprobe integration to parse and validate massive video libraries. | Planned Backlog |
| Cloud AI Repair Gateway | Cloud Pass (Credits) | Paywall-gated API endpoint allowing users to spend credits to utilize remote AI reconstruction. | Completed |
| Dynamic Plugin Architecture | Core System | Decouples plugins from the core Docker image. | Planned Backlog |

## **4\. Development Roadmap & Progress**

### **Phase 1-10: Core Foundation & Detection \[COMPLETED\]**

* Built FastAPI backend, Docker deployment, and monetization hooks.  
* Implemented Triage Gallery, Settings UI, and wired the local detection plugins (JpegInfo/Pillow).

### **Phase 11: UI Polish, State Persistence & Auth \[COMPLETED\]**

* **Theme & Routing:** Upgrade to "Glassmorphism" UI. Create a dedicated Dashboard landing page distinct from the Triage Gallery.  
* **Real Data Wiring:** Replace all fake UI numbers (Cloud Credits, DB Stats) with live backend API fetches.  
* **Phase 11.5 (Triage Engine):** Local snapshot remediation and triage retention system (90-day prune job).  
* **Phase 11.8 (Hot Folder):** Real-time directory monitoring via watchdog library.  
* **Phase 11.9 (Auth Hardening & Setup Wizard):** First-time setup flow, system status check, and proxy routing.

### **Phase 12: Codebase Audit & Hardening \[CURRENT SPRINT\]**

* **Critical Bug Hunt:** Database table initialization, dependency syncing (passlib, bcrypt).  
* **Security Audit:** Global exception handlers, JWT security, CORS policies.  
* **Performance Optimization:** SQLite WAL mode async engine configurations to prevent locking during scans.

### **Phase 13: Advanced Pro Features & Integrations \[NEXT SPRINT\]**

* **License Management:** Lemon Squeezy API activation logic and dynamic unlocking.  
* Live In-App File Browser for manual scans.  
* Implement S3 Cloud Remediation and Video scanning (ffprobe).  
* **Dynamic Plugin Store:** In-app marketplace to download official Pro extensions securely into /data/plugins.

### **Phase 14: Resource Management & QoS \[PLANNED BACKLOG\]**

* **Adaptive I/O Yielding (QoS):** Utilize the psutil library to actively monitor the host server's CPU and I/O wait times. If utilization spikes (e.g., user starts a Plex stream or scrubs video), the Kintsugi scanning engine will temporarily yield (asyncio.sleep) to act as a seamless background appliance.  
* **Dynamic Concurrency (Worker Limits):** Enforce hardware safety by linking the scan semaphore size to the license tier (Free \= 1 Worker, Pro \= Up to 4 Workers, Studio \= Unlimited Workers).  
* **Scan Intensity UI:** Replace arbitrary "worker" terminology with clear modes for the user: Eco Mode, Balanced, Turbo, and Unrestricted.

## **5\. The Aegis Cloud & Kintsugi V2 Roadmap**

To ensure a zero-cost infrastructure during startup, the Kintsugi API Gateway will be deployed on Cloudflare Workers. It will securely proxy AI repair requests to upstream providers (Nano Banana) after verifying Lemon Squeezy credit balances.

### **Kintsugi Universal Desktop (Q3 2024\)**

* Migrate to an Electron \+ PyInstaller wrapper to offer standalone .exe and .app installers.  
* Implement system-native file pickers and external drive "hot-plug" scanning for photographers.

### **The Aegis Cloud & Studio (2025)**

* Multi-user RBAC, advanced S3/B2 Cloud Remediation, and fully-featured enterprise integrations.

| Feature | Kintsugi Free | Kintsugi Pro ($20/seat) | Kintsugi Studio ($100/yr) |
| :---- | :---- | :---- | :---- |
| Core Detection | Images (jpeginfo) | Images \+ Video (ffprobe) | Images \+ Video \+ SOTA |
| Monitored Paths | 1 Local Path | Unlimited (Local/SMB/NFS) | Unlimited \+ Team Seats |
| Local Remediation | Manual Snapshots | Auto-Pilot Snapshots | Auto-Pilot \+ Priority |
| AI Healing | ❌ | Local & Cloud AI Repair | Latest SOTA Models |
| Cloud Restore | ❌ | S3 / Backblaze B2 | Enterprise Cloud Connect |
| Security | Local Auth | Local Auth | SSO (SAML / RBAC) |
| License Type | Personal | Personal (Lifetime Updates\*) | Commercial / Agency |

*\*Lifetime updates apply to the current major version (V1). Future major version upgrades (V2) may require a discounted upgrade fee to support continued development.*
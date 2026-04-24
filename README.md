# 🏺 Kintsugi-DAM
**The Self-Healing Digital Asset Management Integrity Scanner.**

[![Docker Pulls](https://img.shields.io/badge/docker-ready-blue.svg)](#) [![License](https://img.shields.io/badge/license-Open%20Core-green.svg)](#)

Hard drives fail. But worse than a hard drive failing is a hard drive *silently* corrupting your data over years without you knowing. "Bit-rot," truncated network transfers, and failing sectors can destroy your massive media library, and standard backup software will happily sync that corrupted data to your cloud provider, overwriting your good backups.

**Kintsugi-DAM** is a bespoke, self-hosted integrity scanner built to hunt down silent ingest corruption, quarantine it, and automatically restore clean versions from local snapshots—without interrupting your live environment.

## 🚀 The Kintsugi Philosophy
* **Zero False Positives:** We don't blindly delete files. Kintsugi uses a multi-engine consensus system (fast boundary scans via `jpeginfo` + deep RAM verification via `Pillow`) to prove a file is broken.
* **The "Toaster" Philosophy:** Built for low-end homelab servers. Hardware-optimized concurrency limits ensure scanning a 4TB library won't lock up your CPU or RAM.
* **Seamless Remediation:** Natively reads your hidden snapshot directories (ZFS `.zfs/snapshot` or BTRFS `.snapshots`) to find the exact historical moment before the corruption occurred and surgical restores it.

## ⚡ Quick Start

Kintsugi-DAM is deployed as a secure, single-container monolith. We recommend using Docker Compose.

```yaml
version: '3.8'
services:
  kintsugi-dam:
    image: ghcr.io/yourusername/kintsugi-dam:latest
    container_name: kintsugi
    restart: unless-stopped
    ports:
      - "3000:3000" # Web UI
    volumes:
      # We now require rw so Kintsugi can swap the corrupted file for the clean one
      - /mnt/user/media:/media:rw          
      # Explicit read-only mount for the snapshot directory (prevents path mapping hell)
      - /mnt/user/media/.zfs/snapshot:/snapshots:ro 
      # Kintsugi's isolated internal storage (It owns everything in here)
      - ./kintsugi_data:/app/data
    environment:
      - TZ=America/New_York
      
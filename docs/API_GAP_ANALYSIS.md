# Frontend & UI API Gap Analysis

This report identifies missing API capabilities and architectural bottlenecks in the Kintsugi-DAM backend that will prevent or degrade the Next.js frontend experience. These must be patched prior to UI development.

## 1. Triage Endpoints (CRITICAL)

### Missing Pagination, Sorting, and Filtering
- **Current State:** `GET /api/triage/` executes a raw `select(TriageEntry)` and returns an unpaginated array of all records.
- **Impact:** A DAM can hold hundreds of thousands of files. If thousands are corrupted over a network failure, returning a monolithic JSON array will crash the Next.js browser state and overwhelm the backend memory.
- **Resolution Required:**
  - Implement `limit` and `offset` (or cursor-based) pagination.
  - Implement sorting (e.g., `?sort=created_at&order=desc`).
  - Implement filtering by state (e.g., `?status=QUARANTINED` vs `?status=PENDING_APPROVAL`).

### Missing Bulk Actions
- **Current State:** `POST /api/triage/{id}/action` processes a single triage item.
- **Impact:** Approving or restoring 50 files requires the UI to fire 50 individual, blocking HTTP requests, resulting in poor UX and potential race conditions.
- **Resolution Required:** Implement a `POST /api/triage/bulk-action` endpoint that accepts an array of IDs.

## 2. KVS Settings & Schema Introspection (CRITICAL)

### Missing KVS Schema Endpoint
- **Current State:** `GET /api/settings/` returns a dictionary mapping strings to strings/booleans based on what is currently stored in the database.
- **Impact:** The UI is "blind." It cannot dynamically build a settings form because it does not know the *schema* (e.g., what keys actually exist, their expected types, validation constraints, or default values).
- **Resolution Required:** Create `GET /api/settings/schema` to return a predefined dictionary or Pydantic schema detailing all configurable keys in the system.

## 3. Dashboard Metrics (/stats) (HIGH PRIORITY)

### Incomplete Payload
The current `GET /stats` endpoint does not provide a holistic view of the system for a unified dashboard.
- **Current State Returns:** Total files, corrupted files, quarantined files (mapped strictly to `PENDING_APPROVAL`), last scan time, cloud credits, scanner state, and watcher active state.
- **Impact:** The Next.js frontend would be forced to make separate queries or remain ignorant of critical system states.
- **Missing Data Required:**
  1. **Active Fleet Node Count:** To show the health of the edge network.
  2. **Distinct `QUARANTINED` vs `PENDING_APPROVAL` Count:** `total_quarantined` currently only counts files in the `pending_approval` state. We need a count of physically quarantined (`corrupted`/in triage) files as well.
  3. **Rust Worker Pool Queue Depth:** To show progress bars on heavy ingestion tasks.

## 4. Real-time Event Bus (Nexus) Integration

### Missing SSE / WebSocket Bridge
- **Current State:** The backend utilizes `nexus_bus.broadcast()` internally (e.g., firing `event:triage:manual_resolved`).
- **Impact:** The Next.js UI has no way to subscribe to these events. It would be forced to use aggressive, resource-heavy HTTP polling to update the interface when a background scan finds a corrupted file or an AI repair finishes.
- **Resolution Required:** Expose a Server-Sent Events (SSE) or WebSocket endpoint (`/api/events/stream`) that bridges the internal Nexus bus to authenticated clients.

## 5. Other Observations
- **Fleet Endpoints:** `/api/fleet/register` handles token verification securely, but there is no endpoint exposed to list all registered fleet nodes, their statuses, or last-seen timestamps to the frontend. `GET /api/fleet/nodes` must be created.

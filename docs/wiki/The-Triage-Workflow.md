# The Triage Workflow

Kintsugi-DAM is built around the concept of safely processing corrupted, missing, or problematic media assets. This is managed entirely through the Triage Workflow.

## The State Lifecycle

1. **QUARANTINED**
   When a file is flagged as corrupted or failing integrity checks, Kintsugi-DAM moves the physical file to a dedicated Recycle Bin / Triage directory. In the original directory, Kintsugi-DAM leaves behind a physical placeholder file named `[original_filename].kintsugi-quarantined.txt`.

2. **PENDING_APPROVAL**
   Some files may be remediated automatically by Kintsugi-DAM (e.g., extracting from a snapshot, using AI repair, or pulling from Kintsugi Cloud). If the system settings dictate manual review is required (e.g., `auto_restore` is false), the remediated replacement is staged in Kintsugi, and the triage entry is placed in the `PENDING_APPROVAL` state. The original file remains quarantined until an administrator manually approves the fix.

3. **APPROVED**
   Once a user reviews and approves the replacement asset via the WebUI, the backend performs the following:
   - Copies the newly uploaded or staged file over the original path.
   - Deletes the `.kintsugi-quarantined.txt` placeholder.
   - Marks the asset state as "healthy" in the database.
   - Changes the Triage entry status to `APPROVED`.
   - Broadcasts the `event:triage:manual_resolved` event to the Nexus Event Bus so plugins and the UI can react.

## The Time-To-Live (TTL) Grace Period
When an asset fix is `APPROVED`, the database entry tracking the quarantine is not immediately destroyed. Instead, the system assigns an expiration date (TTL) based on the `approved_retention_days` setting in the KVS (defaulting to 30 days if not set).

This serves as a safety net ensuring an audit trail remains available, and physically quarantined files in the recycle bin are purged gracefully rather than instantly.

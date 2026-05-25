# Settings Reference (KVS)

Kintsugi-DAM relies on a robust Key-Value Store (KVS) mapping directly to the `SystemSettings` database table to manage runtime configurations. Below is a comprehensive list of known keys actively queried or mutated by the backend.

### System & Paths
- **`is_setup_complete`** *(boolean)*: Determines if initial configuration has been executed. Prevents further unrestricted local registration.
- **`monitored_directory`** *(string)*: The root path (default: `/media`) that the Watchdog daemon observes for new or changed files.
- **`triage_directory`** *(string)*: The "Recycle Bin" where corrupted files are moved.
- **`snapshot_mount_path`** *(string)*: Path to read-only snapshot directories utilized for automatic restorations.

### Scanning & Worker Pools
- **`max_workers`** *(integer)*: Controls background scanning threads.
- **`scan_intensity`** *(string)*: Can be used to govern CPU profiling/QoS for local AI processing.

### Maintenance & Lifecycle
- **`maintenance_start`** *(string)*: Start time for background maintenance.
- **`maintenance_end`** *(string)*: End time for background maintenance.
- **`retention_days`** *(integer)*: Global log or generalized file retention limit.
- **`approved_retention_days`** *(integer)*: The TTL (Time-To-Live) for files sitting in `APPROVED` triage status (Default: 30) before permanent deletion.

### Remediation Policy
- **`auto_restore`** *(boolean)*: If true, enables replacing files automatically without manual approval in the Triage queue.
- **`auto_restore_cloud`** *(boolean)*: Enables pulling replacements securely from a trusted Kintsugi Cloud pipeline.
- **`auto_restore_ai`** *(boolean)*: Enables autonomous AI repair attempts for broken images/media.
- **`ai_use_kintsugi_cloud`** *(boolean)*: Dictates if AI repair uses local hardware or sends payloads securely to Kintsugi Cloud.
- **`cloud_credits`** *(integer)*: Tracks available credits for executing Cloud-based AI repairs.

### Webhooks & Notifications
- **`discord_webhook_url`** *(string)*: Triggers alerts for system failures or quarantine events to Discord.
- **`ntfy_topic_url`** *(string)*: Triggers push notifications via Ntfy.sh.

### Fleet Management
- **`fleet_registration_token`** *(string)*: The secret token required to enroll a new Edge/Fleet Node via the `/api/fleet/register` endpoint.

### OIDC (OpenID Connect)
- **`oidc_client_id`** *(string)*: The OAuth2 Client ID from your IdP.
- **`oidc_client_secret`** *(string)*: The OAuth2 Client Secret.
- **`oidc_discovery_url`** (or **`oidc_auth_url`**) *(string)*: The IdP's metadata endpoint for auto-configuration.

### SAML 2.0 (Requires Pro/Studio Tier)
- **`saml_idp_entity_id`** *(string)*: Your IdP's unique identifier.
- **`saml_idp_sso_url`** *(string)*: Your IdP's SSO target endpoint.
- **`saml_idp_x509_cert`** *(string)*: Base64/PEM certificate string for your IdP.
- **`saml_sp_entity_id`** *(string)*: The Service Provider Entity ID assigned to Kintsugi.

### Licensing
- **`license_tier`** *(string)*: Displays the tier of the application (e.g., `free`, `pro`, `studio`). Modifying this usually requires license verification workflows.

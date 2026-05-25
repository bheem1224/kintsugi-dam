# Authentication and SSO in Kintsugi-DAM

Kintsugi-DAM supports multiple layers of authentication, ranging from standard local JWT-based login to enterprise Single Sign-On (SSO) via OIDC and SAML 2.0.

## Standard JWT Authentication
The backend utilizes standard FastAPI OAuth2 Password Bearer authentication with JWT (`PyJWT`).
- Passwords are encrypted securely using `passlib[bcrypt]`.
- First-time setup allows creating an administrator account. Once initial setup is completed, self-registration is disabled.
- In-memory fallback secrets are automatically generated at startup to prevent container crashes if a JWT secret key isn't provided.

## OIDC (OpenID Connect)
OIDC integration allows users to log in securely using an external Identity Provider (IdP) (e.g., Google, Okta, Keycloak).

**Configuration Requirements:**
To enable OIDC, the following System Settings (KVS) must be populated:
- `oidc_client_id`: The Client ID assigned by your IdP.
- `oidc_client_secret`: The Secret assigned by your IdP.
- `oidc_discovery_url` (or `oidc_auth_url`): The standard OIDC discovery document URL from your IdP.

*Friction Point:* Currently, modifying these parameters requires updating the Key-Value Store (KVS) directly (or via the backend settings API) and is not fully abstracted in the UI.

**Registration Behavior:**
If a user authenticates via OIDC but does not have a local Kintsugi account, access is denied unless self-registration via OIDC is explicitly permitted by having an empty system (first user login).

## SAML 2.0 Integration
Kintsugi-DAM supports robust enterprise SSO using SAML 2.0.

**Important License Requirement:**
SAML SSO strictly requires a **Pro or Studio License Tier**. Attempting to initiate SAML endpoints on the "free" tier will return a `403 Forbidden` error.

**Configuration Requirements:**
To enable SAML, populate these KVS values:
- `saml_idp_entity_id`: The Entity ID provided by your SAML IdP.
- `saml_idp_sso_url`: The Single Sign-On service URL.
- `saml_idp_x509_cert`: The public certificate used to sign SAML assertions.
- `saml_sp_entity_id`: The Entity ID of your Kintsugi-DAM instance.

Similar to OIDC, configuring SAML currently requires setting these fields inside the backend KVS.

## API Keys & Webhooks
External webhook integrations (e.g., authorizing external triage commands) authenticate using a robust API Key system, mapped to an `ApiKey` database model.
- API keys utilize `passlib[bcrypt]` for key hashing and are verified via Bearer tokens.
- This system operates entirely distinct from the main application's JWT session-based auth.

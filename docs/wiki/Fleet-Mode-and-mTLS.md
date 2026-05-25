# Fleet Mode & mTLS

Kintsugi-DAM supports scaling via "Fleet Nodes"—edge devices or satellite servers that can ingest, process, or chunk assets and transmit them securely back to the core application. Security is managed via Mutual TLS (mTLS).

## Node Registration
When a Fleet Node registers, it sends a CSR (Certificate Signing Request) and a registration token to the core backend.
- The token must match the `fleet_registration_token` value stored in the KVS.
- The Kintsugi Core operates its own internal Root CA (Certificate Authority). If one does not exist, the core automatically generates an RSA-4096 private key and self-signed certificate upon the first node registration.
- The backend signs the CSR, creating a Client Certificate valid for 1 year, and returns it alongside the CA certificate.

**Rate Limiting & Banning:**
To prevent brute-forcing registration tokens, the endpoint strictly enforces an in-memory rate limit per IP. Failing 5 times within 15 minutes results in a 24-hour IP ban.

## Securing API Endpoints via Proxy Headers
In production deployments, the Kintsugi Core is typically positioned behind a reverse proxy. Because the FastAPI process cannot natively terminate client mTLS if behind a standard proxy, the proxy must verify the client certificate against the Kintsugi CA and forward the details to the backend via headers.

The backend accepts the following mTLS verification headers:
- `x-ssl-client-sha1`: A standard hex fingerprint of the client certificate.
- `cf-client-cert-der-base64`: A base64-encoded DER representation used by Cloudflare Tunnel Authenticated Origin Pulls.

### Example: NGINX Configuration
To pass client certificates securely through Nginx Proxy Manager or raw Nginx:

```nginx
server {
    listen 443 ssl;
    server_name core.yourdomain.com;

    ssl_certificate /path/to/server/cert.pem;
    ssl_certificate_key /path/to/server/key.pem;

    # Require client certificate verification against the Kintsugi Core CA
    ssl_client_certificate /path/to/kintsugi/core/ca.crt;
    ssl_verify_client optional; # Or 'on'

    location / {
        proxy_pass http://kintsugi-backend:8000;

        # Forward certificate details to the FastAPI backend
        proxy_set_header X-SSL-Client-Cert $ssl_client_escaped_cert;
        proxy_set_header X-SSL-Client-SHA1 $ssl_client_fingerprint;
        proxy_set_header X-SSL-Client-Verify $ssl_client_verify;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Example: Caddy Configuration
```caddyfile
core.yourdomain.com {
    tls {
        client_auth {
            mode request
            trusted_ca_certs /path/to/kintsugi/core/ca.crt
        }
    }

    reverse_proxy kintsugi-backend:8000 {
        header_up X-SSL-Client-SHA1 {tls_client_fingerprint}
        header_up X-SSL-Client-Verify {tls_client_auth_status}
    }
}
```

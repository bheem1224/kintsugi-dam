from fastapi import Request
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from urllib.parse import urlparse

def get_saml_settings(kvs: dict, request: Request):
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    
    return {
        "strict": True,
        "debug": False,
        "sp": {
            "entityId": kvs.get("saml_sp_entity_id", f"{base_url}/api/auth/saml/metadata"),
            "assertionConsumerService": {
                "url": f"{base_url}/api/auth/saml/acs",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
            },
            "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
        },
        "idp": {
            "entityId": kvs.get("saml_idp_entity_id", ""),
            "singleSignOnService": {
                "url": kvs.get("saml_idp_sso_url", ""),
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
            },
            "x509cert": kvs.get("saml_idp_x509_cert", "")
        }
    }

async def prepare_fastapi_request(request: Request) -> dict:
    form_data = await request.form() if request.method == "POST" else {}
    
    return {
        "https": "on" if request.url.scheme == "https" else "off",
        "http_host": request.url.netloc,
        "server_port": request.url.port,
        "script_name": request.url.path,
        "get_data": dict(request.query_params),
        "post_data": dict(form_data),
        "lowercase_urlencoding": False
    }

async def init_saml_auth(request: Request, kvs: dict) -> OneLogin_Saml2_Auth:
    req = await prepare_fastapi_request(request)
    settings = get_saml_settings(kvs, request)
    auth = OneLogin_Saml2_Auth(req, settings)
    return auth

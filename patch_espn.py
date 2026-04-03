"""
Patches espn-api's requests module to use a proxy before the app starts.
Import this at the very top of main.py before anything else.
"""
import os
import requests
import importlib

def apply_proxy_patch():
    host = os.getenv("PROXY_HOST")
    port = os.getenv("PROXY_PORT")
    user = os.getenv("PROXY_USER")
    pwd  = os.getenv("PROXY_PASS")

    if not all([host, port, user, pwd]):
        return

    proxy_url = f"http://{user}:{pwd}@{host}:{port}"
    proxies = {"http": proxy_url, "https": proxy_url}

    # Import espn_api's requests module and patch its requests.get directly
    try:
        import espn_api.requests.espn_requests as espn_req
        import espn_api.requests.espn_requests as mod

        original_get = mod.requests.get

        def patched_get(url, **kwargs):
            kwargs.setdefault("proxies", proxies)
            return original_get(url, **kwargs)

        mod.requests.get = patched_get
        print(f"ESPN proxy patch applied: {host}:{port}")
    except Exception as e:
        print(f"ESPN proxy patch failed: {e}")

apply_proxy_patch()
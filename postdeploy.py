#!/usr/bin/env python3
""" Script that adds the MuckRock review app redirect URI to the
    MuckRock staging client on Squarelet staging
"""

#!/usr/bin/env python3
import os
import sys
import requests

SQUARELET_URL = os.environ["SQUARELET_URL"]
CLIENT_ID = 1  # Add redirect URIs to MuckRock client
REVIEW_APP_URL = (
    f"https://{os.environ['HEROKU_APP_NAME']}"
    ".herokuapp.com/accounts/complete/squarelet"
)
GITHUB_CLIENT = os.environ["GITHUB_ACTIONS_CLIENT"]
GITHUB_SECRET = os.environ["GITHUB_ACTIONS_SECRET"]
os.environ["https_proxy"] = os.environ["FIXIE_URL"]

def get_access_token():
    """Fetch an access token using client_credentials grant"""
    token_url = f"{SQUARELET_URL}/openid/token"
    data = {"grant_type": "client_credentials"}
    resp = requests.post(token_url, auth=(GITHUB_CLIENT, GITHUB_SECRET), data=data, timeout=20)
    resp.raise_for_status()
    return resp.json()["access_token"]

def patch_redirect_uri(client_id, redirect_uri, cmd_action):
    """PATCH the client redirect URIs on squarelet staging"""
    if cmd_action not in ("add", "remove"):
        raise ValueError("Action must be 'add' or 'remove'")

    access_token = get_access_token()
    endpoint = f"{SQUARELET_URL}/api/clients/{client_id}/redirect_uris/"
    payload = {
        "action": cmd_action,
        "redirect_uris": [redirect_uri],
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    resp = requests.patch(endpoint, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    print(f"Successfully {cmd_action}ed redirect URI: {redirect_uri}")
    print(resp.json())

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./script.py <add|remove>")
        sys.exit(1)

    action = sys.argv[1].lower()
    patch_redirect_uri(CLIENT_ID, REVIEW_APP_URL, action)

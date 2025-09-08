#!/usr/bin/env python3


#!/usr/bin/env python3
import os
import requests

SQUARELET_URL = os.environ["SQUARELET_URL"]
CLIENT_ID = 1  # Add redirect URIs to MuckRock client
REVIEW_APP_URL = f"https://{os.environ['HEROKU_APP_NAME']}.herokuapp.com/"
GITHUB_CLIENT = os.environ["GITHUB_ACTIONS_CLIENT"]
GITHUB_SECRET = os.environ["GITHUB_ACTIONS_SECRET"]

def get_access_token():
    """Fetch an access token using client_credentials grant"""
    token_url = f"{SQUARELET_URL}/openid/token"
    data = {"grant_type": "client_credentials"}
    resp = requests.post(token_url, auth=(GITHUB_CLIENT, GITHUB_SECRET), data=data)
    resp.raise_for_status()
    return resp.json()["access_token"]

def patch_redirect_uri(client_id, redirect_uri):
    """PATCH the client redirect URIs on squarelet staging"""
    access_token = get_access_token()
    endpoint = f"{SQUARELET_URL}/api/clients/{client_id}/redirect_uris/"
    payload = {
        "action": "add",
        "redirect_uris": [redirect_uri],
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    resp = requests.patch(endpoint, json=payload, headers=headers)
    resp.raise_for_status()
    print(f"Successfully added redirect URI: {redirect_uri}")
    print(resp.json())

if __name__ == "__main__":
    patch_redirect_uri(CLIENT_ID, REVIEW_APP_URL)

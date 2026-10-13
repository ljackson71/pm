"""Minimal Fabric REST helper using the az CLI token. All calls carry the skill telemetry header.
Workspace and lakehouse are looked up by name (override with FABRIC_WORKSPACE / FABRIC_LAKEHOUSE)."""
import json
import os
import subprocess
import time
import urllib.error
import urllib.request

API = "https://api.fabric.microsoft.com/v1"
WS_NAME = os.environ.get("FABRIC_WORKSPACE", "LarryJ_DEV")
LH_NAME = os.environ.get("FABRIC_LAKEHOUSE", "nyctaxi_lakehouse")


def az_token(resource):
    return subprocess.run(f"az account get-access-token --resource {resource} --query accessToken -o tsv",
                          shell=True, capture_output=True, text=True, check=True).stdout.strip()


_token = az_token("https://api.fabric.microsoft.com")


def call(method, url, body=None):
    if not url.startswith("http"):
        url = API + url
    data = json.dumps(body).encode() if body is not None else (b"{}" if method == "POST" else None)
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {_token}", "Content-Type": "application/json",
        "x-ms-fabric-skill": "e2e-medallion-architecture"})
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return r.status, dict(r.headers), (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {url} -> {e.code}: {e.read().decode()}") from None


def lro(method, url, body=None):
    """Run a call; if it returns 202, poll its operation until it finishes. Returns the final payload."""
    status, headers, payload = call(method, url, body)
    if status != 202:
        return payload
    loc = headers.get("Location")
    while True:
        time.sleep(int(headers.get("Retry-After", 5)))
        _, headers, op = call("GET", loc)
        if op["status"] in ("Succeeded", "Failed"):
            if op["status"] == "Failed":
                raise RuntimeError(f"LRO failed: {op}")
            try:
                return call("GET", loc + "/result")[2]
            except RuntimeError:
                return op


WS = next(w["id"] for w in call("GET", "/workspaces")[2]["value"] if w["displayName"] == WS_NAME)


def items(item_type):
    return call("GET", f"/workspaces/{WS}/items?type={item_type}")[2]["value"]


LH_ID = next(i["id"] for i in items("Lakehouse") if i["displayName"] == LH_NAME)

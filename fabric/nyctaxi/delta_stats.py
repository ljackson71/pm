"""Row count and schema of lakehouse Delta tables, read from the _delta_log via OneLake.
Usage: python delta_stats.py schema.table [...]  (add --schema to print columns)"""
import json
import sys
import urllib.request

import fabric

BASE = f"https://onelake.dfs.fabric.microsoft.com/{fabric.WS}"
TOKEN = fabric.az_token("https://storage.azure.com")


def get(url):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}", "x-ms-version": "2021-06-08"})
    with urllib.request.urlopen(req) as r:
        return r.read().decode()


def table_state(table):
    schema, name = table.split(".")
    log_dir = f"{fabric.LH_ID}/Tables/{schema}/{name}/_delta_log"
    paths = json.loads(get(f"{BASE}?resource=filesystem&recursive=false&directory={log_dir}"))["paths"]
    commits = sorted(p["name"] for p in paths if p["name"].endswith(".json"))
    files, meta = {}, None
    for c in commits:
        for line in get(f"{BASE}/{c}").splitlines():
            action = json.loads(line)
            if "add" in action:
                files[action["add"]["path"]] = json.loads(action["add"].get("stats") or "{}").get("numRecords", 0)
            elif "remove" in action:
                files.pop(action["remove"]["path"], None)
            elif "metaData" in action:
                meta = action["metaData"]
    return sum(files.values()), json.loads(meta["schemaString"])["fields"], meta.get("partitionColumns", [])


if __name__ == "__main__":
    for t in [a for a in sys.argv[1:] if not a.startswith("--")]:
        rows, fields, parts = table_state(t)
        print(f"{t}: {rows:,} rows, {len(fields)} columns, partitioned by {parts or 'none'}")
        if "--schema" in sys.argv:
            for f in fields:
                print(f"    {f['name']}: {f['type']}")

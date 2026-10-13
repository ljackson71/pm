"""Download NYC TLC yellow trip files (and the zone lookup) and upload them to the lakehouse landing folder.
Usage: python upload_landing.py 2024-01 [2024-02 ...]"""
import sys
import urllib.request

import fabric

TLC = "https://d37ci6vzurychx.cloudfront.net"
ONELAKE = f"https://onelake.dfs.fabric.microsoft.com/{fabric.WS}/{fabric.LH_ID}"
HEADERS = {"Authorization": f"Bearer {fabric.az_token('https://storage.azure.com')}", "x-ms-version": "2021-06-08"}


def put(path, data):
    for method, query, body in [("PUT", "resource=file", b""), ("PATCH", "action=append&position=0", data),
                                ("PATCH", f"action=flush&position={len(data)}", b"")]:
        req = urllib.request.Request(f"{ONELAKE}/{path}?{query}", data=body, method=method, headers=HEADERS)
        urllib.request.urlopen(req).close()
    print(f"uploaded {path} ({len(data):,} bytes)")


def download(url):
    with urllib.request.urlopen(url) as r:
        return r.read()


put("Files/landing/nyctaxi/reference/taxi_zone_lookup.csv", download(f"{TLC}/misc/taxi_zone_lookup.csv"))
for month in sys.argv[1:]:
    name = f"yellow_tripdata_{month}.parquet"
    put(f"Files/landing/nyctaxi/yellow/{name}", download(f"{TLC}/trip-data/{name}"))

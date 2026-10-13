"""Run notebooks in order as RunNotebook jobs, waiting for each to finish. Usage: python run_notebook.py nb1 [nb2 ...]"""
import sys
import time

import fabric

ids = {n["displayName"]: n["id"] for n in fabric.items("Notebook")}
config = {"executionData": {"configuration": {
    "defaultLakehouse": {"name": fabric.LH_NAME, "id": fabric.LH_ID, "workspaceId": fabric.WS}}}}

for name in sys.argv[1:]:
    nb = ids[name]
    base = f"/workspaces/{fabric.WS}/items/{nb}/jobs/instances"
    active = [j for j in fabric.call("GET", base)[2]["value"] if j["status"] in ("NotStarted", "InProgress")]
    if active:
        sys.exit(f"{name} already has an active job {active[0]['id']}; not submitting a duplicate")
    _, headers, _ = fabric.call("POST", f"{base}?jobType=RunNotebook", config)
    loc, start = headers["Location"], time.time()
    print(f"{name}: submitted", flush=True)
    while True:
        time.sleep(20)
        job = fabric.call("GET", loc)[2]
        print(f"{name}: {job['status']} ({int(time.time() - start)}s)", flush=True)
        if job["status"] in ("Completed", "Failed", "Cancelled", "Deduped"):
            break
    if job["status"] != "Completed":
        sys.exit(f"{name} {job['status']}: {job.get('failureReason')}")

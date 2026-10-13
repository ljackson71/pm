"""Create pl_nyctaxi_medallion (Bronze -> Silver -> Gold) with a DISABLED daily 2 AM Pacific schedule."""
import base64
import json

import fabric

NAME = "pl_nyctaxi_medallion"
nb = {n["displayName"]: n["id"] for n in fabric.items("Notebook")}


def activity(name, notebook, depends_on=None):
    return {
        "name": name, "type": "TridentNotebook",
        "dependsOn": [{"activity": depends_on, "dependencyConditions": ["Succeeded"]}] if depends_on else [],
        "policy": {"timeout": "0.02:00:00", "retry": 1, "retryIntervalInSeconds": 300,
                   "secureOutput": False, "secureInput": False},
        "typeProperties": {"notebookId": nb[notebook], "workspaceId": fabric.WS},
    }


content = {"properties": {
    "description": "NYC taxi medallion: bronze ingestion, silver cleansing, gold aggregates",
    "activities": [
        activity("Bronze ingest", "nb_bronze_nyctaxi"),
        activity("Silver transform", "nb_silver_nyctaxi", "Bronze ingest"),
        activity("Gold aggregate", "nb_gold_nyctaxi", "Silver transform"),
    ],
}}
definition = {"parts": [{"path": "pipeline-content.json", "payloadType": "InlineBase64",
                         "payload": base64.b64encode(json.dumps(content).encode()).decode()}]}

existing = {p["displayName"]: p["id"] for p in fabric.items("DataPipeline")}
if NAME in existing:
    pid = existing[NAME]
    fabric.lro("POST", f"/workspaces/{fabric.WS}/items/{pid}/updateDefinition", {"definition": definition})
    print(f"updated {NAME} {pid}")
else:
    fabric.lro("POST", f"/workspaces/{fabric.WS}/items",
               {"displayName": NAME, "type": "DataPipeline", "definition": definition})
    pid = {p["displayName"]: p["id"] for p in fabric.items("DataPipeline")}[NAME]
    print(f"created {NAME} {pid}")

sched_url = f"/workspaces/{fabric.WS}/items/{pid}/jobs/Pipeline/schedules"
if not fabric.call("GET", sched_url)[2]["value"]:
    s = fabric.call("POST", sched_url, {"enabled": False, "configuration": {
        "type": "Daily", "interval": 1, "times": ["02:00"], "localTimeZoneId": "Pacific Standard Time",
        "startDateTime": "2026-10-14T02:00:00", "endDateTime": "2027-10-14T02:00:00"}})[2]
    print(f"schedule {s['id']} enabled={s['enabled']}")
print(json.dumps(fabric.call("GET", sched_url)[2]["value"], indent=1))

"""Build .ipynb payloads (bound to nyctaxi_lakehouse) and create or update the three layer notebooks."""
import base64
import json

import fabric
import notebooks

NOTEBOOKS = {
    "nb_bronze_nyctaxi": (notebooks.BRONZE, "Bronze: ingest raw NYC TLC yellow trip files and zone lookup"),
    "nb_silver_nyctaxi": (notebooks.SILVER, "Silver: clean, validate, deduplicate and enrich NYC taxi trips"),
    "nb_gold_nyctaxi": (notebooks.GOLD, "Gold: NYC taxi aggregates for Power BI"),
}


def to_lines(src):
    lines = src.strip("\n").split("\n")
    return [l + "\n" for l in lines[:-1]] + [lines[-1]]


def build_ipynb(source):
    cells = [{"cell_type": "code", "metadata": {}, "source": to_lines(c), "outputs": [], "execution_count": None}
             for c in source.split("# %%")]
    return {
        "nbformat": 4, "nbformat_minor": 5,
        "metadata": {
            "kernel_info": {"name": "synapse_pyspark"},
            "kernelspec": {"name": "synapse_pyspark", "display_name": "Synapse PySpark", "language": "Python"},
            "language_info": {"name": "python"},
            "dependencies": {"lakehouse": {
                "default_lakehouse": fabric.LH_ID,
                "default_lakehouse_name": fabric.LH_NAME,
                "default_lakehouse_workspace_id": fabric.WS}},
        },
        "cells": cells,
    }


def definition(source):
    payload = base64.b64encode(json.dumps(build_ipynb(source)).encode()).decode()
    return {"format": "ipynb", "parts": [
        {"path": "notebook-content.ipynb", "payload": payload, "payloadType": "InlineBase64"}]}


existing = {n["displayName"]: n["id"] for n in fabric.items("Notebook")}
for name, (source, desc) in NOTEBOOKS.items():
    for c in source.split("# %%"):
        compile(c, name, "exec")  # syntax check before upload
    if name in existing:
        fabric.lro("POST", f"/workspaces/{fabric.WS}/notebooks/{existing[name]}/updateDefinition",
                   {"definition": definition(source)})
        print(f"updated {name} {existing[name]}")
    else:
        fabric.lro("POST", f"/workspaces/{fabric.WS}/items",
                   {"displayName": name, "type": "Notebook", "description": desc, "definition": definition(source)})
        print(f"created {name}")

print({n["displayName"]: n["id"] for n in fabric.items("Notebook") if n["displayName"] in NOTEBOOKS})

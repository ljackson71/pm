# NYC Taxi Medallion (Microsoft Fabric)

Bronze, Silver, Gold lakehouse for NYC TLC yellow taxi trips, plus a Direct Lake semantic model and a pipeline.
Runs in the Fabric workspace `LarryJ_DEV`, lakehouse `nyctaxi_lakehouse` (schemas `bronze`, `silver`, `gold`).

Requires `az login` as an account with access to the workspace. Override names with
`FABRIC_WORKSPACE` / `FABRIC_LAKEHOUSE`.

## Layers

| Layer | Tables | What happens |
|---|---|---|
| Bronze | `yellow_trips_raw`, `taxi_zone_lookup_raw` | Raw files as-is plus `source_file`, `ingestion_timestamp`, `batch_id`; already-loaded files are skipped |
| Silver | `yellow_trips`, `taxi_zones` | Typed, snake_case, quality rules, dedup, derived columns, zone names; partitioned by `pickup_date` |
| Gold | `daily_trip_summary`, `hourly_demand`, `pickup_zone_summary`, `payment_type_summary`, `month` | Aggregates; each must reconcile to silver trips and revenue. `month` lets one slicer filter every table |

## Files

- `notebooks.py` - source of the three notebooks (cells split on `# %%`)
- `deploy_notebooks.py` - create or update `nb_bronze_nyctaxi`, `nb_silver_nyctaxi`, `nb_gold_nyctaxi`
- `upload_landing.py` - download TLC months and upload to `Files/landing/nyctaxi/`
- `run_notebook.py` - run notebooks in order and wait for each
- `deploy_model.py` - create or update the Direct Lake model `sm_nyctaxi_gold` from the gold Delta schemas
- `build_report.py` - write the visuals of the one-page report into `report/rpt_nyctaxi.Report` (PBIR)
- `deploy_pipeline.py` - create `pl_nyctaxi_medallion` with a disabled daily 2 AM Pacific schedule
- `delta_stats.py` - row counts and schemas read from the Delta logs
- `sql.py` - run T-SQL against the lakehouse SQL endpoint
- `fabric.py` - shared REST helper

## Load more months

```bash
python upload_landing.py 2024-02 2024-03
python run_notebook.py nb_bronze_nyctaxi nb_silver_nyctaxi nb_gold_nyctaxi
python delta_stats.py silver.yellow_trips gold.daily_trip_summary
```

Then refresh `sm_nyctaxi_gold`. A model refresh right after new tables are created can fail with
"source tables do not exist or access was denied"; retrying a few minutes later worked.

## Report

`report/rpt_nyctaxi.pbip` is bound live to `sm_nyctaxi_gold`. After editing `build_report.py`:

```bash
python build_report.py
powerbi-report-author validate report/rpt_nyctaxi.Report
powerbi-report-author preview report/rpt_nyctaxi.Report --host service --group <workspace-id> --dataset <model-id>
```

Requires `npm install -g @microsoft/powerbi-report-authoring-cli`. Preview never publishes. `.pbi/` holds the
preview browser profile and is git-ignored.

"""Create/update the Direct Lake semantic model sm_nyctaxi_gold over the gold schema.
Column types come from the actual Delta schemas so the model always matches the tables."""
import base64
import json
import uuid

import fabric
from delta_stats import table_state

NAME = "sm_nyctaxi_gold"
EXPR = "DirectLake - nyctaxi_lakehouse"
TYPES = {"string": "string", "long": "int64", "integer": "int64", "double": "double", "date": "dateTime",
         "timestamp": "dateTime"}
# Gold table -> (model table name, description, columns to hide)
TABLES = {
    "daily_trip_summary": ("Daily Trips", "One row per pickup date: trip counts, revenue and averages.",
                           {"trip_count", "total_passengers", "total_distance_miles", "total_fare", "total_tips",
                            "total_revenue", "avg_fare", "avg_distance_miles", "avg_duration_minutes", "avg_tip_pct",
                            "year_month"}),
    "hourly_demand": ("Hourly Demand", "Trips by month, day of week and pickup hour.", {"year_month"}),
    "pickup_zone_summary": ("Pickup Zones", "Trips by month and TLC pickup zone.", {"pickup_location_id", "year_month"}),
    "payment_type_summary": ("Payment Types", "Trips by month and payment type.", {"year_month"}),
    "month": ("Month", "One row per month; filters every other table through Year Month.", {"month_start"}),
}
NAMES = {"pickup_date": "Pickup Date", "year_month": "Year Month", "pickup_day_of_week": "Day of Week",
         "day_of_week_number": "Day of Week Number", "month_start": "Month Start", "month_name": "Month",
         "pickup_hour": "Pickup Hour", "pickup_location_id": "Pickup Location ID", "pickup_borough": "Borough",
         "pickup_zone": "Zone", "payment_type_desc": "Payment Type", "trip_count": "Trip Count",
         "total_passengers": "Total Passengers", "total_distance_miles": "Total Distance (mi)",
         "total_fare": "Total Fare", "total_tips": "Total Tips", "total_revenue": "Total Revenue",
         "avg_fare": "Average Fare", "avg_distance_miles": "Average Distance (mi)",
         "avg_duration_minutes": "Average Duration (min)", "avg_tip_pct": "Average Tip (%)"}
ADDITIVE = {"trip_count", "total_passengers", "total_distance_miles", "total_fare", "total_tips", "total_revenue"}
MONEY = {"total_fare", "total_tips", "total_revenue", "avg_fare"}

DAILY_MEASURES = [
    ("# Trips", "SUM('Daily Trips'[Trip Count])", "#,0", "Number of valid yellow taxi trips (silver rules applied)."),
    ("Revenue", "SUM('Daily Trips'[Total Revenue])", "\\$#,0", "Total amount charged to passengers, all fees included."),
    ("Fare Revenue", "SUM('Daily Trips'[Total Fare])", "\\$#,0", "Metered fare only, excluding tips, tolls and surcharges."),
    ("Tip Revenue", "SUM('Daily Trips'[Total Tips])", "\\$#,0", "Tips recorded on the trip (cash tips are usually not recorded)."),
    ("Fare per Trip", "DIVIDE([Fare Revenue], [# Trips])", "\\$#,0.00", "Average metered fare per trip."),
    ("Revenue per Trip", "DIVIDE([Revenue], [# Trips])", "\\$#,0.00", "Average total amount per trip."),
    ("Miles per Trip", "DIVIDE(SUM('Daily Trips'[Total Distance (mi)]), [# Trips])", "#,0.00", "Average trip distance in miles."),
    ("Minutes per Trip",
     "DIVIDE(SUMX('Daily Trips', 'Daily Trips'[Average Duration (min)] * 'Daily Trips'[Trip Count]), [# Trips])",
     "#,0.0", "Trip-weighted average duration in minutes."),
    ("Tip Rate (%)", "DIVIDE([Tip Revenue], [Fare Revenue])", "0.0%", "Tips as a share of metered fare."),
]


def q(name):
    return f"'{name}'" if any(c in name for c in " .=:'()#%$") else name


def table_tmdl(gold_table, display, desc, hidden):
    _, fields, _ = table_state(f"gold.{gold_table}")
    lines = [f"/// {desc}", f"table {q(display)}", ""]
    if gold_table == "daily_trip_summary":
        for name, dax, fmt, mdesc in DAILY_MEASURES:
            lines += [f"\t/// {mdesc}", f"\tmeasure {q(name)} = {dax}", f"\t\tformatString: {fmt}", "\t\tdisplayFolder: Measures", ""]
    for f in fields:
        t = f["type"]
        dtype = "decimal" if t.startswith("decimal") else TYPES[t]
        lines += [f"\tcolumn {q(NAMES[f['name']])}", f"\t\tdataType: {dtype}"]
        if f["name"] in MONEY:
            lines.append("\t\tformatString: \\$#,0.00")
        elif dtype == "dateTime":
            lines.append("\t\tformatString: yyyy-mm-dd")
        elif dtype in ("int64", "double", "decimal"):
            lines.append("\t\tformatString: #,0" if dtype == "int64" else "\t\tformatString: #,0.00")
        lines.append(f"\t\tsummarizeBy: {'sum' if f['name'] in ADDITIVE else 'none'}")
        if f["name"] in hidden or f["name"] == "day_of_week_number":
            lines.append("\t\tisHidden")
        if f["name"] == "pickup_day_of_week" and any(x["name"] == "day_of_week_number" for x in fields):
            lines.append("\t\tsortByColumn: 'Day of Week Number'")
        if f["name"] == "month_name":
            lines.append("\t\tsortByColumn: 'Month Start'")
        lines += [f"\t\tsourceColumn: {f['name']}", ""]
    lines += [f"\tpartition {q(display)} = entity", "\t\tmode: directLake", "\t\tsource",
              f"\t\t\tentityName: {gold_table}", "\t\t\tschemaName: gold", f"\t\t\texpressionSource: {q(EXPR)}", ""]
    return "\n".join(lines)


parts = {
    "definition.pbism": json.dumps({"version": "4.2", "settings": {}}),
    "definition/database.tmdl": "database\n\tcompatibilityLevel: 1604\n",
    "definition/model.tmdl": "model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\n"
                             + "".join(f"ref table {q(d)}\n" for d, _, _ in TABLES.values()),
    "definition/expressions.tmdl": (
        f"expression {q(EXPR)} =\n\t\tlet\n\t\t    Source = AzureStorage.DataLake("
        f"\"https://onelake.dfs.fabric.microsoft.com/{fabric.WS}/{fabric.LH_ID}\", [HierarchicalNavigation=true])\n"
        "\t\tin\n\t\t    Source\n"),
}
for gold_table, (display, desc, hidden) in TABLES.items():
    parts[f"definition/tables/{display}.tmdl"] = table_tmdl(gold_table, display, desc, hidden)
# Each summary table is filtered by Month on Year Month (many-to-one). Stable ids keep updates idempotent.
parts["definition/relationships.tmdl"] = "".join(
    f"relationship {uuid.uuid5(uuid.NAMESPACE_URL, 'nyctaxi/' + display)}\n"
    f"\tfromColumn: {q(display)}.'Year Month'\n\ttoColumn: Month.'Year Month'\n\n"
    for gold_table, (display, _, _) in TABLES.items() if gold_table != "month")

if __name__ == "__main__":
    import sys
    if "--print" in sys.argv:
        for p, c in parts.items():
            print(f"===== {p}\n{c}")
        sys.exit()
    definition = {"format": "TMDL", "parts": [
        {"path": p, "payload": base64.b64encode(c.encode()).decode(), "payloadType": "InlineBase64"}
        for p, c in parts.items()]}
    existing = {m["displayName"]: m["id"] for m in fabric.items("SemanticModel")}
    if NAME in existing:
        fabric.lro("POST", f"/workspaces/{fabric.WS}/semanticModels/{existing[NAME]}/updateDefinition",
                   {"definition": definition})
        print(f"updated {NAME} {existing[NAME]}")
    else:
        fabric.lro("POST", f"/workspaces/{fabric.WS}/semanticModels",
                   {"displayName": NAME, "description": "Direct Lake model over nyctaxi_lakehouse gold schema",
                    "definition": definition})
        print(f"created {NAME} {[m['id'] for m in fabric.items('SemanticModel') if m['displayName'] == NAME][0]}")

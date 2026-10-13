"""Write the visuals of rpt_nyctaxi (one page, 1280x720) into the scaffolded PBIR folder.
Re-running replaces the page's visuals. Validate afterwards: powerbi-report-author validate report/rpt_nyctaxi.Report"""
import hashlib
import json
import shutil
from pathlib import Path

REPORT = Path(__file__).parent / "report" / "rpt_nyctaxi.Report"
PAGE_DIR = next((REPORT / "definition" / "pages").glob("*/page.json")).parent
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json"


def lit(value):
    return {"expr": {"Literal": {"Value": value}}}


def vid(name):
    return hashlib.sha1(name.encode()).hexdigest()[:20]


def column(table, col):
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": col}}


def measure_proj(table, m):
    return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": table}}, "Property": m}},
            "queryRef": f"{table}.{m}", "nativeQueryRef": m}


def column_proj(table, col):
    return {"field": column(table, col), "queryRef": f"{table}.{col}", "nativeQueryRef": col}


def sum_field(table, col):
    return {"Aggregation": {"Expression": column(table, col), "Function": 0}}


def sum_proj(table, col):
    return {"field": sum_field(table, col), "queryRef": f"Sum({table}.{col})", "nativeQueryRef": f"Sum of {col}"}


def title(text):
    return {"title": [{"properties": {"show": lit("true"), "text": lit(f"'{text}'")}}],
            "subTitle": [{"properties": {"show": lit("false")}}]}


def category_width(px, **axis):
    """Minimum category width small enough that every category fits without a scrollbar."""
    return {"categoryAxis": [{"properties": {"preferredCategoryWidth": lit(f"{px}D"), **axis}}]}


def visual(name, vtype, pos, query_state, objects=None, vco=None, sort=None, filters=None):
    x, y, w, h = pos
    v = {"visualType": vtype, "query": {"queryState": query_state}}
    if sort:
        v["query"]["sortDefinition"] = {"sort": [sort], "isDefaultSort": True}
    if objects:
        v["objects"] = objects
    if vco:
        v["visualContainerObjects"] = vco
    doc = {"$schema": SCHEMA, "name": vid(name),
           "position": {"x": x, "y": y, "z": 1000, "height": h, "width": w, "tabOrder": 1000}, "visual": v}
    if filters:
        doc["filterConfig"] = {"filters": filters}
    return doc


def dropdown_slicer(name, pos, table, col, header):
    return visual(name, "slicer", pos, {"Values": {"projections": [column_proj(table, col)]}},
                  objects={"data": [{"properties": {"mode": lit("'Dropdown'")}}],
                           "header": [{"properties": {"show": lit("true"), "text": lit(f"'{header}'")}}]},
                  vco={"padding": [{"properties": {s: lit("8D") for s in ("top", "bottom", "left", "right")}}]})


def top_n(table, col, by_col, n):
    """Visual-level Top N filter on table[col] ranked by Sum(table[by_col])."""
    return {
        "name": "Filter" + vid(f"topn-{table}-{col}")[:20], "type": "TopN", "howCreated": "User",
        "field": column(table, col),
        "filter": {"Version": 2, "From": [
            {"Name": "subquery", "Type": 2, "Expression": {"Subquery": {"Query": {
                "Version": 2, "From": [{"Name": "t", "Entity": table, "Type": 0}],
                "Select": [{"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": col}, "Name": "field"}],
                "OrderBy": [{"Direction": 2, "Expression": {"Aggregation": {
                    "Expression": {"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": by_col}},
                    "Function": 0}}}],
                "Top": n}}}},
            {"Name": "p", "Entity": table, "Type": 0}],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "p"}}, "Property": col}}],
                "Table": {"SourceRef": {"Source": "subquery"}}}}}]},
    }


page_title = {
    "$schema": SCHEMA, "name": vid("page-title"),
    "position": {"x": 24, "y": 12, "z": 1000, "height": 40, "width": 1040, "tabOrder": 0},
    "visual": {
        "visualType": "textbox",
        "objects": {"general": [{"properties": {"paragraphs": [{
            "textRuns": [{"value": "NYC Yellow Taxi Trips",
                          "textStyle": {"fontFamily": "Segoe UI Semibold", "fontSize": "24px", "color": "#252423"}}],
            "horizontalTextAlignment": "left"}]}}]},
        "visualContainerObjects": {
            "background": [{"properties": {"show": lit("false")}}],
            "border": [{"properties": {"show": lit("false")}}],
            "padding": [{"properties": {s: lit("0D") for s in ("top", "bottom", "left", "right")}}]},
    },
}

# Card sizing for a 720px canvas: value 20pt, label 11pt, height 82 (card sizing formula).
kpis = visual("kpis", "cardVisual", (24, 60, 1048, 82),
              {"Data": {"projections": [measure_proj("Daily Trips", m)
                                        for m in ("# Trips", "Revenue", "Fare per Trip", "Tip Rate (%)")]}},
              objects={"value": [{"properties": {"fontSize": lit("20D"), "labelDisplayUnits": lit("1D")},
                                  "selector": {"id": "default"}}],
                       "label": [{"properties": {"fontSize": lit("11D")}, "selector": {"id": "default"}}],
                       "padding": [{"properties": {"paddingUniform": lit("8D")}, "selector": {"id": "default"}}],
                       "layout": [{"properties": {"paddingUniform": lit("0D")}, "selector": {"id": "default"}}]},
              vco={"padding": [{"properties": {s: lit("8D") for s in ("top", "bottom", "left", "right")},
                                "selector": {"id": "default"}}],
                   "spacing": [{"properties": {"customizeSpacing": lit("true"), "verticalSpacing": lit("2D")},
                                "selector": {"id": "default"}}]})

month_slicer = dropdown_slicer("month-slicer", (1096, 12, 160, 80), "Month", "Month", "Month")

daily = visual("daily-trend", "lineChart", (24, 154, 600, 210),
               {"Category": {"projections": [column_proj("Daily Trips", "Pickup Date")]},
                "Y": {"projections": [measure_proj("Daily Trips", "# Trips")]}},
               vco=title("Trips per day"))

hourly = visual("hourly-demand", "clusteredColumnChart", (640, 154, 440, 210),
                {"Category": {"projections": [column_proj("Hourly Demand", "Pickup Hour")]},
                 "Y": {"projections": [sum_proj("Hourly Demand", "Trip Count")]}},
                objects={"categoryAxis": [{"properties": {"axisType": lit("'Scalar'")}}]},
                vco=title("Trips by pickup hour"),
                sort={"field": column("Hourly Demand", "Pickup Hour"), "direction": "Ascending"})

dow_slicer = dropdown_slicer("dow-slicer", (1096, 154, 160, 80), "Hourly Demand", "Day of Week", "Day of week")

zones = visual("top-zones", "barChart", (24, 376, 600, 336),
               {"Category": {"projections": [column_proj("Pickup Zones", "Zone")]},
                "Series": {"projections": [column_proj("Pickup Zones", "Borough")]},
                "Y": {"projections": [sum_proj("Pickup Zones", "Trip Count")]}},
               objects={**category_width(12, innerPadding=lit("10L")),
                        "valueAxis": [{"properties": {"show": lit("false")}}],
                        "labels": [{"properties": {"show": lit("true")}}]},
               vco=title("Top 10 pickup zones by trips"),
               sort={"field": sum_field("Pickup Zones", "Trip Count"), "direction": "Descending"},
               filters=[top_n("Pickup Zones", "Zone", "Trip Count", 10)])

payment = visual("payment-revenue", "clusteredBarChart", (640, 376, 616, 336),
                 {"Category": {"projections": [column_proj("Payment Types", "Payment Type")]},
                  "Y": {"projections": [sum_proj("Payment Types", "Total Revenue")]}},
                 vco=title("Revenue by payment type"),
                 sort={"field": sum_field("Payment Types", "Total Revenue"), "direction": "Descending"})

visuals_dir = PAGE_DIR / "visuals"
shutil.rmtree(visuals_dir, ignore_errors=True)
for v in (page_title, kpis, month_slicer, daily, hourly, dow_slicer, zones, payment):
    d = visuals_dir / v["name"]
    d.mkdir(parents=True)
    (d / "visual.json").write_text(json.dumps(v, indent=2))
print(f"wrote 8 visuals to {visuals_dir}")

"""Cell sources for the three NYC taxi medallion notebooks. Cells are separated by '# %%'."""

BRONZE = '''
# Bronze: land raw TLC yellow trip files and the zone lookup as-is, plus lineage columns.
# Write-optimized: no V-Order, append-only, partitioned by ingestion_date.
# Re-runs are idempotent: files already present in bronze are skipped.
import uuid
from pyspark.sql import functions as F

spark.conf.set("spark.sql.parquet.vorder.default", "false")
for schema in ["bronze", "silver", "gold"]:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema}")

LANDING_TRIPS = "Files/landing/nyctaxi/yellow/"
LANDING_ZONES = "Files/landing/nyctaxi/reference/taxi_zone_lookup.csv"
TRIPS_TABLE = "bronze.yellow_trips_raw"
ZONES_TABLE = "bronze.taxi_zone_lookup_raw"
batch_id = str(uuid.uuid4())
print(f"batch_id={batch_id}")
# %%
raw = (spark.read.parquet(LANDING_TRIPS)
       .withColumn("source_file", F.col("_metadata.file_path"))
       .withColumn("ingestion_timestamp", F.current_timestamp())
       .withColumn("ingestion_date", F.current_date())
       .withColumn("batch_id", F.lit(batch_id)))

if spark.catalog.tableExists(TRIPS_TABLE):
    loaded = spark.table(TRIPS_TABLE).select("source_file").distinct()
    raw = raw.join(loaded, "source_file", "left_anti")

new_files = [r.source_file for r in raw.select("source_file").distinct().collect()]
print(f"New files to ingest: {len(new_files)}")
for f in new_files:
    print(f"  {f}")
# %%
if new_files:
    (raw.write.format("delta").mode("append")
        .option("mergeSchema", "true")
        .partitionBy("ingestion_date")
        .saveAsTable(TRIPS_TABLE))

zones = (spark.read.option("header", True).csv(LANDING_ZONES)
         .withColumn("source_file", F.lit(LANDING_ZONES))
         .withColumn("ingestion_timestamp", F.current_timestamp())
         .withColumn("batch_id", F.lit(batch_id)))
zones.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(ZONES_TABLE)
# %%
# Validation
batch_rows = spark.table(TRIPS_TABLE).where(F.col("batch_id") == batch_id).count()
total_rows = spark.table(TRIPS_TABLE).count()
zone_rows = spark.table(ZONES_TABLE).count()
print(f"{TRIPS_TABLE}: {batch_rows:,} rows this batch, {total_rows:,} total")
print(f"{ZONES_TABLE}: {zone_rows:,} rows")
spark.table(TRIPS_TABLE).groupBy("source_file").count().orderBy("source_file").show(truncate=False)
assert total_rows > 0, "Bronze trips table is empty"
assert zone_rows > 250, "Zone lookup looks incomplete"
'''

SILVER = '''
# Silver: typed, snake_case, validated, deduplicated trips enriched with zone names.
# Rebuilt from all of bronze each run (full overwrite), partitioned by pickup_date.
from pyspark.sql import functions as F

spark.conf.set("spark.sql.parquet.vorder.default", "true")

BRONZE_TRIPS = "bronze.yellow_trips_raw"
BRONZE_ZONES = "bronze.taxi_zone_lookup_raw"
SILVER_TRIPS = "silver.yellow_trips"
SILVER_ZONES = "silver.taxi_zones"
# %%
zones = (spark.table(BRONZE_ZONES)
         .select(F.col("LocationID").cast("int").alias("location_id"),
                 F.col("Borough").alias("borough"),
                 F.col("Zone").alias("zone"),
                 F.col("service_zone")))
zones.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(SILVER_ZONES)
# %%
payment_types = F.create_map(*[F.lit(x) for kv in {
    1: "Credit card", 2: "Cash", 3: "No charge", 4: "Dispute", 5: "Unknown", 6: "Voided trip", 0: "Flex fare"
}.items() for x in kv])

bronze = spark.table(BRONZE_TRIPS)
bronze_rows = bronze.count()

typed = bronze.select(
    F.col("VendorID").cast("int").alias("vendor_id"),
    F.col("tpep_pickup_datetime").cast("timestamp").alias("pickup_datetime"),
    F.col("tpep_dropoff_datetime").cast("timestamp").alias("dropoff_datetime"),
    F.col("passenger_count").cast("int").alias("passenger_count"),
    F.col("trip_distance").cast("double").alias("trip_distance"),
    F.col("RatecodeID").cast("int").alias("rate_code_id"),
    F.col("store_and_fwd_flag"),
    F.col("PULocationID").cast("int").alias("pickup_location_id"),
    F.col("DOLocationID").cast("int").alias("dropoff_location_id"),
    F.col("payment_type").cast("int").alias("payment_type"),
    F.col("fare_amount").cast("decimal(10,2)").alias("fare_amount"),
    F.col("extra").cast("decimal(10,2)").alias("extra"),
    F.col("mta_tax").cast("decimal(10,2)").alias("mta_tax"),
    F.col("tip_amount").cast("decimal(10,2)").alias("tip_amount"),
    F.col("tolls_amount").cast("decimal(10,2)").alias("tolls_amount"),
    F.col("improvement_surcharge").cast("decimal(10,2)").alias("improvement_surcharge"),
    F.col("congestion_surcharge").cast("decimal(10,2)").alias("congestion_surcharge"),
    F.col("Airport_fee").cast("decimal(10,2)").alias("airport_fee"),
    F.col("total_amount").cast("decimal(10,2)").alias("total_amount"),
    # The month a file covers comes from its name, e.g. yellow_tripdata_2024-01.parquet
    F.regexp_extract("source_file", r"yellow_tripdata_(\\d{4}-\\d{2})", 1).alias("source_month"),
    F.col("source_file"),
    F.col("batch_id"),
).withColumn("trip_duration_minutes",
             (F.unix_timestamp("dropoff_datetime") - F.unix_timestamp("pickup_datetime")) / 60.0).cache()
# %%
# Quality rules: each rule is checked in order so rejections are attributable.
rules = [
    ("required fields present", F.col("pickup_datetime").isNotNull() & F.col("dropoff_datetime").isNotNull()
        & F.col("pickup_location_id").isNotNull() & F.col("dropoff_location_id").isNotNull()),
    ("pickup within file month", F.date_format("pickup_datetime", "yyyy-MM") == F.col("source_month")),
    ("duration 1 min to 6 h", F.col("trip_duration_minutes").between(1, 360)),
    ("distance 0 to 200 mi", (F.col("trip_distance") > 0) & (F.col("trip_distance") <= 200)),
    ("non-negative amounts", (F.col("fare_amount") >= 0) & (F.col("total_amount") >= 0) & (F.col("tip_amount") >= 0)),
    ("passengers 0 to 9 or unknown", F.col("passenger_count").isNull() | F.col("passenger_count").between(0, 9)),
]
df = typed
print(f"bronze rows: {bronze_rows:,}")
for name, cond in rules:
    before = df.count()
    df = df.where(cond)
    print(f"  rule '{name}': rejected {before - df.count():,}")

before = df.count()
df = df.dropDuplicates(["vendor_id", "pickup_datetime", "dropoff_datetime", "pickup_location_id",
                        "dropoff_location_id", "trip_distance", "total_amount"])
print(f"  deduplication: removed {before - df.count():,}")
# %%
pu = spark.table(SILVER_ZONES).select(F.col("location_id").alias("pickup_location_id"),
                                      F.col("borough").alias("pickup_borough"), F.col("zone").alias("pickup_zone"))
do = spark.table(SILVER_ZONES).select(F.col("location_id").alias("dropoff_location_id"),
                                      F.col("borough").alias("dropoff_borough"), F.col("zone").alias("dropoff_zone"))

silver = (df.join(F.broadcast(pu), "pickup_location_id", "left")
            .join(F.broadcast(do), "dropoff_location_id", "left")
            .withColumn("pickup_date", F.to_date("pickup_datetime"))
            .withColumn("pickup_hour", F.hour("pickup_datetime"))
            .withColumn("pickup_day_of_week", F.date_format("pickup_datetime", "E"))
            .withColumn("trip_duration_minutes", F.round("trip_duration_minutes", 2))
            .withColumn("avg_speed_mph", F.round(F.col("trip_distance") / (F.col("trip_duration_minutes") / 60), 2))
            .withColumn("tip_pct", F.when(F.col("fare_amount") > 0,
                                          F.round(F.col("tip_amount") / F.col("fare_amount") * 100, 2)))
            .withColumn("payment_type_desc", F.coalesce(payment_types[F.col("payment_type")], F.lit("Unknown")))
            .withColumn("processed_timestamp", F.current_timestamp()))

(silver.write.format("delta").mode("overwrite")
    .partitionBy("pickup_date")
    .saveAsTable(SILVER_TRIPS))
spark.sql(f"OPTIMIZE {SILVER_TRIPS}")
# %%
# Validation
silver_rows = spark.table(SILVER_TRIPS).count()
print(f"{SILVER_TRIPS}: {silver_rows:,} rows ({silver_rows / bronze_rows:.1%} of bronze)")
spark.table(SILVER_TRIPS).select(
    F.min("pickup_date").alias("min_date"), F.max("pickup_date").alias("max_date"),
    F.countDistinct("pickup_date").alias("days"),
    F.sum(F.col("pickup_zone").isNull().cast("int")).alias("unmatched_zones")).show()
assert silver_rows > 0.8 * bronze_rows, "More than 20% of bronze rows rejected; investigate before trusting silver"
'''

GOLD = '''
# Gold: read-optimized aggregates for Power BI (Direct Lake) and the SQL endpoint.
from pyspark.sql import functions as F

spark.conf.set("spark.sql.parquet.vorder.default", "true")
spark.conf.set("spark.databricks.delta.optimizeWrite.enabled", "true")
spark.conf.set("spark.databricks.delta.optimizeWrite.binSize", "1g")

trips = (spark.table("silver.yellow_trips")
         .withColumn("year_month", F.date_format("pickup_date", "yyyy-MM"))
         .withColumn("day_of_week_number", F.dayofweek("pickup_date")))  # 1 = Sunday, for sorting day names

def save(df, table, zorder=None):
    df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(table)
    spark.sql(f"OPTIMIZE {table}" + (f" ZORDER BY ({zorder})" if zorder else ""))
    print(f"{table}: {spark.table(table).count():,} rows")

metrics = [
    F.count("*").alias("trip_count"),
    F.sum("passenger_count").alias("total_passengers"),
    F.round(F.sum("trip_distance"), 2).alias("total_distance_miles"),
    F.sum("fare_amount").alias("total_fare"),
    F.sum("tip_amount").alias("total_tips"),
    F.sum("total_amount").alias("total_revenue"),
    F.round(F.avg("fare_amount"), 2).alias("avg_fare"),
    F.round(F.avg("trip_distance"), 2).alias("avg_distance_miles"),
    F.round(F.avg("trip_duration_minutes"), 2).alias("avg_duration_minutes"),
    F.round(F.avg("tip_pct"), 2).alias("avg_tip_pct"),
]
# %%
daily = trips.groupBy("pickup_date", "year_month", "pickup_day_of_week", "day_of_week_number").agg(*metrics)
save(daily, "gold.daily_trip_summary", zorder="pickup_date")

hourly = trips.groupBy("year_month", "pickup_day_of_week", "day_of_week_number", "pickup_hour").agg(*metrics)
save(hourly, "gold.hourly_demand")

zone = (trips.groupBy("year_month", "pickup_location_id", "pickup_borough", "pickup_zone").agg(*metrics))
save(zone, "gold.pickup_zone_summary", zorder="pickup_borough")

payment = trips.groupBy("year_month", "payment_type_desc").agg(*metrics)
save(payment, "gold.payment_type_summary")

# Month dimension: lets one report slicer filter every gold table.
month = (trips.select("year_month").distinct()
         .withColumn("month_start", F.to_date(F.concat("year_month", F.lit("-01"))))
         .withColumn("month_name", F.date_format("month_start", "MMMM yyyy")))
save(month, "gold.month")
# %%
# Validation: every gold table must reconcile to silver trip count and revenue.
silver_totals = trips.agg(F.count("*").alias("trips"), F.sum("total_amount").alias("revenue")).first()
for t in ["gold.daily_trip_summary", "gold.hourly_demand", "gold.pickup_zone_summary", "gold.payment_type_summary"]:
    g = spark.table(t).agg(F.sum("trip_count").alias("trips"), F.sum("total_revenue").alias("revenue")).first()
    assert g.trips == silver_totals.trips and g.revenue == silver_totals.revenue, f"{t} does not reconcile to silver"
print(f"All gold tables reconcile: {silver_totals.trips:,} trips, ${silver_totals.revenue:,.2f} revenue")
spark.table("gold.daily_trip_summary").orderBy("pickup_date").show(31)
'''

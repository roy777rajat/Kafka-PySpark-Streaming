from pyspark.sql import SparkSession

# 1. Start Spark session
spark = SparkSession.builder \
    .appName("Day1 CSV vs Parquet") \
    .master("local[*]") \
    .getOrCreate()

# Optional: show INFO logs
#spark.sparkContext.setLogLevel("INFO")

# 2. Read small CSV
csv_path = r"E:\pyspark-training\data\small\online_retail.csv"
df = spark.read.option("header", "true").option("inferSchema", "true").csv(csv_path)

# 3. Show basic info
print("Row count:", df.count())
df.show(5)
df.printSchema()

# 4. Save as Parquet (optional, for Day 1 exercise)
parquet_path = r"E:\pyspark-training\data\small\online_retail.parquet"
df.write.mode("overwrite").parquet(parquet_path)

# 5. Show Spark UI URL
#print("Spark UI URL:", spark.sparkContext.uiWebUrl)

# Keep script open to observe Spark UI
input("Press Enter to exit...")

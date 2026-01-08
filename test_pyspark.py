from pyspark.sql import SparkSession

# Start Spark session
spark = SparkSession.builder \
    .appName("Day1 Test") \
    .master("local[*]") \
    .getOrCreate()

# Optional: show INFO logs
spark.sparkContext.setLogLevel("INFO")

# Read a small CSV (example)
df = spark.range(10)
df.show()

# Spark UI URL
print("Spark UI URL:", spark.sparkContext.uiWebUrl)

# Keep the script running so you can observe Spark UI
input("Press Enter to exit...")

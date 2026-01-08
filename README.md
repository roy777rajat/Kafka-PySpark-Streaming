# Kappa Architecture: Real-Time Data Pipeline with Kafka, PySpark, PostgreSQL & Delta Lake

![Kafka](https://img.shields.io/badge/Apache%20Kafka-7.4.1-2e3136?style=flat-square&logo=apache-kafka)
![PySpark](https://img.shields.io/badge/Apache%20PySpark-3.5.5-1f77b4?style=flat-square&logo=apache-spark)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square&logo=postgresql)
![Delta Lake](https://img.shields.io/badge/Delta%20Lake-ACID%20Compliant-00a0a0?style=flat-square&logo=delta)
![Docker](https://img.shields.io/badge/Docker%20Compose-Up-2496ed?style=flat-square&logo=docker)
![Python](https://img.shields.io/badge/Python-3.8%2B-3776ab?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)

---

## 📚 Project Overview

This repository implements a **Kappa Architecture** for building real-time data pipelines using Apache Kafka, PySpark Structured Streaming, PostgreSQL, and Delta Lake. The architecture processes streaming data from Kafka topics, transforms it using PySpark, and writes to multiple sinks (PostgreSQL for operational queries and Delta Lake for analytical storage) atomically.

### Key Features
- ✨ **Real-time CDC (Change Data Capture)** from PostgreSQL via Debezium
- ⚡ **Micro-batch Processing** with PySpark Structured Streaming
- 🔄 **Multiple Sinks**: PostgreSQL (OLTP) + Delta Lake (OLAP)
- 🔒 **ACID Guarantees** with Delta Lake transactions
- 📊 **Data Transformation & Schema Evolution**
- 🐳 **Fully Containerized** with Docker Compose
- 📝 **Exactly-Once Semantics** with checkpointing

---

## 🏛️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                             │
│                    (PostgreSQL Database)                        │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│               CHANGE DATA CAPTURE (Debezium CDC)                │
│          Captures INSERT/UPDATE/DELETE from Postgres            │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    KAFKA STREAMING PLATFORM                     │
│    Topics: pgsrc.public.fund_metadata, pgsrc.public.fund_unit   │
│              (Durable, Partitioned, Replayable)                 │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│            PYSPARK STRUCTURED STREAMING LAYER                   │
│         Transformations, Enrichment, Schema Validation          │
│              foreachBatch() for Atomic Writes                   │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
        ┌──────────────────────┐  ┌──────────────────────┐
        │  POSTGRESQL (OLTP)   │  │   DELTA LAKE (OLAP)  │
        │                      │  │                      │
        │ • Fund Metadata      │  │ • Historical Archive │
        │ • Operational Queries│  │ • Time Travel        │
        │ • BI Dashboards      │  │ • Schema Evolution   │
        │ • Real-time Analytics│  │ • Compliance Storage │
        └──────────────────────┘  └──────────────────────┘
```

---

## 📁 Project Structure & File Descriptions

### **1. Docker Infrastructure**

#### 📄 `docker-compose.yml`
Complete containerized setup for the entire Kappa architecture stack.

**Components:**
- **PostgreSQL 15**: Source database with ACID transactions for financial data
- **Zookeeper 7.4.1**: Kafka cluster coordination and leader election
- **Kafka Broker 7.4.1**: Distributed streaming event bus with 2 listener ports:
  - `9092`: Internal broker communication
  - `29092`: External (host) communication for PySpark clients
- **Schema Registry 7.4.1**: Central schema management for Avro/JSON schemas
- **Debezium Kafka Connect 2.2**: CDC engine for capturing database changes
- **ksqlDB 0.29.0**: Streaming SQL for real-time analytics (optional)

**Key Configurations:**
```yaml
# Kafka Persistence
KAFKA_LOG_RETENTION_MS: 86400000  # 24-hour retention
KAFKA_LOG_SEGMENT_BYTES: 104857600  # 100MB segment size

# Debezium Setup
- Plugin: pgoutput (built-in PostgreSQL logical decoder)
- Slot: debezium_slot (replication slot for CDC)
- Publication: dbz_pub (filtering tables to capture)

# Storage Volumes
- pgdata: PostgreSQL persistent storage
- kafka-data: Kafka log persistence
```

**Start the stack:**
```bash
docker-compose up -d
```

---

### **2. Stream Processing Notebooks**

#### 📓 `02-Kafka-Pyspark-Read-Write.ipynb`
**Primary production stream processing pipeline for multiple sink writes**

**Purpose:** Main streaming job that reads from Kafka, transforms data, and writes atomically to both PostgreSQL and Delta Lake.

**Key Sections:**
1. **Spark Session Configuration**
   - Delta Lake extensions enabled
   - Kafka SQL dependencies (`spark-sql-kafka-0-10_2.12:3.5.5`)
   - PostgreSQL JDBC driver (`postgresql:42.7.8`)

2. **Schema Definitions**
   ```python
   fund_schema = StructType([
       StructField("fund_id", IntegerType()),
       StructField("fund_name", StringType()),
       StructField("fund_code", StringType()),
       StructField("fund_description", StringType()),
       StructField("updated_at", LongType()),
       StructField("fund_price", DoubleType())
   ])
   ```

3. **Kafka Stream Reading**
   - Bootstrap servers: `localhost:29092`
   - Topics subscribed: CDC output topics
   - Starting offsets: `earliest` (full replay capability)

4. **Multi-Sink Writing Strategy**
   - `foreachBatch()` orchestration for atomic writes
   - PostgreSQL: JDBC writes with upsert logic
   - Delta Lake: Append-mode with partitioning
   - Exception handling and batch ID logging

5. **Checkpoint Management**
   - Location: `C:/delta/checkpoints/fund_metadata`
   - Ensures exactly-once semantics
   - Enables failure recovery

**Why This Design:**
- Single checkpoint source of truth prevents duplicate writes
- foreachBatch() ensures all sinks succeed or all fail
- Enables monitoring per batch with batch_id and row counts
- Separates business logic from sink implementation

---

#### 📓 `Kafka-pyspark-01.ipynb`
**Basic Kafka streaming read example with Debezium CDC parsing**

**Purpose:** Educational/reference notebook demonstrating CDC stream consumption.

**Key Features:**
1. **Debezium CDC Schema Parsing**
   - Extracts `before`/`after` records from CDC events
   - Identifies operation type (INSERT/UPDATE/DELETE)
   - Parses source metadata (database, table, timestamp)

2. **Schema Mapping**
   ```python
   cdc_schema = StructType([
       StructField("before", MapType(StringType(), StringType())),
       StructField("after", MapType(StringType(), StringType())),
       StructField("source_system", StringType())
   ])
   ```

3. **Streaming Operations**
   - JSON deserialization of Kafka messages
   - Field extraction and type casting
   - Display streaming results in micro-batches

**Use Cases:**
- Understanding CDC data structure
- Debugging Kafka topics
- Single-sink scenarios or analytics

---

#### 📓 `readJson.ipynb`
**JSON batch reading and parsing with Spark**

**Purpose:** Demonstrates batch processing of JSON files with schema validation.

**Key Functionality:**
- Load JSON data from local/distributed storage
- Apply complex nested schemas
- Transform and validate data
- Write to PostgreSQL using batch JDBC

**Use Cases:**
- One-time data migrations
- ETL from JSON APIs
- Schema evolution testing
- Pre-streaming data validation

---

### **3. CDC Configuration**

#### 📄 `postgres-debezium-connector.json`
**Kafka Connect configuration for PostgreSQL Change Data Capture**

**Connector Settings:**
```json
{
  "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
  "database.hostname": "postgres",  // Docker container name
  "database.port": "5432",
  "database.user": "pguser",
  "database.password": "pgpassword",
  "database.dbname": "finance",
  "database.server.name": "pgsrc",  // Kafka topic prefix
  "plugin.name": "pgoutput",        // PostgreSQL logical decoder
  "slot.name": "debezium_slot",     // WAL replication slot
  "publication.name": "dbz_pub",    // Table publication
  "table.include.list": "public.fund_metadata,public.fund_unit",
  "tombstones.on.delete": false,    // Don't emit delete markers
  "snapshot.mode": "initial"        // Full snapshot on startup
}
```

**Transformations Applied:**
```json
{
  "transforms": "addSource,renameField",
  "transforms.addSource.type": "InsertField$Value",
  "transforms.addSource.static.field": "source_system",
  "transforms.addSource.static.value": "finance_db",
  "transforms.renameField.type": "ReplaceField$Value",
  "transforms.renameField.renames": "fund_name:name"
}
```

**Purpose:**
1. Continuous capture of database changes
2. Ensures no data is missed (WAL-based)
3. Provides operation context (INSERT/UPDATE/DELETE)
4. Enables high-fidelity data lineage

**Deployment:**
```bash
curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d @postgres-debezium-connector.json
```

---

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose installed
- Python 3.8+
- Jupyter Notebook
- Git

### Installation & Setup

**1. Clone the Repository**
```bash
git clone https://github.com/roy777rajat/Kafka-PySpark-Streaming.git
cd Kafka-PySpark-Streaming
```

**2. Start Docker Containers**
```bash
docker-compose up -d
```

Wait for all services to be healthy:
```bash
docker-compose ps
```

Expected output:
```
pg_local         PostgreSQL 15           ✓ Up
zookeeper-1      Zookeeper 7.4.1         ✓ Up
kafka-1          Kafka 7.4.1              ✓ Up
schema-registry  Schema Registry 7.4.1   ✓ Up
connect          Debezium Connect 2.2    ✓ Up
ksqldb-server    ksqlDB 0.29.0           ✓ Up
```

**3. Register Debezium CDC Connector**
```bash
curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d @postgres-debezium-connector.json
```

Verify registration:
```bash
curl http://localhost:8083/connectors/postgres-cdc | jq .
```

**4. Create Sample Data in PostgreSQL**
```bash
# Connect to PostgreSQL
docker exec -it pg_local psql -U pguser -d finance

# Create tables
CREATE TABLE public.fund_metadata (
    fund_id SERIAL PRIMARY KEY,
    fund_name VARCHAR(255) NOT NULL,
    fund_code VARCHAR(10) UNIQUE,
    fund_description TEXT,
    updated_at BIGINT,
    fund_price DECIMAL(10,2)
);

CREATE TABLE public.fund_unit (
    unit_id SERIAL PRIMARY KEY,
    fund_id INTEGER REFERENCES fund_metadata(fund_id),
    unit_price DECIMAL(10,2),
    unit_date DATE
);

# Enable logical replication for CDC
ALTER SYSTEM SET wal_level = logical;
# Restart PostgreSQL container after this
```

**5. Run PySpark Stream Processing**
```bash
# Open Jupyter
jupyter notebook

# Execute 02-Kafka-Pyspark-Read-Write.ipynb sequentially
```

---

## 📊 Architecture Deep Dive

### Why Kappa Architecture?

| Aspect | Lambda (Batch + Stream) | Kappa (Stream Only) |
|--------|----------------------|-------------------|
| **Code Duplication** | High (separate paths) | None (single path) |
| **Complexity** | Very High | Moderate |
| **Latency** | Batch: Hours | Stream: Sub-seconds |
| **State Management** | Complex | Simpler |
| **Operational Overhead** | 2x infrastructure | 1x infrastructure |
| **Cost** | Higher | Lower |

**Our Choice: Kappa** ✓
- Real-time processing requirements
- Single code path reduces bugs
- Kafka's durability enables replay
- Lower operational complexity

---

### Data Flow & Processing

**Stage 1: Data Capture (Debezium)**
```
PostgreSQL WAL → Debezium Connector → Kafka Topics
                                    ├─ pgsrc.public.fund_metadata
                                    └─ pgsrc.public.fund_unit
```

**Stage 2: Stream Ingestion**
- Kafka provides buffering (24-hour retention)
- Topics are partitioned for parallel processing
- Offsets tracked for exactly-once semantics

**Stage 3: PySpark Processing**
- Micro-batches (default: 500ms to 10s)
- Stateless transformations (no state store needed)
- Schema validation and enrichment

**Stage 4: Multi-Sink Writes**
```python
def write_to_multiple_sink(batch_df, batch_id):
    # PostgreSQL: Recent data for operational queries
    batch_df.write \
        .mode("append") \
        .jdbc(url, table="public.fund_metadata_trail", properties=jdbc_props)
    
    # Delta Lake: Historical archive with ACID guarantees
    batch_df.write \
        .format("delta") \
        .mode("append") \
        .save("C:/delta/fund_metadata")
```

---

## 🔄 Checkpointing & Fault Tolerance

**Checkpoint Structure:**
```
C:/delta/checkpoints/fund_metadata/
├── offsets/           # Last Kafka offset per partition
├── sources/           # Source metadata
├── metadata/          # Schema and batch info
└── state/             # Optional stateful processing
```

**Guarantees:**
- ✓ **Exactly-once**: Checkpoint prevents reprocessing
- ✓ **Durability**: Offsets persisted to disk
- ✓ **Recoverability**: Job can resume from checkpoint
- ✗ **No duplicates**: Even after crash

---

## 📈 Monitoring & Observability

### Kafka Topics Health
```bash
# List all topics
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Check consumer lag
docker exec kafka kafka-consumer-groups --list --bootstrap-server localhost:9092
```

### Spark Streaming Dashboard
- Visit `http://localhost:4040` (while job is running)
- Monitor: batch duration, processing time, input rate

### Database Verification
```sql
-- PostgreSQL: Recent writes
SELECT COUNT(*) as row_count FROM public.fund_metadata_trail;
SELECT MAX(updated_at) as latest_update FROM public.fund_metadata_trail;

-- Delta Lake: Versioned history
SELECT * FROM delta.`C:/delta/fund_metadata/` LIMIT 100;
DESCRIBE HISTORY delta.`C:/delta/fund_metadata/`;
```

---

## 🎥 Demo Video

Watch the complete walkthrough: [Kappa Architecture Demo](https://youtu.be/e5MuRS6tDaw)

**Demo Covers:**
- Docker Compose startup
- Debezium CDC connector registration
- Inserting test data into PostgreSQL
- Real-time Kafka streams
- PySpark processing with output
- Verification in PostgreSQL and Delta Lake

---

## 📖 Reference Article

Deep-dive technical article: [Kappa Architecture: Multiple Sinks with Kafka, PySpark, PostgreSQL & Delta Lake](https://medium.com/@uk.rajatroy/kappa-architecture-multiple-sink-kafka-pyspark-postgres-and-delta-lake-44cefd33350e)

**Article Highlights:**
- Conceptual architecture comparison
- Detailed configuration walkthroughs
- Production considerations
- Scaling patterns

---

## 🛠️ Technology Stack

| Component | Purpose | Version |
|-----------|---------|---------|
| **Apache Kafka** | Event streaming platform | 7.4.1 |
| **Apache PySpark** | Distributed stream processing | 3.5.5 |
| **PostgreSQL** | OLTP operational database | 15 |
| **Delta Lake** | ACID data lake layer | Latest |
| **Debezium** | Change data capture | 2.2 |
| **Schema Registry** | Schema evolution management | 7.4.1 |
| **ksqlDB** | Stream analytics SQL | 0.29.0 |
| **Docker** | Container orchestration | Latest |
| **Python** | Spark application language | 3.8+ |

---

## 🧪 Testing & Validation

### Test Data Generation
```python
# Insert test data into PostgreSQL
INSERT INTO public.fund_metadata 
(fund_name, fund_code, fund_description, updated_at, fund_price) 
VALUES 
('Aggressive Growth Fund', 'AGF-001', 'High-risk growth portfolio', 1704067200000, 105.50),
('Conservative Fund', 'CON-001', 'Low-volatility bond fund', 1704067200000, 98.75);
```

### Validation Queries
```sql
-- PostgreSQL consistency check
SELECT fund_id, fund_name, COUNT(*) as writes 
FROM public.fund_metadata_trail 
GROUP BY fund_id, fund_name;

-- Delta Lake versioning
SELECT version, num_added_files, num_removed_files 
FROM delta.`C:/delta/fund_metadata/_delta_log` 
ORDER BY timestamp DESC LIMIT 10;
```

---

## 📚 File Reference Guide

| File | Type | Purpose | Key Topics |
|------|------|---------|-----------|
| `docker-compose.yml` | Docker | Infrastructure setup | Kafka, Postgres, Debezium, ksqlDB |
| `02-Kafka-Pyspark-Read-Write.ipynb` | Notebook | Multi-sink streaming pipeline | foreachBatch, JDBC, Delta writes |
| `Kafka-pyspark-01.ipynb` | Notebook | Basic CDC reading | Schema parsing, CDC structure |
| `readJson.ipynb` | Notebook | Batch JSON processing | Batch reads, schema validation |
| `postgres-debezium-connector.json` | Config | CDC connector definition | PostgreSQL CDC, logical replication |

---

## 🔗 Additional Resources

- **Kafka Documentation**: https://kafka.apache.org/documentation/
- **PySpark Structured Streaming**: https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html
- **Delta Lake Guide**: https://docs.delta.io/latest/
- **Debezium PostgreSQL**: https://debezium.io/documentation/reference/stable/connectors/postgresql.html

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes with clear commit messages
4. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👨‍💼 About the Author

**Rajat Roy**
- 🌐 Portfolio: [rajatwork.com](https://rajatwork.com)
- 💼 LinkedIn: [linkedin.com/in/royrajat](https://linkedin.com/in/royrajat)
- 🐙 GitHub: [github.com/roy777rajat](https://github.com/roy777rajat)
- 📱 Twitter/X: [@uk_rajatroy](https://twitter.com/uk_rajatroy)
- 📝 Medium: [@uk.rajatroy](https://medium.com/@uk.rajatroy)

Active AWS Builder specializing in cloud-native AI solutions, FastAPI deployments, and serverless automation.

---

## ⭐ Star & Support

If this project helped you understand Kappa Architecture and real-time streaming, please ⭐ star this repository!

---

**Last Updated**: January 2026
**Status**: ✅ Production-Ready
**Maintenance**: Active

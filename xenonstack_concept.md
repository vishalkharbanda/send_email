# XenonStack Project — Deep Concepts Guide
> Data Engineer | XenonStack, Mohali | Aug 2022 – Sep 2023
> Written to actually help you understand, not just memorize — because it has been 3 years

---

## 0. The Big Picture — What Were You Actually Building?

Before diving into tools, understand the two core problems you were solving.

### Problem 1: UPI Fraud Detection

UPI transactions happen millions of times per day. A fraudulent payment can happen in seconds.
If you detect fraud 3 hours later in a nightly report, the money is already gone. So you needed
a system that could watch every transaction the moment it was created, look for suspicious patterns
in the data, and raise an alert in near real-time.

That required four things:
1. **Capture data the instant a transaction hits the database** — this is what Debezium does
2. **Move it rapidly and reliably without losing records** — this is what Kafka does
3. **Analyze relationship patterns between accounts** — this is what ArangoDB (graph database) does
4. **Show results to the business team on a live dashboard** — this is what Power BI + Azure Synapse does

### Problem 2: Wind Turbine Sensor Pipeline

Wind turbines have dozens of sensors sending data every second — temperature, rotation speed,
voltage, vibration. That is a massive, continuous flood of data. You needed to collect all of it
reliably without dropping anything, store it, and make it available for engineers to analyze.

For this: Kafka was the highway that absorbed all that sensor data, Spark processed it in bulk,
and Airflow scheduled the whole workflow so it ran reliably every day.

Everything you did at XenonStack was in service of one of these two pipelines. Keep this context
in mind as you read about each technology.

---

## 1. ETL — What It Means and Why It Exists

**ETL = Extract → Transform → Load**

Think of it like this: you work at a store and need inventory from a supplier warehouse.
But the supplier labels things differently than your store does — different naming conventions,
different units, some items are damaged, some are missing labels entirely. You cannot just dump
everything directly onto your shelves. You have to sort it, repackage it, fix the labels, and
then put it away. That sorting and repackaging step is the "Transform" in ETL.

### Extract — Pulling Data from the Source

The source system is your live application database — the PostgreSQL or SQL Server database
where UPI transactions are being written in real-time. Extracting means reading data from it.

### Transform — Cleaning and Reshaping

Raw data from a production database is messy:
- Some fields are null that should not be
- Timestamps might be in different timezones
- Account IDs might be in different formats across tables
- You might need to join multiple tables together to get all the context you need
- You might need to compute new fields (like "is this transaction suspicious based on these rules?")

The transform step is where all that work happens — in Spark, in Python scripts, or in SQL.

### Load — Writing to the Destination

After the data is clean and properly structured, you write it to the destination — in your case,
Azure Synapse, the analytics data warehouse where Power BI dashboards query from.

### Why Not Just Query the Source Database Directly?

This is the fundamental question that explains why data warehouses exist at all.

The source database (where UPI transactions are being written) is a **transactional system**.
It is designed to handle thousands of small writes per second — every time someone sends money,
a new row is inserted. This requires the database to maintain indexes, locks, and constraints
carefully. It is optimized for many small operations happening simultaneously.

If you also run a heavy analytical query like "give me all transactions from the last 3 months
grouped by account, calculate the sum and count, filter for amounts over 10,000" — that query
needs to scan millions of rows. Running it directly on the production database:
1. Slows down the database significantly
2. Can lock tables, causing live UPI transactions to queue up
3. In the worst case, crashes the system

So the practice is: copy data to a separate system (the data warehouse) that is designed
specifically for heavy read and aggregation queries. Debezium + Kafka is how you copy it in real-time.

### Batch ETL vs Real-Time ETL

**Old approach (batch ETL):** A cron job runs at 2 AM. It pulls all of yesterday's transactions,
transforms them, and loads them into the warehouse. By 8 AM when people come to work, the
dashboards show yesterday's data. This works fine for monthly reports and business summaries.

**Problem with batch for fraud:** If someone starts laundering money at 11 PM, you don't detect
it until 8 AM the next day — 9 hours later. The money is long gone.

**Real-time ETL (what you built):** Data flows continuously. A transaction happens at 11:00:00 PM.
By 11:00:05 PM, it is in the fraud detection system and being analyzed. That's the difference
Debezium and Kafka made.

---

## 2. Change Data Capture (CDC) and Debezium

### The Problem With Polling

Here is the naive approach to real-time data: write a script that queries the source database
every 5 seconds — "give me all records where updated_at > last_5_seconds". This is called polling.

The problems:
- You keep hitting the database even when nothing changed — wasting resources
- If a record was inserted AND deleted between two polls, you never see it — it just vanishes
- You cannot reliably detect deletes — a deleted row leaves no trace in a SELECT
- You put constant extra load on the production database
- What if the poll fails once? You might miss a window of data entirely.

### How Debezium Solves This

Every serious database (PostgreSQL, MySQL, SQL Server) maintains an internal log called the
**Write-Ahead Log (WAL)** in PostgreSQL, or **transaction log** in SQL Server.

Before the database writes anything to disk, it writes what it's *about to do* to the log:
"I'm about to INSERT this row with these values." "I'm about to UPDATE account_id=ACC123,
change balance from 5000 to 3000." This log is how databases guarantee they don't lose data
even if they crash mid-operation — on restart, they read the log and redo/undo incomplete work.

**Debezium reads this same log.** It does not query your tables at all. It sits at the side like
a passive observer reading the newspaper of what the database is doing. Every INSERT, UPDATE,
or DELETE shows up in the log, and Debezium converts each change into a Kafka message.

This means:
- Zero missed events — the log captures absolutely everything
- Zero extra load from polls — Debezium just reads a file, not the live tables
- Exact order preserved — the log is strictly ordered by time
- Deletes are captured — the log records "I'm deleting row with id=T001"

### What a Debezium Event Actually Looks Like

When a UPI transaction is inserted into the source database, Debezium creates a message like this:

```json
{
  "op": "c",
  "before": null,
  "after": {
    "txn_id": "UPI2023030112345",
    "src_account": "ACC001",
    "dst_account": "ACC999",
    "amount": 85000.00,
    "txn_time": "2023-03-01T12:34:56Z",
    "status": "SUCCESS"
  }
}
```

`"op": "c"` means "create" (insert). If a transaction's status was updated, it would be `"op": "u"`
and the `"before"` field would show the old values, `"after"` shows the new values.
For a delete, `"op": "d"`, `"after"` would be null and `"before"` would show the deleted row.

This event is published to a Kafka topic and flows downstream instantly — picked up by your
fraud detection system, your data warehouse loader, your data lake writer — all simultaneously.

### Key Debezium Concepts You Need to Know

**Connector**: A Debezium "connector" is a configured plugin that watches one specific database.
You tell it: "watch this PostgreSQL server, monitor the transactions table and the accounts table,
publish changes to these Kafka topics." Each connector is a small running process.

**WAL (Write-Ahead Log)**: PostgreSQL's internal change log. Debezium reads it using PostgreSQL's
"logical decoding" feature, which was designed exactly for this purpose. PostgreSQL knows Debezium
is listening and keeps the relevant log segments available.

**Initial Snapshot**: When you first connect Debezium to an existing database that already has
millions of rows, it cannot just start from "changes going forward" — the downstream system needs
the existing data too. So Debezium does a one-time snapshot: reads all existing rows from the
tables you configured, publishes them all as "create" events, and then switches to streaming mode
for new changes. For a large table, this snapshot can take hours.

**Snapshot Mode Options:**
- `initial`: Do a full snapshot of all existing data, then stream new changes. Default.
- `schema_only`: Skip the data snapshot, only capture changes from now on. Use when the
  downstream system already has the historical data.
- `never`: Assume downstream is already in sync. Only capture new changes.

**Schema Registry**: Kafka messages are just bytes. Both Debezium (producer) and your consumers
need to agree on the exact structure of those bytes — which fields, what data types. The Schema
Registry stores this definition (the "schema") and assigns it a version number. Debezium registers
the schema, consumers look it up. If a source table adds a new column, the schema is updated with
a new version, and old consumers continue working with the old version while new consumers can
use the new one. This is "schema evolution."

**At-Least-Once Delivery**: If Debezium crashes and restarts, it might re-send the last few
events it was not 100% sure were delivered. This means your consumers might receive the same
event twice. This is normal and expected. Your consumer must handle it safely — usually by
using an "upsert" operation (insert if not exists, update if it does) keyed on the transaction ID.
This way, processing the same event twice has the same result as processing it once.

### The Complete Pipeline You Built

```
PostgreSQL / SQL Server (source DB, live UPI transactions)
          |
          | Debezium reads the WAL (Write-Ahead Log)
          |
    Debezium Connector
          |
          | publishes change events as messages
          |
    Apache Kafka (topic: upi-transactions)
          |
    +-----+-----+
    |           |
    |     Azure Stream Analytics / Spark Streaming
    |           |
    |     [fraud rule processing, graph updates in ArangoDB]
    |           |
Azure Synapse SQL Pool
    |
Power BI Dashboard
```

---

## 3. Apache Kafka

### What Kafka Actually Is

Kafka is a distributed, durable, high-throughput message streaming platform. That sentence has
a lot of words — let's break it down with a real analogy.

**The old way (direct messaging):** System A sends data directly to System B. If System B is
down when A sends, the message is lost. If B is slow, A has to wait. If C also needs the same
data, A has to send it twice.

**The Kafka way:** System A publishes a message to Kafka. Kafka stores it durably on disk.
System B, C, D can each read it independently at their own pace, even if they were offline when
A published it. If any of them crash and restart, they resume exactly where they left off.
Kafka is the central "post office" — nobody depends on anybody else being available at the same moment.

### Why Kafka at XenonStack Specifically

**For the fraud detection pipeline:**
Debezium publishes a transaction event to Kafka. Three different consumers can each read that
same event independently:
- Consumer 1: Load raw event into Azure Synapse for dashboards
- Consumer 2: Update the ArangoDB fraud graph with the new transaction
- Consumer 3: Archive the raw event to Azure Data Lake for long-term storage

All three happen in parallel, at their own speed. Consumer 2 might be slow because ArangoDB
graph updates take time — that is fine, it does not block or slow down Consumer 1 or Consumer 3.

**For the wind turbine pipeline:**
Hundreds of sensors each send data points every second. That could be millions of messages per
minute. Kafka handles this massive throughput easily. It acts as a buffer: even if the downstream
Spark processing falls behind during a maintenance window, sensor data keeps flowing into Kafka
and nothing is lost. When Spark comes back, it catches up.

### Kafka's Core Building Blocks — Explained Properly

#### Topics — The Mailboxes

A topic is a named, categorized stream of messages. Think of it as a named mailbox.
You create one topic per type of event:
- `upi-transactions` — all UPI transaction change events from Debezium
- `turbine-sensor-readings` — all sensor data from wind turbines
- `fraud-alerts` — alerts generated by the fraud detection system

Producers write to a topic. Consumers read from a topic. A topic can have many producers and
many consumers simultaneously.

#### Partitions — The Lanes on the Highway

Every topic is split into partitions. Each partition is an ordered, immutable log of messages.
Messages are appended to the end; they are never modified or deleted (until they expire based
on retention policy).

Why partitions? Parallelism. One partition can handle a certain throughput. If you need 10x that
throughput, create 10 partitions. Different machines in the Kafka cluster handle different partitions.

How does a message end up in a partition? By the message's "key." If you use account_id as the
key, all messages with the same account_id go to the same partition. This guarantees that all
events for one account are in order (because one partition = one ordered log).

#### Producers — The Writers

Producers are the applications writing to Kafka. Debezium is a producer. Your sensor data
collector is a producer.

When a producer sends a message, it can choose reliability vs speed:

`acks=0` — "Fire and forget." I send the message and don't wait for confirmation. Maximum speed,
but if Kafka is briefly busy or there's a network blip, the message silently disappears.
Only use for non-critical metrics where occasional loss is acceptable.

`acks=1` — "Confirm from the leader." I wait for the partition's leader broker to confirm it
received the message. Safer, but if the leader crashes immediately after confirming but before
replicating to followers, the message is still lost.

`acks=all` — "Confirm from all replicas." I wait until the leader AND all in-sync follower
replicas have saved the message to disk. Slowest but safest. Use this when you cannot afford
to lose data — like financial transactions.

#### Consumers and Consumer Groups — The Readers

A consumer reads messages from a topic. But the powerful concept is **consumer groups**.

Imagine a topic with 6 partitions receiving 600,000 messages/minute. One consumer reading
all 6 partitions would have to process 600,000/min. If you start 6 consumers in the same
consumer group, Kafka assigns one partition to each consumer — each processes only 100,000/min.
Six times the throughput.

If one of those consumers crashes, Kafka automatically reassigns its partition to one of the
remaining consumers (rebalancing). You don't lose data; that consumer just takes on extra load
until the crashed one recovers.

Key rule: within a consumer group, each partition is assigned to exactly one consumer. You
cannot have two consumers in the same group reading the same partition simultaneously.

A completely different application that also wants to read the same topic creates its own
consumer group. It reads all the data completely independently of the first group — without
any coordination or interference. This is how multiple downstream systems (Synapse loader,
ArangoDB updater, Data Lake archiver) can all consume the same Kafka topic without interfering.

#### Offsets — Bookmarks

Every message in a partition has a sequential number called an offset. 0, 1, 2, 3, 4...
Think of it as page numbers in a book.

When a consumer finishes processing message 47, it "commits its offset" — tells Kafka:
"I have successfully processed up to offset 47." If the consumer crashes and restarts, it asks
Kafka: "Where was I?" Kafka says: "You committed up to offset 47." The consumer resumes from
offset 48. No data lost, no data reprocessed from the beginning.

**Critical setting: `enable.auto.commit=false`**

By default, Kafka auto-commits the offset every 5 seconds, regardless of whether your code
finished processing. If Kafka auto-commits offset 47 at time T, but your code crashes at time T+1
before finishing processing message 47 — Kafka thinks you're done with 47 and won't give it to
you again. That message is permanently skipped. You lost data.

With `enable.auto.commit=false`, you manually commit the offset only after your code confirms
it successfully processed the message. This is safer.

#### Replication — The Backup System

Each partition is copied (replicated) across multiple Kafka broker machines.
`replication.factor=3` means 3 copies exist: one leader and two followers.

The leader handles all reads and writes. Followers silently copy everything from the leader
in real-time. If the leader machine dies at 3 AM, Kafka automatically elects one of the
followers as the new leader. No data is lost (assuming `acks=all`), and the system continues
operating within seconds.

#### Consumer Lag — The Health Metric

Consumer lag = (latest offset published to Kafka) minus (last offset the consumer committed).

Lag of 0: Your consumer is processing messages as fast as they arrive. Healthy.
Lag of 10,000: Your consumer is 10,000 messages behind. Could mean the consumer is slow,
or there was a restart, or traffic spiked.
Lag of 1,000,000 and growing: Your consumer is falling further behind. Fraud alerts would
be delayed by the time it takes to process those 1 million backlogged messages.

You monitor consumer lag in production constantly, just like monitoring CPU or memory.

---

## 4. Apache Spark and PySpark

### Why Spark Exists — The Scale Problem

Normal Python pandas code runs on one machine. If you have 50 million rows, pandas loads them
into your laptop's 16GB of RAM, processes them, and you get a result. But what if you have
500 million rows? Or 50 billion rows of wind turbine sensor data?

One machine's RAM and CPU cannot handle that in a reasonable time — or at all.

Spark solves this by distributing the computation across a cluster of machines — 10, 50, or
500 machines working in parallel. Each machine processes a portion of the data simultaneously.
What takes 8 hours on one machine might take 10 minutes on a 50-machine Spark cluster.

### How Spark Is Structured

**The Driver:** This is the brain. Your Python script runs on the Driver node. When you write
`df.groupBy("account_id").count()`, the Driver figures out the execution plan: how to split
the work across all the machines.

**The Executors:** These are the worker processes running on other machines in the cluster.
The Driver sends each Executor a chunk of the data and instructions: "process these 10 million
rows according to this plan." Each Executor runs its chunk in parallel, sends results back to
the Driver, and the Driver assembles the final answer.

**Partitions:** The data is split into chunks called partitions. Think of 1 billion rows split
into 200 partitions of 5 million rows each. Each partition can be processed by one Executor task.
More partitions = more parallelism. The typical guideline is 128MB–256MB per partition.

### Lazy Evaluation — The Most Important Concept

This is the thing that trips people up the most, so let's go through it carefully.

When you write this in PySpark:
```python
df = spark.read.parquet("transactions/")
df = df.filter(df["amount"] > 50000)
df = df.select("account_id", "amount", "timestamp")
```

After these three lines, **Spark has done absolutely nothing**. It has not read a single byte
from disk. It has not filtered a single row. It has only built a *plan* in memory — a description
of what you want to do.

Only when you call an **action** does Spark actually execute:
```python
df.show()   # This triggers actual computation
```

Now Spark executes the entire plan, but it does so after optimizing. The optimizer (called
Catalyst) looks at the full plan and says: "You want to filter rows AND select only 3 columns.
I can combine these into one pass — while reading from the Parquet file, I will only read the
3 columns you need and skip rows that don't match your filter, without even loading them fully."

This optimization is only possible because Spark waited and saw the complete picture before executing.

If Spark executed eagerly (immediately on each line), step 1 would read ALL columns of ALL rows
from the Parquet file into memory, step 2 would then filter them, step 3 would then drop columns.
Three separate passes, reading far more data than needed.

**The practical rule: transformations are lazy, actions trigger execution.**

**Transformations (lazy — just building the plan):**
- `filter()` or `where()` — keep rows matching a condition
- `select()` — keep only certain columns
- `withColumn()` — add or modify a column
- `groupBy().agg()` — group rows and aggregate (sum, count, avg)
- `join()` — combine two DataFrames on a common key
- `orderBy()` — sort rows
- `repartition(n)` — redistribute data into n partitions (involves a network shuffle)
- `coalesce(n)` — reduce partitions without a full shuffle (no network transfer)

**Actions (trigger actual computation):**
- `show()` — print first N rows to console
- `count()` — return the number of rows
- `collect()` — bring all rows back to the Driver (dangerous on large data)
- `write.parquet("path")` — write results to storage
- `take(n)` — return first n rows as a Python list

### The DAG — What Actually Executes

When you trigger an action, Spark builds a **DAG (Directed Acyclic Graph)** — a flowchart of
the execution steps. This DAG is split into **stages** at "shuffle boundaries."

A shuffle happens when data needs to physically move between machines — like during a `groupBy()`,
`join()`, or `repartition()`. Shuffles are expensive because:
1. Each machine writes its chunk to temporary files on disk
2. Data is transferred across the network to the right machine
3. The receiving machine reads it back from disk

Spark tries to minimize shuffles. The Catalyst optimizer can sometimes reorder operations or
choose different algorithms (like a broadcast join instead of a sort-merge join) to avoid shuffles.

### Broadcast Join — Why It Matters

Imagine joining a 500-million-row transactions table with a 10,000-row merchant-categories lookup table.

Normal join: Spark shuffles the transactions by merchant_id, shuffles the lookup by merchant_id,
so matching rows end up on the same machine. 500 million rows being shuffled across the network —
slow and expensive.

Broadcast join: Since the lookup table is tiny (10,000 rows = maybe 500KB), Spark sends a full
copy of it to every single Executor machine. Each Executor can then do the join locally without
any network transfer. The 500-million-row table never moves.

Spark automatically broadcasts tables smaller than `spark.sql.autoBroadcastJoinThreshold`
(default 10MB). You can also force it explicitly with `broadcast(df)`.

### RDD vs DataFrame — What Changed

**RDD (Resilient Distributed Dataset)** was the original Spark API. It is extremely flexible but
low-level. You write `rdd.map(lambda row: transform_row(row))` and Spark has no idea what you're
doing — it just applies your function to each row. No optimization is possible because Spark
does not understand the structure of your data or your transformation.

**DataFrame** (introduced in Spark 2.x, now the standard) is structured. Spark knows the schema
(column names and types), understands what operations like `groupBy` and `join` mean, and can
apply optimizations automatically. The Catalyst optimizer can rewrite your query, push filters
earlier, choose better join strategies, and eliminate unnecessary work.

In PySpark (Python API), DataFrames are what you always use. RDDs are mostly a historical concept.
You might encounter them when reading old documentation or legacy code.

### PySpark in Practice — What You Did at XenonStack

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, sum as spark_sum, when

spark = SparkSession.builder.appName("FraudAnalysis").getOrCreate()

# Read processed transactions from Azure Data Lake
transactions = spark.read.parquet("abfss://container@storage.dfs.core.windows.net/transactions/")

# Filter to recent transactions only (Spark reads only the relevant Parquet partitions)
recent = transactions.filter(col("txn_date") >= "2023-01-01")

# Aggregate by account: total amount sent, number of transactions
account_summary = recent.groupBy("src_account").agg(
    count("*").alias("txn_count"),
    spark_sum("amount").alias("total_sent")
)

# Flag accounts that sent money more than 50 times or over 500,000 total
flagged = account_summary.filter(
    (col("txn_count") > 50) | (col("total_sent") > 500000)
)

# Write results to Synapse staging table
flagged.write.mode("overwrite").parquet("abfss://container@storage.dfs.core.windows.net/flagged/")
```

None of the filter/groupBy/agg/filter steps execute until the final `.write` call.
At that point, Spark plans the full execution, optimizes it, and runs it across all Executors.

---

## 5. Apache Airflow

### The Problem — Why Cron Jobs Are Not Enough

Before Airflow, data pipeline scheduling was done with cron jobs — lines in a crontab file
that ran shell scripts at fixed times. For example:

```
0 2 * * * /opt/scripts/run_etl.sh     # Run ETL at 2 AM every day
```

This works for simple cases but completely falls apart in real pipelines:

**Problem 1: No dependency awareness.** Step 2 of your pipeline depends on Step 1 finishing.
With cron, you just hope Step 1 was done by the time Step 2 starts. If Step 1 runs long one
day and takes 3 hours instead of 1, Step 2 starts anyway and reads incomplete data.

**Problem 2: No retry logic.** If a task fails at 2 AM, cron does nothing — the failure is silent.
You find out in the morning when the dashboard shows no data, and you have no idea what failed or why.

**Problem 3: No history or visibility.** You cannot easily see: which runs succeeded, which failed,
how long each step took, what the trend has been over time.

**Problem 4: Hard to handle complex flows.** What if Step A and Step B can run in parallel,
and Step C waits for both? Cron has no way to express this.

Airflow solves all of these. It is a workflow orchestrator — it manages what runs, when it runs,
in what order, what to do if it fails, and shows you a complete history.

### DAG — The Core Concept

A DAG (Directed Acyclic Graph) is just a formal name for a workflow with dependencies.

"Directed" means arrows have a direction — Task A must complete before Task B starts.
"Acyclic" means no loops — Task B cannot also be a dependency of Task A (that would create an
infinite loop of "A waits for B, B waits for A").

Think of it as your morning routine modeled as a workflow:

```
wake_up → make_coffee ──┐
wake_up → shower        ├──→ eat_breakfast → leave_home
wake_up → get_dressed ──┘
```

- `make_coffee`, `shower`, and `get_dressed` can all happen in parallel after waking up
- `eat_breakfast` cannot start until all three are done
- `leave_home` happens after breakfast

In Airflow code:
```python
wake_up >> [make_coffee, shower, get_dressed]
[make_coffee, shower, get_dressed] >> eat_breakfast
eat_breakfast >> leave_home
```

Airflow draws this visually in its web UI, shows you which tasks are running (yellow), which
succeeded (green), which failed (red), and lets you manually retry a failed task with one click.

### What You Used It For at XenonStack

Your batch ETL pipeline for wind turbine data had multiple steps:
1. Ingest new sensor data from Kafka to staging area
2. Run Spark job to clean and transform the staging data
3. Run data quality checks (row counts match? no nulls in key fields?)
4. Load clean data into Azure Synapse
5. Trigger Power BI dataset refresh
6. Send success notification to the team

Without Airflow, each step would be a separate cron job hoping the previous one finished.
With Airflow, you define these as a DAG. Step 2 only starts after Step 1 confirms success.
Step 3 only runs if Step 2 produced output. If Step 4 fails, Airflow retries it 3 times with
a 5-minute delay before marking it as failed and sending you a Slack alert.

### Key Airflow Concepts Explained

**Task:** A single unit of work — "run this function," "execute this SQL query," "submit
this Spark job." Tasks are instances of Operators.

**Operator:** The template/class defining what a task does.
- `PythonOperator` — calls a Python function you provide
- `BashOperator` — runs a shell command
- `SparkSubmitOperator` — submits a Spark job to a cluster
- `PythonSensor` — keeps checking until a Python function returns True (e.g., "wait until
  this file exists")

**Scheduler:** The Airflow background process that checks: "is it time to trigger a new run
of this DAG?" It reads the `schedule_interval` you define (`@daily`, `@hourly`, `0 6 * * *`
for 6 AM daily, etc.) and creates a DAG Run when it's time.

**Executor:** How Airflow actually runs tasks. In development, `LocalExecutor` runs tasks as
separate processes on the same machine. In production, `CeleryExecutor` sends tasks to a queue
and multiple worker machines pick them up — a Spark job on one worker, a Python function on
another, all running simultaneously.

**XCom (Cross-Communication):** A simple way for tasks to pass small values to each other.
Task A can push a value (like "I processed 50,000 rows, here's the output file path").
Task B pulls that value and uses it. Important: XComs are for small metadata — file paths,
record counts, status strings — NOT for passing large datasets. Large data should go through
storage (HDFS, Azure Blob, S3).

**Retry Configuration:**
```python
default_args = {
    "retries": 3,               # Try up to 3 times before marking as failed
    "retry_delay": timedelta(minutes=5),  # Wait 5 minutes between retries
    "on_failure_callback": notify_slack,  # Call this function when all retries exhausted
    "sla": timedelta(hours=2),  # Alert if the task hasn't finished in 2 hours
}
```

**Task States:** `scheduled → queued → running → success / failed / upstream_failed / skipped`

`upstream_failed` means: "I didn't even run because a task I depended on failed." This is
important — if Step 2 fails, Steps 3, 4, 5, 6 are marked `upstream_failed` automatically.
You see at a glance that the entire downstream chain was affected.

---

## 6. ArangoDB and Graph Databases

### Why a Normal Database Fails for Fraud Detection

Let's look at UPI transactions in a standard SQL table:

```
txn_id | from_account | to_account | amount | time
-------|--------------|------------|--------|----------
T001   | ACC_A        | ACC_B      | 1000   | 12:00:00
T002   | ACC_B        | ACC_C      | 950    | 12:02:00
T003   | ACC_C        | ACC_A      | 900    | 12:04:00
```

To detect that A → B → C → A forms a suspicious money laundering cycle, you need to "follow
the chain." In SQL, this requires a recursive query or multiple self-joins — you join the
table with itself N times to follow N hops. For 3 hops it looks like this:

```sql
SELECT t1.from_account, t1.to_account,
       t2.to_account as hop2,
       t3.to_account as hop3
FROM transactions t1
JOIN transactions t2 ON t1.to_account = t2.from_account
JOIN transactions t3 ON t2.to_account = t3.from_account
WHERE t3.to_account = t1.from_account  -- came back to start!
```

This works for 3 hops. For 5 hops? 5 self-joins. For 10 hops? The query becomes enormous
and unmanageably slow on millions of transactions. SQL is not designed for this pattern.

### What a Graph Database Does Differently

A graph database stores relationships as first-class data. Instead of tables and rows, everything
is either:

**Vertices (nodes):** The "things" in your domain. Each account is a vertex (node).
```json
{ "_id": "accounts/ACC_A", "_key": "ACC_A", "holder": "Alice", "risk_score": 0.2 }
{ "_id": "accounts/ACC_B", "_key": "ACC_B", "holder": "Bob",   "risk_score": 0.8 }
{ "_id": "accounts/ACC_C", "_key": "ACC_C", "holder": "Carol", "risk_score": 0.5 }
```

**Edges:** The "connections" between things. Each transaction is an edge.
```json
{ "_from": "accounts/ACC_A", "_to": "accounts/ACC_B", "amount": 1000, "time": "12:00" }
{ "_from": "accounts/ACC_B", "_to": "accounts/ACC_C", "amount": 950,  "time": "12:02" }
{ "_from": "accounts/ACC_C", "_to": "accounts/ACC_A", "amount": 900,  "time": "12:04" }
```

Now the database physically stores a pointer from ACC_A's document directly to the edge that
leads to ACC_B. Following the chain is a pointer dereference — nearly instant. There is no JOIN
calculation. The database was literally designed to follow these links at high speed.

Detecting the A → B → C → A cycle in ArangoDB: one query, handles any number of hops,
runs in milliseconds even with millions of transactions:
```aql
FOR v, e, p IN 2..5 OUTBOUND "accounts/ACC_A" GRAPH "fraud_graph"
  FILTER v._id == "accounts/ACC_A"
  RETURN p
```

### AQL (ArangoDB Query Language) — How It Works

AQL is ArangoDB's query language. It is similar to SQL in that it is declarative (you describe
WHAT you want, not HOW to get it), but it has native support for document and graph operations.

**FOR ... IN ... FILTER ... RETURN** is the basic pattern (like SQL's SELECT ... FROM ... WHERE):

```aql
// "Give me all transactions over 50,000 after Jan 1"
FOR tx IN transactions
  FILTER tx.amount > 50000
  FILTER tx.time > "2023-01-01"
  RETURN tx
```

**Graph Traversal:** This is where AQL is powerful in ways SQL is not:

```aql
// "Starting from account ACC_A, follow outgoing transactions for 1 to 3 hops.
//  Tell me every account reachable and how many hops away."

FOR vertex, edge, path IN 1..3 OUTBOUND "accounts/ACC_A"
  GRAPH "fraud_graph"
  FILTER edge.amount > 5000
  RETURN {
    account: vertex._key,
    hops_away: LENGTH(path.edges),
    last_transfer: edge.amount
  }
```

`1..3` = minimum 1 hop, maximum 3 hops deep
`OUTBOUND` = follow edges going away from ACC_A (ACC_A sent money)
`INBOUND` = follow edges coming toward ACC_A (money was sent to ACC_A)
`ANY` = follow edges in either direction

`vertex` = the account node you reached at each hop
`edge` = the transaction edge you followed to get there
`path` = the complete path taken (all vertices and edges from start to current)

### Fraud Patterns You Detected as Graph Queries

**Circular transaction (money laundering cycle):**
A sends ₹10,000 to B → B sends ₹9,500 to C → C sends ₹9,000 back to A.
This circles money to "clean" it. Each transfer takes a small cut as "fees."
In a graph: this is a cycle. The above traversal query with `FILTER v._id == start` finds it.

**Fan-out (smurfing):**
One account sends small amounts to 50 different accounts rapidly in an hour.
This breaks up a large fraudulent sum into small transfers to avoid detection thresholds.
In a graph: one vertex with extremely high out-degree (many outgoing edges) in a short time window.
```aql
FOR acc IN accounts
  LET recent_sent = (
    FOR v, e IN 1..1 OUTBOUND acc GRAPH "fraud_graph"
      FILTER e.time > DATE_SUBTRACT(DATE_NOW(), 1, "hour")
      RETURN e
  )
  FILTER LENGTH(recent_sent) > 20
  RETURN { account: acc._key, transfers_in_last_hour: LENGTH(recent_sent) }
```

**Money mule chain:**
A → B → C → D → E, each passing money forward quickly, with each account taking a small cut.
The original source (A) is trying to hide behind layers of "mules."
In a graph: a linear path with high velocity (each transfer happened within minutes of the previous).

### Why ArangoDB Specifically (Multi-Model)

ArangoDB is not a pure graph database — it is a multi-model database. It handles:
- Documents (like MongoDB — flexible JSON objects, no rigid schema)
- Key-value (fast lookups by ID)
- Graphs (vertices and edges)

All in one system, queried with one language. At XenonStack you stored:
- Account data as documents (flexible, no rigid schema needed)
- Transactions as graph edges (for traversal queries)
- Fraud alert summaries as documents in a separate collection

Without ArangoDB, you would need both MongoDB (for documents) and a separate graph database
(like Neo4j) — two systems to maintain. ArangoDB combined them.

---

## 7. OLTP vs OLAP — The Most Important Distinction in Data Engineering

This concept explains WHY data warehouses exist, WHY you cannot just query production databases
for analytics, and WHY your entire pipeline at XenonStack was necessary.

### OLTP — The Live System (Your Production Database)

OLTP means "Online Transaction Processing." This is the database your application writes to
when things happen in real time. When someone sends a UPI payment, your backend writes a row.

It is designed for:
- **Many small, fast writes** — thousands of transactions per second, each touching 1-2 rows
- **Short, simple queries** — "fetch account ACC_A's balance," "update this one transaction's status"
- **Row-oriented storage** — the entire row (all columns of one record) is stored together,
  because when you fetch a transaction, you need ALL its fields
- **Normalized schema** — data is carefully split into separate tables to avoid duplication.
  Account info in one table, merchant info in another, transaction in a third. JOINs connect them.
  This reduces storage and keeps data consistent (update account name in one place, not everywhere).
- **High concurrency with ACID guarantees** — 1000 users writing simultaneously. Every write
  either fully succeeds or fully rolls back — no partial writes. Strict consistency.

### OLAP — The Analytics System (Azure Synapse)

OLAP means "Online Analytical Processing." This is Azure Synapse — designed for analysis.

It is designed for:
- **Few big reads** — "sum the amount of all transactions this month, grouped by merchant category"
- **Complex aggregations across massive data** — scanning hundreds of millions of rows to compute
  one aggregated answer
- **Columnar storage** — more on this below, but columns are stored together for analytical speed
- **Denormalized schema** — data is pre-joined and sometimes duplicated. One wide table
  with account info, merchant info, and transaction info all together. Slower to write, but
  queries don't need expensive JOINs at query time.
- **Few concurrent writers, many readers** — data is loaded in bulk periodically (or via your
  real-time pipeline), then hundreds of analysts query it simultaneously.

### Why You Cannot Mix OLTP and OLAP

Picture a bank. The OLTP database is the vault — constantly in use, every millisecond.
Thousands of transactions happening simultaneously.

Now imagine an analyst walks in and says: "I need to scan every transaction from the last 5 years
and give me a monthly breakdown by merchant category." That scan locks large portions of the
vault while it works. Meanwhile, real transactions queue up, time out, fail. The live system crashes.

This is not a hypothetical. It has happened at real companies. The rule is: never run heavy
analytical queries on production OLTP databases. Build an OLAP system separately.

At XenonStack:
- **OLTP system:** PostgreSQL / SQL Server — live UPI transactions being written every millisecond
- **Pipeline:** Debezium + Kafka + Spark moves data from OLTP to OLAP (this is the ETL)
- **OLAP system:** Azure Synapse — where analysts and Power BI dashboards query

### Columnar Storage — Why OLAP Is Fast for Analytics

**Row storage (OLTP):**
All columns of Row 1 are stored together, then all columns of Row 2, etc.
```
[txn_id=T001, account=ACC_A, merchant=M1, amount=500, date=2023-01-01, status=SUCCESS, ...]
[txn_id=T002, account=ACC_B, merchant=M5, amount=1200, date=2023-01-01, status=FAILED, ...]
```
When you read one transaction record (`SELECT * FROM transactions WHERE txn_id='T001'`),
you read all its columns in one sequential disk read. Efficient for this use case.

**Column storage (OLAP):**
All values of the `amount` column are stored together, then all values of `date`, etc.
```
AMOUNT column: [500, 1200, 750, 200, 8900, ...]     <-- all amounts, millions of them
DATE column:   [2023-01-01, 2023-01-01, 2023-01-02, ...]
```
When you run `SELECT SUM(amount) FROM transactions WHERE date >= '2023-01-01'`, you only need
to read 2 columns from disk out of 20. In a row store, you would read all 20 columns of every
row just to get the 2 you need. That is 10x more data read from disk — much slower.

Additionally, a column of amounts all in similar ranges compresses extremely well (numbers
like 500, 1200, 750 — all small integers). Columnar storage typically achieves 5-10x compression,
further reducing the data that must be read from disk.

Azure Synapse's **Clustered Columnstore Index** is this columnar storage format. It is the
default for all tables in Synapse and is the primary reason Synapse is fast for analytics.

---

## 8. Azure Synapse Analytics

### What It Is

Azure Synapse is Microsoft's cloud analytics platform. The core component you used is the
**Dedicated SQL Pool** — a distributed data warehouse that uses MPP architecture.

### MPP — What It Actually Means

**MPP = Massively Parallel Processing.**

A regular database server has one CPU (or a few). A query runs on that one server.

An MPP system has many "compute nodes" — multiple independent servers, each with their own CPU
and memory. Your data is distributed (spread) across all these nodes. When you run a query,
every node processes its portion of the data simultaneously, and a central "control node"
assembles the final result.

A query that scans 500 million rows:
- On one server: takes 60 seconds
- On an MPP with 20 nodes (each node has 25 million rows): takes 3 seconds

This is why enterprise data warehouses like Synapse, BigQuery, Snowflake, and Redshift can
handle billions of rows — they parallelize across many machines automatically.

### How Data Is Distributed Across Nodes — The Three Strategies

When you create a table in Synapse, you must decide how to spread its rows across nodes.
This decision has a big impact on query performance.

**HASH distribution — use this for large tables you join frequently:**

You pick one column as the "distribution key." Synapse runs a hash function on each row's
value in that column and assigns the row to a node based on the result. All rows with the
same distribution key value always land on the same node.

Why does this matter? If you frequently join `transactions` and `accounts` on `account_id`,
and both tables are HASH distributed on `account_id`, then all transactions for ACC_A and
ACC_A's account record are on the same node. The join happens locally — no data needs to travel
across the network. Dramatically faster.

Bad choice: a column with very few unique values (like `status` which is only SUCCESS/FAILED/PENDING).
Most rows would have the same hash and land on the same node — "data skew." One node does 90%
of the work while others sit idle.

**ROUND_ROBIN distribution — use this for staging tables:**

Rows are distributed evenly: row 1 to node 1, row 2 to node 2, row 3 to node 3, then back
to node 1 for row 4. No logic — purely even distribution.

Use this for temporary staging tables where you are just loading data before transforming it.
Since you haven't decided what queries will need yet, even distribution is neutral.
Bad for join-heavy queries because matching rows could be on any node — every join requires
network shuffling.

**REPLICATED distribution — use this for small lookup tables:**

Every node gets a complete copy of the entire table. When you join a large transactions table
with a small merchant-categories table, every node already has all merchant categories locally.
No data movement. Only makes sense for small tables (under ~2GB) — for large tables, storing
N copies wastes storage.

### Partitioning in Synapse

Partitioning splits a table's data into physical segments based on a column value, typically date.

If your transactions table is partitioned by month, Synapse stores January data in one physical
file segment, February in another, etc.

When a query filters `WHERE txn_date BETWEEN '2023-01-01' AND '2023-01-31'`, Synapse looks at
the partition metadata and says: "I only need to read the January segment — I can completely
skip the other 23 months of data." This is called **partition pruning**.

For your fraud detection queries that always looked at "last 7 days" or "last 30 days," date
partitioning meant the query only touched recent partitions instead of scanning years of history.

### The Performance Optimization You Did (+20%)

**Before:** Power BI was sending complex analytical queries directly against the raw transactions
table in Synapse (500 million rows, no pre-aggregation).

**After (what you did):**
1. Created pre-aggregated summary tables (daily totals, weekly trends, account-level summaries).
   These contain maybe 100,000 rows instead of 500 million.
2. Changed Power BI to query these summary tables instead of raw data.
3. Made sure the transactions table used HASH distribution on `account_id` (the main join key).
4. Added date partitioning so time-filtered queries skipped irrelevant partitions.

Result: dashboard queries that took 50+ seconds now complete in ~40 seconds. That is roughly
a 20% improvement in query time, which was the metric you reported.

---

## 9. Power BI

### What It Actually Does

Power BI is a business intelligence tool. It connects to data sources, lets you build visual
dashboards and reports (charts, tables, KPI cards, maps), and publishes them so business users
can explore data without writing SQL.

At XenonStack, you connected Power BI to Azure Synapse so that fraud analysts and management
could see live fraud metrics, account risk scores, transaction trends — without needing to
write a single query.

### Import Mode vs DirectQuery — The Key Decision

**Import Mode:**
Power BI makes a copy of the data from Synapse into its own in-memory database (called VertiPaq).
Reports query this local copy — extremely fast because everything is in memory. The downside:
data is only as fresh as the last scheduled refresh. If you refresh every hour, your report
could be showing data from 59 minutes ago.

Best for: historical dashboards, executive summaries, reports where "live" data is not critical.

**DirectQuery Mode:**
No data is copied. Every time you click on a chart or change a filter, Power BI sends a real
SQL query to Synapse in real time and shows you the live result. Data is always completely current.
The downside: every interaction hits the database. If your Synapse queries are slow (even after
optimization), your dashboard interactions will feel slow.

Best for: real-time monitoring, fraud detection dashboards where you need to see what is
happening right now, not what happened an hour ago.

**At XenonStack:**
- Fraud detection dashboard → DirectQuery (you need real-time data — stale data defeats the purpose)
- Management reporting dashboard (weekly trends, monthly summaries) → Import mode (fast, acceptable
  to be a few hours old)

### DAX — Power BI's Formula Language

When you need to compute metrics in Power BI (not just show raw data), you write DAX formulas.

**Measure** — calculated at query time based on filters:
```
Total Fraud Amount = CALCULATE(SUM(transactions[amount]), transactions[is_fraud] = 1)
```
When you filter the dashboard to show only "last 7 days," this measure recalculates automatically.

**Calculated Column** — computed once at data load/refresh, stored with the table:
```
Risk Category = IF(accounts[risk_score] > 0.7, "HIGH", IF(accounts[risk_score] > 0.4, "MEDIUM", "LOW"))
```
This adds a new column to the accounts table based on the risk score.

---

## 10. Star Schema and Data Warehouse Design

### The Star Schema — Why It Is Used

A data warehouse organizes data differently from a transactional database. Instead of many
normalized tables (which require many JOINs), a warehouse uses a star schema: one central
**fact table** surrounded by **dimension tables**.

**Fact table:** Records events/measurements. Each row is one transaction, one sale, one sensor reading.
It is wide (many columns) and very long (hundreds of millions of rows).

**Dimension tables:** Describe the entities involved in the events. Account details, merchant info,
date/calendar information. These are relatively small (thousands of rows) and change infrequently.

```
                 [Dim_Date]
                      |
                      |  (one-to-many: one date, many transactions)
[Dim_Account] --------+-------- [FACT_Transaction] -------- [Dim_Merchant]
                      |
                  [Dim_Region]
```

**Fact table columns:**
- `transaction_id` (primary key)
- `account_key` (foreign key to Dim_Account)
- `merchant_key` (foreign key to Dim_Merchant)
- `date_key` (foreign key to Dim_Date)
- `amount` (the measurable fact)
- `is_fraud` (another measurable fact)

**Dim_Account columns:**
- `account_key` (surrogate key)
- `account_id` (original ID from source)
- `holder_name`
- `account_type`
- `risk_score`

**Why is this better for analytics?**
When Power BI builds a chart "show total fraudulent amount by merchant category this month":
1. Filter Dim_Date for this month → get date_keys
2. Filter Fact_Transaction by those date_keys AND is_fraud=1 → get matching transactions
3. Join with Dim_Merchant to get merchant categories
4. Group and sum the amount

Simple joins, clean structure. Power BI auto-detects star schemas and builds relationships
between tables automatically.

### Snowflake Schema

Snowflake is the normalized version of a star schema. Instead of Dim_Account being one flat table,
it might be split into Dim_Account → Dim_City → Dim_Region → Dim_Country.

More normalized = less data duplication = smaller storage = but more JOINs at query time.

For analytics, the extra JOINs make queries slower. The storage savings are usually not worth it.
Star schema wins for most real-world analytics. Snowflake schema exists and you might hear about it.

---

## 11. ETL vs ELT — Two Approaches to Pipeline Design

**ETL (Extract → Transform → Load):** You transform data before it enters the warehouse.
- Extract: pull data from source (Debezium event or Kafka message)
- Transform: Spark cleans it, reshapes it, enriches it, applies business logic
- Load: write the clean, final result into Synapse

**ELT (Extract → Load → Transform):** You dump raw data into the warehouse first, then
use the warehouse's own SQL to transform it.
- Extract: pull raw data from source
- Load: write raw data into a staging area in Synapse
- Transform: run SQL `CREATE TABLE clean_transactions AS SELECT ... FROM staging WHERE ...`

**When to use ETL with Spark:**
- Complex transformations that are hard to express in SQL (parsing binary formats, ML features,
  complex business logic spanning many data sources)
- When you need to mask or encrypt sensitive data (PII like account numbers) before it enters
  long-term storage
- Very large datasets that benefit from Spark's distributed processing before writing to the warehouse

**When to use ELT with SQL:**
- Transformations are SQL-expressible — filtering, joining, aggregating
- You want the transformation logic close to the data (in the warehouse, easy to inspect)
- Cloud warehouses (Synapse, BigQuery, Snowflake) are powerful enough to do the transformation

At XenonStack you used ETL — Spark handling complex parsing of sensor data and multi-source joins
before loading clean results into Synapse.

---

## 12. Data Quality — Why It Matters and What You Checked

A pipeline can move data perfectly and still deliver garbage if the source data is bad.
Data quality checks are safety nets throughout the pipeline.

### Types of Checks (with Real Examples from Your Context)

**Completeness:** Are required fields present?
A UPI transaction without an amount or account ID is useless and will crash downstream processing.
Check: `SELECT COUNT(*) FROM staging_transactions WHERE amount IS NULL` — should return 0.

**Accuracy / Cross-validation:** Does the data make mathematical sense?
After loading a batch into Synapse: does the sum of amounts match the source?
If your ETL loaded 1 million rows from source but Synapse only has 999,000, something was dropped.

**Schema validation:** Did the source database's structure change unexpectedly?
Your pipeline assumes transactions have 15 specific columns. If the source team adds or renames
a column, your pipeline breaks. Schema Registry (Avro schemas) catches this before it causes damage.

**Timeliness / SLA:** Is data arriving when it should?
Your fraud detection system is useless if the Debezium pipeline is 3 hours delayed.
Define: "transaction events must appear in Synapse within 5 minutes of the original write."
Monitor this with alerts — if the lag exceeds 5 minutes, page the on-call engineer.

**Deduplication:**
Because Kafka provides at-least-once delivery, the same event can arrive twice (after a crash
and restart). If you INSERT both copies, you have duplicate transactions — all your fraud counts
and sum calculations are wrong.

The fix is **idempotent writes** using UPSERT (also called MERGE in SQL):
```sql
MERGE INTO transactions AS target
USING staging AS source ON target.txn_id = source.txn_id
WHEN MATCHED THEN UPDATE SET amount = source.amount, status = source.status
WHEN NOT MATCHED THEN INSERT (txn_id, amount, status, ...) VALUES (source.txn_id, ...)
```

Running this twice with the same source data produces the same result as running it once.
That is what "idempotent" means — safe to apply multiple times.

---

## 13. What Each Resume Bullet Actually Meant — Plain English

| What your resume says | What was actually happening |
|---|---|
| "Real-time ETL pipelines using Debezium and Azure services" | Debezium read the PostgreSQL transaction log and streamed each new transaction as a Kafka message within milliseconds of it being written. Azure Stream Analytics or Spark consumed those messages and loaded them into Synapse. |
| "Reducing data latency and improving system availability" | Changed from batch (query DB every hour, get data 1 hour stale) to CDC streaming (events appear in Synapse within seconds). System availability improved because Debezium + Kafka is fault-tolerant — if Synapse is briefly down, Kafka holds the events and they're processed when it recovers. |
| "UPI fraud detection leveraging ArangoDB for pattern-based anomaly detection" | Stored each account as a graph node and each transaction as a directed edge. Ran AQL graph traversal queries to find cycles (circular money flow), fan-out patterns (smurfing), and high-velocity chains (money mule networks). |
| "Kafka-based data ingestion for wind turbine sensor data" | Wind turbine sensors produced millions of data points per minute. Kafka was the high-throughput buffer that absorbed the entire stream reliably. Even if Spark processing fell behind, no sensor data was lost — it waited in Kafka until Spark caught up. |
| "Power BI dashboards with Azure Synapse, boosting analytics performance by 20%" | Connected Power BI to Synapse using DirectQuery for live data. Pre-aggregated the most-queried summary data into smaller tables. Fixed the HASH distribution on transaction tables so joins didn't shuffle data across nodes. Added date partitioning. Together these reduced dashboard query times by ~20%. |
| "Reducing integration time by 20%" | Standardized data contracts (agreed on schema, data types, naming) with source teams upfront. Added automated data quality checks in the pipeline that caught errors early. Built reusable pipeline templates so adding a new data source took days instead of weeks. |

---

*Last updated: August 2026*

# XenonStack Interview Questions & Detailed Answers
> Role: Data Engineer | Aug 2022 – Sep 2023 | XenonStack, Mohali
> Written with full explanations — so you actually understand the answer, not just memorize it

---

## Section 1 — ETL Pipelines and Debezium (CDC)

---

**Q1. What is Debezium, and why did you use it at XenonStack?**

Debezium is an open-source Change Data Capture (CDC) tool. The problem it solves is this:
we needed to know about every UPI transaction the moment it was written to the source database —
not 10 minutes later, not 1 hour later. The obvious approach would be to poll the database
every few seconds ("give me everything updated since last time I checked"), but polling has
real problems: you miss deletes entirely because a deleted row disappears, you can miss inserts
that happened between two polls, and you hammer the production database constantly.

Debezium works completely differently. Every database like PostgreSQL keeps an internal change log
called the WAL (Write-Ahead Log). Before the database writes anything to disk, it records the
change in this log. Debezium reads this log in real time — like a passive observer reading a
newspaper. Every INSERT, UPDATE, and DELETE appears in the log in exact order. Debezium converts
each one into a message and publishes it to Apache Kafka. No polling, no missed events, no extra
load on the production database.

At XenonStack, we used this to feed the fraud detection system. A UPI transaction is written
at 11:00:00 PM, Debezium sees it in the WAL, publishes it to Kafka by 11:00:02 PM, and the
fraud detection system is analyzing it by 11:00:05 PM. Previously with batch ETL, we would
not have detected anything until the next morning.

---

**Q2. Walk me through the full real-time ETL pipeline you built.**

The pipeline had several stages:

**Stage 1 — Capture (Debezium):**
The source database is PostgreSQL — the live production database where UPI transactions land.
Debezium connectors monitored specific tables (transactions, accounts). The moment any row
was inserted or changed, Debezium captured the change from the WAL and published it as a
JSON message to a Kafka topic (e.g., `upi-transactions`).

**Stage 2 — Transport (Apache Kafka):**
Kafka acted as a reliable, durable buffer. It stored every message on disk, so if any downstream
consumer crashed or fell behind, no data was lost — the consumer could resume from exactly where
it left off. Multiple consumers could read the same stream independently: one for fraud detection,
one for loading into the data warehouse, one for archiving to Azure Data Lake.

**Stage 3 — Processing (Azure Stream Analytics or Spark Streaming):**
Consumers read Kafka messages, applied transformations (type corrections, enrichment with account
data, computing derived fields), and prepared records for loading.

**Stage 4 — Load (Azure Synapse / SQL Pool):**
Clean, transformed records were upserted into Synapse tables using the transaction ID as the
idempotency key — so even if Kafka delivered the same event twice, we would not get duplicates.

**Stage 5 — Visualization (Power BI):**
Power BI connected to Synapse in DirectQuery mode, so the fraud dashboard always showed live data.

The key improvement over the old approach was data latency. Previously, a nightly batch job
meant data was 8–18 hours stale. After the Debezium pipeline, data latency was under 30 seconds.

---

**Q3. What is the WAL (Write-Ahead Log) and why is it important for CDC?**

The Write-Ahead Log is PostgreSQL's internal transaction log. Before PostgreSQL writes any change
to the actual data files on disk, it first writes a record of that change to the WAL. The entry
says something like: "I'm about to insert a row into the transactions table with these values."

The primary purpose of the WAL is crash recovery — if PostgreSQL crashes mid-operation, on
restart it reads the WAL and replays or rolls back incomplete operations. The data stays consistent.

Debezium leverages this through PostgreSQL's "logical decoding" feature — a built-in PostgreSQL
capability that was specifically designed to let external tools read the WAL as a stream of
human-readable events. Debezium registers as a logical replication slot and PostgreSQL keeps
the relevant WAL segments available for it to read, converting the binary log entries into
structured change events that Debezium publishes to Kafka.

The key insight: this mechanism was not hacked together — it is officially supported by PostgreSQL
and designed for this exact use case. That is why it is reliable.

---

**Q4. What is the difference between batch ETL and real-time ETL? When would you choose each?**

Think of the difference as doing laundry once a week versus washing a shirt the moment you
spill something on it.

**Batch ETL** runs on a schedule — every hour, every night, every Monday morning. It collects
all the changes since the last run and processes them together. Simpler to build, easier to
debug (you have a fixed dataset to work with), and efficient when you process large volumes at once.

Use batch ETL when:
- The business can tolerate stale data. Monthly financial reports, weekly summaries, HR analytics
  — these do not need second-by-second freshness.
- The source system cannot support real-time extraction (some older databases have no CDC support).
- The transformation logic is extremely complex and easier to reason about in a batch.

**Real-time ETL** processes each event as it arrives — within seconds. More complex infrastructure
(Kafka, Debezium, streaming processors), harder to debug (you're dealing with an infinite stream
of events, not a file you can re-read), but essential when the business outcome depends on freshness.

Use real-time ETL when:
- Decisions must be made immediately. Fraud detection — a transaction flagged 3 hours later is
  3 hours too late. The money is gone.
- You need to react to events, not just report on them. Triggering an alert, blocking a transaction,
  sending a notification — these cannot wait for a nightly batch.
- Real-time dashboards for operations teams who are watching live systems.

At XenonStack, we used both: real-time for the fraud detection pipeline (Debezium + Kafka),
and batch (Spark + Airflow) for the heavy analytical processing of historical sensor data from
wind turbines where latency of a few hours was acceptable.

---

**Q5. What challenges did you face with Debezium and how did you handle them?**

**Challenge 1 — Initial snapshot on a large table:**
When we first set up Debezium on the transactions table that already had 50 million rows, it
needed to snapshot all existing data before streaming new changes. This snapshot took several hours.
During that time, Kafka was being flooded with historical records, which affected consumer lag
on downstream systems. We handled this by running the initial snapshot during a maintenance window
and using `snapshot.mode=schema_only` for tables where the downstream system already had the
historical data, so only new changes needed to be streamed.

**Challenge 2 — Schema changes in the source:**
The source team added a new column to the transactions table. Debezium's next message had a
new field that our consumers were not expecting. Without a schema registry, this would have
crashed consumers that expected a fixed structure. We used Confluent Schema Registry with Avro
schemas. When Debezium detected the schema change, it registered the new schema version.
Consumers used the schema ID embedded in each message to deserialize correctly, and old consumers
continued working with the old schema version.

**Challenge 3 — Duplicate events after restart:**
Kafka provides at-least-once delivery. After a Debezium restart, it might re-deliver the last
few events before it crashed. Our consumers had to handle this. We made all writes to Synapse
idempotent — using MERGE (UPSERT) with the transaction ID as the key. Processing the same event
twice produces the same result as processing it once.

**Challenge 4 — Replication slot lag:**
PostgreSQL keeps WAL segments available for Debezium to read. If Debezium falls behind (e.g.,
it's paused for maintenance), PostgreSQL cannot clean up old WAL segments, and disk usage on
the database server grows. We set a monitoring alert on the replication slot lag and ensured
Debezium was always running or the slot was cleaned up if we needed to take Debezium down for
more than a brief window.

---

## Section 2 — Apache Kafka

---

**Q6. Why did you use Kafka for the wind turbine sensor pipeline?**

Wind turbines have many sensors — rotation speed, blade angle, temperature, voltage, vibration.
Each sensor sends data points every second. With a farm of dozens of turbines, that is potentially
millions of data points per minute flowing in continuously.

Kafka was chosen for several reasons:

**Throughput:** Kafka can handle millions of messages per second. A standard Kafka cluster
handles this comfortably where a traditional message queue like RabbitMQ would struggle at
this scale.

**Durability:** Kafka persists every message to disk with replication. If the downstream Spark
processing falls behind during a planned maintenance window, sensor data keeps flowing into Kafka
and nothing is lost. When processing resumes, it catches up.

**Replayability:** Kafka keeps messages for a configured retention period (e.g., 7 days). If
we discovered a bug in our Spark transformation job, we could fix it and reprocess the last
7 days of sensor data by resetting consumer offsets. You cannot do this with a queue that
deletes messages after consumption.

**Multiple consumers:** The same sensor stream could be consumed by multiple systems independently:
one for real-time anomaly detection (is the turbine behaving abnormally right now?), one for
bulk Spark processing (batch analytics), one for archiving to Azure Data Lake. All read the same
Kafka topic without interfering with each other.

---

**Q7. Explain Kafka topics, partitions, consumer groups, and offsets in plain language.**

These four concepts work together, so let me explain them as a connected system.

**Topics** are named streams. You create a topic called `turbine-sensor-data` for all sensor
readings and another called `upi-transactions` for transaction events. They are logically
separate — subscribing to one does not give you the other.

**Partitions** are how a topic achieves parallel throughput. Every topic is split into N
partitions. Each partition is an ordered, append-only log of messages. If `turbine-sensor-data`
has 10 partitions, 10 machines (or 10 threads) can write to it simultaneously and 10 consumers
can read from it simultaneously. More partitions = more throughput.

When a producer sends a message with a "key" (e.g., turbine ID), Kafka hashes the key to decide
which partition it goes to. All messages with the same turbine ID land in the same partition —
guaranteeing that all readings from turbine #7 are in order relative to each other.

**Consumer groups** are how you scale reading. A consumer group has multiple consumer instances.
Kafka assigns partitions to consumers: if you have 10 partitions and 5 consumer instances in
a group, each consumer gets 2 partitions. They work in parallel. If a consumer crashes, Kafka
reassigns its partitions to the surviving consumers — no message is lost.

A completely different application that also wants the data creates its own consumer group and
reads all 10 partitions independently. The two groups never interfere. This is how your data
warehouse loader and your fraud detection system can both consume the same Kafka topic at the
same time.

**Offsets** are message position numbers within a partition. Message 0, 1, 2, 3... Each consumer
tracks which offset it has processed. When a consumer successfully processes message 500, it
"commits offset 500" — tells Kafka "I'm done with 500." If it crashes and restarts, it asks Kafka
where it left off and resumes from 501. This is how Kafka guarantees no data is lost or reprocessed
unnecessarily after a failure.

---

**Q8. How do you ensure no data loss in a Kafka pipeline?**

There are three layers to think about: the producer side, the Kafka cluster itself, and the
consumer side.

**Producer side:**
Use `acks=all`. When a producer sends a message with `acks=all`, Kafka only sends a "success"
acknowledgment after the partition leader AND all in-sync follower replicas have written the
message to disk. If the leader crashes immediately after, a follower takes over and has the
message. Without `acks=all`, if you use `acks=1` (only leader confirms), and the leader crashes
before replicating to followers, the message is gone.

**Kafka cluster:**
Set `replication.factor=3` for all important topics. This means 3 copies of each partition exist
across 3 different broker machines. A single machine failure does not cause data loss.
Also set `min.insync.replicas=2` — Kafka will reject a write if fewer than 2 replicas are
available, rather than accepting a write that has no redundancy.

**Consumer side:**
Set `enable.auto.commit=false`. With auto-commit, Kafka commits the offset automatically every
few seconds, regardless of whether your processing code actually succeeded. If your code crashes
after the auto-commit but before finishing, Kafka thinks the message was processed and will not
give it to you again — data loss. With manual commit, you only commit the offset after your code
confirms success.

Make your consumer **idempotent** — able to safely process the same message twice. Because
Kafka guarantees at-least-once delivery (not exactly-once, by default), a consumer might
occasionally receive the same message twice after a restart. Use UPSERT (INSERT or UPDATE based
on primary key) instead of plain INSERT when writing to databases.

---

**Q9. What is the difference between Kafka and RabbitMQ? Why did you choose Kafka?**

They solve different problems, and understanding the difference shows you understand both.

**RabbitMQ is a message broker.** It is like a postal service — a message is sent, delivered
to one recipient, and deleted. The broker "routes" messages based on exchange rules. It is
designed for task queues: "here is a job, one worker should pick it up and do it, then it's done."
Messages are pushed to consumers (broker sends to you when ready).

**Kafka is a distributed log.** It is more like a newspaper archive. Every edition is stored
permanently (for a configured retention period). Multiple different readers can read the same
edition independently, at different times. Consumers pull messages at their own pace. Messages
are not deleted after consumption. You can replay from any point in history.

For our use cases, Kafka was the right choice because:

1. **Multiple consumers needed the same data independently.** The fraud detection system, the
   Synapse loader, and the Data Lake archiver all needed the same transaction events. In RabbitMQ,
   a message delivered to Consumer A is gone for Consumer B. In Kafka, all three consumer groups
   read the same topic independently.

2. **Replayability was critical.** If we found a bug in fraud detection logic, we could replay
   the last N days of Kafka data to reprocess transactions with the fixed logic. With RabbitMQ,
   those messages are gone once consumed.

3. **Scale.** Millions of sensor readings per minute from wind turbines. Kafka handles this at
   commodity hardware scale. RabbitMQ at this throughput requires significant tuning and more
   expensive infrastructure.

RabbitMQ would have been fine for a simple task queue — like "send this email" or "process this
payment webhook." For data streaming and event sourcing at our scale, Kafka was the right tool.

---

## Section 3 — Apache Spark and PySpark

---

**Q10. What types of data processing did you do with Spark at XenonStack?**

We used Spark for batch processing of large-scale datasets — things that were too large for
single-machine Python processing.

**For the wind turbine pipeline:**
Raw sensor data from Kafka was archived to Azure Data Lake as Parquet files. Spark jobs ran
on this data daily (orchestrated by Airflow) to:
- Clean and validate sensor readings (filter out obviously corrupted readings, handle missing values)
- Join sensor readings with turbine metadata (turbine ID → location, model, installation date)
- Compute aggregated statistics (hourly averages, min/max values per sensor per turbine)
- Detect anomalies based on statistical thresholds (readings more than 3 standard deviations
  from the historical mean for that sensor)
- Write clean, aggregated results to Azure Synapse for Power BI dashboards

**For the fraud detection pipeline:**
Historical transaction data was processed by Spark to compute baseline behavior profiles per account:
- What is the typical transaction frequency for this account?
- What is the typical transaction amount range?
- Which merchants does this account normally interact with?

These profiles were stored back in Synapse and used as context for the real-time fraud rules
(if a transaction deviates significantly from the account's baseline, flag it).

---

**Q11. Explain lazy evaluation in Spark. Why does it matter?**

When you write PySpark code like `df.filter(col("amount") > 50000).select("account_id", "amount")`,
Spark does not execute anything. It builds a description of what you want — a query plan in memory.

Only when you call an action — like `df.show()`, `df.count()`, or `df.write.parquet(...)` —
does Spark actually execute the plan.

Why is this a big deal? Because Spark's optimizer (called Catalyst) gets to see the entire plan
before executing. It can then make optimizations that would not be possible if it executed eagerly:

**Example — Predicate Pushdown:**
Your Parquet files store data partitioned by date. You have `df.filter(col("date") == "2023-01-15")`.
If Spark executed immediately when you called filter, it would read ALL the Parquet files and
then filter in memory. But because it waits and sees the full plan, the Catalyst optimizer
realizes: "This filter is on the partition key. I can tell the Parquet reader to only open
the files for 2023-01-15 and skip everything else." Dramatic reduction in data read from disk.

**Example — Column Pruning:**
You select only 3 columns out of 20. Parquet is a columnar format — each column is stored
separately. If Spark knew you only needed 3 columns before reading, it would only read those
3 column files from disk. Without lazy evaluation and a global view of the plan, it might read
all 20 and throw away 17 later.

**Example — Combining Transformations:**
`df.filter(col("a") > 1).filter(col("b") > 2)` — Catalyst merges these into a single filter
pass instead of two separate passes. One scan of the data instead of two.

In practice: lazy evaluation is why PySpark code that looks slow (many chained transformations)
can execute very efficiently. The optimization happens automatically under the hood.

---

**Q12. What is the difference between an RDD, a DataFrame, and a Dataset?**

These are three different abstractions for distributed data in Spark, and they represent an
evolution in the API.

**RDD (Resilient Distributed Dataset) — the original:**
An RDD is just a distributed collection of objects. Spark knows nothing about the structure of
those objects. You work with it using low-level functional operations: `map`, `filter`, `reduce`,
`flatMap`. You write Python lambdas, and Spark applies them row by row.

The problem: Spark cannot optimize. If you write `rdd.map(lambda row: (row[2], row[5]))`,
Spark has no idea what you're doing — it just runs your lambda. No Catalyst optimization,
no columnar reading, no automatic filter pushdown. You get raw distributed computation but
no query intelligence.

**DataFrame — the structured evolution:**
A DataFrame has a named schema — Spark knows the column names and data types. Instead of
opaque Python objects, you have a structured table. Operations like `filter`, `groupBy`, `join`
have well-defined semantics that the Catalyst optimizer understands.

With a DataFrame, when you write `df.filter(col("amount") > 50000)`, Catalyst knows exactly
what this means and can optimize it — push the filter to the data source, combine it with other
operations, use statistics to skip entire partitions.

DataFrames are what you always use in PySpark. They are faster, simpler, and automatically
optimized compared to RDDs.

**Dataset — typed DataFrames (JVM only):**
Datasets are only available in Scala and Java (not Python). They are DataFrames with compile-time
type safety — you get IDE autocompletion and type errors at compile time, not runtime. In Python,
you don't have this concept because Python is dynamically typed. When someone says "Dataset" in
a PySpark context, they usually mean DataFrame.

**For your interview:** Say you always used DataFrames. RDDs are the underlying implementation
detail but you rarely work with them directly. Understanding the difference shows maturity.

---

**Q13. What is a broadcast join in Spark and when would you use it?**

A broadcast join is an optimization technique for joining a large table with a small table.

In a normal join, Spark needs both tables' data on the same machine to match rows. If you join
`transactions` (500 million rows) with `merchant_categories` (1,000 rows), Spark would:
1. Shuffle the transactions by merchant_id — 500 million rows moving across the network
2. Shuffle merchant_categories by merchant_id
3. Perform the join where matching rows are co-located

That first step (shuffling 500 million rows) is the expensive part — massive network transfer.

In a broadcast join, Spark recognizes that `merchant_categories` is tiny (maybe 100KB). Instead
of shuffling, it sends a complete copy of `merchant_categories` to every Executor node. Now every
node can join its local portion of transactions with its local copy of merchant_categories.
No shuffling of the large table needed at all.

Spark automatically uses broadcast join when a table is smaller than the configured threshold
(`spark.sql.autoBroadcastJoinThreshold`, default 10MB). You can also force it:

```python
from pyspark.sql.functions import broadcast
result = transactions.join(broadcast(merchant_categories), on="merchant_id")
```

**When to use:** Any join where one table is significantly smaller than the other and fits in
executor memory (typically under a few hundred MB to be safe). Classic examples: joining with
a lookup/reference table, a dimension table in a star schema, or a small mapping table.

**When NOT to use:** If the small table is actually not that small (many GB), broadcasting it
to every executor wastes memory and can cause out-of-memory errors. Test with the actual data sizes.

---

**Q14. How did you handle skewed data in Spark jobs?**

Data skew happens when the data is unevenly distributed across partitions. For example, if you
group transactions by account and 80% of your transactions belong to 3 accounts (maybe test
accounts used for load testing), three partitions would have most of the data while hundreds
of others are nearly empty. Three tasks would take 100x longer than the others, and your job
cannot finish until all tasks complete.

**Approach 1 — Salting for aggregations:**
Add a random number (the "salt") to the skewed key before grouping, then group, then remove the salt
and do a final aggregation.

```python
# Before: heavily skewed groupBy
df.groupBy("account_id").agg(sum("amount"))

# After: salted to distribute load
import random
from pyspark.sql.functions import concat, lit, col, floor, rand

# Step 1: Add random salt 0-9 to the key
df_salted = df.withColumn("salted_key", concat(col("account_id"), lit("_"), (rand()*10).cast("int").cast("string")))

# Step 2: First-level aggregation (now 10x more groups, evenly distributed)
partial = df_salted.groupBy("salted_key").agg(sum("amount").alias("partial_sum"))

# Step 3: Extract original key and do final aggregation
from pyspark.sql.functions import split
final = partial.withColumn("account_id", split(col("salted_key"), "_")[0]) \
               .groupBy("account_id").agg(sum("partial_sum"))
```

**Approach 2 — Broadcast join to avoid skewed shuffle join:**
If the skew is caused by a join on a skewed column, and the other table is small, use a broadcast
join so the large skewed table never gets shuffled.

**Approach 3 — Filter and treat separately:**
Identify the "heavy hitter" keys (the 3 skewed accounts), process them separately with a
different strategy, and union the results with the normally processed data.

**Approach 4 — Repartition:**
If partitions are very uneven in size (not due to a groupBy but just from how data was read),
`df.repartition(200)` redistributes rows randomly and evenly across 200 partitions before
the expensive operation.

---

## Section 4 — Apache Airflow

---

**Q15. How did you use Apache Airflow at XenonStack?**

I used Airflow to orchestrate the batch data pipeline for the wind turbine sensor data.
The pipeline had multiple steps that needed to run in a specific order, with dependencies
between them, on a daily schedule.

Without Airflow, each step would be a separate cron job and I'd be manually managing the
"Step 2 shouldn't start until Step 1 is done" logic. If Step 2 failed at 3 AM, I'd find out
in the morning when the dashboard showed no data.

With Airflow, I defined the entire workflow as a DAG in Python code. The flow was:
1. Check that new sensor data has arrived in Azure Data Lake (a Sensor task — waits until true)
2. Run the Spark transformation job (SparkSubmitOperator)
3. Run data quality validation checks (PythonOperator — verify row counts, check for nulls)
4. If quality checks pass: load into Azure Synapse (PythonOperator)
5. Trigger Power BI dataset refresh (HTTP call)
6. Send success notification to the team (SlackOperator)

The key benefits in practice:
- If the Spark job failed (Step 2), Steps 3–6 were automatically skipped
- Spark was configured to retry up to 3 times with a 10-minute delay before failing
- I could see the complete run history in Airflow's web UI — every run, which tasks succeeded,
  how long each took, what the error message was when something failed
- The DAG code lived in version control — I could review the entire pipeline logic in a code review

---

**Q16. What is a DAG in Airflow and what does "Directed Acyclic Graph" actually mean?**

A DAG in Airflow is a workflow — a collection of tasks with defined dependencies.

"Directed" means the arrows between tasks have direction — Task A must complete before Task B
starts. The direction is the dependency order.

"Acyclic" means no loops. Task A cannot depend on Task B if Task B also depends on Task A.
That would create a deadlock: A is waiting for B, B is waiting for A, nothing ever runs.
Airflow enforces that the dependency graph never has cycles.

"Graph" just means nodes (tasks) connected by edges (dependencies).

In practice, you write it in Python like this:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime, timedelta

default_args = {
    "retries": 3,
    "retry_delay": timedelta(minutes=10),
    "on_failure_callback": alert_slack,
}

with DAG(
    "sensor_data_pipeline",
    start_date=datetime(2023, 1, 1),
    schedule_interval="0 6 * * *",  # Run at 6 AM every day
    default_args=default_args,
) as dag:

    wait_for_data = FileSensor(task_id="wait_for_data", filepath="/data/turbine/daily/")
    run_spark = SparkSubmitOperator(task_id="run_spark", application="jobs/transform.py")
    validate = PythonOperator(task_id="validate", python_callable=run_quality_checks)
    load_synapse = PythonOperator(task_id="load_synapse", python_callable=load_to_synapse)

    wait_for_data >> run_spark >> validate >> load_synapse
```

The `>>` operator defines the dependency: left task must complete before right task starts.

Airflow's scheduler reads this file, and at 6 AM every day, it creates a "DAG run" and starts
executing the first task. The web UI shows you a color-coded graph: green for success, red for
failed, yellow for running, grey for not started yet.

---

**Q17. How do you handle failures in Airflow?**

There are several layers of failure handling:

**Automatic retries:**
Configure `retries=3` and `retry_delay=timedelta(minutes=5)` in `default_args`. If a task
fails, Airflow waits 5 minutes and retries. It does this up to 3 times. Only if all 3 retries
fail does it mark the task as "failed" and trigger the failure callback.

This handles transient failures — network blips, temporary database unavailability, brief API
timeouts — without requiring human intervention.

**Failure callbacks:**
`on_failure_callback` is a Python function that Airflow calls when a task exhausts all retries
and is marked failed. You use this to send a Slack message, page the on-call engineer, or
create a PagerDuty alert. At XenonStack we sent Slack messages that included the DAG name,
task name, execution date, and a link to the Airflow log so the engineer could click directly
to the error.

**SLA misses:**
Some tasks are latency-sensitive. For the fraud detection pipeline, we needed data in Synapse
within 5 minutes of transactions being written. We set `sla=timedelta(minutes=5)` on the load
task. If the task had not completed within 5 minutes of its scheduled time, Airflow triggered
an SLA miss callback — a separate alert that says "the task ran but took too long, investigate."

**Upstream failures:**
When Task A fails, all tasks that depend on A are automatically marked `upstream_failed`.
They do not even try to run. This prevents a cascade of misleading errors — you only get alerted
about the root cause, not every downstream consequence.

**Manual recovery:**
In Airflow's UI, you can manually "clear" a failed task run. This resets it to pending and
re-queues it for execution. You can also trigger a "backfill" — manually execute a DAG run for
a past date that was missed or failed.

---

## Section 5 — ArangoDB and Graph Databases

---

**Q18. Why did you choose ArangoDB for fraud detection instead of a relational database?**

The core issue is the nature of fraud patterns. Fraud in UPI transactions often involves networks
of accounts working together — not just individual suspicious transactions in isolation.

The patterns we needed to detect were:
- Circular money flow: A sends to B, B sends to C, C sends back to A (layering to obscure the source)
- Fan-out: One account rapidly sends small amounts to 50 different accounts (smurfing — breaking
  a large fraudulent sum into amounts below detection thresholds)
- Money mule chains: A → B → C → D → E, each account passing money forward and taking a cut,
  making the origin hard to trace

All of these are fundamentally graph problems — they require following chains of relationships
across multiple steps.

In a relational database, to find a chain A → B → C → A, you would need a recursive SQL query
or multiple self-joins on the transactions table. For 3 hops, this is manageable. For 5 hops,
it is complex and slow. For 8 hops across 100 million transactions, it becomes impractically
slow — you're doing many large table scans and joining the result with itself repeatedly.

ArangoDB stores transactions as graph edges with physical pointers between connected accounts.
Following a chain of 5 hops requires 5 pointer dereferences — nearly instant. The same pattern
that requires 8 self-joins in SQL requires one AQL traversal query in ArangoDB and runs in milliseconds.

Additionally, ArangoDB is a multi-model database — it handles documents, key-value, and graphs
in one system. We stored account profiles as documents (flexible JSON, no rigid schema required)
and transactions as graph edges. One database, one query language (AQL), for everything.

---

**Q19. Explain how graph traversal works and how it helps detect fraud.**

In ArangoDB, data exists as a graph: vertices (accounts) connected by edges (transactions).
Each edge goes from the sender account to the receiver account and carries the transaction data
(amount, timestamp, status) as properties.

When we want to detect suspicious patterns for account ACC_A, we "traverse" the graph starting
from ACC_A's vertex and follow edges.

**Finding circular money flow:**
Start at ACC_A, follow outgoing edges (money sent) for up to 5 hops, check if any path leads
back to ACC_A:

```aql
FOR vertex, edge, path IN 2..5 OUTBOUND "accounts/ACC_A"
  GRAPH "fraud_graph"
  FILTER vertex._id == "accounts/ACC_A"
  FILTER edge.time > DATE_SUBTRACT(DATE_NOW(), 24, "hours")
  RETURN path
```

This says: "Starting from ACC_A, follow money-out paths 2 to 5 steps deep. If you arrive back
at ACC_A, return that path." A result means a circular money flow exists in the last 24 hours.

**Finding fan-out (smurfing):**
Count how many different accounts ACC_A sent money to in the last hour:

```aql
FOR vertex, edge IN 1..1 OUTBOUND "accounts/ACC_A"
  GRAPH "fraud_graph"
  FILTER edge.time > DATE_SUBTRACT(DATE_NOW(), 1, "hours")
  COLLECT WITH COUNT INTO transfer_count
RETURN transfer_count
```

If this returns a number above our threshold (say, 20), we flag ACC_A for review.

**What makes this fast:**
ArangoDB stores a physical pointer (memory address) on each edge pointing to the target vertex.
Traversing one hop is literally following a pointer in memory. For SQL to do the equivalent,
it has to perform a JOIN — look up a value in an index across millions of rows. The pointer
dereference is orders of magnitude faster for multi-hop traversals.

---

**Q20. What is anomaly detection and how did you implement it?**

Anomaly detection is identifying data that deviates significantly from normal or expected behavior.
In fraud detection, "normal" means "how this specific account typically behaves" or "how UPI
transactions typically look across the whole population."

I implemented three complementary approaches:

**1. Rule-based velocity detection (simplest):**
Define thresholds based on business knowledge. "More than 10 transactions in 60 seconds from
one account is suspicious." This is direct and explainable — easy to audit and adjust. We ran
these rules on the real-time stream via Azure Stream Analytics.

Implementation: sliding window aggregation over the Kafka stream. Count transactions per account
in the last 60 seconds. If count > 10, publish an alert to a separate Kafka topic that triggers
an account review.

**2. Graph-based pattern detection:**
The circular flow and fan-out patterns I described above. These are structural anomalies —
suspicious because of the shape of the relationship network, not just the numbers.

**3. Statistical deviation from personal baseline:**
Compute historical baseline behavior per account: typical transaction amount range, typical
transaction frequency, typical set of destination accounts. When a new transaction deviates
significantly from this account's personal baseline — sending 100x more than their typical
transaction to an account they've never transacted with before — flag it.

We computed baselines in Spark as batch jobs (run nightly, stored in Synapse). Real-time
alerts compared incoming transactions against these pre-computed baselines.

The three approaches are complementary: some fraud passes individual rule thresholds but shows
up in graph patterns; other fraud has individually suspicious amounts but no network patterns.
Using all three together improved detection accuracy.

---

## Section 6 — Azure Synapse and Power BI

---

**Q21. What is Azure Synapse Analytics and what did you use it for?**

Azure Synapse is Microsoft's cloud analytics platform — a system designed specifically for
storing and querying large volumes of data for business intelligence and analytics.

The core component I used is the **Dedicated SQL Pool** — previously called Azure SQL Data
Warehouse. It is a Massively Parallel Processing (MPP) database. "MPP" means the data is
distributed across many independent compute nodes, and every query runs in parallel across all
of them. A query that takes 60 seconds on one server might take 3 seconds if 20 nodes each
process 1/20th of the data simultaneously.

At XenonStack, Synapse was the central destination for all processed data:
- The Debezium + Kafka real-time pipeline loaded clean transaction events into Synapse tables
- The Spark batch jobs processed sensor data and loaded analytical summaries
- Power BI connected to Synapse for all dashboards and reports

Synapse replaced the need for us to query production databases for analytics — keeping the live
system isolated from analytical workload.

---

**Q22. Explain the three data distribution strategies in Synapse: HASH, ROUND_ROBIN, REPLICATED.**

When you create a table in a Synapse Dedicated SQL Pool, you must choose how rows are
distributed across the compute nodes. This choice significantly affects query performance.

**HASH distribution:**
You choose one column as the "distribution column." Synapse applies a hash function to each
row's value in that column and assigns the row to a node based on the hash result. All rows
with the same value in the distribution column always land on the same node.

Why this matters: if your most frequent query pattern joins `transactions` and `accounts` on
`account_id`, and both tables are HASH distributed on `account_id`, then for any given account,
all its transactions AND its account record are on the same node. The join can be completed
locally — no data needs to travel across the network between nodes. Without this alignment,
joins require a network "shuffle" — moving large amounts of data between nodes, which is slow.

**ROUND_ROBIN distribution:**
Rows are assigned to nodes in order: row 1 to node 1, row 2 to node 2, row 3 to node 3,
then back to node 1 for row 4. Perfectly even distribution with no logic.

Best for staging tables — temporary landing areas where you load raw data before transforming
it. No join queries run on staging tables, so even distribution without alignment is fine.

**REPLICATED distribution:**
Every node gets a complete copy of the entire table.

Only makes sense for small tables (under ~2GB). If you have a small `merchant_categories` table
that you join against transactions frequently, replicating it means every node has the full
lookup table locally. Joins never need network transfer. For large tables, the storage overhead
of keeping N complete copies is not worth it.

---

**Q23. What is a Columnstore Index and why does it make analytics fast?**

Traditional databases store data row by row. All 20 columns of row 1 are stored together, then
all 20 of row 2, etc. When your query only needs 3 columns, the database still has to read all
20 columns of every row from disk and discard the 17 you don't need.

A Columnstore Index stores data column by column. All values of the `amount` column are stored
together, all values of `txn_date` are stored together, etc. When your query needs only `amount`
and `txn_date`, the database reads only those two column files from disk — skipping the other 18.

For analytical queries that scan millions of rows but only need a handful of columns (SUM this,
COUNT that, GROUP BY these), columnar storage reduces the physical data read from disk by a
factor of (total columns / needed columns). With 20 columns and needing 3, that is 6.7x less
data read — directly translating to faster queries.

Additional benefit: columns compress much better than rows. A column of amounts like
[500, 1200, 750, 200, 8900, 500, 1200, ...] — all within a similar range, with repeating
values — compresses to a small fraction of its original size. Less data on disk = faster reads.

Azure Synapse uses **Clustered Columnstore Index** by default on all tables. This is the
primary architectural reason Synapse is fast for analytical workloads.

---

**Q24. What is the difference between DirectQuery and Import mode in Power BI?**

These are two fundamentally different ways Power BI gets data.

**Import mode:**
Power BI makes a complete copy of the data from Synapse into its own in-memory database
(called VertiPaq). When you interact with a report, it queries this local copy — extremely fast
because everything is in memory and the VertiPaq engine is highly optimized for this.

The downside: data is only as fresh as the last scheduled refresh. If you refresh every 4 hours,
your report could be showing data from 3 hours and 59 minutes ago. For a fraud dashboard that
needs to show transactions from the last 5 minutes, this is unacceptable.

**DirectQuery mode:**
No data is copied. Every interaction with the report (clicking a filter, hovering on a chart,
changing a date range) sends a live SQL query directly to Synapse and shows the result in real time.
Data is always completely current.

The downside: every interaction hits Synapse. If your underlying Synapse queries are slow,
your dashboard interactions will feel slow. You also need to be careful not to have too many
visuals that each fire their own query simultaneously.

**Our choices at XenonStack:**
- Fraud detection dashboard → DirectQuery. Real-time fraud monitoring requires current data.
  A transaction happening right now should appear in the dashboard within seconds, not hours.
- Management dashboard (weekly trends, monthly fraud summaries, executive KPIs) → Import mode.
  Management looking at trends does not need second-by-second freshness. Import mode gave them
  a fast, responsive experience.

---

## Section 7 — General Data Engineering Concepts

---

**Q25. What is the difference between OLTP and OLAP?**

These represent two fundamentally different types of database workloads, and understanding
them explains why data warehouses like Synapse exist at all.

**OLTP (Online Transaction Processing)** is your live application database — where transactions
are recorded as they happen. When someone sends a UPI payment, a row is written to the OLTP
database. It is designed for:

- Thousands of small, fast writes per second — each INSERT or UPDATE touches only 1–2 rows
- Short, simple queries — "fetch account ACC_A's balance," "update transaction T001 to status=SUCCESS"
- Row-oriented storage — one transaction's complete data (all columns) stored together, because
  when you look up one transaction, you need all its fields
- Normalized schema — data split into many tables (accounts in one, merchants in another,
  transactions in a third) to eliminate duplication and maintain consistency
- Strict ACID guarantees — every write is fully atomic, consistent, isolated, and durable

**OLAP (Online Analytical Processing)** is your data warehouse — where processed data is stored
for analysis. When a fraud analyst queries "show me all high-risk accounts in Maharashtra this month
sorted by total flagged transaction value," that query runs on the OLAP system, not the live DB.
It is designed for:

- Complex aggregations scanning millions or billions of rows
- A few large reads, not thousands of small writes
- Columnar storage — query only the columns you need, skip the rest
- Denormalized schema — pre-joined, wide tables so queries don't need expensive JOINs at runtime
- Batch data loading and then many analytical reads

**Why you cannot mix them:**
If you run a heavy analytical query on your OLTP database — "sum all transactions last month,
group by merchant" — that query locks and scans large portions of the table. Meanwhile, your
real application is trying to write live transactions to that same table. The live system slows
dramatically or crashes. This has caused real production outages at companies.

The solution (what you built): Debezium + Kafka + Spark copies data from OLTP to OLAP
continuously. Analysts and dashboards query OLAP (Synapse). The live OLTP database is never
touched for analytical purposes.

---

**Q26. What is a star schema and why is it used in data warehouses?**

A star schema is the standard way to design tables in a data warehouse for analytical queries.
It has two types of tables: fact tables and dimension tables.

**Fact table:** Records measurable events. Every row is one thing that happened.
For fraud detection: each row = one UPI transaction.
Columns: transaction_id, account_key, merchant_key, date_key, amount, is_fraud, risk_score.
These "key" columns reference dimension tables. The measurable values (amount, is_fraud) are
called "measures" — the things you aggregate (SUM, COUNT, AVG).

**Dimension tables:** Describe the entities that participated in the events.
- Dim_Account: account_key, account_id, holder_name, account_type, risk_tier, city
- Dim_Merchant: merchant_key, merchant_name, category, city, is_verified
- Dim_Date: date_key, full_date, day_of_week, month, quarter, year, is_holiday

When Power BI builds a chart "total fraud amount by merchant category, by month":
1. Filter Dim_Date for the months you want → get date_keys
2. Filter Fact_Transaction by those date_keys AND is_fraud=1
3. Join with Dim_Merchant → get merchant categories
4. Group and sum

Simple, clean, fast. Power BI auto-detects star schema relationships and builds the model automatically.

**Why it's better than a fully normalized schema for analytics:**
A normalized schema has the data split into 10+ tables with many foreign keys. Every query
requires many JOINs. For a reporting database with hundreds of users running reports, that join
cost is paid over and over. A star schema pre-joins the data — dimension tables are denormalized
(merchant name stored with every merchant record, city repeated for every merchant in that city).
Yes, some data is duplicated. But analytical query performance is dramatically faster, which
matters more for a reporting system.

---

**Q27. What is data partitioning in a data warehouse and why does it matter?**

Partitioning means physically splitting a table's data into separate files or segments based on
the value of one column (usually a date column).

Imagine a `transactions` table with 5 years of data — roughly 2 billion rows. Without partitioning,
every query has to scan 2 billion rows to find what it needs. With monthly partitioning, the
table is split into 60 segments (one per month). Each segment is a separate physical file on disk.

When you query `WHERE txn_date BETWEEN '2023-01-01' AND '2023-01-31'`, the database reads the
partition metadata, identifies that only the January-2023 segment is relevant, and reads only
that file. The other 59 segments are completely skipped. This is called **partition pruning**.

For fraud detection queries that always look at "last 7 days" or "last 30 days," partitioning by
date means each query reads 1–2 partitions out of 60. Without partitioning, it reads all 60.
The performance difference is enormous for large tables.

In Azure Synapse, you partition like this:
```sql
CREATE TABLE transactions (
    txn_id      NVARCHAR(100) NOT NULL,
    account_id  NVARCHAR(50)  NOT NULL,
    amount      DECIMAL(18,2),
    txn_date    DATE
)
WITH (
    DISTRIBUTION = HASH(account_id),
    CLUSTERED COLUMNSTORE INDEX,
    PARTITION (txn_date RANGE RIGHT FOR VALUES (
        '2023-01-01','2023-02-01','2023-03-01'  -- partition boundaries
    ))
);
```

**Important:** Partitioning is only useful if your queries frequently filter on the partition
column. Partitioning by date works great when your queries always filter by date. Partitioning
by an arbitrary column that queries don't filter on provides no benefit.

---

**Q28. How did you reduce data integration time by 20%?**

Integration time here means the time it takes to onboard a new data source into the pipeline —
from initial requirement to data flowing reliably into Synapse.

When I joined XenonStack, adding a new data source involved a lot of manual, repetitive work:
figuring out the source schema from scratch, writing custom extraction code, building transformation
logic from zero, manually testing each field. For a complex source, this took 2–3 weeks.

I reduced this by:

**Standardized data contracts upfront:**
Before writing any code, we formally documented the agreed schema — column names, data types,
nullability, example values — with the source team. This document became a binding contract.
Previously, we discovered schema mismatches after writing the pipeline, causing rework.
With contracts, we caught these upfront.

**Automated data quality checks as part of the pipeline template:**
I built a reusable set of quality checks (null checks, data type validation, row count
cross-validation, referential integrity checks) that ran automatically as an Airflow task after
every data load. Previously, quality issues were caught manually by analysts days later.
Catching them in the pipeline immediately reduced the back-and-forth debugging cycle.

**Pipeline templates:**
I created parameterized Airflow DAG templates for the most common patterns (e.g., "batch load
from Azure Blob to Synapse table"). Adding a new source with this pattern meant filling in
parameters (table name, schema, source path, schedule) rather than writing the whole pipeline
from scratch. Cut the standard onboarding from 2 weeks to under a week.

Together these reduced integration time for new data sources by approximately 20%.

---

## Section 8 — Behavioral / Situational Questions

---

**Q29. Tell me about yourself and your role at XenonStack.**

I worked at XenonStack as a Data Engineer for about 13 months, from August 2022 to September 2023,
at their office in Mohali.

My main responsibility was the data infrastructure for two projects. The primary one was a
UPI fraud detection system — real-time detection of suspicious transaction patterns. I designed
and built the end-to-end data pipeline: using Debezium to capture transaction events from the
source database in real time, Apache Kafka as the transport layer, Azure services (Stream Analytics,
Synapse) for processing and storage, ArangoDB as the graph database for detecting relational
fraud patterns like circular money flow and fan-out smurfing patterns, and Power BI for the
fraud analyst dashboard.

The second project was a wind turbine monitoring data pipeline — collecting high-throughput
sensor data from turbines via Kafka, processing it in bulk with Spark and PySpark, orchestrating
the workflow with Apache Airflow, and loading analytical results into Azure Synapse for reporting.

The outcomes I contributed to: data latency went from hours (batch) to under 30 seconds (real-time);
Power BI analytics performance improved by about 20% through Synapse optimization; and data
integration time for new sources was reduced by about 20% through pipeline templates and
automated quality checks.

---

**Q30. What was your biggest technical challenge at XenonStack?**

The biggest challenge was making the fraud detection truly real-time when the original design
had a 3–5 minute lag that made it ineffective.

The initial design used polling — a Python script querying the transactions database every 3
minutes to get new records. Three problems: the 3-minute lag was too slow to prevent fraud in
progress, the polling query was putting constant load on the production database, and the script
sometimes missed records that were inserted and updated between polls.

I proposed replacing the polling with Debezium CDC reading the PostgreSQL WAL. The technical
challenge was that the production DBA team was initially hesitant — enabling PostgreSQL logical
replication required a configuration change and a restart of the database server, which needed
maintenance window approval.

I worked with the DBA team to demonstrate the approach in a staging environment first, documented
the configuration changes and their impact (minimal — logical replication has very low overhead
compared to the polling load we were currently imposing), and presented the comparison: 3-minute
lag with polling vs. under-30-second lag with CDC. They approved the change.

The second challenge was that after switching to Debezium, we had to ensure all downstream
consumers handled duplicate events gracefully (Kafka at-least-once delivery). I added idempotent
UPSERT logic to all Synapse writes, which also fixed a separate pre-existing bug where duplicate
transactions occasionally appeared in the data warehouse.

The result was data latency reduced from 3+ minutes to under 30 seconds, with lower load on the
production database than the previous polling approach.

---

**Q31. How did you measure success for the fraud detection system?**

We defined success across several dimensions:

**Technical metrics (pipeline health):**
- Data latency: time from transaction written in source DB to appearing in Synapse (target < 60 seconds)
- Pipeline availability: uptime of Debezium connectors and Kafka consumers (monitored in Grafana)
- Consumer lag: how far behind our consumers were (target < 1,000 messages, meaning < a few seconds)
- Duplicate rate: number of duplicate records detected by the idempotency checks (target = 0)

**Detection quality metrics (fraud effectiveness):**
- False positive rate: legitimate transactions incorrectly flagged as suspicious. Too high = analysts
  waste time reviewing false alarms, which they then start ignoring.
- False negative rate: fraudulent transactions that slipped through undetected. This is the most
  dangerous metric — fraud we missed.
- Mean time to detection: average time from when a fraudulent pattern started to when we raised an alert.

**Business impact:**
- Volume and value of fraudulent transactions detected and blocked per week/month
- Analyst review time (did the dashboard changes reduce the time needed per flagged case?)
- Confirmed fraud cases per quarter, tracked by the business team

We tracked technical metrics in a Grafana dashboard connected to our monitoring infrastructure.
Detection quality and business impact were reviewed in weekly fraud review meetings with the
fraud analyst team and reported to management monthly.

---

*Last updated: August 2026*

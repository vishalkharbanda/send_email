# Scenario-Based Interview Questions — Tech Mahindra + XenonStack
> These are "what would you do if..." questions interviewers love
> Based on your actual experience across both roles
> Full answers written so you can understand the reasoning, not just memorize

---

## Section 1 — Production Incidents & Troubleshooting

---

**Scenario 1: A critical microservice keeps crashing every 30 minutes in production. How do you investigate and fix it?**

This is a real scenario from TMDC. Here's how I'd approach it:

**Step 1 — Confirm the impact and stabilize:**
First question: is it affecting users right now? If yes, consider a temporary workaround (restart,
rollback to previous version) to restore service while you investigate. Don't spend 2 hours
debugging while users are stuck.

At TMDC, PM2 auto-restarts crashed services within seconds, so users might only experience brief
blips. But repeated crashes (every 30 minutes) mean something systematic is wrong — auto-restart
is a bandaid, not a fix.

**Step 2 — Check the logs:**
SSH into the server, run `pm2 logs service-name --lines 500`. Look at what happens right before
each crash. Is there an exception? An out-of-memory kill? A segfault?

```bash
# Check if it's an OOM kill (OS killed it for using too much memory)
dmesg | grep -i "oom\|killed" | tail -20

# Check PM2 restart history and memory at time of crash
pm2 show service-name
```

**Step 3 — Identify the pattern:**
"Every 30 minutes" suggests either:
- A scheduled task triggers it (cron, timer, scheduled background job)
- A resource leak — something accumulates until it hits a limit every ~30 min
- An external dependency that goes unhealthy on a cycle (connection pool exhaustion, token expiry)

**Step 4 — Reproduce and fix:**
Once I know the cause:
- Memory leak → find the growing data structure, add cleanup. Add memory monitoring.
- Unhandled exception from a specific input → add error handling, add a test case for that input.
- External dependency timeout → add retry logic, circuit breaker, increase timeout.
- Scheduled task conflict → fix the task logic or schedule.

**Step 5 — Prevent recurrence:**
- Add monitoring for the specific metric that would catch this earlier
- Add a test that covers the failure scenario
- Document the incident for the team

**Example from my experience:** At TMDC, our telemetry service had a memory leak — device
connection objects were never removed from a dictionary when devices disconnected. Memory grew
50MB/day. After 4-5 days, OOM kill. Fixed by adding cleanup on disconnect + background sweep
for stale entries + memory usage alerting.

---

**Scenario 2: Your real-time fraud detection pipeline at XenonStack suddenly has a 10-minute delay instead of the normal 30 seconds. Users are complaining. What do you do?**

**Step 1 — Identify WHERE the delay is:**
The pipeline has multiple stages. The delay could be in any of them:
- Debezium reading from PostgreSQL WAL → Kafka (capture lag)
- Kafka → consumers (consumer lag)
- Consumer processing → Synapse write (processing bottleneck)

I'd check Kafka consumer lag first — it's the easiest metric to check and the most common cause:
```bash
kafka-consumer-groups.sh --bootstrap-server kafka:9092 --describe --group fraud-consumer
```

If consumer lag is 600,000 messages (and we produce ~1000/sec), that's 10 minutes of backlog.

**Step 2 — Diagnose the root cause based on where the lag is:**

**If consumer lag is high (consumer is behind):**
- Consumer might be slow. Why? Check consumer service logs:
  - Is the Synapse write failing and retrying repeatedly?
  - Is the transformation step taking unusually long?
  - Did the consumer crash and restart (losing its in-memory state)?
  - Did Kafka rebalance consumers? (Happens when a consumer dies and partitions are reassigned)

**If consumer lag is low but data is still delayed:**
- Check Debezium connector status. It might be paused or in snapshot mode.
- Check PostgreSQL replication slot lag (Debezium might be stuck).

**If Debezium is fine but Kafka itself is slow:**
- Broker disk full? A full disk causes Kafka to stop accepting messages.
- Network issue between Debezium and Kafka cluster?

**Step 3 — Fix based on cause:**

If the consumer was overwhelmed by a traffic spike:
- Short-term: add more consumer instances to the consumer group (Kafka will rebalance partitions)
- Long-term: capacity plan for peak traffic, autoscale consumers

If Synapse was temporarily unavailable (causing consumer retries):
- The consumer was probably retrying writes for minutes. Once Synapse recovered, the backlog
  clears naturally. But add a dead-letter queue so consumer doesn't block on persistent failures.

If Debezium was stuck on a large transaction:
- One extremely large transaction (or a long-running transaction that holds the WAL slot) can
  delay Debezium. Consider increasing `max.batch.size` or investigating the source DB for
  problematic transactions.

**Step 4 — Communicate:**
While fixing, notify stakeholders: "Fraud detection pipeline is delayed by ~10 minutes due to
[cause]. Working on resolution. ETA [X minutes]." Transparency during incidents builds trust.

---

**Scenario 3: You deployed a new version to production and the API response time doubled. How do you handle this?**

**Immediate action — rollback:**
If response time doubled and is affecting users, roll back to the previous version immediately.
Don't debug in production while users suffer. At TMDC, our CI/CD does rolling deployments
(5 servers at a time), so if we catch it on the first batch, only 5 servers are affected.

```bash
# Rollback: restart with previous version
pm2 restart service-name --update-env
# Or redeploy previous Git commit via CI/CD
```

**Investigation (after rollback, production is stable):**

1. **Diff the code:** What changed between the old and new version? Often the cause is obvious
   once you look at the diff — a new database query without an index, a loop that does N+1 queries,
   a large object being created on every request.

2. **Profile locally:** Run the new version locally with production-like data. Use profiling tools
   (`cProfile` for Python, `--inspect` for Node.js) to find where time is spent.

3. **Common culprits I've seen at TMDC:**
   - New API endpoint that accidentally queries the entire device table without pagination
   - A database migration that dropped an index (unintentional)
   - A new dependency that adds overhead to every request (heavy middleware)
   - Debug logging accidentally left enabled (writing verbose logs to disk synchronously)

4. **Fix and redeploy with confidence:** Fix the issue, add a performance test that would catch
   similar regressions, deploy again through the normal pipeline.

**Key principle:** Never debug in production at the cost of users. Roll back first, investigate second.

---

**Scenario 4: One of your 80 servers has 95% disk full. What's your immediate action and long-term fix?**

**Immediate — free space:**
```bash
ssh admin@srv-42

# What's using the space?
du -sh /var/log/tmdc/* | sort -rh | head -10
# Often: old log files that were never rotated

# Quick cleanup: remove old logs (keep last 3 days)
find /var/log/tmdc/ -name "*.log" -mtime +3 -delete
find /tmp/ -mtime +7 -delete

# Verify
df -h
```

**Long-term — prevent recurrence:**
1. **Set up log rotation** (logrotate config or PM2 log rotation):
   ```bash
   pm2 install pm2-logrotate
   pm2 set pm2-logrotate:max_size 100M
   pm2 set pm2-logrotate:retain 7
   ```

2. **Add disk usage monitoring:** Alert when any server exceeds 80% disk usage — gives you
   time to investigate before hitting 95% and services start failing.

3. **Archive old data:** If raw packet dumps need to be retained, compress and move to
   cheaper storage (Azure Blob / S3) instead of keeping them on the server's SSD.

4. **Audit all services:** Which services produce the most disk output? Are they logging
   at an appropriate level (not DEBUG in production)?

---

## Section 2 — System Design & Architecture Decisions

---

**Scenario 5: Your team is building a new feature that requires data from three different microservices. How do you design the interaction?**

This is a real problem at TMDC. Say the dashboard needs to show: device info (from device service),
current test status (from test service), and latest battery level (from telemetry service).

**Option A — API Gateway / BFF (Backend for Frontend):**
Create a single endpoint that internally calls all three services and assembles the response:

```python
@app.get("/dashboard/device/{device_id}")
async def dashboard_view(device_id: str):
    # Call all three services in parallel (not sequentially!)
    device, test, telemetry = await asyncio.gather(
        device_client.get(device_id),
        test_client.get_active(device_id),
        telemetry_client.get_latest(device_id),
    )
    return {
        "device": device,
        "current_test": test,
        "battery": telemetry.get("battery_level")
    }
```

Pros: Frontend makes one call, gets everything. Simple for the client.
Cons: If one downstream service is slow, the entire response is slow.

**Option B — Frontend aggregation:**
Frontend makes 3 separate API calls in parallel and assembles the view itself.

Pros: If telemetry is slow, device info and test status still load immediately (progressive rendering).
Cons: More complex frontend logic, more network requests.

**Option C — Event-driven denormalization:**
Maintain a "device summary" table that gets updated whenever any of the three services publishes
an event. One query returns everything pre-assembled.

Pros: Single query, always fast, no inter-service calls at request time.
Cons: Eventually consistent (summary might be a few seconds behind), more infrastructure to maintain.

**What I'd recommend (and have done at TMDC):**
Option A with timeouts — use `asyncio.gather` with a timeout. If telemetry is slow (>2 seconds),
return the response without telemetry rather than making the user wait. Show "battery data
unavailable" in the UI. Graceful degradation > total failure.

---

**Scenario 6: At XenonStack, the source team wants to add 5 new columns to the transactions table. How do you handle this in the Debezium pipeline without breaking anything?**

This is a schema evolution problem — exactly what we faced at XenonStack.

**The risk:** If you just add columns, Debezium starts sending messages with new fields that
downstream consumers don't expect. Old consumer code might crash on unexpected fields, or
worse, silently ignore important data.

**Step-by-step approach:**

**1. Schema Registry with backward compatibility:**
We used Confluent Schema Registry with Avro schemas. The compatibility mode was set to
`BACKWARD` — new schemas must be readable by consumers using the old schema. Adding new fields
with default values is backward-compatible. Renaming or removing fields is NOT.

**2. Update consumers BEFORE the source change:**
Deploy updated consumer code that can handle both the old schema (without new columns) and
the new schema (with new columns). Make the new fields optional in the consumer's deserialization
logic.

```python
# Consumer code — handles both old and new schema gracefully
def process_transaction(event):
    txn = event["after"]
    result = {
        "txn_id": txn["txn_id"],
        "amount": txn["amount"],
        "account_id": txn["src_account"],
        # New fields — use .get() with defaults so old events don't crash
        "merchant_category": txn.get("merchant_category", "UNKNOWN"),
        "device_type": txn.get("device_type", None),
        "risk_flag": txn.get("risk_flag", False),
    }
    return result
```

**3. Source team makes the change:**
Once consumers are ready, the source team adds the columns. Debezium detects the schema change,
registers the new schema version in the registry, and starts sending events with the new fields.

**4. Update Synapse tables:**
Add the new columns to the destination Synapse tables:
```sql
ALTER TABLE transactions ADD merchant_category NVARCHAR(50) DEFAULT 'UNKNOWN';
ALTER TABLE transactions ADD device_type NVARCHAR(50) NULL;
ALTER TABLE transactions ADD risk_flag BIT DEFAULT 0;
```

**5. Verify and backfill:**
Monitor for a day. Confirm new fields are flowing correctly. If historical data needs the new
columns populated, run a one-time backfill job.

**Key principle:** Always update consumers (downstream) before changing the producer (upstream).
This ensures there's never a moment where events are produced that consumers can't handle.

---

**Scenario 7: You need to add a new data source to the analytics pipeline (a new API providing merchant data). How do you approach this?**

This is the "reduce integration time by 20%" scenario from XenonStack — using the templates
and processes I built.

**Step 1 — Define the data contract (day 1-2):**
Before writing any code, sit with the merchant data team and document:
- API endpoint URL and authentication method
- Response schema (field names, data types, nullable fields)
- Data volume (how many records? how often does it update?)
- Delivery frequency (real-time API, daily batch file, etc.)
- Quality expectations (are there known issues? missing data periods?)

Write this as a formal data contract document. Both teams sign off.

**Step 2 — Design the ingestion (day 2-3):**
Based on the contract:
- If it's a REST API → write an extraction script that calls the API and writes responses to staging
- If it's a daily file drop → configure a file watcher / Airflow sensor
- Decide: is this batch (Airflow DAG) or real-time (Kafka)?

For a merchant data API that updates daily → batch approach using Airflow.

**Step 3 — Build using the template (day 3-5):**
Use the parameterized Airflow DAG template I created:
```python
merchant_pipeline = create_batch_pipeline(
    name="merchant_data_ingest",
    source_type="rest_api",
    source_config={
        "url": "https://merchant-api.example.com/v1/merchants",
        "auth": "bearer_token",
        "pagination": "cursor",
    },
    destination_table="dim_merchants",
    schedule="0 6 * * *",  # 6 AM daily
    quality_checks=["no_nulls:merchant_id", "row_count_min:1000"],
)
```

**Step 4 — Test (day 5-6):**
- Run in staging environment with production-like data
- Verify all quality checks pass
- Verify Synapse table has correct data
- Verify Power BI can query the new table

**Step 5 — Deploy and monitor (day 6-7):**
- Deploy to production
- Monitor first 3 runs closely (check logs, quality check results, row counts)
- Document in the team wiki

Total: ~7 days. Before the templates and contracts, this took 2-3 weeks.

---

**Scenario 8: The Power BI dashboard is loading slowly (30+ seconds). How do you diagnose and fix it?**

This is the "boosted analytics performance by 20%" story from XenonStack.

**Step 1 — Identify what's slow:**
Open Power BI Desktop, use Performance Analyzer (View → Performance Analyzer → Start Recording).
Interact with the dashboard — it shows how long each visual takes to load and the actual
SQL query sent to Synapse.

Common findings:
- One visual takes 25 seconds while others load in 2 seconds → that visual has a bad query
- All visuals are slow → the Synapse connection or table is the bottleneck

**Step 2 — Analyze the slow query:**
Take the SQL query from Performance Analyzer, run it directly in Synapse with `SET STATISTICS TIME ON`:
```sql
SET STATISTICS TIME ON;
SELECT merchant_category, SUM(amount), COUNT(*)
FROM transactions
WHERE txn_date > '2023-01-01'
GROUP BY merchant_category;
```

If it takes 25 seconds in Synapse directly, the problem is Synapse/table design, not Power BI.

**Step 3 — Fix the Synapse side:**

**Check distribution:** If the transactions table uses ROUND_ROBIN distribution but is being
joined with accounts on `account_id`, every join requires a network shuffle. Change to HASH
distribution on `account_id`.

**Check partitioning:** If the query filters by date but the table isn't partitioned by date,
it scans the entire table. Add date partitioning — now the query only reads the relevant partition.

**Pre-aggregate:** If the dashboard shows "total by merchant category by month" — create a
materialized summary table with those pre-computed aggregates. 100,000 rows instead of 500 million.
Power BI queries the summary table instead.

**Check statistics:** Synapse uses statistics to plan queries. If statistics are outdated, the
query plan is suboptimal. Run `UPDATE STATISTICS transactions`.

**Step 4 — Fix the Power BI side:**
- Use Import mode for visuals that show historical/static data (not DirectQuery for everything)
- Reduce the number of visuals that load simultaneously on one page
- Use aggregations — tell Power BI to query summary tables for zoomed-out views

**Result at XenonStack:** Combined these fixes → dashboard load time reduced by ~20%.

---

## Section 3 — Data & Pipeline Scenarios

---

**Scenario 9: Debezium suddenly stops sending events. The Kafka topic has no new messages. What do you do?**

**Step 1 — Check Debezium connector status:**
```bash
curl http://debezium-host:8083/connectors/upi-connector/status
```
Is it running? Or is it in "FAILED" state?

**If FAILED — check the error:**
Common reasons:
- Source database credentials expired → update connector config with new credentials
- Source database unreachable → network issue, check connectivity
- WAL (replication slot) fell behind and PostgreSQL dropped the needed WAL segments → need to
  do a new snapshot
- Schema registry unavailable → connector can't register new schema versions

**If RUNNING but no new events:**
- Is the source database actually receiving transactions? Check the source directly.
- Is the replication slot advancing? `SELECT * FROM pg_replication_slots;` — if `confirmed_flush_lsn`
  isn't moving, Debezium is stuck.
- Did someone accidentally pause the connector? Check task status.

**Step 2 — Fix and verify:**
After fixing the root cause:
```bash
# Restart the connector if needed
curl -X POST http://debezium-host:8083/connectors/upi-connector/restart

# Verify events are flowing again
kafka-console-consumer.sh --topic upi-transactions --bootstrap-server kafka:9092 --from-latest
```

**Step 3 — Check for data gap:**
Calculate: how long was the connector down? What data was generated in the source during
that window? If PostgreSQL kept the WAL segments (replication slot wasn't dropped), Debezium
will replay the missed events upon restart. If the slot was dropped, you need a new snapshot.

---

**Scenario 10: A Kafka consumer is processing messages but writing duplicates to the database. How do you fix it?**

This is one of the most common issues in event-driven architectures.

**Why duplicates happen:**
1. Consumer processes a message, writes to DB, but crashes BEFORE committing the offset to Kafka
2. Consumer restarts, Kafka gives it the same message again (offset wasn't committed)
3. Consumer processes it again and writes to DB again → duplicate

Or: Kafka consumer group rebalance — partitions are reassigned. The new consumer might reprocess
some messages that the old consumer already processed but didn't commit.

**Fix 1 — Idempotent writes (primary fix):**
Use UPSERT (INSERT ... ON CONFLICT UPDATE) instead of plain INSERT:

```sql
-- Instead of:
INSERT INTO transactions (txn_id, amount, account_id) VALUES ('T001', 5000, 'ACC_A');
-- This would create a duplicate if the same event is processed twice

-- Use:
INSERT INTO transactions (txn_id, amount, account_id)
VALUES ('T001', 5000, 'ACC_A')
ON CONFLICT (txn_id) DO UPDATE SET amount = EXCLUDED.amount, account_id = EXCLUDED.account_id;
-- Processing the same event twice has no effect — idempotent
```

In Azure Synapse, this is done with MERGE:
```sql
MERGE INTO transactions AS target
USING (VALUES ('T001', 5000, 'ACC_A')) AS source(txn_id, amount, account_id)
ON target.txn_id = source.txn_id
WHEN MATCHED THEN UPDATE SET amount = source.amount
WHEN NOT MATCHED THEN INSERT (txn_id, amount, account_id) VALUES (source.txn_id, source.amount, source.account_id);
```

**Fix 2 — Exactly-once processing (Kafka Transactions):**
Kafka 0.11+ supports transactions. You can atomically: process message + write to DB + commit offset.
If any step fails, everything rolls back. But this requires the sink (database) to participate
in Kafka transactions, which not all systems support.

**Fix 3 — Deduplication table:**
Maintain a table of processed message IDs. Before processing, check if the ID exists:
```python
async def process_event(event):
    event_id = event["txn_id"]
    
    # Check if already processed
    if await db.exists("processed_events", event_id):
        logger.info("Duplicate event, skipping", event_id=event_id)
        return
    
    # Process the event
    await db.insert("transactions", event)
    await db.insert("processed_events", {"id": event_id, "processed_at": now()})
    
    # Commit Kafka offset
    consumer.commit()
```

**At XenonStack, we used Fix 1 (UPSERT)** because it's the simplest and most reliable. The
transaction ID is the natural unique key, so UPSERT guarantees idempotency regardless of how
many times the same event is processed.

---

**Scenario 11: Your Spark job is running for 4 hours instead of the usual 30 minutes. What do you investigate?**

**Step 1 — Check the Spark UI:**
Every Spark job exposes a web UI showing job progress, stage breakdown, and task details.
Look for:
- Which stage is taking most of the time?
- Are any tasks significantly slower than others (data skew)?
- Are there many shuffle reads/writes (expensive data movement)?

**Step 2 — Common causes:**

**Data skew:**
Look at the stage with the slowest tasks. If 199 tasks finished in 10 seconds but 1 task has
been running for 3 hours, you have a skewed key. That one partition has way more data than the others.

Fix: salting, broadcast join, or filter the skewed keys and process separately.

**Shuffle explosion:**
A join between two large tables causes both to be shuffled across the network. If yesterday
a new bulk data load doubled the size of one table, the shuffle that used to move 10GB now
moves 20GB.

Fix: Is one table small enough to broadcast? Can you filter earlier to reduce data before the join?

**Source data changed:**
Did the input dataset grow significantly? Did someone add a new partition that previously didn't
exist? Check input data size vs. previous successful runs.

**External dependency slow:**
If the Spark job reads from or writes to an external system (Azure Synapse, S3, JDBC database),
that system might be throttling. Check for errors or slow responses in Spark executor logs.

**Resource starvation:**
Is another job running on the same cluster, consuming resources? Check cluster resource manager
(YARN, Kubernetes) for competing workloads.

**Step 3 — Fix at XenonStack:**
One time our daily Spark job went from 30 minutes to 3 hours because a Kafka → Data Lake archiver
had started dumping uncompressed data (a config change upstream). Input data size jumped 5x
overnight. Fix: coordinate with the archiver team to restore compression, and add a monitoring
check on input data size change rate.

---

**Scenario 12: An Airflow DAG has been failing every night for 3 nights but nobody noticed. How do you prevent this?**

**The problem:** The DAG failed, the alert presumably fired, but nobody acted on it. By the time
someone noticed, 3 nights of data were missing from the dashboard.

**Root cause analysis:**
1. Was the alert actually sent? Check: is `on_failure_callback` configured? Is the Slack webhook
   still active? Did someone's email filter catch it?
2. Was the alert clear enough? "DAG sensor_pipeline failed" is less actionable than "DAG
   sensor_pipeline failed — task 'load_synapse' hit DB connection timeout after 3 retries.
   Impact: Power BI dashboard showing stale data."
3. Is there an on-call rotation that requires acknowledgment of alerts?

**Fixes to prevent recurrence:**

**1. Alert that cannot be ignored:**
- Send to a dedicated alerts channel (not buried in a general channel)
- Require acknowledgment — if no one acks within 30 minutes, escalate
- Include direct link to the Airflow log and clear description of impact

**2. Data freshness monitoring (independent of the pipeline):**
Don't only alert when the pipeline fails. Also alert when the DATA is stale:
```sql
-- Run this check every hour independently:
SELECT MAX(load_timestamp) as latest_load FROM synapse_table;
-- If latest_load is more than 24 hours old → alert "Dashboard data is stale!"
```

This catches cases where the pipeline fails silently (no error, but no data flows either).

**3. Dashboard shows data freshness:**
Add a "last updated" timestamp on the Power BI dashboard itself. If a user sees "Last updated:
3 days ago", they'll report it immediately.

**4. Airflow monitoring DAG:**
A separate DAG that runs hourly and checks: "did the main pipeline succeed today?" If not, it
fires an independent alert through a different channel.

**At XenonStack:** We implemented approach #2 — an independent data freshness check in Synapse
that alerted when the latest record in key tables was older than expected. This was a safety
net independent of the pipeline's own alerting.

---

## Section 4 — Scalability & Performance

---

**Scenario 13: Traffic to your device management API at TMDC has doubled. Response times are degrading. How do you scale?**

**Short-term (minutes to hours):**

**1. Add more instances:**
If the service runs as one PM2 process, increase to 4 instances:
```bash
pm2 scale device-service 4
```
NGINX automatically load-balances across them (if upstream is configured properly).

**2. Check if it's the service or the database:**
If the service instances have low CPU but the database has high CPU, adding more service
instances won't help — the database is the bottleneck. In that case:
- Add response caching (Redis) for frequently-requested data that doesn't change every second
- Optimize slow queries (add indexes, rewrite queries)
- Enable read replicas for the database

**3. Check for inefficient code:**
Is there a new endpoint or feature that makes expensive queries? Is there an N+1 query pattern
(fetching 100 devices, then making 100 separate DB calls for their telemetry)?

**Medium-term (days to weeks):**

**4. Horizontal scaling:**
Add more servers to the fleet. Deploy the device service on new servers. Update NGINX upstream
configuration to include the new servers.

**5. Caching layer:**
Add Redis for frequently-accessed, rarely-changing data:
```python
@app.get("/devices/{device_id}")
async def get_device(device_id: str):
    # Check cache first
    cached = await redis.get(f"device:{device_id}")
    if cached:
        return json.loads(cached)
    
    # Cache miss — fetch from DB
    device = await db.get_device(device_id)
    await redis.set(f"device:{device_id}", json.dumps(device), ex=60)  # 60 sec TTL
    return device
```

**6. Database optimization:**
- Connection pooling (if not already in place)
- Read replicas for read-heavy endpoints
- Query optimization (EXPLAIN ANALYZE on slow queries)
- Index tuning

**Long-term (weeks to months):**

**7. Architecture improvements:**
- Separate read-heavy queries from write operations (CQRS pattern)
- Event-driven updates: instead of querying device status on every request, maintain a
  cached view that's updated by events (device service publishes status change events)
- Auto-scaling: configure infrastructure to automatically add/remove instances based on traffic

---

**Scenario 14: At XenonStack, the ArangoDB fraud detection queries are getting slower as the transaction volume grows. How do you address this?**

**Diagnosis:**
Graph traversal queries that ran in 50ms when we had 10 million edges now take 5 seconds with
100 million edges. The graph grew 10x but traversal performance degraded 100x — not linear scaling.

**Why this happens:**
As the graph grows, a traversal from one node might reach thousands of intermediate nodes.
Without proper constraints, the traversal "explores" exponentially more paths at each depth level.

**Fix 1 — Time-bound the traversal:**
Fraud patterns are temporal — we only care about recent transactions. Add time filters to limit
the traversal to edges within the last N hours:

```aql
FOR v, e, p IN 1..5 OUTBOUND "accounts/ACC_A" GRAPH "fraud_graph"
  FILTER e.time > DATE_SUBTRACT(DATE_NOW(), 24, "hours")  -- Only last 24 hours!
  RETURN v
```

Before this filter, a 5-hop traversal might explore millions of historical edges. With the
24-hour filter, it only explores edges from the last day — dramatically fewer.

**Fix 2 — Index on timestamp:**
Create a persistent index on the edge collection's `time` field:
```aql
db.transactions.ensureIndex({ type: "persistent", fields: ["time"] })
```
This makes the time filter in traversals use an index instead of scanning all edges.

**Fix 3 — Graph partitioning (time-based subgraphs):**
Maintain separate "active" and "archive" edge collections:
- `transactions_active` — last 30 days of transactions (queried for fraud detection)
- `transactions_archive` — older data (kept for compliance/reporting, not queried in real-time)

Move edges from active to archive with a nightly batch job. Fraud queries only traverse
`transactions_active`, which stays a manageable size.

**Fix 4 — Limit traversal depth and fan-out:**
If an account has 10,000 outgoing edges (a payment processor, not a fraud mule), traversing
ALL of them is expensive and unnecessary. Add a fan-out limit:

```aql
FOR v, e, p IN 1..3 OUTBOUND "accounts/ACC_A" GRAPH "fraud_graph"
  FILTER e.time > DATE_SUBTRACT(DATE_NOW(), 24, "hours")
  LIMIT 1000  -- Stop exploring after finding 1000 paths
  RETURN v
```

Or skip known high-degree nodes (payment processors, merchant accounts) that have legitimate
high transaction volumes.

**Fix 5 — Pre-compute risk scores:**
Instead of doing expensive traversals in real-time for every query, run a background job that
computes risk scores for all accounts nightly (using Spark). Store the pre-computed risk score
on the account vertex. Real-time queries just read the score — no traversal needed.

---

**Scenario 15: A Kafka topic is filling up faster than consumers can process it. Consumer lag is growing continuously. What do you do?**

**Immediate (stop the bleeding):**

**1. Add more consumers to the consumer group:**
If you have a topic with 10 partitions and only 2 consumers, each consumer handles 5 partitions.
Adding 8 more consumers (total 10 = one per partition) distributes the load evenly.

Note: you cannot have more consumers than partitions in a group. If you already have 10 consumers
and 10 partitions, adding an 11th consumer won't help — it will sit idle.

**2. Increase partition count (if needed):**
If you've maxed out at 10 consumers and still can't keep up, increase the topic's partition count.
More partitions = more parallelism. But this requires careful coordination — rebalancing takes time
and message ordering within partitions may change.

**3. Check for slow consumer code:**
Is the consumer doing something unnecessarily expensive per message?
- Synchronous HTTP calls to a slow service on every message? → batch them or make async
- Complex per-message database writes? → batch writes (accumulate 100 messages, write once)
- Heavy per-message transformations? → optimize or offload to a separate processing step

**Medium-term:**

**4. Back-pressure and flow control:**
Implement a pattern where consumers can signal "I'm overwhelmed" — temporarily pause fetching
new messages while processing the current batch, rather than accepting more than they can handle.

**5. Consumer optimization:**
- Batch processing: instead of processing one message at a time, consume 500 messages, batch-write
  them to the database in one transaction. Network round-trips reduced 500x.
- Async I/O: if the consumer is waiting for DB writes synchronously, switch to async. While
  waiting for one write to complete, start processing the next message.

**At XenonStack (wind turbine pipeline):** Consumer lag grew during a period when turbine sensors
were upgraded and started sending data 3x more frequently than before. We solved it by:
1. Adding consumer instances (short-term)
2. Switching from single-message DB writes to batch writes of 500 messages (reduced round-trips)
3. Coordinating with the sensor team to reduce unnecessary duplicate readings

---

## Section 5 — Team & Process Scenarios

---

**Scenario 16: A junior developer's code passed all tests but caused a production incident. What do you do?**

**During the incident:**
Fix the issue first. Don't assign blame during an active incident. Focus entirely on restoring
service — whether that's a rollback, a hotfix, or a configuration change.

**After the incident (blameless post-mortem):**
Schedule a post-mortem meeting. The goal is NOT "whose fault was this?" but "what did our
process miss that allowed this to happen?"

Questions to ask:
- Why didn't our tests catch this? → Are we testing the right things? Do we need a new test category?
- Why didn't code review catch this? → Was the PR too large to review effectively? Did the
  reviewer lack context about this area of the code?
- Can we add automated checks to prevent this class of issue? → Linting rules, CI checks, canary deployments?

**Actions after the post-mortem:**
- Add a test that specifically covers the scenario that caused the incident
- If it was a performance issue, add performance benchmarks to CI
- If it was a configuration issue, add validation of configs before deployment
- Share the learnings with the team (not as a blame post, but as "here's what we learned")

**The junior developer:**
- Don't blame them publicly. This demoralizes people and makes them afraid to commit code.
- Pair with them on the fix — they learn the most from fixing their own bugs with support.
- Help them understand WHY it happened, not just WHAT happened.
- Everyone causes production incidents at some point. The system should be resilient enough
  that one person's mistake doesn't bring everything down.

---

**Scenario 17: You have a production database change that could break the pipeline if done wrong. How do you handle it?**

**Context:** The DBA team needs to rename a column in the transactions table (`src_account` →
`sender_account`). This change will break Debezium events, consumer parsing, Synapse table
definitions, and Power BI reports if not handled carefully.

**The safe approach (backward-compatible migration):**

**Step 1 — Add the new column alongside the old one:**
```sql
ALTER TABLE transactions ADD sender_account VARCHAR(50);
UPDATE transactions SET sender_account = src_account;
-- Both columns now exist with the same data
```

**Step 2 — Update all consumers to read from the new column:**
Deploy updated consumer code that reads `sender_account`. The old `src_account` still exists
as a fallback.

**Step 3 — Update Debezium configuration to include the new column:**
Debezium starts sending events with both fields. Consumers use the new one.

**Step 4 — Update Synapse and Power BI:**
Add the new column to Synapse tables. Update Power BI measures and visuals.

**Step 5 — Only after everything is working with the new column — drop the old one:**
```sql
ALTER TABLE transactions DROP COLUMN src_account;
```

**Why this approach (expand-contract pattern):**
- At no point is any system broken. Old column exists throughout the transition.
- If anything goes wrong at any step, you can roll back without data loss.
- Each step can be deployed independently with confidence.
- The opposite approach (rename in one shot) would break everything simultaneously.

**Timing:**
- Steps 1-4 can be done over a week with normal deployment cycles
- Step 5 only happens after a monitoring period confirms everything works with the new column
- Total time: 1-2 weeks. But zero downtime and zero broken pipelines.

---

**Scenario 18: The business wants a new feature in 2 days but you estimate it needs 2 weeks. How do you handle this?**

**Don't just say no. Break it down:**

**1. Understand what they actually need by the deadline:**
"We need fraud detection for a new payment method in 2 days" might actually mean "we need
SOMETHING running — even basic rule checks — before the payment method launches." The full
graph-based detection can come later.

**2. Propose an MVP (Minimum Viable Product) for the 2-day deadline:**
"In 2 days, I can implement basic velocity checks (more than N transactions in M seconds = flag).
This catches the simplest fraud patterns and gives us some protection. The full graph-based
detection and pattern analysis will take 2 weeks — I'll deliver that as Phase 2."

**3. Be explicit about trade-offs:**
"If we rush the full feature in 2 days: no tests, no monitoring, no documentation, high risk
of production issues. The MVP approach gives us protection now AND quality later."

**4. Get agreement in writing:**
Email summary: "Agreed: Phase 1 (basic velocity rules) by Thursday. Phase 2 (full graph detection)
by end of next sprint. Let me know if this works."

**Key principle:** Almost never is the "real deadline" truly about the full feature. Understanding
what the business actually needs by the deadline (vs. what they asked for) usually reveals a
smaller deliverable that satisfies the real requirement.

---

## Section 6 — Cross-Cutting Concerns

---

**Scenario 19: How do you ensure your systems handle duplicate data safely?**

Duplicates are inevitable in distributed systems. They happen because:
- Kafka provides at-least-once delivery (safe, but may deliver twice after failure)
- Network retries (your HTTP request succeeded but the response was lost, so you retry)
- User error (clicking "submit" twice)
- Debezium replays after restart

**The rule: make your systems idempotent.**

Idempotent means: applying the same operation multiple times produces the same result as
applying it once. Like pressing an elevator button 5 times — the elevator still comes once.

**In databases — UPSERT:**
```sql
-- Instead of INSERT (creates duplicates):
INSERT INTO telemetry (device_id, timestamp, battery) VALUES ('D001', '12:00', 78);

-- Use UPSERT (safe to run multiple times):
INSERT INTO telemetry (device_id, timestamp, battery) VALUES ('D001', '12:00', 78)
ON CONFLICT (device_id, timestamp) DO UPDATE SET battery = EXCLUDED.battery;
```

**In APIs — idempotency keys:**
Client sends a unique request ID with every request. Server checks: "have I already processed
this request ID?" If yes, return the cached response without processing again.

```python
@app.post("/transactions")
async def create_transaction(request: TransactionRequest):
    # Check if this idempotency key was already processed
    existing = await db.get("idempotency_keys", request.idempotency_key)
    if existing:
        return existing.response  # Return cached response, don't process again
    
    # Process the transaction
    result = await process_transaction(request)
    
    # Store the response for this idempotency key
    await db.insert("idempotency_keys", {
        "key": request.idempotency_key,
        "response": result,
        "created_at": now()
    })
    
    return result
```

**In Kafka consumers — deduplication window:**
Keep a set of recently processed message IDs. Skip any message whose ID is already in the set.
Periodically clean old IDs from the set.

---

**Scenario 20: You notice that a service you depend on (an external API or database) has intermittent failures — it works 95% of the time but fails randomly. How do you make your system resilient?**

**Approach 1 — Retry with exponential backoff:**
If it fails, wait a short time and retry. Each subsequent retry waits longer:
- 1st retry: wait 1 second
- 2nd retry: wait 2 seconds
- 3rd retry: wait 4 seconds
- Give up after 3 retries

```python
import asyncio

async def call_with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise  # Final attempt failed, propagate error
            wait = 2 ** attempt  # 1, 2, 4 seconds
            logger.warning(f"Attempt {attempt+1} failed, retrying in {wait}s", error=str(e))
            await asyncio.sleep(wait)
```

**Approach 2 — Circuit breaker:**
If a service has failed 5 times in a row, stop trying for 30 seconds. Don't hammer a dead service.

States:
- **CLOSED** (normal): requests flow through. If failures exceed threshold → switch to OPEN.
- **OPEN** (tripped): all requests immediately fail without calling the service. After timeout → switch to HALF-OPEN.
- **HALF-OPEN** (testing): allow one request through. If it succeeds → CLOSED. If fails → OPEN again.

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=30):
        self.failures = 0
        self.state = "CLOSED"
        self.last_failure_time = None
        self.threshold = failure_threshold
        self.timeout = reset_timeout
    
    async def call(self, func):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"  # Try one request
            else:
                raise CircuitOpenError("Service unavailable, circuit is open")
        
        try:
            result = await func()
            self.failures = 0
            self.state = "CLOSED"
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.threshold:
                self.state = "OPEN"
            raise
```

**Approach 3 — Fallback:**
If the external service is down, return a degraded but still useful response:
- If telemetry service is down: return device info without battery level (instead of 500 error)
- If Power BI can't reach Synapse: show "data temporarily unavailable" message (instead of broken charts)

**Approach 4 — Timeout:**
Never wait forever. Set a timeout on every external call:
```python
try:
    result = await asyncio.wait_for(external_api.call(), timeout=5.0)
except asyncio.TimeoutError:
    logger.error("External API timed out after 5s")
    return fallback_response()
```

**At TMDC:** We use all four approaches together. Retries handle transient failures (network blip).
Circuit breaker prevents cascading failures (if the device database is down, don't keep hammering
it — fail fast and let other services remain healthy). Timeouts prevent threads from being
blocked indefinitely. Fallbacks ensure users see something useful even when parts of the
system are degraded.

---

*Last updated: August 2026*

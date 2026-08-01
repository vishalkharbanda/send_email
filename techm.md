# Tech Mahindra (TMDC) — Deep Concepts Guide
> Software Engineer | Tech Mahindra, Noida | Dec 2023 – Present
> Project: TMDC (Tech Mahindra Device Cloud) | Jan 2024 – Present
> Written to actually help you understand and recall, not just list keywords

---

## 0. The Big Picture — What Is TMDC and What Are You Building?

TMDC (Tech Mahindra Device Cloud) is a **mobile device cloud platform**. Think of it like this:

Imagine a QA team needs to test a mobile app on 200 different real phones — Samsung, iPhone,
Pixel, OnePlus, different Android versions, different iOS versions. Buying and physically
maintaining 200 phones in a lab is expensive and hard to manage. TMDC solves this by making
those real physical devices accessible remotely over the internet.

The platform allows testers and developers to:
- Remotely access and control real physical devices (Android, iOS) from their browser
- Run automated tests on these devices
- Collect telemetry data (battery level, CPU usage, network stats, logs) from devices
- Manage a fleet of 80+ servers hosting these devices across multiple locations

You are a backend engineer on this platform. Your work is the Python and Node.js services that
make the entire system work — device orchestration, data collection, APIs, CI/CD, and server
management.

### Your Core Contributions

1. **Python microservices** for device orchestration, automation, and telemetry
2. **Battery optimization service** — a Python service that reduced device battery drain by 35%
3. **RESTful APIs** in Flask/FastAPI and Node.js/Express for communication between components
4. **Data transformation pipelines** parsing Qualcomm chipset packet data (improved efficiency by 40%)
5. **CI/CD pipelines** with GitHub Actions, including code obfuscation for IP protection
6. **Encryption/obfuscation** mechanisms for security compliance
7. **Server operations** — monitoring and troubleshooting 80+ production servers

---

## 1. Microservices Architecture

### What Is a Microservice?

The opposite of a microservice is a "monolith" — one big application where everything lives
together in one codebase, one deployment, one process. If the login module has a bug, you
redeploy the entire application. If the reporting module needs more resources, you scale the
entire application.

A microservice architecture splits the system into small, independent services, each responsible
for one specific thing:
- One service handles device connection management
- Another handles test orchestration
- Another handles telemetry collection
- Another handles user authentication

Each microservice:
- Has its own codebase and can be deployed independently
- Communicates with other services through APIs (usually REST or message queues)
- Can be written in different languages (your platform uses both Python and Node.js)
- Can be scaled independently — if telemetry collection needs more resources, scale only that service

### Why Microservices at TMDC?

TMDC has many different concerns:
- Device connectivity (keeping a live connection to physical devices)
- Test execution (running automated test scripts on connected devices)
- Data collection (gathering battery, CPU, network telemetry from devices)
- User management (authentication, permissions)
- Dashboard/reporting (presenting data to users)
- Packet parsing (transforming raw Qualcomm data into structured format)

If all of this were one monolithic application:
- A bug in packet parsing could crash the entire platform, including live device sessions
- Deploying a small fix to the dashboard would require redeploying everything
- The team working on telemetry would have to coordinate every deployment with the device team

With microservices, each concern is isolated. The packet parsing service can crash and restart
without affecting live device sessions. The telemetry service can be redeployed without
touching any other component.

### How Your Microservices Communicate

**REST APIs (synchronous):** Service A makes an HTTP request to Service B and waits for a response.
Used when Service A needs an immediate answer — like "is device D001 currently available?"

**Message passing (asynchronous):** Service A publishes a message, Service B picks it up
whenever it's ready. Used for fire-and-forget operations — like "device D001 just disconnected,
notify all interested services."

In TMDC, your REST APIs handle synchronous queries and commands, while PM2 and internal
messaging handle event propagation across services.

### Cross-Platform Support (Linux, Windows, iOS)

TMDC manages real devices connected to servers running different operating systems:
- **Linux servers** — hosting Android device farms (most common)
- **Windows servers** — for devices requiring Windows-specific USB drivers
- **macOS/iOS** — Apple devices require macOS for connectivity (Xcode tools)

Your Python microservices need to work across all three OS environments. This means:
- Using cross-platform Python libraries (not Windows-only or Linux-only paths)
- Abstracting OS-specific operations behind interfaces (file paths, process management, USB access)
- Testing deployments on all three platforms in CI/CD

---

## 2. RESTful APIs — Flask, FastAPI, Express

### What Is a REST API?

REST (Representational State Transfer) is an architecture style for building APIs over HTTP.
When your frontend or another service needs to interact with your backend, it makes HTTP requests
to specific URLs (endpoints), and your backend responds with data (usually JSON).

The key principles:
- **Resources** are identified by URLs: `/devices/D001`, `/tests/T123`, `/telemetry/D001/battery`
- **HTTP methods** define the action:
  - `GET /devices/D001` — fetch information about device D001
  - `POST /devices/D001/connect` — initiate a connection to device D001
  - `PUT /devices/D001/config` — update device D001's configuration
  - `DELETE /tests/T123` — cancel/delete test T123
- **Stateless** — each request contains all information needed; the server doesn't remember
  previous requests (no session state between calls)
- **JSON** responses with appropriate HTTP status codes (200 OK, 201 Created, 404 Not Found, 500 Server Error)

### Flask vs FastAPI — When to Use Which

**Flask** — the established, minimal Python web framework:
- Simple, well-documented, massive ecosystem of plugins
- Synchronous by default (one request blocks until complete)
- You used it for straightforward CRUD APIs and internal service endpoints

```python
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/devices/<device_id>', methods=['GET'])
def get_device(device_id):
    device = device_service.get(device_id)
    if not device:
        return jsonify({"error": "Device not found"}), 404
    return jsonify(device), 200

@app.route('/devices/<device_id>/telemetry', methods=['POST'])
def submit_telemetry(device_id):
    data = request.json
    telemetry_service.store(device_id, data)
    return jsonify({"status": "stored"}), 201
```

**FastAPI** — the modern, high-performance Python web framework:
- Built-in async/await support (handles many concurrent requests efficiently)
- Automatic request/response validation using Python type hints (Pydantic)
- Auto-generates OpenAPI/Swagger documentation from your code
- Significantly faster than Flask for I/O-bound workloads (waiting for database, external APIs)
- You used it for performance-critical endpoints and newer services

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class TelemetryData(BaseModel):
    battery_level: float
    cpu_usage: float
    timestamp: str

@app.get("/devices/{device_id}")
async def get_device(device_id: str):
    device = await device_service.get(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

@app.post("/devices/{device_id}/telemetry", status_code=201)
async def submit_telemetry(device_id: str, data: TelemetryData):
    await telemetry_service.store(device_id, data.dict())
    return {"status": "stored"}
```

**Key difference:** FastAPI validates incoming data automatically using the `TelemetryData` model.
If someone sends `battery_level: "abc"` (a string instead of float), FastAPI returns a 422
validation error without your code ever executing. In Flask, you'd have to validate manually.

### Node.js / Express — Why Both Python and Node.js?

Express is the standard web framework for Node.js. At TMDC, some services are written in
Node.js because:

- **WebSocket support:** Node.js handles long-lived WebSocket connections more naturally than
  Python. Device remote control often uses WebSockets for real-time bidirectional communication
  (sending touch events to a device, receiving screen updates).
- **Event-driven architecture:** Node.js's event loop handles thousands of concurrent connections
  efficiently — ideal for the device connectivity layer where many devices maintain persistent connections.
- **Existing code:** Some TMDC services were built in Node.js before the team expanded, and
  rewriting them in Python wasn't justified.

```javascript
const express = require('express');
const app = express();
app.use(express.json());

app.get('/devices/:deviceId/status', async (req, res) => {
    const device = await deviceService.getStatus(req.params.deviceId);
    if (!device) return res.status(404).json({ error: 'Device not found' });
    res.json(device);
});

app.listen(3000, () => console.log('Service running on port 3000'));
```

### API Design Patterns You Use

**Pagination:** When listing devices, you don't return all 500 at once. You return pages:
`GET /devices?page=1&limit=20` returns devices 1–20. `GET /devices?page=2&limit=20` returns 21–40.

**Error responses:** Consistent error format across all services:
```json
{
  "error": "device_not_found",
  "message": "Device D001 is not registered in the system",
  "status_code": 404
}
```

**Health checks:** Every microservice exposes `GET /health` that returns 200 if the service is
running. Load balancers and monitoring systems hit this endpoint to detect unhealthy services.

---

## 3. The Battery Optimization Service (35% Reduction)

### The Problem

Devices in the cloud platform need to stay powered on and available 24/7 for testers to use.
But real mobile devices consume battery — especially when the screen is on, cellular radios
are active, and test automation is running continuous operations.

If a device's battery drains to 0%, it becomes unavailable until someone physically plugs it
in and charges it. For a remote cloud platform with devices in multiple locations, this means
downtime and manual intervention.

### What You Built

A dedicated Python service that intelligently manages device states to minimize unnecessary
battery consumption while keeping devices available. Key strategies:

**1. Adaptive screen management:**
Instead of keeping the screen always on at full brightness, the service turns the screen off
when no user is actively connected, dims it during idle periods, and only activates it at
full brightness when an active session begins. Screen is the biggest battery drain on modern phones.

**2. Radio/connectivity management:**
Disabling unnecessary radios (WiFi scanning, Bluetooth discovery, GPS) when they're not needed
for the current test. Only enabling what's actively required.

**3. Background process optimization:**
Killing unnecessary background applications and services on managed devices that consume CPU
cycles (and therefore battery) without contributing to testing.

**4. Charging cycle optimization:**
Monitoring battery levels across the fleet and scheduling charging cycles — connecting to/
disconnecting from power based on battery health best practices (not keeping at 100% constantly,
which degrades battery health over time).

**5. Device state machine:**
The service maintains a state machine per device:
- `ACTIVE` — user connected, full functionality
- `IDLE` — no user, minimal power consumption mode
- `CHARGING` — battery below threshold, power connected
- `MAINTENANCE` — device being updated or reconfigured

Transitions between states are managed by the service based on user sessions, battery levels,
and scheduled maintenance windows.

### Technical Implementation

```python
class DevicePowerManager:
    def __init__(self, device_id, adb_connection):
        self.device_id = device_id
        self.adb = adb_connection
        self.state = DeviceState.IDLE

    async def on_user_disconnect(self):
        """Called when a user session ends."""
        self.state = DeviceState.IDLE
        await self.adb.turn_screen_off()
        await self.adb.disable_wifi_scan()
        await self.adb.kill_background_apps()
        await self.adb.set_brightness(0)
        # Battery consumption drops significantly in this state

    async def on_user_connect(self):
        """Called when a new user session starts."""
        self.state = DeviceState.ACTIVE
        await self.adb.turn_screen_on()
        await self.adb.set_brightness(128)
        # Only enable what the test profile requires
```

### The 35% Metric

The 35% reduction was measured by comparing average battery drain rate (% per hour) before and
after deploying the service:
- Before: devices averaged ~8% battery drain per hour when idle between test sessions
- After: devices averaged ~5.2% per hour in the optimized idle state
- That's approximately 35% less battery consumed per hour of idle time

This translated to significantly fewer manual interventions for charging and higher device
availability across the platform.

---

## 4. Data Transformation — Qualcomm Packet Parsing (40% Efficiency Improvement)

### The Problem

TMDC interacts with devices at a very low level — especially for automation and testing.
Qualcomm chipsets (which power most Android devices) expose diagnostic data as raw binary/text
packet dumps. These packets contain valuable information:
- Signal strength readings
- Network connection events
- Hardware state changes
- Diagnostic errors

But the raw format is not human-readable or queryable. It looks something like this:

```
[2024-01-15 12:34:56.789] PKT: 0x4A 0x7F type=DIAG_MSG id=0x0031 len=128 
payload: 00 1A 3F 00 00 00 45 7C B2 01 00 00 ...
[2024-01-15 12:34:56.812] PKT: 0x4A 0x7F type=LOG_MSG id=0x1537 len=64
payload: 54 65 6D 70 3A 33 38 2E 35 ...
```

The automation testing team needed this data in a structured, queryable format — not raw hex dumps.

### What You Built

A Python data transformation pipeline that:
1. Reads raw packet streams from device connections
2. Parses the binary/text format using regex patterns and custom parsers
3. Extracts meaningful fields (message type, timestamp, device ID, payload data)
4. Converts payloads into structured JSON/dictionary format
5. Routes the structured data to the automation testing team's systems

### How the Parsing Works

```python
import re
from datetime import datetime

# Pattern for the packet header
PACKET_PATTERN = re.compile(
    r'\[(?P<timestamp>[\d\-\s:\.]+)\]\s+'
    r'PKT:\s+0x[0-9A-F]+\s+0x[0-9A-F]+\s+'
    r'type=(?P<msg_type>\w+)\s+'
    r'id=(?P<msg_id>0x[0-9A-F]+)\s+'
    r'len=(?P<length>\d+)\s*'
    r'payload:\s*(?P<payload>[0-9A-Fa-f\s]+)'
)

def parse_packet(raw_line: str) -> dict | None:
    match = PACKET_PATTERN.match(raw_line)
    if not match:
        return None
    
    return {
        "timestamp": datetime.strptime(match.group("timestamp").strip(), "%Y-%m-%d %H:%M:%S.%f"),
        "type": match.group("msg_type"),
        "id": match.group("msg_id"),
        "length": int(match.group("length")),
        "payload_bytes": bytes.fromhex(match.group("payload").replace(" ", "")),
    }
```

### What Made It 40% More Efficient

The original parsing code had several performance problems:

**Problem 1 — Sequential file reading and parsing:**
The old code read one packet at a time, parsed it fully, processed it, then moved to the next.
For files with millions of packets, this was slow.

**Fix:** Batch processing — read chunks of data, apply regex over the entire chunk at once
(`re.finditer` over a large string), yielding parsed results as a generator.

**Problem 2 — Recompiling regex on every call:**
The original code defined the regex pattern inside the parsing function, causing Python to
recompile the regex on every single function call.

**Fix:** Pre-compile the regex once at module level (`re.compile(pattern)`) and reuse the
compiled object. This is minor per call but significant when called millions of times.

**Problem 3 — Unnecessary data copying:**
The old code converted parsed data through multiple intermediate formats — raw bytes to hex
string to list of ints back to bytes. Each conversion allocates memory and copies data.

**Fix:** Minimized intermediate representations. Parse directly from hex string to final format
without intermediate steps.

**Problem 4 — No streaming/buffering:**
The old code loaded entire files into memory before processing.

**Fix:** Streaming parser that reads and processes data in fixed-size chunks, keeping memory
usage constant regardless of file size.

Combined, these changes reduced the time to parse a standard daily device packet log from
~25 seconds to ~15 seconds — approximately 40% faster.

---

## 5. CI/CD Pipelines — GitHub Actions

### What Is CI/CD?

**CI (Continuous Integration):** Every time a developer pushes code to GitHub, automated checks
run immediately — linting, unit tests, integration tests. If anything fails, the team is notified
and the code is not merged. This catches bugs early.

**CD (Continuous Deployment/Delivery):** After code passes CI, it is automatically deployed to
production (or a staging environment). No manual "download the code, SSH to server, restart the
service" — it happens automatically and consistently.

### Why CI/CD Matters at TMDC

You have 80+ production servers. Deploying a code update manually to 80 servers:
- Takes hours of SSH-ing into each server
- Is error-prone (did you miss one? did the command fail silently on server #47?)
- Requires the entire team to coordinate (no one else can deploy until you finish)

With GitHub Actions:
- Push to `main` branch → CI runs tests → if tests pass → CD deploys to all servers automatically
- Every deployment is identical and reproducible
- Takes minutes, not hours
- Deployment history is tracked in GitHub (who deployed what, when, did it succeed)

### Your GitHub Actions Workflow

A typical workflow file at TMDC (`.github/workflows/deploy.yml`):

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pytest tests/ --tb=short

  build:
    needs: test  # Only runs if tests pass
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install pyinstaller pyarmor
      - run: pyarmor obfuscate --src="." main.py  # Code obfuscation
      - uses: actions/upload-artifact@v3
        with:
          name: obfuscated-build
          path: dist/

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v3
        with:
          name: obfuscated-build
      - name: Deploy to servers
        run: |
          # Deploy to all Zoho servers via SSH
          for server in ${{ secrets.SERVER_LIST }}; do
            scp -r dist/ user@$server:/opt/tmdc/
            ssh user@$server "cd /opt/tmdc && pm2 restart all"
          done
```

### Code Obfuscation — What and Why

**The problem:** TMDC's code runs on Zoho-managed servers. The code contains proprietary
algorithms and business logic that Tech Mahindra wants to protect as intellectual property.
If someone gains access to the server, they should not be able to read the source code easily.

**What obfuscation does:** Transforms readable Python/JavaScript source code into functionally
equivalent but unreadable code — variable names are replaced with meaningless strings, logic
is restructured to be hard to follow, strings are encrypted, control flow is flattened.

**Tools used:**
- Python: PyArmor — encrypts Python bytecode so it cannot be easily decompiled
- Node.js: javascript-obfuscator — mangles variable names, encrypts strings, adds dead code

**Important distinction:** Obfuscation is NOT encryption of data. It is a code protection
measure. It makes reverse engineering harder, not impossible. It is one layer of defense as
part of defense-in-depth.

### The Encryption Layer (100% Compliance)

Separate from code obfuscation, you also implemented encryption for data protection:

**Data in transit:** All API communication uses HTTPS (TLS). Internal service-to-service
communication also encrypted. Device telemetry data encrypted during transmission.

**Data at rest:** Sensitive configuration (API keys, database passwords) stored encrypted.
Device logs containing potentially sensitive test data encrypted before storage.

**The 100% compliance metric:** An internal security audit checked that all services met
data protection standards — no plaintext credentials in code, all API endpoints using HTTPS,
all sensitive data encrypted at rest. Your work achieved 100% pass rate on this audit.

---

## 6. NGINX

### What NGINX Does in Your Architecture

NGINX is a web server and reverse proxy. In TMDC's architecture, it sits in front of your
Python/Node.js services and handles several critical functions:

**Reverse proxy:** External requests come to NGINX first (port 80/443). NGINX routes them to
the correct internal service based on the URL path:
- `/api/devices/*` → routes to the Python device management service (port 5000)
- `/api/tests/*` → routes to the test orchestration service (port 5001)
- `/ws/device/*` → routes to the Node.js WebSocket service (port 3000)

This means the outside world only sees one server (NGINX on ports 80/443), while internally
you have many services on many ports.

**SSL termination:** NGINX handles HTTPS (decrypts incoming TLS traffic, encrypts outgoing).
Your internal Python/Node services don't need to deal with certificates — they communicate with
NGINX in plain HTTP on localhost. This simplifies service code.

**Load balancing:** If you have multiple instances of the device service running (for high
availability), NGINX distributes requests across them. If one instance crashes, NGINX stops
sending traffic to it.

**Static file serving:** Dashboard HTML/CSS/JS files are served directly by NGINX without
involving any Python/Node.js service — much faster.

### NGINX Configuration (simplified example)

```nginx
upstream device_service {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;  # second instance for load balancing
}

server {
    listen 443 ssl;
    server_name tmdc.techmahindra.com;

    ssl_certificate     /etc/ssl/certs/tmdc.pem;
    ssl_certificate_key /etc/ssl/private/tmdc.key;

    location /api/devices/ {
        proxy_pass http://device_service;
        proxy_set_header Host $host;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location / {
        root /var/www/tmdc-dashboard;
        index index.html;
    }
}
```

---

## 7. PM2 — Process Management

### What PM2 Is

PM2 is a process manager for Node.js (and also Python/other processes). On a production server,
you don't just run `python app.py` and leave it — if it crashes at 3 AM, it stays dead until
someone manually restarts it.

PM2 solves this:
- **Auto-restart:** If a process crashes, PM2 restarts it immediately (within seconds)
- **Process monitoring:** Shows CPU usage, memory usage, restart count for each managed process
- **Log management:** Captures stdout/stderr from all processes and writes to log files
- **Cluster mode:** Can run multiple instances of the same service (for multi-core utilization)
- **Startup hook:** Ensures processes restart after server reboot

### PM2 at TMDC

On each of the 80+ servers, PM2 manages all the running services:

```bash
# List all running processes on a server
pm2 list
# Output:
# ┌─────────────────────┬────┬─────────┬──────┬───────┬────────┬──────────┐
# │ Name                │ id │ mode    │ ↺    │ status│ cpu    │ memory   │
# ├─────────────────────┼────┼─────────┼──────┼───────┼────────┼──────────┤
# │ device-manager      │ 0  │ cluster │ 2    │ online│ 3%     │ 120MB    │
# │ telemetry-service   │ 1  │ fork    │ 0    │ online│ 1%     │ 85MB     │
# │ packet-parser       │ 2  │ fork    │ 0    │ online│ 12%    │ 200MB    │
# │ websocket-server    │ 3  │ cluster │ 0    │ online│ 5%     │ 150MB    │
# └─────────────────────┴────┴─────────┴──────┴───────┴────────┴──────────┘

# Restart a specific service after deployment
pm2 restart device-manager

# View logs for a service
pm2 logs telemetry-service --lines 100

# Monitor all services in real-time (CPU, memory, event loop)
pm2 monit
```

### What "Operated 80+ Production Servers" Means

Your daily operational work included:
- SSH-ing into servers to check service health via PM2
- Investigating alerts when a service crashed repeatedly (reading PM2 logs)
- Deploying updates — pulling new code, restarting services via PM2
- Monitoring resource usage — if a server's CPU or memory is consistently high, identifying
  which service is responsible
- Adding new servers to the fleet as the platform grew
- Coordinating maintenance windows for server OS updates

---

## 8. Structured Logging and Monitoring

### Why Structured Logging Matters

Normal print statements and basic logging:
```
ERROR: Something went wrong processing device D001
INFO: Device connected
WARNING: Timeout while fetching telemetry
```

This is unstructured. When you have 80 servers each running 5 services, all producing logs,
searching for "why did device D001 disconnect at 3:47 AM?" in millions of log lines is nearly
impossible.

**Structured logging** adds machine-readable context to every log entry:

```python
import structlog

logger = structlog.get_logger()

logger.info("device_connected",
    device_id="D001",
    server="srv-42",
    connection_type="usb",
    os="android",
    timestamp="2024-06-15T03:47:12Z"
)
```

Output (JSON format):
```json
{
  "event": "device_connected",
  "device_id": "D001",
  "server": "srv-42",
  "connection_type": "usb",
  "os": "android",
  "timestamp": "2024-06-15T03:47:12Z",
  "level": "info"
}
```

Now you can search across all servers: "show me all events where device_id=D001 in the last 24 hours,
sorted by timestamp." The structured fields make this trivial with log aggregation tools.

### Log Levels and When to Use Them

| Level | When to Use | Example |
|---|---|---|
| **DEBUG** | Verbose detail for development. Disabled in production. | "Parsing packet at offset 1024" |
| **INFO** | Normal operations worth recording. | "Device D001 connected successfully" |
| **WARNING** | Something unexpected but not broken. | "Telemetry response took 5s (expected < 2s)" |
| **ERROR** | Something failed but the service continues. | "Failed to store telemetry for D001: DB timeout" |
| **CRITICAL** | The service is about to crash or is in an unrecoverable state. | "Cannot connect to database after 10 retries, shutting down" |

### Monitoring and Alerting

Beyond logs, you monitor system health metrics:
- **CPU usage per service** (via PM2) — if consistently > 80%, service may need optimization or scaling
- **Memory usage** — watch for memory leaks (memory growing indefinitely)
- **Response time** of APIs — if P95 latency exceeds 2 seconds, something is wrong
- **Error rate** — if 5% of requests are returning 5xx errors, investigate immediately
- **Device availability** — percentage of devices in the pool that are online and ready

Alerts trigger when metrics cross thresholds — sent via email, Slack, or monitoring dashboards.

---

## 9. Docker (Containerization)

### What Docker Does

Docker packages your application with all its dependencies into a "container" — a lightweight,
isolated environment that runs identically regardless of the host machine.

Without Docker: "It works on my machine but not on the server" — because the server has a
different Python version, missing libraries, different OS configuration.

With Docker: You define exactly what Python version, which libraries, what system packages your
app needs in a `Dockerfile`. Docker builds an image — a snapshot of that environment. That
image runs identically on your laptop, on the CI server, on production servers.

### Dockerfile for a TMDC Python Service

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (for some Python packages that need C libraries)
RUN apt-get update && apt-get install -y libusb-1.0-0 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (cached layer — only rebuilds if requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the service
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
```

### Key Docker Concepts

**Image:** A read-only template containing the OS, dependencies, and code. Built once, runs many times.

**Container:** A running instance of an image. You can run 5 containers from the same image on the same machine — 5 independent copies of your service.

**Layer caching:** Docker caches each step in the Dockerfile. If only your Python code changes
(not requirements.txt), Docker skips the `pip install` step on rebuild because that layer hasn't
changed. Builds are fast.

**docker-compose:** For local development, you often need multiple services running together
(your service + a database + NGINX). `docker-compose.yml` defines all of them and starts them
with one command:

```yaml
version: '3'
services:
  device-service:
    build: ./device-service
    ports:
      - "5000:5000"
  telemetry-service:
    build: ./telemetry-service
    ports:
      - "5001:5001"
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

`docker-compose up` starts everything. `docker-compose down` stops everything.

---

## 10. SSH and Remote Server Management

### Why SSH Matters at TMDC

You manage 80+ servers that are not physically accessible. They could be in data centers across
different cities. SSH (Secure Shell) is how you access them remotely:

```bash
# Connect to a production server
ssh admin@srv-42.tmdc.internal

# Run a quick command without entering an interactive session
ssh admin@srv-42 "pm2 status"

# Copy a file to the server
scp build.tar.gz admin@srv-42:/opt/tmdc/deployments/

# Copy logs from the server for analysis
scp admin@srv-42:/var/log/tmdc/device-service.log ./local_analysis/
```

### SSH Key Authentication

Production servers don't use passwords — they use SSH keys:
- You have a private key on your machine (`~/.ssh/id_rsa`)
- The server has your public key in its authorized list (`~/.ssh/authorized_keys`)
- When you connect, SSH proves you have the private key without transmitting it — challenge/response

This is more secure than passwords (can't be brute-forced), auditable (each key is tied to
a person), and revocable (remove one person's key from servers without changing any passwords).

### Remote Troubleshooting Pattern

When you get an alert that a service is down on server srv-42:

```bash
# 1. Connect to the server
ssh admin@srv-42

# 2. Check all services
pm2 list

# 3. If packet-parser is in "errored" status, check recent logs
pm2 logs packet-parser --lines 200

# 4. The log might show: "OSError: [Errno 28] No space left on device"
# Check disk space
df -h

# 5. Find and clean large old log files
du -sh /var/log/tmdc/*
rm /var/log/tmdc/old-packet-dumps/*.gz

# 6. Restart the service
pm2 restart packet-parser

# 7. Confirm it's running
pm2 list
```

---

## 11. Zoho Server Management

### What Zoho Servers Are in This Context

Tech Mahindra uses Zoho-provided infrastructure for TMDC. These are managed cloud servers
where your services run. They differ from AWS/Azure in that they are part of an enterprise
agreement — the infrastructure is managed by Zoho's team, and you manage the software running on them.

Your responsibilities on these servers:
- Deploying your Python/Node.js services
- Configuring NGINX
- Managing PM2 processes
- Monitoring disk space, memory, CPU
- Coordinating with Zoho support for infrastructure issues (network, hardware failures)

The CI/CD pipeline deploys code to these servers automatically via SSH, and PM2 manages the
running processes.

---

## 12. Unit Testing

### Why Testing Matters at TMDC

When you push code that goes to 80 servers automatically via CI/CD, a bug in production affects
all 80 servers simultaneously. Tests are the safety net that prevents bad code from being deployed.

### What You Test

**Unit tests:** Test individual functions in isolation.
```python
# test_packet_parser.py
def test_parse_valid_packet():
    raw = '[2024-01-15 12:34:56.789] PKT: 0x4A 0x7F type=DIAG_MSG id=0x0031 len=4 payload: 1A 2B 3C 4D'
    result = parse_packet(raw)
    assert result is not None
    assert result["type"] == "DIAG_MSG"
    assert result["id"] == "0x0031"
    assert result["length"] == 4
    assert result["payload_bytes"] == b'\x1a\x2b\x3c\x4d'

def test_parse_invalid_packet():
    raw = 'some garbage data'
    result = parse_packet(raw)
    assert result is None

def test_parse_empty_payload():
    raw = '[2024-01-15 12:34:56.789] PKT: 0x4A 0x7F type=LOG_MSG id=0x0001 len=0 payload: '
    result = parse_packet(raw)
    assert result is not None
    assert result["length"] == 0
```

**Integration tests:** Test services communicating with each other — API returns correct response,
database stores data correctly.

**In CI pipeline:** `pytest tests/ --tb=short` runs all tests. If any fail, the build stops
and deployment does not happen.

---

## 13. What Each Resume Bullet Actually Means — Plain English

| Resume Statement | What Was Happening |
|---|---|
| "Scalable Python-based microservices for mobile device testing platform" | You wrote independent Python services (Flask/FastAPI) that each handled a specific responsibility — device management, telemetry collection, packet parsing. They communicated via REST APIs and ran as separate PM2 processes on 80+ servers. |
| "Reduced device battery consumption by 35%" | You built a service that intelligently manages device power states (screen off when idle, radios disabled when unnecessary, optimized charging cycles), reducing hourly battery drain from ~8% to ~5.2% during idle periods. |
| "RESTful APIs in Python (Flask/FastAPI) and Node.js (Express)" | Backend API endpoints that the frontend, other services, and automated systems call. Flask/FastAPI for Python services, Express for the Node.js WebSocket/connectivity layer. |
| "CI/CD pipelines using GitHub Actions with code obfuscation" | Automated build-test-deploy pipeline. Push code → tests run automatically → code is obfuscated (PyArmor/js-obfuscator) to protect IP → deployed to all 80 servers via SSH. No manual deployment steps. |
| "Encryption and obfuscation achieving 100% compliance" | Passed internal security audit: all APIs use HTTPS, all credentials encrypted, no plaintext secrets in code, source code obfuscated on servers to prevent reverse engineering. |
| "Optimized data transformation pipelines for Qualcomm chipset packet data, improving efficiency by 40%" | Rewrote the raw packet parser: pre-compiled regex, batch processing, streaming instead of loading entire files, eliminated unnecessary data copies. Parsing time dropped from ~25s to ~15s per daily log. |
| "Operated and monitored distributed backend services across 80+ production servers" | Daily operations: SSH into servers, check PM2 status, investigate alerts, deploy updates, clean up disk space, restart failed services, coordinate maintenance windows. |

---

*Last updated: August 2026*

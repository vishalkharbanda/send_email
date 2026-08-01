# Tech Mahindra (TMDC) — Interview Questions & Detailed Answers
> Software Engineer | Tech Mahindra, Noida | Dec 2023 – Present
> Project: TMDC (Tech Mahindra Device Cloud) | Jan 2024 – Present
> Written with full, real explanations — not one-liners

---

## Section 1 — Microservices and System Design

---

**Q1. Tell me about the TMDC project and your role in it.**

TMDC (Tech Mahindra Device Cloud) is a platform that gives QA teams and developers remote access
to real physical mobile devices — Samsung, iPhone, Pixel, OnePlus — without needing to physically
hold them. Testers connect through a browser, control the device remotely, run automated tests,
and get back results and telemetry data. The platform manages a fleet of devices connected to
80+ servers across multiple locations.

My role is backend engineering. I build and maintain the Python and Node.js microservices that
power the platform — device management, telemetry collection, data transformation, and APIs.
I also handle the CI/CD pipeline that deploys code across all servers, a battery optimization
service that reduced device battery drain by 35%, and day-to-day operations and monitoring of
the entire production server fleet.

---

**Q2. What is a microservices architecture? Why did TMDC use it?**

A microservices architecture means the system is split into many small, independent services,
each responsible for one thing. This is the opposite of a monolith, where everything lives in
one big application.

At TMDC we have separate services for:
- Device connection management (keeping live connections to phones)
- Test orchestration (queuing and running automated tests)
- Telemetry collection (battery, CPU, network stats from devices)
- Packet parsing (transforming raw Qualcomm data into structured format)
- User authentication
- WebSocket server (real-time screen streaming for remote control)

Why microservices? Three main reasons:

**Independent deployment:** If I fix a bug in the packet parser, I deploy only that service.
The device connection service, which keeps live user sessions running, is not touched. In a
monolith, every fix requires redeploying the entire system, which means brief downtime for
everything — including active user sessions.

**Independent scaling:** The telemetry service receives high volumes of data from hundreds of
devices. It might need 4 instances running. The user authentication service handles maybe 10
requests per minute — one instance is plenty. With microservices, I scale only what needs scaling.

**Fault isolation:** If the packet parser crashes because it encountered a malformed data format
it didn't handle, only that service goes down. Active device sessions continue unaffected.
If this were a monolith, a crash in one module crashes everything.

---

**Q3. How do your microservices communicate with each other?**

Two primary patterns:

**Synchronous (REST APIs):** When Service A needs an immediate response from Service B, it makes
an HTTP request and waits. For example, when the test orchestration service needs to know if a
device is available, it calls `GET /devices/D001/status` on the device management service and
waits for a 200 response with the device state.

This is straightforward but has a risk: if Service B is slow or down, Service A is blocked.
To mitigate this, all inter-service HTTP calls have timeouts (5 seconds typically) and circuit
breakers — if Service B has failed 5 times in a row, stop calling it for 30 seconds instead of
hammering a dead service.

**Asynchronous (events/messages):** When Service A needs to notify other services but doesn't
need a response. For example, when a device disconnects, the device management service publishes
a "device_disconnected" event. The telemetry service, dashboard service, and test orchestration
service each independently react to this event.

This decouples the services — the device management service doesn't need to know what other
services exist or care if they're currently running. It just publishes the event and moves on.

---

**Q4. How do you handle failures in a microservices system?**

Several strategies:

**Auto-restart with PM2:** Every service runs under PM2, which automatically restarts it within
seconds of a crash. Most transient failures (out-of-memory spike, unhandled exception) are
resolved by a quick restart.

**Health checks:** Every service exposes a `/health` endpoint. The load balancer (NGINX) calls
this every 30 seconds. If a service stops responding to health checks, NGINX stops routing
traffic to it — users never see a 500 error from a dead service.

**Timeouts and retries:** All inter-service calls have a timeout. If the device service doesn't
respond in 5 seconds, the caller retries once with exponential backoff. If the retry also fails,
it returns a graceful error to the user instead of hanging indefinitely.

**Graceful degradation:** If the telemetry service is down, device sessions still work — users
just don't see live battery/CPU stats. The system degrades gracefully rather than failing entirely.

**Monitoring and alerting:** If a service restarts more than 3 times in 10 minutes, an alert fires.
If response times exceed thresholds, an alert fires. If error rates exceed 5%, an alert fires.
These let us investigate and fix before users notice.

---

## Section 2 — REST APIs (Flask, FastAPI, Express)

---

**Q5. What is a REST API and what are the key design principles?**

REST (Representational State Transfer) is an architecture style for building web APIs. The key idea
is that you model your system as "resources" (things that exist — devices, tests, users) and
you interact with them through standard HTTP operations.

**Key principles:**

**Resources have URLs:**
- `/devices` — the collection of all devices
- `/devices/D001` — one specific device
- `/devices/D001/telemetry` — telemetry data for device D001
- `/tests/T123/results` — results for test T123

**HTTP methods define the action:**
- `GET` — read/fetch data (never changes anything on the server)
- `POST` — create something new
- `PUT` — update/replace something that exists
- `DELETE` — remove something
- `PATCH` — partially update something

**Stateless:** Each request contains everything needed to process it. The server does not remember
"you were on page 2 last time." If you need page 3, your request explicitly says `?page=3`.

**Standard HTTP status codes:**
- 200 OK — request succeeded
- 201 Created — a new resource was created (after POST)
- 400 Bad Request — client sent invalid data
- 401 Unauthorized — not logged in
- 403 Forbidden — logged in but don't have permission
- 404 Not Found — resource doesn't exist
- 500 Internal Server Error — server crashed or had an unhandled error

**JSON for request/response bodies:**
```json
// GET /devices/D001 response:
{
  "device_id": "D001",
  "model": "Samsung Galaxy S23",
  "os": "Android 14",
  "status": "available",
  "battery_level": 78,
  "server": "srv-42"
}
```

---

**Q6. What is the difference between Flask and FastAPI? Why use both?**

**Flask** is mature, minimal, and simple. It has been the standard Python web framework for over
a decade. It processes requests synchronously — one request at a time per worker process.
If you need to handle 100 simultaneous requests, you run 100 worker processes.

**FastAPI** is modern, built on top of Python's async/await. It processes requests asynchronously —
a single process can handle hundreds of concurrent requests. While waiting for a database query
or an external API call, it can process other incoming requests. Much more efficient for
I/O-bound workloads (which most APIs are).

Additional FastAPI advantages:
- Automatic input validation using Python type hints and Pydantic models
- Auto-generates OpenAPI documentation (Swagger UI)
- Built-in dependency injection for clean, testable code

**Why both at TMDC?** Some services were initially written in Flask when the platform was smaller
and simpler. As the platform grew and needed to handle more concurrent connections, newer services
were built with FastAPI. Rewriting the existing Flask services was not justified — they worked
fine for their traffic level.

**In an interview, you'd say:** "For new services at TMDC, I use FastAPI because of the built-in
async support, automatic validation, and better performance under concurrent load. Older services
still run Flask reliably and we migrate them to FastAPI when they need significant changes anyway."

---

**Q7. How do you handle authentication and authorization in your APIs?**

**Authentication** (who are you?): Users authenticate with JWT (JSON Web Tokens) or API keys.
When a user logs in, the auth service issues a JWT token containing their user ID and permissions.
Subsequent API calls include this token in the `Authorization: Bearer <token>` header.
Each microservice validates the token signature (without contacting the auth service again).

**Authorization** (what can you do?): The JWT contains roles/permissions. Middleware on each
endpoint checks: does this user's token include the permission needed for this action?
- Read-only users can `GET` device data but cannot `POST` commands
- Admin users can configure devices and manage the server fleet
- Automation service accounts can execute tests but cannot modify user permissions

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def require_admin(token = Depends(security)):
    user = validate_jwt(token.credentials)
    if "admin" not in user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

@app.delete("/devices/{device_id}", dependencies=[Depends(require_admin)])
async def remove_device(device_id: str):
    # Only admins can delete devices
    await device_service.remove(device_id)
    return {"status": "removed"}
```

---

**Q8. How do you design APIs for error handling?**

Consistent error responses across all services — consumers should always get the same error format
regardless of which service they're calling:

```json
{
  "error": {
    "code": "DEVICE_NOT_FOUND",
    "message": "Device D001 is not registered in the system",
    "details": null
  },
  "status": 404
}
```

**Error handling hierarchy:**

1. **Validation errors (400):** Input didn't match the expected schema. FastAPI handles this
   automatically with Pydantic — wrong types, missing required fields.

2. **Business logic errors (4xx):** The request is valid but can't be fulfilled. "Device is
   currently in use by another user" (409 Conflict). "You've exceeded your test quota" (429).

3. **Infrastructure errors (5xx):** The server failed. Database connection timeout, out of memory,
   unhandled exception. These should be caught, logged with full stack trace, and returned as
   500 with a generic error message (never expose internal error details to external callers).

```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception", error=str(exc), path=request.url.path, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}}
    )
```

---

## Section 3 — The Battery Optimization Service

---

**Q9. Explain the battery optimization service that achieved 35% reduction.**

The problem: TMDC has hundreds of real mobile devices that need to be available 24/7 for
testers. But devices drain battery — especially when the screen is on, radios are active, and
apps are running. When a device battery dies, it becomes unavailable until someone physically
intervenes. For a remote platform, this means downtime.

The solution: I built a Python service that intelligently manages device power states based on
their current usage status. The core insight is that most of the time, most devices are idle
(not actively being used by a tester). During these idle periods, they don't need full power.

**What the service does during idle (no active user session):**
- Turns the screen completely off (screen is the #1 battery drain)
- Reduces brightness to minimum when screen must be on
- Disables unnecessary radios: WiFi scanning, Bluetooth discovery, GPS
- Kills non-essential background processes
- Puts the device into a low-power mode defined by Android's power management APIs

**What happens when a user connects:**
- Screen turns on immediately
- Brightness set to functional level
- Required radios enabled based on test profile
- Background services that tests depend on are started

**How the 35% was measured:**
We tracked average battery drain rate (% per hour) across the device fleet:
- Before the service: devices averaged about 8% battery drain per hour when idle between sessions
- After: idle drain dropped to about 5.2% per hour
- That is (8 - 5.2) / 8 = 35% reduction in idle battery consumption

This directly translated to: fewer devices dying overnight, fewer manual interventions needed,
higher overall device availability percentage.

---

**Q10. How did you interact with the devices programmatically?**

For Android devices, we use **ADB (Android Debug Bridge)** — a command-line tool that lets you
communicate with an Android device connected via USB or network. ADB can:
- Turn screen on/off
- Adjust settings (brightness, WiFi, Bluetooth)
- Install/uninstall apps
- Run shell commands on the device
- Capture screenshots and video
- Push/pull files

In the battery service, I wrapped ADB commands in Python:

```python
import subprocess

class ADBDevice:
    def __init__(self, device_id: str):
        self.device_id = device_id
    
    def _run(self, command: str) -> str:
        result = subprocess.run(
            ["adb", "-s", self.device_id, "shell", command],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip()
    
    def turn_screen_off(self):
        # Simulate pressing the power button to turn screen off
        self._run("input keyevent KEYCODE_POWER")
    
    def set_brightness(self, level: int):
        self._run(f"settings put system screen_brightness {level}")
    
    def disable_wifi_scan(self):
        self._run("settings put global wifi_scan_always_enabled 0")
    
    def get_battery_level(self) -> int:
        output = self._run("dumpsys battery | grep level")
        # Output: "  level: 78"
        return int(output.split(":")[1].strip())
    
    def kill_background_apps(self):
        # Get list of running packages, kill non-essential ones
        packages = self._run("pm list packages -3")  # Third-party only
        for line in packages.split("\n"):
            pkg = line.replace("package:", "").strip()
            if pkg not in ESSENTIAL_PACKAGES:
                self._run(f"am force-stop {pkg}")
```

For iOS devices, a similar approach using Apple's tools (libimobiledevice, Xcode instruments),
though iOS gives less granular control over power management than Android.

---

## Section 4 — Data Pipelines and Packet Parsing

---

**Q11. Explain the Qualcomm packet parsing pipeline you optimized.**

Qualcomm chipsets (which power most Android devices) produce diagnostic data as raw packet streams.
When TMDC runs tests on these devices, we collect these diagnostic packets for analysis — they
contain information about signal strength, network events, hardware states, and errors.

The raw data looks like binary/text dumps with hex-encoded payloads. The automation testing team
needs this data in structured, queryable format (JSON) to write test assertions against it.

My job was building the parser that transforms raw packets into structured data:

```
Raw input:
[2024-01-15 12:34:56.789] PKT: 0x4A 0x7F type=DIAG_MSG id=0x0031 len=4 payload: 1A 2B 3C 4D

Structured output:
{
  "timestamp": "2024-01-15T12:34:56.789",
  "type": "DIAG_MSG",
  "id": "0x0031",
  "length": 4,
  "payload": {"signal_strength": -82, "network_type": "LTE", ...}
}
```

The parser uses regex patterns to extract the structured fields from each line, then interprets
the hex payload bytes based on the message type (different types have different payload formats).

---

**Q12. How did you achieve the 40% efficiency improvement?**

The original parser was written quickly and had several performance issues. I identified four problems
and fixed each one:

**Problem 1 — Regex recompilation:**
The original code defined the regex pattern inside the parsing function. Python's `re.match(pattern, text)`
compiles the regex to an internal state machine every time it's called. When called millions of
times (once per packet), compilation overhead adds up significantly.

Fix: `COMPILED_PATTERN = re.compile(pattern)` at module level — compile once, reuse everywhere.
This alone improved throughput by about 10% on our benchmark.

**Problem 2 — Line-by-line processing with full interpretation:**
The old code read one line from the file, fully parsed it (regex + payload interpretation +
dictionary construction), stored the result, then moved to the next line. This means the CPU
is alternating between I/O (reading) and computation (parsing) without overlap.

Fix: Batch processing. Read a large chunk of the file (say 10MB), apply `re.finditer(pattern, chunk)`
to extract all matches at once, then process all matches. This allows Python's I/O and regex engine
to work on larger contiguous data, which is more cache-friendly and avoids per-line function call overhead.

**Problem 3 — Unnecessary data copies:**
The old code extracted hex payload as a string ("1A 2B 3C 4D"), split it into a list of strings
(["1A", "2B", "3C", "4D"]), converted each to an int, then to a bytes object. Three intermediate
data structures, each allocating memory and copying data.

Fix: `bytes.fromhex(payload_string.replace(" ", ""))` — one operation, no intermediate copies.
Direct conversion from hex string to bytes object.

**Problem 4 — Loading entire files into memory:**
Some daily device logs are hundreds of MB. The old code did `data = file.read()` — loading
everything into RAM at once. On servers running multiple parsers simultaneously, this caused
memory pressure and sometimes triggered the OS OOM killer.

Fix: Streaming parser with fixed buffer size. Read 10MB at a time, process, discard, read next
chunk. Handle the edge case where a packet line straddles two chunks by keeping a small
"leftover" buffer at the end of each chunk.

Combined result: parsing time for a typical daily device log dropped from ~25 seconds to ~15 seconds.
That's a 40% reduction in processing time. Additionally, memory usage became constant (~50MB)
regardless of file size, eliminating the OOM issues.

---

**Q13. What is regex and how did you use it for packet parsing?**

Regex (Regular Expressions) is a pattern matching language for text. You define a pattern that
describes the structure of the text you're looking for, and the regex engine finds all matches.

For the packet parsing, the pattern needed to match lines with this structure:
```
[timestamp] PKT: 0xNN 0xNN type=TYPE_NAME id=0xNNNN len=NUMBER payload: HEX_BYTES
```

The regex:
```python
import re

PACKET_PATTERN = re.compile(
    r'\[(?P<timestamp>[\d\-\s:\.]+)\]\s+'     # [2024-01-15 12:34:56.789]
    r'PKT:\s+0x[0-9A-F]+\s+0x[0-9A-F]+\s+'   # PKT: 0x4A 0x7F
    r'type=(?P<msg_type>\w+)\s+'               # type=DIAG_MSG
    r'id=(?P<msg_id>0x[0-9A-F]+)\s+'          # id=0x0031
    r'len=(?P<length>\d+)\s*'                  # len=4
    r'payload:\s*(?P<payload>[0-9A-Fa-f\s]*)'  # payload: 1A 2B 3C 4D
)
```

Key regex elements:
- `(?P<name>...)` — named capture group. Whatever matches inside the parentheses is accessible by name.
- `\d+` — one or more digits
- `\s+` — one or more whitespace characters
- `[0-9A-F]+` — one or more hex characters
- `\w+` — one or more word characters (letters, digits, underscore)
- `*` vs `+` — zero-or-more vs one-or-more

Using named groups (`?P<timestamp>`) makes the code much more readable when extracting values:
```python
match = PACKET_PATTERN.match(line)
if match:
    timestamp = match.group("timestamp")
    msg_type = match.group("msg_type")
    # vs positional: match.group(1), match.group(2) — hard to maintain
```

---

## Section 5 — CI/CD and DevOps

---

**Q14. Explain your CI/CD pipeline with GitHub Actions.**

The pipeline has three stages: Test, Build, Deploy.

**Stage 1 — Test (runs on every push and every pull request):**
- Check out the code
- Set up the Python/Node.js environment
- Install dependencies
- Run linting (code style checks)
- Run unit tests and integration tests
- If any test fails, the pipeline stops. Code cannot be merged or deployed.

**Stage 2 — Build (runs only if tests pass, only on main branch):**
- Install build tools (PyArmor for Python obfuscation, javascript-obfuscator for Node.js)
- Obfuscate the source code (transforms readable code into protected, unreadable form)
- Package the obfuscated code as a build artifact
- Upload the artifact for the deploy stage

**Stage 3 — Deploy (runs only if build succeeds, only on main branch):**
- Download the build artifact
- Connect to all production servers via SSH (server list stored as GitHub Secrets)
- Copy the new build to each server
- Restart the relevant PM2 processes on each server
- Verify health check on each server (hit `/health` endpoint and confirm 200 response)

**Why this matters:** Without this pipeline, deploying to 80 servers means manually SSH-ing into
each one, copying files, restarting services, and checking they started correctly. That takes hours,
is error-prone, and blocks other work. With the pipeline: push to main, wait 10 minutes,
everything is deployed and verified automatically.

---

**Q15. What is code obfuscation and why did you implement it?**

Code obfuscation transforms your source code into a version that works identically but is
extremely hard for a human to read or reverse-engineer.

**Why at TMDC:** The code runs on Zoho-managed servers. While access is restricted, the
principle of defense-in-depth says: even if someone gains unauthorized access to the server,
they should not be able to simply read the source code and understand proprietary algorithms.
The code contains business logic, optimization strategies, and implementation details that
Tech Mahindra considers intellectual property.

**What obfuscation does:**

For Python (using PyArmor):
- Encrypts Python bytecode so it cannot be easily decompiled back to source
- The encrypted code needs a runtime helper to decrypt and execute
- Even if someone copies the `.pyc` files, standard decompilation tools produce garbled output

For Node.js (using javascript-obfuscator):
- Renames all variables and functions to meaningless strings (`handleDevice` → `_0x4a3f`)
- Encrypts string literals ("device_connected" → encrypted bytes decoded at runtime)
- Inserts dead code that doesn't affect functionality but confuses readers
- Transforms control flow (if/else becomes switch statements with computed indices)

Before obfuscation:
```javascript
function connectDevice(deviceId) {
    const device = findDevice(deviceId);
    if (device.status === 'available') {
        device.status = 'connected';
        return { success: true };
    }
    return { success: false, error: 'Device busy' };
}
```

After obfuscation:
```javascript
function _0x4a3f(_0x2b1c){var _0x5e8d=_0x1a2b(_0x2b1c);if(_0x5e8d['\x73\x74\x61\x74\x75\x73']===_0x3c4d('\x30\x78\x31')){_0x5e8d['\x73\x74...
```

**Important to clarify in an interview:** Obfuscation is NOT security by itself. It is one
layer of defense. It raises the cost of reverse engineering from "trivial" to "time-consuming."
Combined with access controls, encryption, and monitoring, it provides meaningful IP protection.

---

**Q16. What is GitHub Actions and how does it work?**

GitHub Actions is GitHub's built-in CI/CD platform. You define workflows as YAML files in the
`.github/workflows/` directory of your repository. GitHub watches for events (push, pull request,
schedule) and automatically executes the workflow steps.

Key concepts:
- **Workflow:** A YAML file defining the complete pipeline (test → build → deploy)
- **Trigger:** What starts the workflow (`on: push`, `on: pull_request`, `on: schedule`)
- **Job:** A collection of steps that run on one machine. Jobs can run in parallel or sequentially.
- **Step:** A single command or action within a job
- **Runner:** The machine (virtual server) that executes the job. `runs-on: ubuntu-latest` means
  GitHub provides a fresh Ubuntu VM for this job.
- **Secrets:** Sensitive values (SSH keys, server passwords) stored encrypted in GitHub settings.
  Referenced as `${{ secrets.SSH_KEY }}` — never visible in logs.
- **Artifacts:** Files produced by one job and consumed by another (the obfuscated build output).

```yaml
name: Deploy Pipeline

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install -r requirements.txt
      - run: pytest tests/

  deploy:
    needs: test  # Only runs after 'test' job succeeds
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to servers
        env:
          SSH_KEY: ${{ secrets.DEPLOY_SSH_KEY }}
        run: ./scripts/deploy.sh
```

---

**Q17. What is Docker and how do you use it at TMDC?**

Docker is a containerization tool. It packages your application plus all its dependencies (Python
version, library versions, system packages) into a portable "container" that runs identically
everywhere.

**The problem Docker solves:** Your Python service needs Python 3.10, specific versions of
Flask, specific system libraries for USB communication. On your development machine, everything
works. On the production server, it's Python 3.8 and a different library version — your code
crashes with a cryptic error. "Works on my machine" is a real and common problem.

**With Docker:** You define a `Dockerfile` that says exactly what your container needs. Docker
builds an image — a snapshot of that environment. That image runs identically on your laptop,
in CI, and on production servers. No more environment mismatches.

At TMDC, Docker is used for:
- Ensuring consistent deployment environments across all 80 servers
- Running integration tests in CI with exact production-like environments
- Isolating services from each other on shared servers (one container per service)
- Easy rollback — if a new version has issues, restart with the previous image

---

## Section 6 — Server Operations and Monitoring

---

**Q18. What does "operated and monitored 80+ production servers" mean in practice?**

It means I was responsible for keeping the entire production infrastructure healthy. On a daily
basis this involved:

**Deployment operations:**
- Pushing new code releases to servers (via CI/CD, but sometimes manual hotfixes)
- Verifying services started correctly after deployment (health checks, log inspection)
- Rolling back deployments when a new version caused issues

**Monitoring and alerting:**
- Watching monitoring dashboards for anomalies (high CPU, memory leaks, disk filling up)
- Responding to alerts: "Service X on server Y has crashed 5 times in 10 minutes"
- Tracking trends: "Server Z's disk usage has been growing 2% per day — will be full in 2 weeks"

**Troubleshooting:**
- SSH into a server to investigate why a service is failing
- Reading PM2 logs and application logs to identify the root cause
- Finding and fixing resource issues (full disk, exhausted file descriptors, network saturation)
- Coordinating with the Zoho infrastructure team when issues are hardware/network-level

**Maintenance:**
- Scheduling and performing server OS updates
- Rotating log files to prevent disk exhaustion
- Adding new servers to the fleet as the platform grew
- Decommissioning old servers

**On-call:**
- Being available during incidents — if the platform is down at 2 AM, I'm the one SSH-ing into
  servers to diagnose and fix. Understanding the system end-to-end is essential for quick incident resolution.

---

**Q19. How do you troubleshoot a failing service in production?**

Real example: I receive an alert at 3 PM — "packet-parser service on srv-42 is in error state."

Step-by-step:
```bash
# 1. SSH into the server
ssh admin@srv-42.tmdc.internal

# 2. Check PM2 status — which services are running/errored
pm2 list
# Output shows packet-parser in "errored" state with 12 restarts in the last hour

# 3. Check recent logs
pm2 logs packet-parser --lines 200
# Log shows: "OSError: [Errno 28] No space left on device"

# 4. Check disk space
df -h
# Output: /var/log is 100% full

# 5. Find what's consuming disk
du -sh /var/log/tmdc/*
# /var/log/tmdc/packet-dumps/ is 45GB — old, unrotated log files

# 6. Clean up old files (keep last 7 days)
find /var/log/tmdc/packet-dumps/ -mtime +7 -delete

# 7. Verify disk is freed
df -h
# /var/log is now 34% — healthy

# 8. Restart the service
pm2 restart packet-parser

# 9. Monitor for a few minutes
pm2 logs packet-parser --lines 20
# Service is processing normally again

# 10. Prevent recurrence: add log rotation config
# (either logrotate config or a cron job to clean old files daily)
```

Then I document the incident, add monitoring on disk usage for this server, and add log rotation
to prevent it from happening again.

---

**Q20. What is PM2 and how do you use it?**

PM2 is a production process manager. It runs your services and keeps them alive. Think of it as
a supervisor that watches your processes — if one crashes, PM2 immediately restarts it without
any human intervention.

Key capabilities I use daily:

**Process management:**
```bash
pm2 start main.py --name "packet-parser" --interpreter python3
pm2 start server.js --name "websocket-server" -i 4  # 4 instances (cluster mode)
pm2 restart packet-parser
pm2 stop telemetry-service
pm2 delete old-service
```

**Monitoring:**
```bash
pm2 list                     # Overview of all processes (status, CPU, memory, restarts)
pm2 monit                    # Real-time dashboard in terminal
pm2 logs packet-parser       # Stream logs from one service
pm2 logs --lines 500         # Last 500 lines across all services
```

**Cluster mode (for Node.js):**
Node.js is single-threaded. On a server with 8 CPU cores, one instance uses only 1 core.
`pm2 start server.js -i 4` launches 4 instances — PM2 load-balances requests across them,
utilizing 4 cores. If one instance crashes, PM2 restarts it while the other 3 continue serving.

**Startup hook:**
```bash
pm2 save         # Save current process list
pm2 startup      # Generate OS-level startup script
```
After this, if the server reboots (OS update, power issue), PM2 automatically starts and
restores all processes. No manual intervention needed.

---

**Q21. What is NGINX and how does it fit into your architecture?**

NGINX is a high-performance web server that acts as a reverse proxy — it sits in front of your
application services and handles incoming traffic.

In TMDC's architecture:
```
Internet → NGINX (port 443, HTTPS) → routes to internal services (ports 5000, 5001, 3000, etc.)
```

**What NGINX does for us:**

**SSL termination:** External traffic is encrypted (HTTPS). NGINX decrypts it so your internal
services don't need to manage SSL certificates. Service code is simpler.

**Routing:** NGINX looks at the request URL and forwards to the correct service:
- `/api/devices/*` → Python device service (port 5000)
- `/api/tests/*` → Python test orchestration (port 5001)
- `/ws/*` → Node.js WebSocket server (port 3000)
- `/` → static dashboard files (served directly by NGINX)

**Load balancing:** For services with multiple instances, NGINX distributes requests evenly.

**Static files:** Dashboard HTML/CSS/JS served directly by NGINX — never hits your application
servers. NGINX serves static files much faster than Python/Node.js can.

**Rate limiting:** NGINX can throttle excessive requests from one IP, protecting backend services
from being overwhelmed.

---

## Section 7 — Security and Encryption

---

**Q22. How did you achieve 100% compliance with security standards?**

An internal security audit evaluated all services against a checklist. I ensured:

**All communication encrypted in transit:**
- All external APIs served over HTTPS (TLS 1.2+) via NGINX
- Inter-service communication on shared servers uses localhost (no network exposure)
- Service-to-service calls on different servers use mutual TLS or VPN

**No credentials in source code:**
- Database passwords, API keys, SSH keys — stored as environment variables or in a secrets manager
- Never committed to Git (`.gitignore` includes all `.env` files, checked with git-secrets hook)
- In CI/CD: stored as GitHub Secrets, injected at deploy time

**Source code protected on servers:**
- Python code obfuscated with PyArmor — bytecode encrypted, not human-readable
- Node.js code obfuscated — variable names mangled, strings encrypted
- File permissions: only the service user can read the code files (`chmod 700`)

**Input validation on all endpoints:**
- All API inputs validated (type, length, format) before processing
- SQL queries use parameterized statements (no SQL injection possible)
- File paths sanitized (no path traversal attacks)
- Request size limits enforced to prevent denial-of-service

**Logging hygiene:**
- Logs never contain passwords, tokens, or full credit card numbers
- Sensitive fields are masked in logs: `"auth_token": "***REDACTED***"`

The audit checked 50+ specific items. After my security hardening work, all 50 passed — 100% compliance.

---

## Section 8 — Performance and Optimization

---

**Q23. How do you identify and fix performance bottlenecks in production?**

I follow a systematic approach:

**Step 1 — Identify the symptom:**
"API response time for /devices endpoint has increased from 200ms to 2 seconds."

**Step 2 — Determine where time is spent:**
Add timing logs or use profiling:
```python
import time

@app.get("/devices")
async def list_devices():
    t1 = time.time()
    devices = await db.query("SELECT * FROM devices")  # Is the DB slow?
    t2 = time.time()
    result = [transform(d) for d in devices]  # Is transformation slow?
    t3 = time.time()
    
    logger.info("timing", db_ms=(t2-t1)*1000, transform_ms=(t3-t2)*1000)
    return result
```

**Step 3 — Fix the bottleneck:**
If DB is slow: check query plan (EXPLAIN), add missing indexes, optimize the query.
If transformation is slow: profile the transform function, find the expensive operation.
If the service itself is fine but NGINX/network is slow: check connection pooling, keep-alive settings.

**Common optimizations I've done at TMDC:**
- Added database connection pooling (reuse connections instead of creating new ones per request)
- Added response caching for device status queries that don't change every second
- Pre-compiled regex patterns instead of recompiling on each call
- Used streaming responses for large data downloads instead of loading everything in memory
- Moved heavy computation to background tasks, returning 202 Accepted immediately

---

**Q24. What is connection pooling and why does it matter?**

Opening a database connection is expensive — TCP handshake, authentication, SSL negotiation.
If every API request opens a new connection, uses it for one query, then closes it, you waste
time on setup/teardown for every single request.

**Connection pool:** You create N connections upfront and keep them open. When a request needs
to talk to the database, it borrows a connection from the pool, uses it, and returns it.
No setup/teardown per request. The next request immediately gets a pre-opened connection.

```python
# Without pooling: ~50ms overhead per request to establish connection
connection = create_connection()  # Expensive
result = connection.query("SELECT ...")
connection.close()

# With pooling: ~0ms overhead — connection is already open
async with pool.acquire() as connection:  # Instant - borrows from pool
    result = await connection.query("SELECT ...")
# Connection returned to pool, stays open for next request
```

At TMDC, this was especially important for the telemetry service that receives hundreds of
device updates per minute — connection pooling reduced average response time significantly.

---

## Section 9 — Behavioral / Situational Questions

---

**Q25. Tell me about yourself and your current role.**

I'm working as a Software Engineer at Tech Mahindra, Noida, since December 2023. My main
project is TMDC — Tech Mahindra Device Cloud — a platform that provides remote access to real
mobile devices for testing and automation.

I work primarily on the backend — building Python microservices with Flask and FastAPI, maintaining
Node.js services with Express, implementing CI/CD pipelines with GitHub Actions, and managing
the production infrastructure of 80+ servers. My key achievements include building a battery
optimization service that reduced device battery drain by 35%, optimizing our Qualcomm packet
parsing pipeline by 40%, achieving 100% security audit compliance through encryption and
obfuscation implementation, and running the day-to-day operations of the production fleet.

Before Tech Mahindra, I worked at XenonStack as a Data Engineer building real-time ETL pipelines
and a UPI fraud detection system. So I bring both backend engineering and data engineering perspectives.

---

**Q26. What was the most challenging bug or issue you faced at Tech Mahindra?**

One of the trickiest issues was a memory leak in the telemetry collection service that only
manifested after several days of running in production.

**Symptoms:** PM2 showed the telemetry service's memory growing by about 50MB per day. After
4-5 days it would consume all available RAM and get killed by the OS. PM2 would restart it,
but then the cycle repeated.

**Investigation:**
- Added memory profiling hooks to the service
- Discovered that device connection objects were being added to an in-memory dictionary when
  devices connected, but never removed when they disconnected (a forgotten cleanup step)
- Over days, with hundreds of connect/disconnect cycles, thousands of stale connection objects
  accumulated

**Fix:**
- Added proper cleanup in the disconnect handler
- Added a background sweep task that checks for stale entries every hour (defense in depth)
- Added a memory usage metric to monitoring so we would catch similar issues early in the future

**Lesson:** Memory leaks don't show up in unit tests because tests run for seconds, not days.
You need production monitoring and the discipline to investigate slow resource growth, not just
sudden crashes.

---

**Q27. How do you handle deploying to 80+ servers when something goes wrong?**

We use a **rolling deployment** strategy. The CI/CD pipeline doesn't deploy to all 80 servers
simultaneously. It deploys to 5 servers at a time, runs health checks, and only proceeds to
the next batch if the health checks pass.

If a health check fails after deploying to the first 5 servers:
1. Pipeline stops automatically
2. Alert fires to the team
3. The 5 affected servers are rolled back (restart with previous version)
4. I investigate what went wrong, fix it, and the next deployment goes through the full pipeline again

This limits the blast radius: at worst, 5 out of 80 servers have the bad version for a few
minutes before rollback. Not the entire fleet.

For critical hotfixes that need to go out fast, we can override and deploy to all servers at once,
but this is rare and requires explicit approval.

---

**Q28. How do you prioritize work when you have multiple things to do?**

At TMDC, my work typically falls into three categories:

1. **Production incidents (immediate):** If a service is down or users are affected, this takes
   priority over everything. Fix the issue, get production stable, then investigate root cause.

2. **Feature development (planned):** Building new services, new endpoints, optimizing existing
   code. This is sprint-planned work with deadlines and story points. I break large features into
   smaller PRs for easier review and safer deployment.

3. **Technical debt / improvements (scheduled):** Upgrading dependencies, improving monitoring,
   adding tests for uncovered code paths. I allocate time for this each sprint to prevent the
   codebase from degrading.

Production incidents override everything. Within feature work, I prioritize based on sprint
commitments and discuss with the tech lead if priorities conflict.

---

**Q29. How do you ensure code quality in your team?**

Several practices:

**Code reviews:** Every PR must be reviewed by at least one other engineer before merging.
Reviews check for logic errors, security issues, performance concerns, and adherence to team conventions.

**Automated testing in CI:** Unit tests and integration tests run automatically on every push.
PRs cannot be merged if tests fail.

**Linting:** Automated code style enforcement (flake8 for Python, ESLint for Node.js). Consistent
formatting across the codebase.

**Structured PR descriptions:** Every PR has: what changed, why, how to test, any deployment notes.
This makes reviews faster and serves as documentation.

**Post-incident reviews:** After production issues, we do a blameless review: what happened,
why, how we detected it, how we fixed it, and what we'll do to prevent it from recurring.
This improves the system over time.

---

*Last updated: August 2026*

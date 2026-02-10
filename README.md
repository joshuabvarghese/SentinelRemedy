# SentinelRemedy 🔄

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)

> **Autonomous Database Reliability Engine for PostgreSQL**

SentinelRemedy is a proactive Site Reliability Engineering (SRE) solution designed to maintain high availability for PostgreSQL databases. It bridges the gap between simple container restarts and complex orchestration by implementing intelligent health checks, automated log preservation, and instant incident notification.

---

## 🌟 Core SRE Principles Implemented

### MTTR Reduction
Automates the detection-to-recovery pipeline, reducing the **Mean Time To Recovery** from minutes of manual intervention to seconds of autonomous action.

### Observability & Forensics
Implements a **"Log-First" recovery strategy**. Before a service is restarted, the system snapshots database logs to AWS S3, ensuring root cause analysis (RCA) is possible even after a "clean" restart.

### Error Budget Protection
Prevents unnecessary downtime by using configurable retry/threshold logic to distinguish between transient blips and hard failures.

### Infrastructure as Code (IaC)
Environment parity is maintained through Docker Compose (Local) and Terraform (AWS).

---

## 🏗️ Technical Architecture

The system operates as a **Sidecar Monitor** pattern:

```
┌─────────────────────────────────────────────┐
│          SentinelRemedy Monitor             │
├─────────────────────────────────────────────┤
│                                             │
│  1. Monitor (Python)                        │
│     └─ Executes SQL-level probes            │
│                                             │
│  2. Snapshotter                             │
│     └─ Triggers boto3 upload to S3          │
│        (/var/lib/postgresql/data/pg_log)    │
│                                             │
│  3. Healer                                  │
│     └─ Issues docker-compose restart        │
│                                             │
│  4. Notifier                                │
│     └─ Dispatches JSON to Discord/Slack     │
│                                             │
└─────────────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   PostgreSQL Database │
        └───────────────────────┘
```

### Workflow

1. **Monitor** executes SQL-level probes against the target database
2. **Snapshotter** uploads logs to S3 upon failure detection
3. **Healer** restores service via orchestration commands
4. **Notifier** sends recovery status to configured webhooks

---

## 🚀 Getting Started

### Prerequisites

- **Docker** & **Docker Compose** (v2.0+)
- **(Optional)** AWS credentials for S3 logging
- **(Optional)** Slack/Discord webhook for alerting

### Installation

Clone the repository and set up the environment:

```bash
git clone https://github.com/your-username/SentinelRemedy.git
cd SentinelRemedy
chmod +x quickstart.sh test_system.sh
```

### Configuration

The system uses environment variables for security and configuration:

```bash
# Copy the template
cp .env.template .env

# Edit with your credentials
nano .env
```

**Required Environment Variables:**

```bash
# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_NAME=yourdb
DB_USER=youruser
DB_PASSWORD=yourpassword

# AWS S3 (Optional - for log archival)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=sentinel-remedy-logs

# Alerting (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK/URL

# Monitor Configuration
HEALTH_CHECK_INTERVAL=30
FAILURE_THRESHOLD=3
```

### Launch

The quickstart script handles network creation and container builds:

```bash
./quickstart.sh
```

**What happens:**
- Creates Docker network
- Builds monitor container
- Starts PostgreSQL database
- Begins automated health monitoring

---

## 🧪 Chaos Engineering (Testing)

Validate the self-healing capability by manually simulating a database failure:

```bash
./test_system.sh
```

### Expected Outcome

```
1. ❌ Monitor detects 0/3 health checks
2. 📤 Logs are pushed to S3 (if configured)
3. 🚨 Alert notification sent
4. 🔄 Database container restarted
5. ✅ Recovery notification sent once SQL probe passes
```

### Manual Testing

You can also manually test the system:

```bash
# Stop the database
docker-compose stop postgres

# Watch the monitor logs
docker-compose logs -f sentinel-monitor

# The system should automatically restart the database
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Language** | Python 3.11 |
| **Database Driver** | Psycopg2 |
| **Cloud SDK** | Boto3 (AWS) |
| **Runtime** | Docker / Alpine Linux |
| **Cloud Platform** | AWS (S3, EC2) |
| **IaC** | Terraform |
| **Alerting** | Slack/Discord Webhooks |

---

## 📊 Monitoring & Observability

### Health Check Logic

```python
# Simplified pseudocode
failures = 0
while True:
    if sql_probe_succeeds():
        failures = 0
    else:
        failures += 1
        if failures >= FAILURE_THRESHOLD:
            archive_logs_to_s3()
            restart_database()
            send_alert()
    sleep(HEALTH_CHECK_INTERVAL)
```

### Log Preservation

All database logs are automatically archived to S3 before any restart operation, preserving critical forensic data for post-incident analysis.

**S3 Structure:**
```
s3://your-bucket/
└── sentinel-remedy-logs/
    └── {timestamp}-{db_name}/
        ├── postgresql.log
        ├── pg_hba.conf
        └── postgresql.conf
```

---

## 🔧 Advanced Configuration

### Custom Health Checks

Modify the health check query in `monitor/health_checker.py`:

```python
HEALTH_CHECK_QUERY = "SELECT 1;"  # Default
# Custom example:
HEALTH_CHECK_QUERY = "SELECT COUNT(*) FROM critical_table WHERE status = 'active';"
```

### Threshold Tuning

Adjust failure tolerance in `.env`:

```bash
FAILURE_THRESHOLD=3      # Number of consecutive failures before action
HEALTH_CHECK_INTERVAL=30 # Seconds between checks
```

---

## 📁 Project Structure

```
SentinelRemedy/
├── monitor/
│   ├── health_checker.py    # SQL probe logic
│   ├── log_archiver.py      # S3 upload handler
│   ├── healer.py            # Container restart logic
│   └── notifier.py          # Webhook dispatcher
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── docker-compose.yml
├── Dockerfile
├── .env.template
├── quickstart.sh
├── test_system.sh
└── README.md
```

---

## 🙏 Acknowledgments

- Built with SRE best practices in mind
- Inspired by the principles in Google's SRE Book
- Designed for teams who need reliability without complexity

---

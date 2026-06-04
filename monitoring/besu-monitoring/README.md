# DIGI4ECO Besu Monitoring Service

This service records lightweight machine and Docker resource usage for a Besu node host. It is designed for servers running the DIGI4ECO private Besu network.

The monitor is append-only: every run adds one compact JSON object to `logs/metrics.jsonl`. This avoids creating a new report file every hour and keeps historical data easy to query.

## What It Collects

- Host disk usage for `/`
- Host memory usage
- Host load average
- Docker CPU and memory usage for Besu containers
- Disk usage for important blockchain directories

Default containers:

```text
blockchain-validator1-1
blockchain-validator2-1
blockchain-validator3-1
blockchain-validator4-1
rpcnode
```

Default directories:

```text
/home/manos/blockchain
/home/manos/blockchain/config/besu
/home/manos/blockchain/logs/besu
/home/manos/blockchain/config/nodes/validator1
/home/manos/blockchain/config/nodes/validator2
/home/manos/blockchain/config/nodes/validator3
/home/manos/blockchain/config/nodes/validator4
```

## Files

```text
besu-monitoring/
├── besu_monitor.py
├── requirements.txt
├── scripts/
│   ├── install.sh
│   └── run_once.sh
├── systemd/
│   ├── besu-monitor.service.template
│   └── besu-monitor.timer
└── logs/
    └── .gitkeep
```

## Install As A Systemd Timer

From this directory on the server:

```bash
chmod +x scripts/*.sh
./scripts/install.sh
```

The installer copies the monitor to `/opt/digi4eco-besu-monitoring`, creates a Python virtual environment, installs dependencies, renders the systemd service, and enables the hourly timer.

You can override the install path or service user:

```bash
INSTALL_DIR=/home/manos/besu-monitoring SERVICE_USER=manos ./scripts/install.sh
```

## Service Commands

```bash
# Check timer status
sudo systemctl status besu-monitor.timer

# See scheduled runs
sudo systemctl list-timers | grep besu-monitor

# Run one collection immediately
sudo systemctl start besu-monitor.service

# Follow service logs
sudo journalctl -u besu-monitor.service -f
```

## Manual Test Run

Before installing systemd, you can run one sample locally:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./scripts/run_once.sh
```

This writes to `logs/metrics.jsonl` in the current directory unless `BESU_MONITOR_LOG_DIR` is set.

## Configuration

The defaults match the current DIGI4ECO Besu deployment, but these environment variables can override them:

```bash
export BESU_MONITOR_LOG_DIR=/var/log/digi4eco-besu-monitoring
export BESU_MONITOR_CONTAINERS=validator1,validator2,rpcnode
export BESU_MONITOR_DIRS=/home/manos/blockchain,/home/manos/blockchain/logs/besu
```

For systemd deployments, add overrides with:

```bash
sudo systemctl edit besu-monitor.service
```

Example override:

```ini
[Service]
Environment=BESU_MONITOR_CONTAINERS=blockchain-validator1-1,blockchain-validator2-1,rpcnode
Environment=BESU_MONITOR_DIRS=/home/manos/blockchain,/home/manos/blockchain/logs/besu
```

Then reload and restart the timer:

```bash
sudo systemctl daemon-reload
sudo systemctl restart besu-monitor.timer
```

## Reading Current And Historical Data

Latest sample:

```bash
tail -n 1 /opt/digi4eco-besu-monitoring/logs/metrics.jsonl | python3 -m json.tool
```

Last 24 samples:

```bash
tail -n 24 /opt/digi4eco-besu-monitoring/logs/metrics.jsonl
```

Disk and memory history:

```bash
jq -r '[.timestamp, .system.disk.percent, .system.memory.percent] | @tsv' \
  /opt/digi4eco-besu-monitoring/logs/metrics.jsonl
```

RPC node CPU and memory history:

```bash
jq -r '[.timestamp, .containers.rpcnode.cpu_percent, .containers.rpcnode.memory.percent] | @tsv' \
  /opt/digi4eco-besu-monitoring/logs/metrics.jsonl
```

Blockchain directory size history:

```bash
jq -r '[.timestamp, .directories["/home/manos/blockchain"].size] | @tsv' \
  /opt/digi4eco-besu-monitoring/logs/metrics.jsonl
```

## Log Files

- `logs/metrics.jsonl`: append-only historical metrics, one JSON object per run
- `logs/monitor.log`: monitor service execution log

Runtime logs are ignored by git.

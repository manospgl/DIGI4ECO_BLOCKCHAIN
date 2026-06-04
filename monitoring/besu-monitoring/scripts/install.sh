#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

INSTALL_DIR="${INSTALL_DIR:-/opt/digi4eco-besu-monitoring}"
SERVICE_USER="${SERVICE_USER:-$USER}"
SERVICE_GROUP="${SERVICE_GROUP:-$(id -gn "$SERVICE_USER")}"

echo "Installing Besu monitor to $INSTALL_DIR"
echo "Service user: $SERVICE_USER:$SERVICE_GROUP"

sudo mkdir -p "$INSTALL_DIR" "$INSTALL_DIR/logs"
sudo rsync -a \
  --exclude ".git" \
  --exclude "venv" \
  --exclude "logs" \
  "$PROJECT_DIR"/ "$INSTALL_DIR"/

sudo python3 -m venv "$INSTALL_DIR/venv"
sudo "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
sudo "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
sudo chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"

export INSTALL_DIR SERVICE_USER SERVICE_GROUP
python3 - <<'PY' | sudo tee /etc/systemd/system/besu-monitor.service >/dev/null
import os
from pathlib import Path

template = Path(os.environ["INSTALL_DIR"]) / "systemd" / "besu-monitor.service.template"
content = template.read_text()
content = content.replace("__INSTALL_DIR__", os.environ["INSTALL_DIR"])
content = content.replace("__SERVICE_USER__", os.environ["SERVICE_USER"])
content = content.replace("__SERVICE_GROUP__", os.environ["SERVICE_GROUP"])
print(content, end="")
PY

sudo cp "$INSTALL_DIR/systemd/besu-monitor.timer" /etc/systemd/system/besu-monitor.timer
sudo systemctl daemon-reload
sudo systemctl enable --now besu-monitor.timer

echo "Besu monitor installed."
echo "Check timer: sudo systemctl status besu-monitor.timer"
echo "Run once:    sudo systemctl start besu-monitor.service"

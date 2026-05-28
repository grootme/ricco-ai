#!/bin/bash
set -e

BENCH_DIR="/home/frappe/frappe-bench"
WORKSPACE="/workspace"
# These credentials are intentionally simple – this is a local dev environment only.
MARIADB_ROOT_PASSWORD="${MARIADB_ROOT_PASSWORD:-123}"

# ---------------------------------------------------------------------------
# CI mode: only verify that required tooling is present inside the container.
# The full bench + site setup only makes sense in an interactive Codespace.
# ---------------------------------------------------------------------------
if [ "${CI:-false}" = "true" ]; then
	echo "CI mode detected – skipping full bench setup."
	echo ""
	echo "Tool versions:"
	bench --version
	python --version
	node --version
	echo ""
	echo "Container environment verified successfully."
	exit 0
fi

# Skip if bench has already been initialised (e.g. after a container restart)
if [ -d "$BENCH_DIR/apps/frappe" ]; then
	echo "Bench already initialised, skipping setup."
	exit 0
fi

# ---------------------------------------------------------------------------
# Wait for MariaDB to be ready
# ---------------------------------------------------------------------------
echo "Waiting for MariaDB..."
until mariadb --host mariadb --port 3306 -u root -p"${MARIADB_ROOT_PASSWORD}" -e "SELECT 1" &>/dev/null; do
	sleep 2
done
echo "MariaDB is ready."

# ---------------------------------------------------------------------------
# Initialise frappe bench
# ---------------------------------------------------------------------------
echo "Initialising frappe-bench..."
bench init --skip-redis-config-generation "$BENCH_DIR"
cd "$BENCH_DIR"

# Point bench at the containerised services
bench set-mariadb-host mariadb
bench set-redis-cache-host redis:6379
bench set-redis-queue-host redis:6379
bench set-redis-socketio-host redis:6379

# Redis and the asset watcher are managed outside bench in this environment
sed -i '/redis/d' ./Procfile
sed -i '/watch/d' ./Procfile

# ---------------------------------------------------------------------------
# Install the gameplan app from the workspace (symlinked so edits are live)
# ---------------------------------------------------------------------------
echo "Linking gameplan app from workspace..."
ln -sfn "$WORKSPACE" apps/gameplan
./env/bin/pip install -e apps/gameplan

# ---------------------------------------------------------------------------
# Create the development site
# ---------------------------------------------------------------------------
echo "Creating development site..."
bench new-site gameplan.localhost \
	--force \
	--mariadb-root-password "${MARIADB_ROOT_PASSWORD}" \
	--admin-password admin \
	--no-mariadb-socket

bench --site gameplan.localhost install-app gameplan
bench --site gameplan.localhost set-config developer_mode 1
bench --site gameplan.localhost set-config mute_emails 1
bench --site gameplan.localhost add-user alex@example.com \
	--first-name Alex \
	--last-name Scott \
	--password 123 \
	--user-type "System User" \
	--add-role "Gameplan Admin"
bench use gameplan.localhost

# ---------------------------------------------------------------------------
# Set up the frontend
# ---------------------------------------------------------------------------
echo "Setting up frontend..."
cd "$WORKSPACE"
git submodule update --init
cd frontend && yarn install && cd ..

echo ""
echo "============================================================"
echo " Gameplan dev environment is ready!"
echo ""
echo " Start the backend:  cd ~/frappe-bench && bench start"
echo " Start the frontend: cd /workspace/frontend && yarn dev"
echo ""
echo " Backend  → http://localhost:8000"
echo " Frontend → http://localhost:8080/g"
echo ""
echo " Login: alex@example.com / 123"
echo "============================================================"

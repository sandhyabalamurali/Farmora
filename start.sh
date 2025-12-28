#!/bin/bash
set -e

echo "🌾 Starting FarMora AI..."

# Create log directory for supervisor
mkdir -p /var/log/supervisor

# Start supervisor (which manages nginx and fastapi)
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf

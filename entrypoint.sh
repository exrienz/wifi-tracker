#!/bin/bash

# Ensure required directories exist and have correct permissions
mkdir -p /app/data /app/uploads /app/instance
chown -R appuser:appuser /app/data /app/uploads /app/instance

# Switch to appuser and run the application
exec su -s /bin/bash appuser -c "exec $*"
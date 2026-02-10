cat > test_system.sh << 'EOF'
#!/bin/bash
echo "🧪 Starting Self-Healing Test..."
echo "------------------------------"

# 1. Kill the database
echo "1. Simulating crash: Killing postgres_db container..."
docker-compose kill postgres

# 2. Wait and watch
echo "2. Waiting for monitor to detect failure (Check interval is 30s)..."
tail -f db_monitor.log | sed '/Recovery command executed successfully/ q'

echo "------------------------------"
echo "✅ SUCCESS: Monitor detected failure and restarted the database!"
EOF

chmod +x test_system.shs
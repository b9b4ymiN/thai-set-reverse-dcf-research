#!/bin/bash
# Monitor SET100 fetch progress

echo "=================================="
echo "SET100 FETCH MONITOR"
echo "=================================="

# Check if process is running
PID=$(ps aux | grep "python3 set100_fetcher.py" | grep -v grep | awk '{print $2}')
if [ -n "$PID" ]; then
    echo "✅ Process running (PID: $PID)"
    
    # Check memory usage
    MEM=$(ps -p $PID -o rss= | awk '{printf "%.1f MB", $1/1024}')
    echo "📊 Memory: $MEM"
    
    # Check runtime
    RUNTIME=$(ps -p $PID -o etimes= | awk '{printf "%d:%02d", $1/60, $1%60}')
    echo "⏱️  Runtime: $RUNTIME"
else
    echo "❌ Process not running"
fi

echo ""
echo "LATEST OUTPUT:"
tail -20 /tmp/claude-1000/-home-opc-RDCF/cd01452f-ba0f-4eb7-8075-5cc9e6a2a814/tasks/b82euazd4.output

echo ""
echo "=================================="

#!/bin/bash
# StockAnalysis.com Scraping Monitor
# Watch the scraping progress in real-time

while true; do
    clear
    echo "======================================================================"
    echo "     STOCKANALYSIS.COM SCRAPING MONITOR"
    echo "======================================================================"
    echo "🕐 Time: $(date '+%H:%M:%S %Y-%m-%d')"
    echo

    # Check if script is running
    if ps aux | grep -q "[s]crape_remaining_batches.py"; then
        echo "✅ Status: RUNNING"
        # Get PID
        PID=$(ps aux | grep "[s]crape_remaining_batches.py" | awk '{print $2}')
        echo "   PID: $PID"
    else
        echo "⚠️  Status: STOPPED or FINISHED"
    fi
    echo

    # Count stock files
    STOCK_COUNT=$(ls -1 data/processed/metadata/stockanalysis_*.json 2>/dev/null | wc -l)
    echo "📊 Progress: $STOCK_COUNT / 100 stocks"

    # Progress bar
    PERCENT=$((STOCK_COUNT))
    FILLED=$((PERCENT / 2))
    EMPTY=$((50 - FILLED))
    printf "   ["
    printf "%${FILLED}s" | tr ' ' '█'
    printf "%${EMPTY}s" | tr ' ' '░'
    printf "] %d%%\n" $PERCENT
    echo

    # Check batch results
    echo "📦 Batch Status:"
    BATCHES_DONE=0
    for i in {1..5}; do
        BATCH_FILE="data/processed/metadata/batch_${i}_results.json"
        if [ -f "$BATCH_FILE" ]; then
            # Get success count from batch file
            SUCCESS=$(grep -o '"successful": \[' "$BATCH_FILE" -A 100 | grep -c '".*\.BK"' || echo "0")
            echo "   ✅ Batch $i: $SUCCESS/20 stocks"

            # Check if batch had errors
            if grep -q '"aborted": true' "$BATCH_FILE"; then
                echo "      ⚠️  ABORTED: $(grep '"abort_reason"' "$BATCH_FILE" | cut -d'"' -f4)"
            fi
            BATCHES_DONE=$((BATCHES_DONE + 1))
        else
            if [ $i -le $BATCHES_DONE ]; then
                echo "   ❌ Batch $i: FAILED (no result file)"
            else
                echo "   ⏳ Batch $i: Pending"
            fi
        fi
    done
    echo

    # Latest stocks
    echo "📁 Latest Files (last 3):"
    ls -t data/processed/metadata/stockanalysis_*.json 2>/dev/null | head -3 | while read file; do
        basename "$file"
        ls -lh "$file" | awk '{print "   Size: " $5 ", Modified: " $6 " " $7 " " $8}'
    done
    echo

    # Check for rate limiting
    if grep -rq "rate" data/processed/metadata/batch_*.json 2>/dev/null; then
        echo "🚨 WARNING: Rate limiting detected!"
        grep -l "rate" data/processed/metadata/batch_*.json
    else
        echo "✅ No rate limiting detected"
    fi
    echo

    # Estimate remaining time
    if [ $STOCK_COUNT -gt 20 ] && [ $STOCK_COUNT -lt 100 ]; then
        # Calculate average time per stock (from start)
        # Started at 10:34, roughly 20 stocks in ~15 min = 45 sec/stock
        REMAINING=$((100 - STOCK_COUNT))
        ESTIMATED_MINUTES=$((REMAINING * 45 / 60))
        echo "⏱️  Estimated remaining: ~${ESTIMATED_MINUTES} minutes"
    fi

    echo "======================================================================"
    echo "Press Ctrl+C to stop monitoring (scraping continues)"
    echo "Refresh every 30 seconds..."
    sleep 30
done

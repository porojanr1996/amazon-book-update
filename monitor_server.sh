#!/bin/bash
# Monitor server for errors and issues

LOG_FILE="server.log"
ERROR_KEYWORDS=("ERROR" "WARNING" "Exception" "Traceback" "Error" "Failed" "✗" "❌")

echo "🔍 Monitoring server for issues..."
echo "Press Ctrl+C to stop"
echo ""

while true; do
    if [ -f "$LOG_FILE" ]; then
        # Check for new errors
        ERRORS=$(tail -50 "$LOG_FILE" | grep -iE "$(IFS='|'; echo "${ERROR_KEYWORDS[*]}")" | tail -5)
        
        if [ -n "$ERRORS" ]; then
            echo "⚠️  New issues detected:"
            echo "$ERRORS"
            echo ""
        fi
        
        # Check if server is responding
        if ! curl -s http://localhost:5001/api/scheduler-status > /dev/null 2>&1; then
            echo "❌ Server not responding!"
        fi
    fi
    
    sleep 5
done

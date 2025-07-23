#!/bin/bash

LOG_FILE="/var/log/httpd/access.log"
MAX_SIZE_BYTES=1073741824 # 1GB in bytes
JENKINS_URL="http://localhost:8080"
JOB_NAME="Task-04"
JENKINS_USER="admin"
API_TOKEN="1151a10ae5accfe386201e2990397d4e37" # Generate this in Jenkins user settings

# Get file size in bytes
FILE_SIZE=$(stat -c%s "$LOG_FILE")

if [ "$FILE_SIZE" -gt "$MAX_SIZE_BYTES" ]; then
    echo "Log file size ($FILE_SIZE bytes) exceeds 1GB. Triggering Jenkins job..."
    # Trigger Jenkins job remotely
    curl -X POST "$JENKINS_URL/job/$JOB_NAME/buildWithParameters" \
     --user "$JENKINS_USER:$API_TOKEN" \
     --data-urlencode "LOG_FILE_PATH=$LOG_FILE"
else
    echo "Log file size ($FILE_SIZE bytes) is within limits."
fi

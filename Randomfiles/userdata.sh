front end userdata

#!/bin/bash

# Ensure Nginx loads cleanly with the new instance's AWS network settings
systemctl restart nginx

=====================================

# --- NEW: Set Global Timezone to IST ---
timedatectl set-timezone Asia/Kolkata
systemctl restart rsyslog

# 1. Fetch the secure metadata token (IMDSv2)
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

# 2. Extract the Instance ID and the AWS Region
INSTANCE_ID=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/instance-id)
REGION=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/placement/region)

# 3. Get the current time (hh:mm) and date (YYYY-MM-DD)
CURRENT_TIME=$(date +"%H:%M")
CURRENT_DATE=$(date +"%Y-%m-%d")

# 4. Define your Base Name 
BASE_NAME="Sri-ASG"

# 5. Combine them into your unique format
FINAL_NAME="${BASE_NAME}-${CURRENT_TIME}-${CURRENT_DATE}"

# 6. Command the AWS CLI to update the Name tag
aws ec2 create-tags \
  --resources "$INSTANCE_ID" \
  --tags "Key=Name,Value=$FINAL_NAME" \
  --region "$REGION"

=======================================
Backend userdata

#!/bin/bash

# 1. Navigate to the exact directory shown in your terminal
cd /root/sri-backend-api

# 2. Start the Flask app using PM2
pm2 start app.py --interpreter python3 --name "flask-backend"

# 3. Save the PM2 process list so it survives any unexpected instance reboots
pm2 save

# 4. Generate and apply the startup script for the root user
pm2 startup systemd -u root --hp /root

==================================================

req.txt

Flask
boto3
pymysql
~=================================================npm install -g pm2
cd /etc/nginx/
 vi nginx.conf
 
   # Use the AWS VPC DNS resolver to dynamically resolve the Route 53 name
    resolver 169.254.169.253 valid=30s;
    
    location /api/ {
    # 1. Define the backend variable FIRST
    set $backend "http://10.0.3.77:8000";

    # 2. Strip /api from the URI path
    rewrite ^/api/(.*)$ /$1 break;

    # 3. Pass the rewritten request to the backend variable
    proxy_pass $backend;

    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
    ======================================

    sudo pm2 show flask-backend
     sudo pm2 logs flask-backend



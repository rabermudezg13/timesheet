#!/bin/bash

# Deployment script for Timesheet Reminder Generator
# Usage: ./deploy.sh

set -e

echo "🚀 Starting deployment for timesheet.fromcolombiawithcoffees.com"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as correct user (not root)
if [ "$EUID" -eq 0 ]; then
   echo -e "${RED}❌ Do not run as root. Run as your regular user.${NC}"
   exit 1
fi

# Pull latest code (if using git)
if [ -d .git ]; then
    echo -e "${YELLOW}📥 Pulling latest code...${NC}"
    git pull origin main || echo "Not using git or already up to date"
fi

# Install/update dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
pip install -r requirements.txt --quiet

# Check if systemd service exists
if systemctl list-unit-files | grep -q "timesheet.service"; then
    # Restart service
    echo -e "${YELLOW}🔄 Restarting Streamlit service...${NC}"
    sudo systemctl restart timesheet

    # Wait a moment for service to start
    sleep 2

    # Check service status
    if systemctl is-active --quiet timesheet; then
        echo -e "${GREEN}✅ Streamlit service running${NC}"
    else
        echo -e "${RED}❌ Streamlit service failed to start${NC}"
        sudo systemctl status timesheet
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Systemd service not found. Starting manually...${NC}"
    # Kill existing process if any
    pkill -f "streamlit run app.py" || true
    sleep 1
    # Start in background
    nohup streamlit run app.py --server.address=0.0.0.0 --server.port=8501 > streamlit.log 2>&1 &
    echo -e "${GREEN}✅ Streamlit started in background (PID: $!)${NC}"
fi

# No Nginx needed - Cloudflare handles everything!

echo ""
echo -e "${GREEN}✨ Deployment complete!${NC}"
echo ""
echo "📊 Status:"
if systemctl list-unit-files | grep -q "timesheet.service"; then
    sudo systemctl status timesheet --no-pager -l
else
    ps aux | grep "streamlit run app.py" | grep -v grep
fi

echo ""
echo "🌐 Access the app at:"
echo "   https://timesheet.fromcolombiawithcoffees.com"
echo ""
echo "📝 View logs:"
if systemctl list-unit-files | grep -q "timesheet.service"; then
    echo "   sudo journalctl -u timesheet -f"
else
    echo "   tail -f streamlit.log"
fi

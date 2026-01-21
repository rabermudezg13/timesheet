# ⚡ Quick Start - 5 Minutes to Deploy

Deploy Streamlit app to **timesheet.fromcolombiawithcoffees.com** using Cloudflare (NO Nginx!)

## 🎯 Prerequisites

- [x] Server with public IP
- [x] Domain in Cloudflare: `fromcolombiawithcoffees.com`
- [x] SSH access to server

## 🚀 Step-by-Step (5 Minutes)

### 1️⃣ On Your Server (2 min)

```bash
# Clone/upload app files to server
cd /home/your-username/
git clone <your-repo> Keona
cd Keona

# Install dependencies
pip install -r requirements.txt

# Open firewall port
sudo ufw allow 8501/tcp

# Create systemd service
sudo nano /etc/systemd/system/timesheet.service
```

Paste this (update paths):
```ini
[Unit]
Description=Timesheet Reminder Generator
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/Keona
ExecStart=/usr/local/bin/streamlit run app.py
Restart=always
RestartSec=10
StandardOutput=append:/home/your-username/Keona/streamlit.log
StandardError=append:/home/your-username/Keona/streamlit-error.log

[Install]
WantedBy=multi-user.target
```

Start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable timesheet
sudo systemctl start timesheet
sudo systemctl status timesheet  # Should show "active (running)"
```

### 2️⃣ In Cloudflare Dashboard (2 min)

1. **Add DNS Record:**
   - Go to **DNS** → **Records** → **Add record**
   - Type: `A`
   - Name: `timesheet`
   - IPv4 address: `[Your Server IP]`
   - Proxy status: ✅ **Proxied** (orange cloud)
   - Click **Save**

2. **Configure SSL:**
   - Go to **SSL/TLS** → **Overview**
   - Set encryption mode: **Flexible**

3. **Enable WebSockets:**
   - Go to **Network**
   - Toggle **WebSockets** → ON

### 3️⃣ Test (1 min)

Wait 30 seconds for DNS propagation, then visit:
```
https://timesheet.fromcolombiawithcoffees.com
```

You should see the Timesheet Reminder Generator! 🎉

## ✅ Verification Checklist

```bash
# On server - check Streamlit is running
sudo systemctl status timesheet
curl http://localhost:8501

# Check port is open
sudo netstat -tlnp | grep 8501

# From browser - should load with HTTPS
https://timesheet.fromcolombiawithcoffees.com
```

## 🔧 Quick Troubleshooting

**Error 522 (Connection Timed Out)?**
```bash
# Check firewall
sudo ufw status | grep 8501

# If not allowed:
sudo ufw allow 8501/tcp
```

**Streamlit not running?**
```bash
# Check status
sudo systemctl status timesheet

# View logs
sudo journalctl -u timesheet -f

# Restart
sudo systemctl restart timesheet
```

**WebSocket connection error?**
- Check Cloudflare **Network** → **WebSockets** is ON

## 🔄 Future Updates

Just run:
```bash
./deploy.sh
```

## 📖 Need More Help?

- Full guide: `CLOUDFLARE_SETUP.md`
- App docs: `README.md`

---

**That's it!** Your app is now live with:
- ✅ HTTPS (Cloudflare SSL)
- ✅ DDoS protection
- ✅ Global CDN
- ✅ Auto-restart on crash
- ✅ No Nginx needed!

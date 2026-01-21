# Cloudflare Setup for timesheet.fromcolombiawithcoffees.com

## 🌐 Overview

This guide covers deploying the Timesheet app **directly** behind Cloudflare (NO Nginx needed).
Streamlit runs on port 8501, Cloudflare handles SSL/TLS, caching, and security.

## 📋 Prerequisites

1. Domain: `fromcolombiawithcoffees.com` added to Cloudflare
2. Server with public IP address
3. Firewall allowing port 8501 (or custom port)

## 🚀 Deployment Steps

### 1. Configure Firewall (Allow Port 8501)

**Ubuntu/Debian with UFW:**
```bash
sudo ufw allow 8501/tcp
sudo ufw status
```

**CentOS/RHEL with firewalld:**
```bash
sudo firewall-cmd --permanent --add-port=8501/tcp
sudo firewall-cmd --reload
```

**AWS/Cloud Provider:**
- Add inbound rule: TCP port 8501 from anywhere (0.0.0.0/0)

### 2. Run Streamlit on Your Server

```bash
# Install dependencies
pip install -r requirements.txt

# Run in production mode (background)
nohup streamlit run app.py > streamlit.log 2>&1 &
```

**Or use systemd (recommended):**

Create systemd service file:
```bash
sudo nano /etc/systemd/system/timesheet.service
```

Content:
```ini
[Unit]
Description=Timesheet Reminder Generator
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/Keona
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/local/bin/streamlit run app.py
Restart=always
RestartSec=10
StandardOutput=append:/path/to/Keona/streamlit.log
StandardError=append:/path/to/Keona/streamlit-error.log

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable timesheet
sudo systemctl start timesheet
sudo systemctl status timesheet
```

### 3. Cloudflare DNS Setup

1. Log into Cloudflare Dashboard
2. Select domain: `fromcolombiawithcoffees.com`
3. Go to **DNS** → **Records**
4. Add A record:
   - **Type**: A
   - **Name**: timesheet
   - **IPv4 address**: [Your server IP]
   - **Proxy status**: ✅ Proxied (orange cloud)
   - **TTL**: Auto

### 4. Cloudflare SSL/TLS Configuration

1. Go to **SSL/TLS** → **Overview**
2. Set encryption mode: **Flexible**
   - **Flexible**: Cloudflare ↔️ User (HTTPS), Cloudflare ↔️ Your server (HTTP)
   - This is the simplest setup since Streamlit runs on HTTP (port 8501)
   - Cloudflare handles all SSL/TLS encryption for your users

**No SSL certificate needed on your server!** Cloudflare does all the HTTPS work.

### 5. Cloudflare Security Settings

#### Page Rules (Optional)
Go to **Rules** → **Page Rules**:

Rule 1: Cache bypass for dynamic content
- **URL**: `timesheet.fromcolombiawithcoffees.com/*`
- **Setting**: Cache Level = Bypass

Rule 2: Force HTTPS
- **URL**: `http://timesheet.fromcolombiawithcoffees.com/*`
- **Setting**: Always Use HTTPS

#### Firewall Rules
Go to **Security** → **WAF**:

Rule: Block bad bots
- **Expression**: `(cf.bot_management.score lt 30)`
- **Action**: Block

#### Speed Optimization
Go to **Speed** → **Optimization**:
- ✅ Auto Minify: HTML, CSS, JavaScript
- ✅ Brotli
- ✅ Early Hints

### 6. Verify Deployment

```bash
# Check Streamlit is running locally
curl http://localhost:8501

# Check systemd service
sudo systemctl status timesheet

# Check from outside (should use HTTPS via Cloudflare)
curl https://timesheet.fromcolombiawithcoffees.com

# Check port is accessible
sudo netstat -tlnp | grep 8501
```

You should see:
- Streamlit running on `0.0.0.0:8501`
- HTTPS working via Cloudflare
- WebSocket connections stable

## 🔧 Troubleshooting

### WebSocket Connection Issues

If Streamlit shows "Connection error":

1. Check Cloudflare WebSocket setting:
   - Go to **Network** → Enable **WebSockets**

2. Verify `.streamlit/config.toml` (already configured):
   ```toml
   [server]
   enableWebsocketCompression = true
   address = "0.0.0.0"
   ```

3. Check firewall allows port 8501:
   ```bash
   sudo ufw status
   ```

### Error 522 (Connection Timed Out)

- **Verify firewall allows port 8501:**
  ```bash
  sudo ufw allow 8501/tcp
  ```

- **Check Streamlit is running:**
  ```bash
  sudo systemctl status timesheet
  sudo netstat -tlnp | grep 8501
  ```

- **Check logs:**
  ```bash
  sudo journalctl -u timesheet -f
  tail -f streamlit.log
  ```

### Error 521 (Web Server Is Down)

- Streamlit process crashed or stopped
- Check status: `sudo systemctl status timesheet`
- Restart: `sudo systemctl restart timesheet`

### Port Already in Use

```bash
# Find process using port 8501
sudo lsof -i :8501

# Kill it if needed
sudo kill -9 <PID>

# Restart service
sudo systemctl restart timesheet
```

## 📊 Monitoring

View logs:
```bash
# Streamlit logs (systemd)
sudo journalctl -u timesheet -f

# Streamlit log files
tail -f /path/to/Keona/streamlit.log
tail -f /path/to/Keona/streamlit-error.log

# Check app status
sudo systemctl status timesheet
```

## 🔒 Security Checklist

- [x] HTTPS enabled via Cloudflare
- [x] Cloudflare proxy enabled (orange cloud)
- [x] Real IP forwarding configured
- [x] WAF rules enabled
- [x] Bot protection enabled
- [x] Rate limiting (optional - in Cloudflare dashboard)
- [x] DDoS protection (automatic with Cloudflare)

## 🚀 Quick Deploy Script

Already included! Use `deploy.sh`:
```bash
./deploy.sh
```

It will:
- Pull latest code (if using git)
- Install dependencies
- Restart Streamlit service
- Show status and logs

## 📱 Access URLs

- **Production**: https://timesheet.fromcolombiawithcoffees.com
- **Direct Server**: http://[YOUR_SERVER_IP]:8501 (for debugging only)
- **Local Development**: http://localhost:8501

## 🎯 Performance Tips

1. **Enable Cloudflare Caching** for static assets:
   - Go to **Caching** → **Configuration**
   - Cache Level: Standard

2. **Enable Cloudflare CDN** (automatic with proxy)

3. **Enable HTTP/3** in Cloudflare:
   - Go to **Network** → Enable **HTTP/3 (with QUIC)**

4. **Monitor with Cloudflare Analytics**:
   - Dashboard shows traffic, threats blocked, bandwidth saved

## 📞 Support

If you encounter issues:
1. Check Cloudflare status: https://www.cloudflarestatus.com/
2. Review Streamlit logs: `sudo journalctl -u timesheet -f`
3. Test direct server access: `curl http://localhost:8501`
4. Verify DNS propagation: `nslookup timesheet.fromcolombiawithcoffees.com`

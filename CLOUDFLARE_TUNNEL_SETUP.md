# Cloudflare Tunnel Setup for timesheet.fromcolombiawithcoffees.com

## 🌐 Overview

You're using **Cloudflare Tunnel** (Zero Trust), not direct DNS. This is MORE secure - no firewall ports needed!

Your tunnel ID: `3ddca40e-bf23-478d-af5b-ef489a997ad5.cfargotunnel.com`

## 🚀 Setup Steps

### 1. Run Streamlit on Your Server (localhost only)

```bash
# Install dependencies
pip install -r requirements.txt

# Run Streamlit (NO need for 0.0.0.0, just localhost)
streamlit run app.py
```

**Or use systemd:**

Create `/etc/systemd/system/timesheet.service`:
```ini
[Unit]
Description=Timesheet Reminder Generator
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/Keona
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
```

### 2. Configure Cloudflare Tunnel

Go to **Cloudflare Zero Trust Dashboard** → **Access** → **Tunnels**

#### Option A: Add Route to Existing Tunnel

1. Click on your existing tunnel (ID: `3ddca40e-bf23-478d-af5b-ef489a997ad5`)
2. Go to **Public Hostname** tab
3. Click **Add a public hostname**
4. Configure:
   - **Subdomain**: `timesheet`
   - **Domain**: `fromcolombiawithcoffees.com`
   - **Service**:
     - Type: `HTTP`
     - URL: `localhost:8501`
5. Click **Save**

#### Option B: Update cloudflared config file

If using config file (usually `/etc/cloudflared/config.yml` or `~/.cloudflared/config.yml`):

```yaml
tunnel: 3ddca40e-bf23-478d-af5b-ef489a997ad5
credentials-file: /path/to/credentials.json

ingress:
  # Add this route for timesheet
  - hostname: timesheet.fromcolombiawithcoffees.com
    service: http://localhost:8501

  # Your other routes (keep existing)
  - hostname: trackhelper.fromcolombiawithcoffees.com
    service: http://localhost:[PORT]

  # Catch-all rule (must be last)
  - service: http_status:404
```

Restart cloudflared:
```bash
sudo systemctl restart cloudflared
```

### 3. Add DNS Record (CNAME)

Go to **Cloudflare Dashboard** → **DNS** → **Records**

Add CNAME record:
- **Type**: CNAME
- **Name**: `timesheet`
- **Target**: `3ddca40e-bf23-478d-af5b-ef489a997ad5.cfargotunnel.com`
- **Proxy status**: ✅ Proxied (orange cloud)
- **TTL**: Auto

### 4. Verify

Visit: https://timesheet.fromcolombiawithcoffees.com

Should work immediately!

## 🔧 Fix trackhelper Issue

If trackhelper stopped working, check your tunnel config:

```bash
# View cloudflared status
sudo systemctl status cloudflared

# View cloudflared logs
sudo journalctl -u cloudflared -f

# Check config file
cat /etc/cloudflared/config.yml
# or
cat ~/.cloudflared/config.yml
```

**Common issue:** If you accidentally changed the tunnel config, restore it:

```yaml
tunnel: 3ddca40e-bf23-478d-af5b-ef489a997ad5
credentials-file: /path/to/credentials.json

ingress:
  # Your existing trackhelper route
  - hostname: trackhelper.fromcolombiawithcoffees.com
    service: http://localhost:[TRACKHELPER_PORT]

  # New timesheet route
  - hostname: timesheet.fromcolombiawithcoffees.com
    service: http://localhost:8501

  # Catch-all (must be last)
  - service: http_status:404
```

Then restart:
```bash
sudo systemctl restart cloudflared
```

## 🎯 Key Differences from Direct DNS

| Feature | Cloudflare Tunnel | Direct DNS |
|---------|------------------|------------|
| Firewall ports | ❌ None needed | ✅ Must open 8501 |
| Public IP | ❌ Not needed | ✅ Required |
| Security | ✅ More secure | ⚠️ Port exposed |
| Setup | ⚠️ Cloudflared required | ✅ Simple |
| Address binding | `localhost:8501` | `0.0.0.0:8501` |

## 📋 Checklist

- [x] Streamlit running on `localhost:8501`
- [x] Cloudflared tunnel running
- [x] Tunnel route added for `timesheet.fromcolombiawithcoffees.com`
- [x] DNS CNAME pointing to tunnel
- [x] trackhelper route still exists in config
- [x] Both sites accessible

## 🔍 Troubleshooting

### trackhelper not accessible

1. Check cloudflared status:
   ```bash
   sudo systemctl status cloudflared
   ```

2. View tunnel routes in dashboard:
   - Go to Zero Trust → Access → Tunnels
   - Click your tunnel
   - Check **Public Hostname** tab
   - Verify trackhelper route exists

3. Check DNS records:
   ```bash
   nslookup trackhelper.fromcolombiawithcoffees.com
   ```
   Should point to: `3ddca40e-bf23-478d-af5b-ef489a997ad5.cfargotunnel.com`

### timesheet not working

1. Check Streamlit is running:
   ```bash
   sudo systemctl status timesheet
   curl http://localhost:8501
   ```

2. Check tunnel logs:
   ```bash
   sudo journalctl -u cloudflared -n 50
   ```

3. Verify DNS:
   ```bash
   nslookup timesheet.fromcolombiawithcoffees.com
   ```

## 📖 Quick Commands

```bash
# Restart everything
sudo systemctl restart cloudflared
sudo systemctl restart timesheet

# Check status
sudo systemctl status cloudflared
sudo systemctl status timesheet

# View logs
sudo journalctl -u cloudflared -f
sudo journalctl -u timesheet -f
```

## 🚀 Deploy Script

The `deploy.sh` script still works - it only manages the Streamlit app, not the tunnel.

```bash
./deploy.sh
```

---

**Note:** With Cloudflare Tunnel, you don't need to worry about firewalls, port forwarding, or public IPs. Everything goes through the secure tunnel!

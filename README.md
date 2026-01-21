# Timesheet Reminder Generator

Streamlit app to generate email reminders for substitutes with missing timesheets.

## 🌐 Deployment

This app is configured to run at: **timesheet.fromcolombiawithcoffees.com**

## 🚀 Local Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will be accessible at:
- Local: http://localhost:8501
- Network: http://timesheet.fromcolombiawithcoffees.com:8501

## 📦 Production Deployment with Cloudflare

**Simple setup - NO Nginx needed!** Cloudflare handles SSL, security, and caching.

### Step 1: Configure Firewall (Allow Port 8501)

```bash
sudo ufw allow 8501/tcp
sudo ufw status
```

### Step 2: Create systemd Service

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
sudo systemctl status timesheet
```

### Step 3: Configure Cloudflare DNS

1. Log into Cloudflare Dashboard
2. Select domain: `fromcolombiawithcoffees.com`
3. Go to **DNS** → Add record:
   - **Type**: A
   - **Name**: timesheet
   - **IPv4**: [Your Server IP]
   - **Proxy**: ✅ Enabled (orange cloud)

### Step 4: Configure Cloudflare SSL

1. Go to **SSL/TLS** → Set to **Flexible**
2. Go to **Network** → Enable **WebSockets**

Done! Your app is now live at https://timesheet.fromcolombiawithcoffees.com

### Quick Deploy Script

Use the included `deploy.sh` for future updates:
```bash
./deploy.sh
```

### Full Setup Guide

See `CLOUDFLARE_SETUP.md` for complete instructions and troubleshooting.

## 🔧 Configuration

The app is configured via `.streamlit/config.toml`:

- **Port**: 8501
- **Domain**: timesheet.fromcolombiawithcoffees.com
- **Theme**: Blue (#0066cc)

## 📋 Features

- Upload Excel reports (.xlsx)
- Automatic data cleaning and grouping
- Email template generation
- One-click Outlook integration
- Clipboard auto-copy
- Search and filter substitutes
- Warning for overdue timesheets (>21 days)

## 🗂️ Expected Excel Columns

- Identifier
- Substitute
- Email
- Confirmation #
- School
- Date
- Days Old

## 📧 Email Template

The app generates emails with:
- Subject: "Past Due Timesheet(s) – Action Required"
- Video link to Frontline Reference
- List of pending dates with confirmation numbers
- Warning about account deactivation risk

## 🛡️ Security Notes

- No data is stored on the server
- Excel files are processed in memory only
- Email addresses are validated before sending
- All processing happens client-side in the browser

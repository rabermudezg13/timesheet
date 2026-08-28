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

- Secure email/password login with Firebase Authentication
- Administrator panel to create, disable, enable, and reset user passwords
- User and administrator roles
- Upload Excel reports (.xlsx)
- Automatic data cleaning and grouping
- Email template generation
- One-click Outlook integration
- Clipboard auto-copy
- Search and filter substitutes
- Warning for overdue timesheets (>21 days)

## 🔐 User authentication setup

The app uses Firebase Authentication so accounts remain available when Streamlit restarts.

1. In Firebase Console, enable **Authentication → Sign-in method → Email/Password**.
2. Create a Firebase service account and download its JSON key.
3. In the Streamlit app, open **Settings → Secrets** and add:

```toml
[firebase]
web_api_key = "YOUR_FIREBASE_WEB_API_KEY"
admin_email = "YOUR_ADMIN_EMAIL"
service_account_json = """
{
  "type": "service_account",
  "project_id": "YOUR_PROJECT_ID",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n",
  "client_email": "...",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "..."
}
"""
```

4. Create the first account in **Firebase Authentication → Users**, using the same email entered as `admin_email`.
5. Sign in to the app with that account. It becomes the administrator automatically, and all other accounts can then be managed inside the app.

Never commit the service-account JSON or passwords to GitHub.

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

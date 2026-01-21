import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from urllib.parse import quote
import streamlit.components.v1 as components

st.set_page_config(page_title="Timesheet Reminder Generator", layout="wide")

# Header
st.title("📧 Timesheet Reminder Generator")
st.markdown("**Hello Keona, I'm ready to help you** ☕")
st.markdown("Upload your Excel report to generate email reminders for substitutes with missing timesheets.")

# Video link constant
VIDEO_LINK = "https://www.kellyeducation.com/hubfs/kelc/payroll-webtime/index.html#/lessons/3Zo1Sd7m3z2BI8sG-FtRR9Aa0vDukbmD"

def normalize_date(date_val):
    """Robustly convert various date formats to datetime"""
    if pd.isna(date_val):
        return None

    # Already datetime
    if isinstance(date_val, (pd.Timestamp, datetime)):
        return pd.to_datetime(date_val)

    # Excel serial number (float/int)
    if isinstance(date_val, (int, float)):
        try:
            return pd.to_datetime('1899-12-30') + pd.Timedelta(days=date_val)
        except:
            return None

    # String
    if isinstance(date_val, str):
        try:
            return pd.to_datetime(date_val)
        except:
            return None

    return None

def generate_email_body(dates_data):
    """Generate email body with dates block"""
    days_lines = []
    for date_str, confirmations in dates_data:
        if len(confirmations) == 1:
            days_lines.append(f"- {date_str} (Confirmation: {confirmations[0]})")
        else:
            conf_str = ", ".join(confirmations)
            days_lines.append(f"- {date_str} (Confirmation: {conf_str})")

    days_block = "\n".join(days_lines)

    email_body = f"""Hello,

I am reaching out from Kelly Education payroll department to inform you that your account has some timesheet/s that are PAST DUE. If you worked on the day/s listed below, please log into Frontline and submit the timesheet as SOON as possible:

{days_block}

If you did not work on the specified dates, please respond to this message so that I can update your account accordingly.

This short video walks through some of the basics of the Frontline Absence Management System and can help with submitting your timesheet.
Link to Frontline Reference Video: {VIDEO_LINK}

NOTE: If your timesheet/s are overdue by more than three weeks, it may result in the deactivation of your account.

If you did not work on this day, please notify me so that I can have it removed from your profile.

Thank you for your prompt attention to this matter."""

    return email_body

def create_mailto_button(email_to, subject, body, button_key):
    """Create a button that copies to clipboard and opens mailto link"""
    # URL encode subject and body
    encoded_subject = quote(subject)
    encoded_body = quote(body)

    # Check body length - if too long, omit from mailto
    if len(encoded_body) > 1400:
        mailto_link = f"mailto:{email_to}?subject={encoded_subject}"
        body_included = False
    else:
        mailto_link = f"mailto:{email_to}?subject={encoded_subject}&body={encoded_body}"
        body_included = True

    # JavaScript to copy to clipboard and open mailto
    js_code = f"""
    <script>
    function copyAndOpenMailto_{button_key}() {{
        const emailBody = `{body.replace('`', '\\`').replace('$', '\\$')}`;

        // Copy to clipboard
        if (navigator.clipboard && navigator.clipboard.writeText) {{
            navigator.clipboard.writeText(emailBody).then(function() {{
                document.getElementById('success_{button_key}').style.display = 'block';
                // Open mailto
                window.location.href = "{mailto_link}";
            }}).catch(function(err) {{
                document.getElementById('fallback_{button_key}').style.display = 'block';
            }});
        }} else {{
            // Fallback for older browsers
            document.getElementById('fallback_{button_key}').style.display = 'block';
        }}
    }}
    </script>

    <button onclick="copyAndOpenMailto_{button_key}()"
            style="background-color: #0066cc; color: white; padding: 12px 24px;
                   border: none; border-radius: 4px; font-size: 16px; cursor: pointer;
                   font-weight: bold;">
        📧 Open Outlook + Copy Template
    </button>

    <div id="success_{button_key}" style="display:none; margin-top: 10px; padding: 10px;
         background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px; color: #155724;">
        ✅ <strong>Copied!</strong> Paste into Outlook (Ctrl+V).
    </div>

    <div id="fallback_{button_key}" style="display:none; margin-top: 10px; padding: 10px;
         background-color: #fff3cd; border: 1px solid #ffeeba; border-radius: 4px; color: #856404;">
        ⚠️ Clipboard access denied. Please manually copy the email from the text area below.
    </div>
    """

    components.html(js_code, height=100)

# File upload
uploaded_file = st.file_uploader("Upload Excel Report (.xlsx)", type=['xlsx'])

if uploaded_file:
    try:
        # Read Excel
        df = pd.read_excel(uploaded_file, engine='openpyxl')

        st.success(f"✅ Loaded {len(df)} rows")

        # Required columns
        required_cols = ['Identifier', 'Substitute', 'Email', 'Confirmation #', 'School', 'Date', 'Days Old']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
            st.stop()

        # Drop rows with missing Email or Date
        initial_count = len(df)
        df_clean = df.dropna(subset=['Email', 'Date']).copy()
        dropped_count = initial_count - len(df_clean)

        if dropped_count > 0:
            st.warning(f"⚠️ Dropped {dropped_count} rows with missing Email or Date")

        if len(df_clean) == 0:
            st.error("❌ No valid rows remaining after dropping missing Email/Date")
            st.stop()

        # Normalize Date
        df_clean['Date_normalized'] = df_clean['Date'].apply(normalize_date)
        df_clean = df_clean.dropna(subset=['Date_normalized'])

        # Treat Confirmation # as string
        df_clean['Confirmation #'] = df_clean['Confirmation #'].astype(str).str.strip()

        # Clean Email
        df_clean['Email'] = df_clean['Email'].astype(str).str.strip().str.lower()

        # De-duplicate exact duplicates (Email, Date, Confirmation #)
        df_clean = df_clean.drop_duplicates(subset=['Email', 'Date_normalized', 'Confirmation #'])

        # Group by Email
        grouped_data = {}

        for email, group in df_clean.groupby('Email'):
            # Get first non-null Substitute and Identifier
            substitute = group['Substitute'].dropna().iloc[0] if not group['Substitute'].dropna().empty else "Unknown"
            identifier = group['Identifier'].dropna().iloc[0] if not group['Identifier'].dropna().empty else "Unknown"

            # Collect dates with confirmations
            dates_dict = {}
            for _, row in group.iterrows():
                date_obj = row['Date_normalized']
                date_str = date_obj.strftime('%Y-%m-%d')
                conf = row['Confirmation #']

                if date_str not in dates_dict:
                    dates_dict[date_str] = set()
                dates_dict[date_str].add(conf)

            # Sort dates and prepare data
            sorted_dates = sorted(dates_dict.items(), key=lambda x: x[0])
            dates_data = [(date, sorted(list(confs))) for date, confs in sorted_dates]

            # Calculate summary metrics
            total_dates = len(dates_data)
            max_days_old = group['Days Old'].max()
            unique_schools = group['School'].nunique()

            grouped_data[email] = {
                'substitute': substitute,
                'identifier': identifier,
                'total_dates': total_dates,
                'max_days_old': max_days_old,
                'unique_schools': unique_schools,
                'dates_data': dates_data
            }

        # Create summary table
        summary_rows = []
        for email, data in grouped_data.items():
            summary_rows.append({
                'Substitute': data['substitute'],
                'Email': email,
                'Identifier': data['identifier'],
                'Total Pending Dates': data['total_dates'],
                'Max Days Old': int(data['max_days_old']) if not pd.isna(data['max_days_old']) else 0,
                'Unique Schools': data['unique_schools']
            })

        summary_df = pd.DataFrame(summary_rows)

        st.markdown("---")
        st.subheader(f"📊 Summary: {len(summary_df)} Substitutes with Missing Timesheets")
        st.dataframe(summary_df, use_container_width=True, height=300)

        # Search and select
        st.markdown("---")
        st.subheader("🔍 Select Substitute")

        col1, col2 = st.columns([2, 1])

        with col1:
            search_term = st.text_input("Search by name or email", "")

        # Filter options based on search
        if search_term:
            filtered_options = [
                f"{data['substitute']} ({email})"
                for email, data in grouped_data.items()
                if search_term.lower() in data['substitute'].lower() or search_term.lower() in email.lower()
            ]
        else:
            filtered_options = [f"{data['substitute']} ({email})" for email, data in grouped_data.items()]

        filtered_options = sorted(filtered_options)

        with col2:
            if filtered_options:
                selected_option = st.selectbox("Select substitute", filtered_options, key="substitute_select")
            else:
                st.warning("No matches found")
                selected_option = None

        if selected_option:
            # Extract email from selection
            selected_email = selected_option.split('(')[1].rstrip(')')
            selected_data = grouped_data[selected_email]

            st.markdown("---")

            # Show warning if over 3 weeks
            if selected_data['max_days_old'] > 21:
                st.error(f"⚠️ **WARNING:** Over 3 weeks past due ({int(selected_data['max_days_old'])} days) - Risk of account deactivation!")

            # Display details
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 📅 Pending Dates")
                for date_str, confirmations in selected_data['dates_data']:
                    if len(confirmations) == 1:
                        st.write(f"- {date_str} (Confirmation: {confirmations[0]})")
                    else:
                        conf_str = ", ".join(confirmations)
                        st.write(f"- {date_str} (Confirmation: {conf_str})")

            with col2:
                st.markdown("### 📧 Email Details")
                st.write(f"**Substitute:** {selected_data['substitute']}")
                st.write(f"**Email:** {selected_email}")
                st.write(f"**Identifier:** {selected_data['identifier']}")
                st.write(f"**Total Dates:** {selected_data['total_dates']}")
                st.write(f"**Max Days Old:** {int(selected_data['max_days_old'])}")

            st.markdown("---")

            # Generate email
            email_body = generate_email_body(selected_data['dates_data'])
            subject = "Past Due Timesheet(s) – Action Required"

            st.markdown("### 📝 Generated Email")

            # Validate email
            email_valid = '@' in selected_email and '.' in selected_email.split('@')[1]

            if not email_valid:
                st.error("❌ Invalid email address. Cannot generate mailto link.")
            else:
                # Create the button
                button_key = selected_email.replace('@', '_').replace('.', '_')
                create_mailto_button(selected_email, subject, email_body, button_key)

            st.markdown("---")

            # Show email in text area for manual copy fallback
            st.text_area(
                "Email Template (Manual Copy Fallback)",
                email_body,
                height=400,
                key="email_preview"
            )

    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

else:
    st.info("👆 Please upload an Excel file to begin")

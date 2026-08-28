import json

import firebase_admin
import requests
import streamlit as st
from firebase_admin import auth, credentials


def _firebase_settings():
    try:
        settings = st.secrets["firebase"]
        api_key = settings["web_api_key"]
        service_account = settings["service_account_json"]
        admin_email = settings["admin_email"].strip().lower()
    except (KeyError, TypeError):
        st.error("Firebase authentication has not been configured yet.")
        st.code(
            '[firebase]\nweb_api_key = "YOUR_WEB_API_KEY"\nadmin_email = "YOUR_EMAIL"\n'
            'service_account_json = """{ ...service account JSON... }"""'
        )
        st.stop()

    if isinstance(service_account, str):
        service_account = json.loads(service_account)
    else:
        service_account = dict(service_account)
    return api_key, service_account, admin_email


@st.cache_resource
def _firebase_app(service_account_json):
    service_account = json.loads(service_account_json)
    if firebase_admin._apps:
        return firebase_admin.get_app()
    return firebase_admin.initialize_app(credentials.Certificate(service_account))


def initialize_firebase():
    api_key, service_account, admin_email = _firebase_settings()
    _firebase_app(json.dumps(service_account, sort_keys=True))
    return api_key, admin_email


def _friendly_auth_error(response):
    try:
        code = response.json()["error"]["message"].split(":", 1)[0]
    except (KeyError, TypeError, ValueError):
        return "Unable to sign in. Please try again."

    messages = {
        "EMAIL_NOT_FOUND": "Email or password is incorrect.",
        "INVALID_PASSWORD": "Email or password is incorrect.",
        "INVALID_LOGIN_CREDENTIALS": "Email or password is incorrect.",
        "USER_DISABLED": "This account has been disabled. Contact the administrator.",
        "TOO_MANY_ATTEMPTS_TRY_LATER": "Too many attempts. Please wait and try again.",
    }
    return messages.get(code, "Unable to sign in. Please verify your information.")


def _sign_in(api_key, email, password, admin_email):
    response = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=15,
    )
    if not response.ok:
        raise ValueError(_friendly_auth_error(response))

    payload = response.json()
    user = auth.get_user(payload["localId"])
    role = (user.custom_claims or {}).get("role", "user")
    if user.email and user.email.lower() == admin_email and role != "admin":
        auth.set_custom_user_claims(user.uid, {**(user.custom_claims or {}), "role": "admin"})
        role = "admin"
    return {
        "uid": user.uid,
        "email": user.email,
        "name": user.display_name or user.email.split("@")[0],
        "role": role,
    }


def logout():
    st.session_state.pop("timesheet_user", None)
    st.rerun()


def require_login():
    api_key, admin_email = initialize_firebase()

    if "timesheet_user" not in st.session_state:
        st.title("🔐 Timesheet Login")
        st.caption("Sign in with the account provided by your administrator.")

        with st.form("login_form"):
            email = st.text_input("Email").strip().lower()
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", use_container_width=True)

        if submitted:
            if not email or not password:
                st.warning("Enter your email and password.")
            else:
                try:
                    st.session_state["timesheet_user"] = _sign_in(api_key, email, password, admin_email)
                    st.rerun()
                except requests.RequestException:
                    st.error("Could not connect to the login service. Please try again.")
                except ValueError as exc:
                    st.error(str(exc))
        st.stop()

    user = st.session_state["timesheet_user"]
    with st.sidebar:
        st.write(f"Signed in as **{user['name']}**")
        st.caption(user["email"])
        if st.button("Log out", use_container_width=True):
            logout()
    return user


def _list_users():
    return sorted(auth.list_users().iterate_all(), key=lambda user: (user.display_name or user.email or "").lower())


def render_admin_panel(current_user):
    if current_user.get("role") != "admin":
        return

    with st.sidebar.expander("⚙️ User administration"):
        st.caption("Create accounts and control access to this app.")

        with st.form("create_user_form", clear_on_submit=True):
            name = st.text_input("Full name")
            email = st.text_input("User email").strip().lower()
            password = st.text_input("Temporary password", type="password")
            role = st.selectbox("Role", ["user", "admin"], format_func=lambda value: value.title())
            create_user = st.form_submit_button("Create user", use_container_width=True)

        if create_user:
            if not name.strip() or not email or len(password) < 6:
                st.error("Enter a name, a valid email, and a password of at least 6 characters.")
            else:
                try:
                    new_user = auth.create_user(email=email, password=password, display_name=name.strip())
                    auth.set_custom_user_claims(new_user.uid, {"role": role})
                    st.success(f"Account created for {name.strip()}.")
                except Exception as exc:
                    st.error(f"Could not create the account: {exc}")

        st.divider()
        users = _list_users()
        if users:
            labels = {
                user.uid: f"{user.display_name or 'No name'} — {user.email or 'No email'}"
                for user in users
            }
            selected_uid = st.selectbox(
                "Manage existing user",
                options=list(labels),
                format_func=lambda uid: labels[uid],
            )
            selected = next(user for user in users if user.uid == selected_uid)
            selected_role = (selected.custom_claims or {}).get("role", "user")
            st.caption(f"Role: {selected_role.title()} · Status: {'Disabled' if selected.disabled else 'Active'}")

            new_password = st.text_input("New password", type="password", key="admin_new_password")
            if st.button("Change password", use_container_width=True):
                if len(new_password) < 6:
                    st.error("The password must contain at least 6 characters.")
                else:
                    auth.update_user(selected.uid, password=new_password)
                    st.success("Password updated.")

            action_label = "Enable user" if selected.disabled else "Disable user"
            if st.button(action_label, use_container_width=True, disabled=selected.uid == current_user["uid"]):
                auth.update_user(selected.uid, disabled=not selected.disabled)
                st.success(f"User {'enabled' if selected.disabled else 'disabled'}.")
                st.rerun()

import streamlit as st
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
GROUP_ID = "6a241cfcb29152fe5570a4e3"

st.set_page_config(page_title="One Piece Chat", page_icon="🏴‍☠️", layout="wide")

# ── session state init ────────────────────────────────────────────
def init_session():
    defaults = {
        "token": None,
        "user_id": None,
        "user_name": None,
        "email": None,
        "expires_at": None,
        "logged_in": False,
        "chat_session_id": None,   # ← created on login
        "session_memory": "",
        "messages": [],
        "conv_id": "",
        "sessions_list": []
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

def get_headers():
    return {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json"
    }

# ── session helpers ───────────────────────────────────────────────
def create_chat_session() -> str | None:
    """Create a new chat session after login"""
    try:
        resp = requests.post(
            f"{BASE_URL}/session/create",
            json={"grp_id": GROUP_ID},
            headers=get_headers()
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"[session] Created: {data['session_id']}")
            return data["session_id"]
        print(f"[session] Create failed: {resp.text}")
        return None
    except Exception as e:
        print(f"[session] Error creating session: {e}")
        return None

def load_sessions():
    """Load all sessions for sidebar"""
    try:
        resp = requests.get(
            f"{BASE_URL}/session/list/{GROUP_ID}",
            headers=get_headers()
        )
        if resp.status_code == 200:
            st.session_state.sessions_list = resp.json()["sessions"]
    except Exception as e:
        print(f"[session] Error loading sessions: {e}")

def switch_session(session_id: str, memory: str):
    """Switch to an existing session"""
    st.session_state.chat_session_id = session_id
    st.session_state.session_memory = memory
    st.session_state.messages = []
    st.session_state.conv_id = ""
    st.rerun()

def start_new_session():
    """Create and switch to a new session"""
    new_id = create_chat_session()
    if new_id:
        st.session_state.chat_session_id = new_id
        st.session_state.session_memory = ""
        st.session_state.messages = []
        st.session_state.conv_id = ""
        load_sessions()
        st.rerun()
    else:
        st.error("Failed to create new session")

def delete_session(session_id: str):
    try:
        requests.delete(
            f"{BASE_URL}/session/{session_id}",
            headers=get_headers()
        )
        # If deleted current session start a new one
        if st.session_state.chat_session_id == session_id:
            load_sessions()
            start_new_session()
        else:
            load_sessions()
            st.rerun()
    except Exception as e:
        st.error(f"Error deleting: {e}")

# ── auth helpers ──────────────────────────────────────────────────
def do_login(email: str, password: str) -> bool:
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": email, "password": password}
        )
        if resp.status_code == 200:
            data = resp.json()
            st.session_state.token      = data["token"]
            st.session_state.user_id    = data["user_id"]
            st.session_state.user_name  = data["name"]
            st.session_state.email      = email
            st.session_state.expires_at = data["expires_at"]
            st.session_state.logged_in  = True

            # ← Create session immediately after login
            load_sessions()
            existing = st.session_state.sessions_list

            if existing:
                # Resume most recent session
                latest = existing[0]
                st.session_state.chat_session_id = latest["session_id"]
                st.session_state.session_memory  = latest["memory_summary"]
                print(f"[login] Resuming session: {latest['session_id']}")
            else:
                # No sessions yet — create first one
                new_id = create_chat_session()
                if new_id:
                    st.session_state.chat_session_id = new_id
                    st.session_state.session_memory  = ""
                    print(f"[login] Created first session: {new_id}")

            return True

        st.error(resp.json().get("detail", "Login failed"))
        return False
    except Exception as e:
        st.error(f"Connection error: {e}")
        return False

def do_logout():
    try:
        requests.post(f"{BASE_URL}/auth/logout", headers=get_headers())
    except:
        pass
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

def do_register(name: str, email: str, password: str) -> bool:
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/signup",
            json={"name": name, "email": email, "password": password}
        )
        if resp.status_code == 200:
            return True
        st.error(resp.json().get("detail", "Registration failed"))
        return False
    except Exception as e:
        st.error(f"Connection error: {e}")
        return False

def verify_session() -> bool:
    if not st.session_state.token:
        return False
    try:
        resp = requests.get(f"{BASE_URL}/auth/me", headers=get_headers())
        return resp.status_code == 200
    except:
        return False

def refresh_token_if_needed():
    if not st.session_state.expires_at:
        return
    expires = datetime.fromisoformat(st.session_state.expires_at)
    remaining = (expires - datetime.now()).total_seconds()
    if remaining < 86400:  # less than 1 day
        try:
            resp = requests.post(f"{BASE_URL}/auth/refresh", headers=get_headers())
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.token = data["token"]
                st.session_state.expires_at = data["expires_at"]
        except:
            pass

# ── Auth page ─────────────────────────────────────────────────────
def show_auth_page():
    st.title("🏴‍☠️ One Piece Chat")
    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login_form"):
            email    = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login", use_container_width=True):
                if do_login(email, password):
                    st.rerun()

    with tab_register:
        with st.form("register_form"):
            name     = st.text_input("Name")
            email    = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Register", use_container_width=True):
                if do_register(name, email, password):
                    st.success("Registered! Please login.")

# ── Chat page ─────────────────────────────────────────────────────
def show_chat_page():
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user_name}")
        st.caption(f"📧 {st.session_state.email}")

        if st.session_state.expires_at:
            expires = datetime.fromisoformat(st.session_state.expires_at)
            days_left = (expires - datetime.now()).days
            if days_left <= 1:
                st.warning(f"⚠️ Session expires in {days_left}d")
            else:
                st.caption(f"✅ Session valid · {days_left}d left")

        st.divider()

        if st.button("➕ New Chat", use_container_width=True):
            start_new_session()

        st.markdown("### 💬 Chats")
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🔄"):
                load_sessions()
                st.rerun()

        for s in st.session_state.sessions_list:
            is_active = s["session_id"] == st.session_state.chat_session_id
            c1, c2 = st.columns([5, 1])
            with c1:
                label = f"{'▶ ' if is_active else ''}{s['title'][:28] or 'New Chat'}"
                if st.button(label, key=f"s_{s['session_id']}", use_container_width=True):
                    if not is_active:
                        switch_session(s["session_id"], s["memory_summary"])
            with c2:
                if st.button("🗑", key=f"d_{s['session_id']}"):
                    delete_session(s["session_id"])

        st.divider()

        if st.session_state.session_memory:
            with st.expander("🧠 Session Memory"):
                st.caption(st.session_state.session_memory)

        st.caption(f"Session: `{st.session_state.chat_session_id or 'none'}`")
        st.divider()

        if st.button("🚪 Logout", use_container_width=True):
            do_logout()

    # ── Chat area ─────────────────────────────────────────────────
    st.title("🏴‍☠️ One Piece Group Chat")

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🏴‍☠️"):
                st.markdown(f"**{msg['character_name']}**")
                st.markdown(msg["content"])

    query = st.chat_input("Ask the crew something...")
    if query:
        st.session_state.messages.append({
            "role": "user", "content": query, "character_name": "You"
        })
        with st.chat_message("user"):
            st.markdown(query)

        payload = {
            "group_id": GROUP_ID,
            "query": query,
            "session_id": st.session_state.chat_session_id
        }

        try:
            with requests.post(
                f"{BASE_URL}/conv/chat/stream",
                json=payload,
                headers={**get_headers(), "Accept": "text/event-stream"},
                stream=True,
                timeout=120
            ) as response:
                if response.status_code == 401:
                    st.warning("⚠️ Session expired. Please login again.")
                    do_logout()
                    return

                response.raise_for_status()
                buffer = ""
                current_event = None

                for raw_chunk in response.iter_content(chunk_size=None):
                    if not raw_chunk:
                        continue
                    buffer += raw_chunk.decode("utf-8")

                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()

                        if line.startswith("event:"):
                            current_event = line[len("event:"):].strip()

                        elif line.startswith("data:"):
                            data_str = line[len("data:"):].strip()
                            if not current_event or not data_str:
                                continue
                            try:
                                data = json.loads(data_str)
                            except json.JSONDecodeError:
                                continue

                            if current_event == "character_response":
                                char_name     = data.get("character_name", "")
                                response_text = data.get("response", "")
                                conv_id       = data.get("conv_id", "")

                                if conv_id:
                                    st.session_state.conv_id = conv_id

                                with st.chat_message("assistant", avatar="🏴‍☠️"):
                                    st.markdown(f"**{char_name}**")
                                    st.markdown(response_text)

                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "character_name": char_name,
                                    "content": response_text
                                })

                            elif current_event == "done":
                                # Refresh session memory from backend
                                try:
                                    sess_resp = requests.get(
                                        f"{BASE_URL}/session/{st.session_state.chat_session_id}",
                                        headers=get_headers()
                                    )
                                    if sess_resp.status_code == 200:
                                        st.session_state.session_memory = sess_resp.json().get("memory_summary", "")
                                        load_sessions()  # refresh sidebar titles
                                except:
                                    pass
                                st.toast("✅ Done!")

                            elif current_event == "error":
                                st.error(f"❌ {data}")

                            current_event = None

        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to backend.")
        except Exception as e:
            st.error(f"❌ {str(e)}")

# ── Main ──────────────────────────────────────────────────────────
if st.session_state.logged_in:
    refresh_token_if_needed()
    if not verify_session():
        st.warning("Session expired. Please login again.")
        do_logout()
    else:
        show_chat_page()
else:
    show_auth_page()
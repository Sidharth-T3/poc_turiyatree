import streamlit as st
import requests
import uuid
import json

# --- Configuration ---
API_URL = "https://dev-app.turiyaskills.co/api/method/turiya_app.turiyaforms_v2.usage_limits_team.api.chatbot_api"
PAGE_TITLE = "Turibot"
PAGE_ICON = "💬"

st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON)

# --- Session State Initialization ---
if "sessionId" not in st.session_state:
    # Generate a unique session ID for this user session
    st.session_state.sessionId = uuid.uuid4().hex

if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_email" not in st.session_state:
    st.session_state.user_email = None

# --- Helper Function: Call API ---
def get_bot_response(user_input, email, session_id):
    headers = {'Content-Type': 'application/json'}
    payload = {
        "sessionId": session_id,
        "action": "sendMessage",
        "chatInput": user_input,
        "metadata": {
            "user_email": email
        }
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        response.raise_for_status() # Raise error for bad status codes (4xx, 5xx)
        
        data = response.json()
        print("API Response:", json.dumps(data, indent=2))  # Debug print
        
        # Parse nested response structure based on sample output
        if "message" in data and isinstance(data["message"], dict):
            return data["message"].get("message", "No message received from server.")
        else:
            return "Unexpected response format."
            
    except requests.exceptions.RequestException as e:
        return f"Error connecting to server: {str(e)}"
    except ValueError:
        return "Error parsing server response."

# --- UI Logic ---

st.title(PAGE_TITLE)

# 1. Login Screen (Email Input)
if not st.session_state.user_email:
    st.markdown("Please enter your email to start the chat.")
    
    with st.form("email_form"):
        email_input = st.text_input("Email Address", placeholder="name@example.com")
        submitted = st.form_submit_button("Start Chat")
        
        if submitted and email_input:
            st.session_state.user_email = email_input
            st.rerun() # Refresh app to show chat interface

# 2. Chat Interface (Shown only after email is set)
else:
    # Optional: Sidebar with session info
    with st.sidebar:
        st.write(f"Logged in as:")
        st.code(st.session_state.user_email)
        if st.button("Logout"):
            st.session_state.user_email = None
            st.session_state.messages = []
            st.rerun()

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("Ask about Assess360..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get response from API
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                bot_reply = get_bot_response(
                    prompt, 
                    st.session_state.user_email, 
                    st.session_state.sessionId
                )
                st.markdown(bot_reply)
        
        # Add assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})

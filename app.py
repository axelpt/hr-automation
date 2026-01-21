import streamlit as st
from supabase import create_client, Client
import requests
import os
import mimetypes
import uuid

# --- Configuration ---
# Helper to get secrets with a fallback or nicer error
def get_secret(section, key):
    try:
        return st.secrets[section][key]
    except (KeyError, FileNotFoundError):
        return None

# --- Page Setup ---
st.set_page_config(page_title="Workflow Uploader", page_icon="📂")
st.title("📂 Upload to Workflow")

# --- Authentication (Optional/Simple) ---
# --- Authentication ---
password = st.text_input("Access Password", type="password")
auth_pass = get_secret("general", "auth_password") or "admin" # Default to 'admin' if not set

if password != auth_pass:
    st.warning("Please enter the correct password to access this tool.")
    st.stop()


# --- Validation ---
supabase_url = get_secret("supabase", "url")
supabase_key = get_secret("supabase", "key")
supabase_bucket = get_secret("supabase", "bucket") or "uploads"

# Note: For Prod, ensure this is a tr_prod_... key
trigger_secret = get_secret("trigger", "secret_key") 
trigger_task_id = get_secret("trigger", "task_id")

if not all([supabase_url, supabase_key, trigger_secret, trigger_task_id]):
    st.error("❌ Missing configuration secrets! Please check `.streamlit/secrets.toml`.")
    st.info("""
    **Required Secrets Structure:**
    ```toml
    [supabase]
    url = "..."
    key = "..."
    bucket = "uploads"

    [trigger]
    secret_key = "tr_prod_..." # Use Prod key for production
    task_id = "..."
    ```
    """)
    st.stop()

# Initialize Supabase
try:
    supabase: Client = create_client(supabase_url, supabase_key)
except Exception as e:
    st.error(f"Failed to initialize Supabase client: {e}")
    st.stop()

# --- Main Interface ---
candidate_name = st.text_input("Candidate Name", value="Test User")
candidate_notes = st.text_area("Notes", value="Added via Trigger.dev task")

uploaded_files = st.file_uploader("Drag and drop files here", accept_multiple_files=True)

if uploaded_files:
    if st.button(f"Process {len(uploaded_files)} File(s)", type="primary"):
        if not candidate_name:
            st.error("Please enter a candidate name.")
            st.stop()

        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, file in enumerate(uploaded_files):
            file_name_original = file.name
            file_ext = os.path.splitext(file_name_original)[1]
            # Generate random filename
            random_filename = f"{uuid.uuid4()}{file_ext}"
            
            mime_type = file.type or mimetypes.guess_type(file_name_original)[0] or "application/octet-stream"
            
            # 1. Upload to Supabase
            status_text.text(f"Uploading {file_name_original}...")
            
            try:
                # Read file bytes
                file_bytes = file.getvalue()
                
                # Upload with random filename
                path_on_storage = random_filename
                
                res = supabase.storage.from_(supabase_bucket).upload(
                    path=path_on_storage,
                    file=file_bytes,
                    file_options={"content-type": mime_type, "x-upsert": "true"}
                )
                
                # Get Public URL
                # If the bucket is public:
                public_url = supabase.storage.from_(supabase_bucket).get_public_url(path_on_storage)
                # Strip trailing '?' if present
                if public_url.endswith("?"):
                    public_url = public_url.rstrip("?")
                
                # If bucket is private, we might need a signed URL
                # signed_url_res = supabase.storage.from_(supabase_bucket).create_signed_url(path_on_storage, 60*60)
                # public_url = signed_url_res['signedURL']
                
            except Exception as e:
                st.error(f"Error uploading {file_name_original}: {e}")
                continue

            # 2. Trigger Task
            status_text.text(f"Triggering workflow for {file_name_original}...")
            
            try:
                trigger_url = f"https://api.trigger.dev/api/v1/tasks/{trigger_task_id}/trigger"
                headers = {
                    "Authorization": f"Bearer {trigger_secret}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "payload": {
                        "cells": {
                            "Name": candidate_name,
                            "Notes": candidate_notes,
                            "Status": "Inbox",
                            "Resume": public_url
                        }
                    }
                }
                
                response = requests.post(trigger_url, headers=headers, json=payload)
                response.raise_for_status()
                
                run_data = response.json()
                run_id = run_data.get("id")
                
                st.success(f"✅ Triggered! Run ID: `{run_id}` (File: {file_name_original})")
                
            except Exception as e:
                st.error(f"Failed to trigger task for {file_name_original}: {e}")
                if 'response' in locals():
                    st.code(response.text)

            progress_bar.progress((i + 1) / len(uploaded_files))
            
        status_text.text("All done!")

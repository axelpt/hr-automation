# Frontend Development Prompt: Streamlit File Upload with Trigger.dev

## Overview
Create the simplest possible internal tool for uploading files that triggers a background workflow.
The app should allow users to upload files via a web interface. These files are stored in Supabase Storage, and then a Trigger.dev task is fired to process each file.

## Tech Stack
- **Framework**: Streamlit (Python)
- **Deployment**: Streamlit Community Cloud (free & easy) or local
- **Storage**: Supabase Storage
- **Orchestration**: Trigger.dev (v3)

## Requirements

### 1. Simple Interface
- Use `st.file_uploader` to accept one or more files.
- Display a "Process Files" button (or trigger automatically on upload).
- Show simple status messages (Uploading... -> Triggering... -> Done).

### 2. Supabase Storage Integration
- Use the `supabase` Python client.
- Upload each file to a dedicated Storage Bucket (e.g., `uploads`).
- **Important**: Generate a signed URL or public URL for the file so Trigger.dev can access it.

### 3. Trigger.dev Integration
- After a successful upload, make a standard HTTP POST request to the Trigger.dev API.
- **Endpoint**: `https://api.trigger.dev/api/v1/tasks/{task_id}/trigger`
- **Headers**: `Authorization: Bearer <TRIGGER_SECRET_KEY>`
- **Payload**:
  ```json
  {
    "payload": {
      "file_url": "https://...",
      "filename": "document.pdf"
    }
  }
  ```

### 4. Configuration (Secrets)
- Do NOT hardcode keys. Use `st.secrets` (via `.streamlit/secrets.toml`).
- Required secrets:
  ```toml
  [supabase]
  url = "..."
  key = "..." # Service_role key is best for secure backend uploads, or standard anon key if bucket policies allow
  bucket = "uploads"

  [trigger]
  secret_key = "tr_dev_..."
  task_id = "process-file-task"
  ```

## Implementation Steps

1.  **Setup**: Create `app.py` and `requirements.txt`.
    -   `requirements.txt`: `streamlit`, `supabase`, `requests`
2.  **Auth**: If this tool is public, add a simple password check using `st.text_input` ("Enter Access Password").
3.  **Core Logic**:
    -   Iterate through `st.session_state` or the uploaded files list.
    -   `supabase.storage.from_(bucket).upload(...)`
    -   `requests.post(...)` to Trigger.dev.
    -   `st.success(f"Started run: {run_id}")`

## Code Structure Goal (Single File)
Keep it to a single `app.py` file if possible. Simplicity is key.

```python
import streamlit as st
from supabase import create_client
import requests

# Init
supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

st.title("📂 Upload to Workflow")

files = st.file_uploader("Drop files here", accept_multiple_files=True)

if files and st.button("Start Processing"):
    for file in files:
        with st.spinner(f"Uploading {file.name}..."):
            # 1. Upload to Supabase
            # 2. Get URL
            # 3. Trigger Task
            st.toast(f"Triggered workflow for {file.name}")
```

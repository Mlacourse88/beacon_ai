# Google Integration Authentication Setup

## Overview
BEACON_AI uses a **Service Account** to interact with Google Calendar, Sheets, Docs, and Drive. This allows the AI to run securely in the background without requiring manual user login every time.

## Prerequisites
1. A Google Cloud Platform (GCP) Project.
2. The Google Calendar, Google Sheets, Google Docs, and Google Drive APIs enabled in that project.

## Setup Steps

### 1. Create Service Account & Key
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g., "Beacon-AI-Personal").
3. Navigate to **IAM & Admin** > **Service Accounts**.
4. Click **Create Service Account**. Name it (e.g., "beacon-bot").
5. Grant it the **Editor** role (Project > Editor) so it can read/write.
6. Click on the newly created service account > **Keys** tab > **Add Key** > **Create new key** > **JSON**.
7. A file will download. Rename this file to `service_account_key.json`.
8. **MOVE** this file to the root directory of your BEACON_AI project: `C:\Users\mwlac\BEACON_AI\service_account_key.json`.

### 2. Enable APIs
In the Google Cloud Console, search for and **ENABLE** the following APIs:
- **Google Calendar API**
- **Google Sheets API**
- **Google Docs API**
- **Google Drive API**

### 3. Share Resources (CRITICAL STEP)
Since Service Accounts have their own separate data storage, they cannot see *your* personal files unless you share them.

**To let the AI access your Calendar:**
1. Open [Google Calendar](https://calendar.google.com/).
2. Go to Settings > Select your primary calendar.
3. Scroll to **"Share with specific people"**.
4. Click **Add people**.
5. Paste the **Service Account Email** (e.g., `beacon-bot@beacon-ai-personal.iam.gserviceaccount.com`).
6. Set permission to **"Make changes to events"**.

**To let the AI access Drive/Sheets/Docs:**
1. Create a folder in your Google Drive (e.g., "Shared_With_Beacon").
2. Right-click > Share.
3. Paste the Service Account Email.
4. Set as **Editor**.
5. Any file the AI creates will ideally be placed here, or you can move files into it.

## Troubleshooting
- **File Not Found Error:** Ensure `service_account_key.json` is in the root folder.
- **Permission Denied:** Double-check Step 3. The Service Account email MUST be added to your Calendar/Folder permissions.

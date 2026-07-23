# Streamlit Course Selection App

This is a Streamlit application built with an MVC architecture and integrated with Google OAuth 2.0 for authentication.

## Setup Instructions

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**
   - Copy `.env.temp` to a new file named `.env`
   - Fill in your Google OAuth credentials (see instructions below).

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

## How to get Google OAuth 2.0 Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. In the left sidebar, navigate to **APIs & Services > Credentials**.
4. Click on **+ CREATE CREDENTIALS** at the top and select **OAuth client ID**.
5. If prompted, configure the **OAuth consent screen** first:
   - Choose **External** (or Internal if you have a Google Workspace).
   - Fill in the required App name, User support email, and Developer contact information.
   - Click Save and Continue through the Scopes and Test users screens (you can add your email as a Test user).
6. Back on the Credentials page, choose **Web application** as the Application type.
7. Give it a name (e.g., "Streamlit App").
8. Under **Authorized redirect URIs**, click **ADD URI** and enter: `http://localhost:8501` (Make sure this matches the `REDIRECT_URI` in your `.env` file).
9. Click **Create**.
10. A modal will appear with your **Client ID** and **Client Secret**. Copy these into your `.env` file.

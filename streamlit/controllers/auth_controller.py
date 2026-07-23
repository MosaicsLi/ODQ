import os
import requests
import streamlit as st
from urllib.parse import urlencode

class AuthController:
    def __init__(self):
        self.client_id = os.environ.get("GOOGLE_CLIENT_ID")
        self.client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.environ.get("REDIRECT_URI", "http://localhost:8501")
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"

    def get_login_url(self):
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"{self.auth_url}?{urlencode(params)}"

    def get_access_token(self, code):
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }
        response = requests.post(self.token_url, data=data)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            st.error(f"Error fetching access token: {response.text}")
            return None

    def get_user_info(self, access_token):
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(self.userinfo_url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error fetching user info: {response.text}")
            return None

    def login(self):
        # Check if auth code is in URL (redirected from Google)
        if "code" in st.query_params:
            code = st.query_params["code"]
            # Clear the query params so it doesn't try to re-authenticate on refresh
            st.query_params.clear()
            
            with st.spinner("Authenticating..."):
                access_token = self.get_access_token(code)
                if access_token:
                    user_info = self.get_user_info(access_token)
                    if user_info:
                        from models.db import SessionLocal, User
                        
                        email = user_info.get("email")
                        name = user_info.get("name")
                        
                        session = SessionLocal()
                        db_user = session.query(User).filter_by(email=email).first()
                        
                        if db_user:
                            # User exists in DB, proceed with login
                            st.session_state["user"] = {"email": email, "name": db_user.name, "role": db_user.role, "id": db_user.id}
                            st.session_state["logged_in"] = True
                            st.rerun()
                        else:
                            # Check if the email corresponds to a student (starts with 's')
                            account_prefix = email.split('@')[0]
                            if account_prefix.startswith('s') and len(account_prefix) > 1:
                                student_id = account_prefix[1:]
                                new_student = User(
                                    id=student_id,
                                    email=email,
                                    name=student_id, # Default name is student ID, can be updated later
                                    role="student"
                                )
                                session.add(new_student)
                                session.commit()
                                
                                st.session_state["user"] = {"email": email, "name": new_student.name, "role": "student", "id": student_id}
                                st.session_state["logged_in"] = True
                                st.rerun()
                            else:
                                st.error("登入失敗：查無此帳號。如果您是老師，請聯繫管理員建立帳號。")
                                
                        session.close()

    def logout(self):
        if "user" in st.session_state:
            del st.session_state["user"]
        if "logged_in" in st.session_state:
            del st.session_state["logged_in"]
        st.rerun()

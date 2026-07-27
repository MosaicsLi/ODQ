import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

import views.login_view as login_view
import views.home_view as home_view
import views.admin_view as admin_view
import views.course_admin_view as course_admin_view
import views.student_view as student_view
from models.db import init_db

# Initialize database
init_db()

# Initialize session state for login
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- Page Setup ---
login_page = st.Page(login_view.render, title="Login", icon="🔒", url_path="login")
home_page = st.Page(home_view.render, title="Home", icon="🏠", url_path="home")
admin_page = st.Page(admin_view.render, title="Admin Panel", icon="⚙️", url_path="admin")
course_admin_page = st.Page(course_admin_view.render, title="Course Admin", icon="📚", url_path="course_admin")
student_page = st.Page(student_view.render, title="選課大廳", icon="🎓", url_path="student_lobby")

with st.sidebar:
    if st.session_state["logged_in"]:
        user_info = st.session_state.get("user", {})
        username = user_info.get("name", "使用者")
        
        st.write(f"👋 **{username}**，您好！")
        
        # 已登入者可以在側邊欄點登出
        if st.button("🚪 登出", key="logout_btn", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state.pop("user", None)
            st.rerun()

if st.session_state["logged_in"]:
    # If logged in, show home page
    pages = [home_page]
    
    role = st.session_state.get("user", {}).get("role")
    
    # If student or admin, append student page (Lobby)
    if role in ["student", "admin"]:
        pages.append(student_page)
    
    # If admin, append admin pages
    if role == "admin":
        pages.append(admin_page)
        pages.append(course_admin_page)
        
    pg = st.navigation(pages)
else:
    # If not logged in, only show login page
    pg = st.navigation([login_page])

pg.run()

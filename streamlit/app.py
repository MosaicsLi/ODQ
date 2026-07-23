import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from views import login_view, home_view, admin_view

# Initialize session state for login
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# Define pages using Streamlit 1.36+ st.Page
login_page = st.Page(login_view.render, title="Login", icon="🔒", url_path="login")
home_page = st.Page(home_view.render, title="Home", icon="🏠", url_path="home")
admin_page = st.Page(admin_view.render, title="Admin Panel", icon="⚙️", url_path="admin")

if st.session_state["logged_in"]:
    # If logged in, show home page
    pages = [home_page]
    
    # If admin, append admin page
    if st.session_state.get("user", {}).get("role") == "admin":
        pages.append(admin_page)
        
    pg = st.navigation(pages)
else:
    # If not logged in, only show login page
    pg = st.navigation([login_page])

pg.run()

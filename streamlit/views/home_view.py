import streamlit as st
from controllers.auth_controller import AuthController

def render():
    st.title("Home Page")
    
    user_info = st.session_state.get("user", {})
    user_name = user_info.get("name", "User")
    
    st.write(f"Hello World! Welcome, {user_name} ({user_info.get('role', 'Unknown')}).")

    # For testing purposes: Allow student to promote themselves to admin
    if user_info.get("role") == "student":
        st.warning("測試功能：您可以將自己的帳號升級為管理員 (Admin) 以測試管理員介面。")
        if st.button("成為管理員 (Test Mode)"):
            from models.db import SessionLocal, User
            session = SessionLocal()
            db_user = session.query(User).filter_by(id=user_info.get("id")).first()
            if db_user:
                db_user.role = "admin"  
                session.commit()
                st.session_state["user"]["role"] = "admin"
                st.success("成功升級為管理員！請重新整理網頁。")
                st.rerun()
            session.close()

    auth_controller = AuthController()
    if st.button("Logout"):
        auth_controller.logout()

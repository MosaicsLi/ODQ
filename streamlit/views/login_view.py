import streamlit as st
from controllers.auth_controller import AuthController

def render():
    st.title("Login to Course Selection System")
    st.write("Please log in using your Google account to access the system.")

    auth_controller = AuthController()
    
    # Run the login flow to check if there is an authorization code in the URL
    auth_controller.login()

    # Display the login button
    login_url = auth_controller.get_login_url()
    st.link_button(
        label="🔑 Login with Google",
        url=login_url,
        type="primary",
        use_container_width=True,
    )
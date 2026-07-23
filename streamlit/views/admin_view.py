import streamlit as st
from models.db import SessionLocal, User

def render():
    st.title("Admin Panel - 管理員介面")
    
    if st.session_state.get("user", {}).get("role") != "admin":
        st.error("您沒有權限訪問此頁面。")
        return
        
    st.write("在這裡您可以管理系統的教師帳號。")
    
    st.subheader("新增教師帳號")
    with st.form("add_teacher_form"):
        teacher_email = st.text_input("教師 Email (Google 帳號)")
        teacher_name = st.text_input("教師姓名")
        submit = st.form_submit_button("新增教師")
        
        if submit:
            if not teacher_email or not teacher_name:
                st.error("請填寫所有欄位")
            else:
                session = SessionLocal()
                # Check if email already exists
                existing_user = session.query(User).filter_by(email=teacher_email).first()
                if existing_user:
                    st.error(f"該 Email 已存在系統中 (目前身分為: {existing_user.role})")
                else:
                    # Generate a new teacher ID (e.g. T0001)
                    teacher_count = session.query(User).filter_by(role="teacher").count()
                    new_teacher_id = f"T{teacher_count + 1:04d}"
                    
                    new_teacher = User(
                        id=new_teacher_id,
                        email=teacher_email,
                        name=teacher_name,
                        role="teacher"
                    )
                    session.add(new_teacher)
                    session.commit()
                    st.success(f"成功新增教師！ 教師編號: {new_teacher_id}, 姓名: {teacher_name}")
                session.close()

    st.subheader("目前系統中的教師列表")
    session = SessionLocal()
    teachers = session.query(User).filter_by(role="teacher").all()
    if teachers:
        for t in teachers:
            st.write(f"- **{t.name}** ({t.email}) - 編號: `{t.id}`")
    else:
        st.write("目前尚無教師資料。")
    session.close()

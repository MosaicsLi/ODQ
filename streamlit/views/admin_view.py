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

    st.subheader("目前系統中的教師列表 (可編輯)")
    session = SessionLocal()
    teachers = session.query(User).filter_by(role="teacher").all()
    
    if teachers:
        import pandas as pd
        
        # Prepare data for editor
        teacher_data = []
        for t in teachers:
            teacher_data.append({
                "ID": t.id,
                "姓名": t.name,
                "Email": t.email
            })
            
        df = pd.DataFrame(teacher_data)
        
        with st.form("edit_teachers_form"):
            edited_df = st.data_editor(
                df,
                disabled=["ID"],
                num_rows="dynamic",
                key="teacher_editor",
                use_container_width=True
            )
            
            submit_edits = st.form_submit_button("儲存編輯與刪除")
            
            if submit_edits:
                try:
                    # 1. Ensure TBD teacher exists in case of deletions
                    tbd_teacher = session.query(User).filter_by(id="TBD").first()
                    if not tbd_teacher:
                        tbd_teacher = User(id="TBD", name="待定教師", email="tbd@system", role="teacher")
                        session.add(tbd_teacher)
                        session.flush()
                        
                    # 2. Identify existing IDs in the edited dataframe
                    existing_ids = edited_df["ID"].dropna().tolist()
                    
                    # 3. Delete missing teachers (assign their offerings to TBD)
                    from models.db import OfferingTeacher
                    for t in teachers:
                        if t.id not in existing_ids and t.id != "TBD":
                            # Assign offerings to TBD
                            offerings = session.query(OfferingTeacher).filter_by(teacher_id=t.id).all()
                            for ot in offerings:
                                # Check if TBD is already assigned to avoid duplicate composite key
                                existing_tbd = session.query(OfferingTeacher).filter_by(offering_id=ot.offering_id, teacher_id="TBD").first()
                                if existing_tbd:
                                    session.delete(ot) # Just remove the old one if TBD already exists
                                else:
                                    ot.teacher_id = "TBD"
                            
                            session.delete(t)
                            
                    # 4. Update existing
                    for idx, row in edited_df.dropna(subset=["ID"]).iterrows():
                        t_id = row["ID"]
                        if t_id == "TBD": continue
                        
                        db_t = session.query(User).filter_by(id=t_id).first()
                        if db_t:
                            db_t.name = row["姓名"]
                            db_t.email = row["Email"]
                            
                    session.commit()
                    st.success("成功更新教師資料！")
                    st.rerun()
                except Exception as e:
                    session.rollback()
                    st.error(f"儲存失敗：{str(e)}")
                    
    else:
        st.info("目前尚無教師資料。")
        
    session.close()

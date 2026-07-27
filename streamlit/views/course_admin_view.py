import streamlit as st
import pandas as pd
from io import StringIO
from datetime import datetime
from models.db import SessionLocal, Course, CourseOffering, ClassSession, User, OfferingTeacher, Enrollment, Attendance

def process_dataframe(df):
    """Processes the bulk import dataframe and inserts into DB."""
    session = SessionLocal()
    success_count = 0
    error_count = 0
    errors = []
    
    # Required columns mapping
    # 年月	日付	分類	Code	LanguageCode	課程名稱(title)	教師(teacher)	開始時間	終了時間	作業時間
    
    for index, row in df.iterrows():
        try:
            # Safely extract data with defaults
            semester = str(row.get('年月', '')).strip()
            date_str = str(row.get('日付', '')).strip()
            course_id = str(row.get('Code', '')).strip()
            course_name = str(row.get('課程名稱(title)', '')).strip()
            teacher_id = str(row.get('教師(teacher)', '')).strip()
            start_time_str = str(row.get('開始時間', '')).strip()
            end_time_str = str(row.get('終了時間', '')).strip()
            
            # Additional optional fields
            category = str(row.get('分類', '')).strip()
            language_code = str(row.get('LanguageCode', '')).strip()
            
            if course_id == 'nan' or date_str == 'nan' or start_time_str == 'nan' or not course_id or not date_str or not start_time_str:
                errors.append(f"Row {index+1}: 缺少必填欄位 (Code, 日付, 或開始時間)")
                error_count += 1
                continue
                
            # 1. Handle Course
            course = session.query(Course).filter_by(id=course_id).first()
            if not course:
                c_name = course_name if course_name != 'nan' and course_name else f"Course {course_id}"
                course = Course(id=course_id, name=c_name, credits=2)
                session.add(course)
                session.flush() # Ensure it's in the session
                
            # 2. Handle CourseOffering
            offering = session.query(CourseOffering).filter_by(course_id=course_id, semester=semester).first()
            if not offering:
                offering = CourseOffering(course_id=course_id, semester=semester)
                session.add(offering)
                session.flush()
                
            # 3. Handle Teacher and OfferingTeacher
            if teacher_id and teacher_id != 'nan':
                teacher = session.query(User).filter_by(id=teacher_id, role="teacher").first()
                if not teacher:
                    # Create a placeholder teacher so admin can adjust later
                    teacher = User(
                        id=teacher_id, 
                        email=f"temp_{teacher_id}@unassigned.com", 
                        name=f"臨時教師 ({teacher_id})", 
                        role="teacher"
                    )
                    session.add(teacher)
                    session.flush()
                    
                # Link teacher to offering
                offering_teacher = session.query(OfferingTeacher).filter_by(offering_id=offering.id, teacher_id=teacher.id).first()
                if not offering_teacher:
                    offering_teacher = OfferingTeacher(offering_id=offering.id, teacher_id=teacher.id)
                    session.add(offering_teacher)
                    session.flush()
                    
            # 4. Handle ClassSession
            try:
                start_dt = pd.to_datetime(f"{date_str} {start_time_str}")
                if end_time_str and end_time_str != 'nan':
                    end_dt = pd.to_datetime(f"{date_str} {end_time_str}")
                else:
                    end_dt = start_dt
            except Exception as e:
                errors.append(f"Row {index+1}: 日期或時間格式錯誤 ({date_str} {start_time_str})")
                error_count += 1
                continue
                
            # Create session
            description = ""
            if category and category != 'nan': description += f"[{category}] "
            if language_code and language_code != 'nan': description += language_code
            description = description.strip()
            if not description: description = None
            
            # Avoid exact duplicates
            existing_session = session.query(ClassSession).filter_by(
                offering_id=offering.id,
                start_time=start_dt.to_pydatetime(),
                end_time=end_dt.to_pydatetime()
            ).first()
            
            if not existing_session:
                new_session = ClassSession(
                    offering_id=offering.id,
                    start_time=start_dt.to_pydatetime(),
                    end_time=end_dt.to_pydatetime(),
                    description=description
                )
                session.add(new_session)
                
            success_count += 1
            
        except Exception as e:
            errors.append(f"Row {index+1}: 發生未預期的錯誤 ({str(e)})")
            error_count += 1
            
    if success_count > 0:
        session.commit()
    else:
        session.rollback()
        
    session.close()
    return success_count, error_count, errors


def render():
    st.title("📚 課程與排程管理")
    
    user_info = st.session_state.get("user", {})
    if user_info.get("role") != "admin":
        st.error("此頁面僅限管理員存取。")
        return
        
    st.write("此模組可讓您快速建立課程 (Course)、本學期開課 (Course Offering)，並排定具體的上課時段 (Class Session)。")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📤 批量匯入 (Excel/CSV/Text)", "✍️ 手動新增排程", "📋 課程管理", "🗓️ 排程管理"])
    
    with tab1:
        st.subheader("批量匯入課表")
        st.markdown('''
        **資料格式要求**：必須包含以下欄位 (大小寫與標題需相符或相似)：
        `年月` | `日付` | `分類` | `Code` | `LanguageCode` | `課程名稱(title)` | `教師(teacher)` | `開始時間` | `終了時間` | `作業時間`
        
        *備註：* 
        - 學分將預設為 `2`。
        - `教師(teacher)` 欄位請填寫教師的 **ID** (例如 `T0001`)。若該教師不存在，系統將自動建立一個臨時教師帳號供後續修改。
        ''')
        
        # Option 1: File Upload
        uploaded_file = st.file_uploader("選擇 CSV 或 Excel 檔案", type=["csv", "xlsx", "xls"])
        
        # Option 2: Text Area
        pasted_text = st.text_area("或直接貼上 TSV (Tab分隔) 資料：", height=200, placeholder="2026/04\\t2026/04/11\\tS1\\t1202\\tF10\\tLinux基礎\\tT0001\\t9:20:00\\t12:30:00\\t3小時10分鐘")
        
        if st.button("開始匯入資料", type="primary"):
            df = None
            if uploaded_file is not None:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    try:
                        df = pd.read_excel(uploaded_file)
                    except Exception as e:
                        st.error(f"讀取 Excel 失敗，請確認已安裝 openpyxl ({str(e)})")
            elif pasted_text:
                df = pd.read_csv(StringIO(pasted_text), sep='\\t')
                
            if df is not None:
                if len(df) == 0:
                    st.warning("無資料可匯入！")
                else:
                    st.write("預覽解析的資料：")
                    st.dataframe(df.head(5))
                    
                    with st.spinner("正在匯入並寫入資料庫..."):
                        success_c, error_c, err_msgs = process_dataframe(df)
                        
                        if success_c > 0:
                            st.success(f"匯入成功！共新增或處理了 {success_c} 筆排程。")
                        if error_c > 0:
                            st.error(f"有 {error_c} 筆資料匯入失敗。")
                            with st.expander("查看錯誤詳情"):
                                for e in err_msgs:
                                    st.write(e)
            else:
                st.warning("請先上傳檔案或貼上文字資料！")
                
    with tab2:
        st.subheader("手動新增課程與排程")
        with st.form("manual_add_course_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                m_course_id = st.text_input("課程代碼 (Code)*")
                m_course_name = st.text_input("課程名稱 (Title)*")
                m_credits = st.number_input("學分", value=2, min_value=0)
                m_semester = st.text_input("學期 (年月)*", placeholder="例如：2026/04")
                m_teacher_id = st.text_input("教師 ID (Teacher)*", placeholder="例如：T0001")
            
            with col2:
                m_date = st.date_input("上課日期 (日付)*")
                m_start_time = st.time_input("開始時間*")
                m_end_time = st.time_input("結束時間*")
                m_category = st.text_input("分類 (Category)", placeholder="例如：S1")
                m_language = st.text_input("語言代碼 (LanguageCode)", placeholder="例如：F10")
                
            submitted = st.form_submit_button("新增排程", type="primary")
            
            if submitted:
                if not m_course_id or not m_course_name or not m_semester or not m_teacher_id:
                    st.error("請填寫所有帶星號 (*) 的必填欄位！")
                else:
                    session = SessionLocal()
                    try:
                        # 1. Course
                        course = session.query(Course).filter_by(id=m_course_id).first()
                        if not course:
                            course = Course(id=m_course_id, name=m_course_name, credits=int(m_credits))
                            session.add(course)
                        session.flush()
                        
                        # 2. Offering
                        offering = session.query(CourseOffering).filter_by(course_id=m_course_id, semester=m_semester).first()
                        if not offering:
                            offering = CourseOffering(course_id=m_course_id, semester=m_semester)
                            session.add(offering)
                        session.flush()
                        
                        # 3. Teacher
                        teacher = session.query(User).filter_by(id=m_teacher_id, role="teacher").first()
                        if not teacher:
                            teacher = User(
                                id=m_teacher_id, 
                                email=f"temp_{m_teacher_id}@unassigned.com", 
                                name=f"臨時教師 ({m_teacher_id})", 
                                role="teacher"
                            )
                            session.add(teacher)
                        session.flush()
                        
                        # OfferingTeacher
                        ot = session.query(OfferingTeacher).filter_by(offering_id=offering.id, teacher_id=teacher.id).first()
                        if not ot:
                            ot = OfferingTeacher(offering_id=offering.id, teacher_id=teacher.id)
                            session.add(ot)
                        session.flush()
                        
                        # 4. Class Session
                        start_dt = datetime.combine(m_date, m_start_time)
                        end_dt = datetime.combine(m_date, m_end_time)
                        
                        description = ""
                        if m_category: description += f"[{m_category}] "
                        if m_language: description += m_language
                        description = description.strip() if description.strip() else None
                        
                        existing_session = session.query(ClassSession).filter_by(
                            offering_id=offering.id,
                            start_time=start_dt,
                            end_time=end_dt
                        ).first()
                        
                        if not existing_session:
                            new_session = ClassSession(
                                offering_id=offering.id,
                                start_time=start_dt,
                                end_time=end_dt,
                                description=description
                            )
                            session.add(new_session)
                            session.commit()
                            st.success(f"成功新增排程：{m_course_name} ({m_date})")
                        else:
                            st.warning("此時段的排程已存在，未重複新增。")
                            
                    except Exception as e:
                        session.rollback()
                        st.error(f"錯誤：{str(e)}")
                    finally:
                        session.close()
                
    with tab3:
        st.subheader("課程管理 (可編輯)")
        session = SessionLocal()
        courses = session.query(Course).all()
        
        if not courses:
            st.info("目前尚無任何課程資料。")
        else:
            course_data = []
            for c in courses:
                course_data.append({
                    "Code": c.id,
                    "課程名稱": c.name,
                    "學分": c.credits
                })
            df_c = pd.DataFrame(course_data)
            
            with st.form("edit_courses_form"):
                edited_c_df = st.data_editor(
                    df_c,
                    disabled=["Code"],
                    num_rows="dynamic",
                    key="course_editor",
                    use_container_width=True
                )
                
                if st.form_submit_button("儲存課程變更"):
                    try:
                        existing_ids = edited_c_df["Code"].dropna().tolist()
                        
                        # 1. Handle Deletions (Cascade manually for safety)
                        for c in courses:
                            if c.id not in existing_ids:
                                c_to_del = session.query(Course).filter_by(id=c.id).first()
                                if c_to_del:
                                    offerings = session.query(CourseOffering).filter_by(course_id=c.id).all()
                                    for off in offerings:
                                        session.query(OfferingTeacher).filter_by(offering_id=off.id).delete()
                                        session.query(Enrollment).filter_by(offering_id=off.id).delete()
                                        sessions = session.query(ClassSession).filter_by(offering_id=off.id).all()
                                        for s in sessions:
                                            session.query(Attendance).filter_by(session_id=s.id).delete()
                                            session.delete(s)
                                        session.delete(off)
                                    session.delete(c_to_del)
                        
                        # 2. Handle Updates
                        for idx, row in edited_c_df.dropna(subset=["Code"]).iterrows():
                            db_c = session.query(Course).filter_by(id=row["Code"]).first()
                            if db_c:
                                db_c.name = row["課程名稱"]
                                db_c.credits = int(row["學分"])
                                
                        session.commit()
                        st.success("課程資料已更新！")
                        st.rerun()
                    except Exception as e:
                        session.rollback()
                        st.error(f"儲存失敗：{str(e)}")
        session.close()

    with tab4:
        st.subheader("排程細節管理")
        session = SessionLocal()
        # Create a dropdown to select a course
        all_courses = session.query(Course).all()
        if not all_courses:
            st.info("目前尚無任何課程資料。")
        else:
            course_options = {c.id: f"{c.id} - {c.name}" for c in all_courses}
            selected_course_id = st.selectbox("選擇課程", options=list(course_options.keys()), format_func=lambda x: course_options[x])
            
            if selected_course_id:
                # Find offerings and sessions
                offerings = session.query(CourseOffering).filter_by(course_id=selected_course_id).all()
                offering_ids = [o.id for o in offerings]
                sessions = session.query(ClassSession).filter(ClassSession.offering_id.in_(offering_ids)).order_by(ClassSession.start_time).all()
                
                if not sessions:
                    st.info("該課程目前沒有排程 (Class Sessions)。")
                else:
                    session_data = []
                    for s in sessions:
                        session_data.append({
                            "ID": s.id,
                            "學期 (Offering)": s.offering.semester,
                            "開始時間": s.start_time,
                            "結束時間": s.end_time,
                            "描述/分類": s.description
                        })
                    
                    df_s = pd.DataFrame(session_data)
                    with st.form("edit_sessions_form"):
                        edited_s_df = st.data_editor(
                            df_s,
                            disabled=["ID", "學期 (Offering)"],
                            num_rows="dynamic",
                            key="session_editor",
                            use_container_width=True
                        )
                        
                        if st.form_submit_button("儲存排程變更"):
                            try:
                                existing_s_ids = edited_s_df["ID"].dropna().tolist()
                                
                                # 1. Handle Deletions
                                for s in sessions:
                                    if s.id not in existing_s_ids:
                                        s_to_del = session.query(ClassSession).filter_by(id=s.id).first()
                                        if s_to_del:
                                            session.query(Attendance).filter_by(session_id=s.id).delete()
                                            session.delete(s_to_del)
                                            
                                # 2. Handle Updates
                                for idx, row in edited_s_df.dropna(subset=["ID"]).iterrows():
                                    db_s = session.query(ClassSession).filter_by(id=row["ID"]).first()
                                    if db_s:
                                        db_s.start_time = pd.to_datetime(row["開始時間"]).to_pydatetime()
                                        db_s.end_time = pd.to_datetime(row["結束時間"]).to_pydatetime()
                                        db_s.description = row["描述/分類"] if pd.notna(row["描述/分類"]) else None
                                        
                                session.commit()
                                st.success("排程資料已更新！")
                                st.rerun()
                            except Exception as e:
                                session.rollback()
                                st.error(f"儲存失敗：{str(e)}")
                                
        session.close()

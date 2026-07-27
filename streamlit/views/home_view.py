import streamlit as st
import datetime
from streamlit_calendar import calendar
from controllers.auth_controller import AuthController
from models.db import SessionLocal, User, CustomEvent

def render():
    st.title("個人行事曆與系統首頁")
    
    user_info = st.session_state.get("user", {})
    user_name = user_info.get("name", "User")
    user_id = user_info.get("id")
    
    st.write(f"歡迎回來, {user_name} ({user_info.get('role', 'Unknown')})")

    # DB session
    session = SessionLocal()

    # Expandable section to add custom event
    with st.expander("➕ 新增自訂行程 (與課表無關)"):
        with st.form("add_event_form", clear_on_submit=True):
            event_title = st.text_input("行程標題", placeholder="例如：迎新活動、圖書館讀書")
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("開始日期")
                start_time = st.time_input("開始時間")
            with col2:
                end_date = st.date_input("結束日期")
                end_time = st.time_input("結束時間")
                
            event_color = st.color_picker("事件顏色", "#4285F4")
            
            submit_btn = st.form_submit_button("儲存行程")
            
            if submit_btn:
                if not event_title:
                    st.error("請輸入行程標題！")
                else:
                    start_dt = datetime.datetime.combine(start_date, start_time)
                    end_dt = datetime.datetime.combine(end_date, end_time)
                    if end_dt < start_dt:
                        st.error("結束時間不能早於開始時間！")
                    else:
                        new_event = CustomEvent(
                            user_id=user_id,
                            title=event_title,
                            start_time=start_dt,
                            end_time=end_dt,
                            color=event_color
                        )
                        session.add(new_event)
                        session.commit()
                        st.success("行程已新增！")
                        st.rerun()
                        
    # Fetch all custom events for this user
    db_events = session.query(CustomEvent).filter_by(user_id=user_id).all()
    
    with st.expander("✏️ 管理行程列表 (可在此編輯或刪除)"):
        import pandas as pd
        event_data = []
        for e in db_events:
            event_data.append({
                "ID": e.id,
                "標題": e.title,
                "開始時間": e.start_time,
                "結束時間": e.end_time,
                "顏色": e.color
            })
        
        df = pd.DataFrame(event_data)
        if df.empty:
            # Create empty structure so they can add rows even if empty
            df = pd.DataFrame(columns=["ID", "標題", "開始時間", "結束時間", "顏色"])
        else:
            df["開始時間"] = pd.to_datetime(df["開始時間"])
            df["結束時間"] = pd.to_datetime(df["結束時間"])
            
        with st.form("event_editor_form"):
            edited_df = st.data_editor(
                df,
                hide_index=True,
                column_config={
                    "ID": None, # Hide ID column
                    "標題": st.column_config.TextColumn("標題", required=True),
                    "開始時間": st.column_config.DatetimeColumn("開始時間", format="YYYY-MM-DD HH:mm", required=True),
                    "結束時間": st.column_config.DatetimeColumn("結束時間", format="YYYY-MM-DD HH:mm", required=True),
                    "顏色": st.column_config.TextColumn("顏色")
                },
                num_rows="dynamic",
                key="event_editor"
            )
            
            submit_edits = st.form_submit_button("儲存編輯變更")
            
        if submit_edits:
            try:
                # 1. Identify existing IDs in the edited dataframe
                existing_ids = edited_df["ID"].dropna().tolist()
                
                # 2. Delete events that are no longer in the dataframe
                for ev in db_events:
                    if ev.id not in existing_ids:
                        session.delete(ev)
                        
                # 3. Update existing events
                for idx, row in edited_df.dropna(subset=["ID"]).iterrows():
                    ev = session.query(CustomEvent).filter_by(id=row["ID"]).first()
                    if ev:
                        ev.title = row["標題"]
                        ev.start_time = pd.to_datetime(row["開始時間"]).to_pydatetime()
                        ev.end_time = pd.to_datetime(row["結束時間"]).to_pydatetime()
                        ev.color = row.get("顏色", "#4285F4") if pd.notna(row.get("顏色")) else "#4285F4"
                        
                # 4. Add new events (where ID is NaN or None)
                new_rows = edited_df[edited_df["ID"].isna()]
                for idx, row in new_rows.iterrows():
                    if pd.notna(row["標題"]) and pd.notna(row["開始時間"]) and pd.notna(row["結束時間"]):
                        new_ev = CustomEvent(
                            user_id=user_id,
                            title=row["標題"],
                            start_time=pd.to_datetime(row["開始時間"]).to_pydatetime(),
                            end_time=pd.to_datetime(row["結束時間"]).to_pydatetime(),
                            color=row.get("顏色", "#4285F4") if pd.notna(row.get("顏色")) else "#4285F4"
                        )
                        session.add(new_ev)
                        
                session.commit()
                st.success("變更已成功儲存！")
                st.rerun()
            except Exception as e:
                st.error(f"儲存失敗，錯誤訊息：{str(e)}")
    
    # Format custom events for streamlit-calendar
    calendar_events = []
    for ev in db_events:
        calendar_events.append({
            "title": ev.title,
            "start": ev.start_time.isoformat(),
            "end": ev.end_time.isoformat(),
            "backgroundColor": ev.color,
            "borderColor": ev.color,
        })
        
    # Fetch enrolled courses and add to calendar
    from models.db import Enrollment, ClassSession
    enrolled = session.query(Enrollment).filter_by(student_id=user_id).all()
    for enr in enrolled:
        offering = enr.offering
        course_name = offering.course.name
        # Find all sessions for this offering
        sessions = session.query(ClassSession).filter_by(offering_id=offering.id).all()
        for s in sessions:
            desc = f" [{s.description}]" if s.description else ""
            calendar_events.append({
                "title": f"📚 {course_name}{desc}",
                "start": s.start_time.isoformat(),
                "end": s.end_time.isoformat(),
                "backgroundColor": "#34A853", # Green color for enrolled courses
                "borderColor": "#34A853",
            })
        
    session.close()

    # Calendar rendering
    st.subheader("我的行事曆")
    
    calendar_options = {
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "timeGridDay,timeGridWeek,dayGridMonth",
        },
        "initialView": "dayGridMonth",
        "slotMinTime": "00:00:00",
        "slotMaxTime": "24:00:00",
        "navLinks": True,
        "selectable": True,
    }
    
    custom_css = """
        .fc-event-title {
            font-weight: 500;
        }
    """
    
    calendar(events=calendar_events, options=calendar_options, custom_css=custom_css)
    
    st.divider()

    # For testing purposes: Allow student to promote themselves to admin
    if user_info.get("role") == "student" or user_info.get("role") == "teacher":
        st.warning("測試功能：您可以將自己的帳號升級為管理員 (Admin) 以測試管理員介面。")
        if st.button("成為管理員 (Test Mode)"):
            session = SessionLocal()
            db_user = session.query(User).filter_by(id=user_info.get("id")).first()
            if db_user:
                db_user.role = "admin"  
                session.commit()
                st.session_state["user"]["role"] = "admin"
                st.success("成功升級為管理員！請重新整理網頁。")
                st.rerun()
            session.close()
    elif user_info.get("role") == "admin":
        st.info("測試功能：您目前是管理員，可以切換回普通學生/教師身份。")
        
        # 透過學號/編號的特徵來判斷原本的身分
        # 老師的編號開頭是 'T' (例如 T0001)，學生的編號是純數字
        user_id_str = str(user_info.get("id", ""))
        target_role = "teacher" if user_id_str.startswith("T") else "student"
    
        if st.button(f"切換回普通使用者 ({target_role})", use_container_width=True):
            session = SessionLocal()
            db_user = session.query(User).filter_by(id=user_info.get("id")).first()
            if db_user:
                db_user.role = target_role
                session.commit()
            
            # 同步更新 session_state 並重新渲染
                st.session_state["user"]["role"] = target_role
                st.success(f"已切換回 {target_role} 身份！")
                st.rerun()
            session.close()
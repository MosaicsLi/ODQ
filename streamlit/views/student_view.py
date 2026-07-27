import streamlit as st
import pandas as pd
from models.db import SessionLocal, Course, CourseOffering, ClassSession, User, Enrollment

def get_academic_year(semester_str):
    # e.g., "2026/04" or "2026-F1" -> "2026"
    return semester_str.split('/')[0].split('-')[0] if semester_str else "Unknown"

def check_time_conflict(session_db, student_id, new_offering_id):
    # Fetch all sessions for the new offering
    new_sessions = session_db.query(ClassSession).filter_by(offering_id=new_offering_id).all()
    if not new_sessions:
        return False, None
    
    # Fetch all sessions for currently enrolled offerings
    enrolled = session_db.query(Enrollment).filter_by(student_id=student_id).all()
    enrolled_offering_ids = [e.offering_id for e in enrolled]
    
    if not enrolled_offering_ids:
        return False, None
        
    existing_sessions = session_db.query(ClassSession).filter(ClassSession.offering_id.in_(enrolled_offering_ids)).all()
    
    for ns in new_sessions:
        for es in existing_sessions:
            # Check overlap: (StartA < EndB) and (EndA > StartB)
            if ns.start_time < es.end_time and ns.end_time > es.start_time:
                conflict_msg = f"時間衝突：與已選課程 ({es.offering.course.name}) 重疊 ({es.start_time.strftime('%Y-%m-%d %H:%M')} ~ {es.end_time.strftime('%H:%M')})"
                return True, conflict_msg
                
    return False, None

def check_credit_limit(session_db, student_id, new_offering):
    academic_year = get_academic_year(new_offering.semester)
    new_credits = new_offering.course.credits
    
    # Get all enrollments for the student in the same academic year
    enrolled = session_db.query(Enrollment).filter_by(student_id=student_id).all()
    
    current_credits = 0
    for e in enrolled:
        if get_academic_year(e.offering.semester) == academic_year:
            current_credits += e.offering.course.credits
            
    if current_credits + new_credits > 40:
        return True, f"超過每學年學分上限 (40學分)！目前已選 {current_credits} 學分，欲加選 {new_credits} 學分。"
    return False, None

def render():
    st.title("🎓 選課系統大廳")
    
    user_info = st.session_state.get("user", {})
    if not user_info:
        st.error("請先登入")
        return
        
    student_id = user_info.get("id")
    role = user_info.get("role")
    
    if role not in ["student", "admin"]:
        st.error("此頁面僅限學生與管理員存取。")
        return
        
    tab1, tab2 = st.tabs(["📚 選課大廳 (加選)", "📝 我的課表 (退選)"])
    
    session = SessionLocal()
    
    # ------------------
    # TAB 1: Available Courses
    # ------------------
    with tab1:
        st.subheader("瀏覽與加選課程")
        
        # Get all unique semesters
        offerings = session.query(CourseOffering).all()
        unique_semesters = sorted(list(set([o.semester for o in offerings])), reverse=True)
        
        if not unique_semesters:
            st.info("目前系統尚無任何開課紀錄。")
        else:
            selected_semester = st.selectbox("選擇學期 (Semester)", unique_semesters)
            
            # Fetch offerings for selected semester
            current_offerings = session.query(CourseOffering).filter_by(semester=selected_semester).all()
            
            # Get already enrolled offering IDs for UI state
            enrolled_db = session.query(Enrollment).filter_by(student_id=student_id).all()
            enrolled_ids = [e.offering_id for e in enrolled_db]
            
            # Count current credits for the academic year
            academic_year = get_academic_year(selected_semester)
            current_yr_credits = sum(e.offering.course.credits for e in enrolled_db if get_academic_year(e.offering.semester) == academic_year)
            st.caption(f"ℹ️ {academic_year} 學年目前已選學分：**{current_yr_credits} / 40**")
            
            for off in current_offerings:
                with st.expander(f"{off.course.id} - {off.course.name} ({off.course.credits} 學分)"):
                    # Display Teachers
                    teacher_names = [t.teacher.name for t in off.teachers]
                    st.write(f"👨‍🏫 **授課教師**：{', '.join(teacher_names) if teacher_names else '待定'}")
                    
                    # Display Sessions
                    sessions = session.query(ClassSession).filter_by(offering_id=off.id).order_by(ClassSession.start_time).all()
                    if sessions:
                        st.write("🗓️ **上課時段**：")
                        for s in sessions:
                            desc = f" [{s.description}]" if s.description else ""
                            st.write(f"- {s.start_time.strftime('%Y-%m-%d %H:%M')} ~ {s.end_time.strftime('%H:%M')}{desc}")
                    else:
                        st.write("🗓️ **上課時段**：(尚未排定)")
                        
                    # Action Button
                    if off.id in enrolled_ids:
                        st.button("✅ 已加選", key=f"enrolled_{off.id}", disabled=True)
                    else:
                        if st.button("➕ 加選", key=f"enroll_{off.id}"):
                            # 1. Check time conflicts
                            has_conflict, conflict_msg = check_time_conflict(session, student_id, off.id)
                            if has_conflict:
                                st.error(conflict_msg)
                            else:
                                # 2. Check credit limits
                                exceed_limit, limit_msg = check_credit_limit(session, student_id, off)
                                if exceed_limit:
                                    st.error(limit_msg)
                                else:
                                    # Enroll
                                    new_enroll = Enrollment(student_id=student_id, offering_id=off.id)
                                    session.add(new_enroll)
                                    session.commit()
                                    st.success(f"成功加選：{off.course.name}！")
                                    st.rerun()

    # ------------------
    # TAB 2: My Enrollments
    # ------------------
    with tab2:
        st.subheader("我的課表")
        
        my_enrollments = session.query(Enrollment).filter_by(student_id=student_id).all()
        
        if not my_enrollments:
            st.info("您目前尚未加選任何課程。")
        else:
            for enr in my_enrollments:
                off = enr.offering
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{off.course.name}** ({off.course.id}) - {off.semester}")
                        st.caption(f"{off.course.credits} 學分")
                    with col2:
                        if st.button("❌ 退選", key=f"drop_{enr.id}", type="secondary"):
                            session.delete(enr)
                            session.commit()
                            st.success(f"已退選 {off.course.name}")
                            st.rerun()

    session.close()

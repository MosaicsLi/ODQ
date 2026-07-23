import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.db')
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False) # 'student', 'teacher', 'admin'
    
    # Relationships
    enrollments = relationship("Enrollment", back_populates="student")
    taught_offerings = relationship("OfferingTeacher", back_populates="teacher")
    attendances = relationship("Attendance", back_populates="student")

class Course(Base):
    __tablename__ = 'course'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    credits = Column(Integer, nullable=False)
    
    # Relationships
    offerings = relationship("CourseOffering", back_populates="course")

class CourseOffering(Base):
    __tablename__ = 'course_offering'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(String, ForeignKey('course.id'), nullable=False)
    semester = Column(String, nullable=False)
    
    # Relationships
    course = relationship("Course", back_populates="offerings")
    teachers = relationship("OfferingTeacher", back_populates="offering")
    enrollments = relationship("Enrollment", back_populates="offering")
    sessions = relationship("ClassSession", back_populates="offering")

class OfferingTeacher(Base):
    __tablename__ = 'offering_teacher'
    
    offering_id = Column(Integer, ForeignKey('course_offering.id'), primary_key=True)
    teacher_id = Column(String, ForeignKey('user.id'), primary_key=True)
    
    # Relationships
    offering = relationship("CourseOffering", back_populates="teachers")
    teacher = relationship("User", back_populates="taught_offerings")

class ClassSession(Base):
    __tablename__ = 'class_session'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    offering_id = Column(Integer, ForeignKey('course_offering.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    description = Column(String, nullable=True)
    
    # Relationships
    offering = relationship("CourseOffering", back_populates="sessions")
    attendances = relationship("Attendance", back_populates="session")

class Attendance(Base):
    __tablename__ = 'attendance'
    
    session_id = Column(Integer, ForeignKey('class_session.id'), primary_key=True)
    student_id = Column(String, ForeignKey('user.id'), primary_key=True)
    status = Column(String, nullable=False) # 'Present', 'Absent', 'Late'
    
    # Relationships
    session = relationship("ClassSession", back_populates="attendances")
    student = relationship("User", back_populates="attendances")

class Enrollment(Base):
    __tablename__ = 'enrollment'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String, ForeignKey('user.id'), nullable=False)
    offering_id = Column(Integer, ForeignKey('course_offering.id'), nullable=False)
    regular_score = Column(Float, nullable=True)
    final_score = Column(Float, nullable=True)
    
    # Relationships
    student = relationship("User", back_populates="enrollments")
    offering = relationship("CourseOffering", back_populates="enrollments")

def init_db(admin_email="admin@example.com"):
    """Create tables and initialize default admin"""
    Base.metadata.create_all(engine)
    
    session = SessionLocal()
    # Check if admin exists
    admin = session.query(User).filter_by(role='admin').first()
    if not admin:
        default_admin = User(
            id="admin_01",
            email=admin_email,
            name="System Admin",
            role="admin"
        )
        session.add(default_admin)
        session.commit()
    session.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")

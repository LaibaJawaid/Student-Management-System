# api/services/firebase.py
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

# Load env file
load_dotenv("../.env")

# Path to service account JSON
SERVICE_ACCOUNT = os.getenv("FIREBASE_SERVICE_ACCOUNT", "./stu sys.json")

# -----------------------------
#   Initialize Firebase App
# -----------------------------
if not firebase_admin._apps:
    # Safely initialize Firebase only once
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT)
        firebase_admin.initialize_app(cred) 
    except FileNotFoundError:
        print("ERROR: Firebase service account file not found.")
        # Handle initialization failure gracefully in production
        pass

db = firestore.client()

# -----------------------------
#   FIRESTORE COLLECTIONS - UPDATED
# -----------------------------
COL_STUDENTS = "students"              # student documents (rollno → student info)
COL_COURSES = "_courses"               # CHANGED: course documents (course_code → course metadata)
COL_ATTENDANCE_ROOT = "attendance"     # attendance/<course>/logs/<date>
COL_MARKS_ROOT = "marks"               # marks/<course>/students/<rollno>

# ======================================================
#               COURSE MANAGEMENT (UPDATED)
# ======================================================

def create_course_if_not_exists(course_code: str, course_name: str, credit_hours: int = 3):
    """Creates a course metadata document if it doesn't already exist."""
    ref = db.collection(COL_COURSES).document(course_code)
    doc = ref.get()
    if not doc.exists:
        ref.set({
            "name": course_name,
            "credit_hours": credit_hours,
            "created_at": firestore.SERVER_TIMESTAMP,
        })
        return True
    return False

def list_all_courses():
    """Returns a list of all course documents."""
    docs = db.collection(COL_COURSES).stream()
    courses = []
    for doc in docs:
        courses.append({
            "id": doc.id,
            "name": doc.id,
            "created_at": doc.to_dict().get("created_at", ""),
            "student_count": doc.to_dict().get("student_count", 0)
        })
    return courses

def get_course_info(course_code: str):
    """Get course information"""
    doc = db.collection(COL_COURSES).document(course_code).get()
    if doc.exists:
        return doc.to_dict()
    return None

# ======================================================
#               STUDENT MANAGEMENT (UPDATED)
# ======================================================

def create_student(rollno: str, data: dict):
    """Create or overwrite a student"""
    db.collection(COL_STUDENTS).document(rollno).set(data)

def bulk_create_students(list_of_students: list):
    """Bulk insert student list into Firestore"""
    batch = db.batch()
    for s in list_of_students:
        ref = db.collection(COL_STUDENTS).document(str(s["rollno"]))
        # Initialize 'enrolled_courses' if not present during bulk upload
        s['enrolled_courses'] = s.get('enrolled_courses', [])
        batch.set(ref, s, merge=True)
    batch.commit()
    return True

def get_student(rollno: str):
    doc = db.collection(COL_STUDENTS).document(rollno).get()
    return doc.to_dict() if doc.exists else None

def update_student_enrollments(rollno: str, course_code: str):
    """Add course to student's enrolled_courses list"""
    ref = db.collection(COL_STUDENTS).document(rollno)
    doc = ref.get()
    if not doc.exists:
        return False

    data = doc.to_dict()
    courses = data.get("enrolled_courses", [])
    
    if course_code not in courses:
        courses.append(course_code)

    ref.update({"enrolled_courses": courses})
    return True

def get_students_by_course(course_code: str):
    """Get all students who are enrolled in a given course"""
    docs = db.collection(COL_STUDENTS).where(
        "enrolled_courses", "array_contains", course_code
    ).stream()
    return [d.to_dict() for d in docs]

# NEW FUNCTION: Get students from course collection (not enrolled_courses)
def get_students_from_course_collection(course_code: str):
    """Get students from the course-specific collection"""
    docs = db.collection(course_code).stream()
    students = []
    for doc in docs:
        student_data = doc.to_dict()
        student_data["rollno"] = doc.id  # Ensure rollno is included
        students.append(student_data)
    return students

# ======================================================
#               ATTENDANCE MANAGEMENT (UPDATED)
# ======================================================

def save_attendance(course_code: str, date_iso: str, time_iso: str, attendance_map: dict):
    """
    Saves attendance log for a specific course and date.
    """
    ref = (
        db.collection(COL_ATTENDANCE_ROOT)
        .document(course_code)
        .collection("logs")
        .document(date_iso)
    )

    payload = {
        "date": date_iso,  # ADDED: date field
        "time": time_iso,
        "course": course_code,  # ADDED: course field
        "attendance": attendance_map,
        "saved_at": firestore.SERVER_TIMESTAMP,
    }

    ref.set(payload)
    return True

def get_attendance(course_code: str, date_iso: str):
    doc = (
        db.collection(COL_ATTENDANCE_ROOT)
        .document(course_code)
        .collection("logs")
        .document(date_iso)
        .get()
    )
    return doc.to_dict() if doc.exists else None

def list_attendance_dates(course_code: str, limit: int = 50):
    docs = (
        db.collection(COL_ATTENDANCE_ROOT)
        .document(course_code)
        .collection("logs")
        .limit(limit)
        .stream()
    )
    dates = []
    for d in docs:
        dates.append({
            "date": d.id,
            **d.to_dict()
        })
    return dates

# NEW FUNCTION: For teacher portal (different structure)
def save_attendance_teacher_portal(course_code: str, data: dict):
    """
    Save attendance in teacher portal format (compatible with upload.py)
    """
    date = data.get("date")
    time = data.get("time")
    attendance_map = data.get("attendance", {})
    
    if not date or not attendance_map:
        return False
    
    # Save in teacher portal format (same collection as course)
    attendance_collection = db.collection(f"attendance_{course_code}")
    attendance_collection.document(date).set({
        "date": date,
        "time": time,
        "course": course_code,
        "attendance": attendance_map,
        "timestamp": firestore.SERVER_TIMESTAMP
    })
    return True

# ======================================================
#                   MARKS MANAGEMENT (UPDATED)
# ======================================================

def save_marks(course_code: str, rollno: str, marks_dict: dict):
    """Save or update marks for a student"""
    ref = (
        db.collection(COL_MARKS_ROOT)
        .document(course_code)
        .collection("students")
        .document(rollno)
    )
    ref.set(marks_dict, merge=True)
    return True

def get_marks_for_course(course_code: str, rollno: str = None):
    col = (
        db.collection(COL_MARKS_ROOT)
        .document(course_code)
        .collection("students")
    )

    if rollno:
        doc = col.document(rollno).get()
        return doc.to_dict() if doc.exists else None

    return [d.to_dict() for d in col.stream()]

# NEW FUNCTION: Get marks from course collection (for teacher portal)
def get_marks_from_course_collection(course_code: str):
    """Get marks from the course-specific collection"""
    docs = db.collection(course_code).stream()
    marks_list = []
    for doc in docs:
        data = doc.to_dict()
        # Check if this document has marks data
        if any(key in data for key in ['mids_marks', 'finals_marks', 'sessional', 'assignment', 'quiz']):
            marks_list.append(data)
    return marks_list
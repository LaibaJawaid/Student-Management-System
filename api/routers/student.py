# api/routers/student.py
from fastapi import APIRouter, HTTPException
from services.firebase import (
    get_student,
    create_student,
    update_student_enrollments,
    get_students_by_course,
    get_students_from_course_collection,
    db  # ADD THIS
)

router = APIRouter(prefix="/students", tags=["Students"])

@router.get("/{rollno}")
async def fetch_student(rollno: str):
    s = get_student(rollno)
    if not s:
        raise HTTPException(404, "Student not found")
    return s

@router.post("/")
async def add_student(data: dict):
    roll = data.get("rollno")
    if not roll:
        raise HTTPException(400, "rollno is required")
    create_student(roll, data)
    return {"status": "created"}

@router.post("/enroll/{rollno}/{course_code}")
async def enroll_student(rollno: str, course_code: str):
    ok = update_student_enrollments(rollno, course_code)
    if not ok:
        raise HTTPException(404, "Student not found")
    return {"status": "enrolled"}

@router.get("/by-course/{course_code}")
async def fetch_by_course(course_code: str):
    """Get students from course-specific collection (for teacher portal)"""
    students = get_students_from_course_collection(course_code)
    if not students:
        raise HTTPException(404, "No students found in this course. Please upload student roster first.")
    return students

# NEW ENDPOINTS FOR EDIT/DELETE/ADD

@router.post("/add")
async def add_student_to_course(data: dict):
    """
    Add a single student to a course
    """
    try:
        course_code = data.get("course_code")
        student_data = data.get("student")
        
        if not course_code or not student_data:
            raise HTTPException(400, "Course code and student data are required")
        
        rollno = student_data.get("rollno")
        if not rollno:
            raise HTTPException(400, "Student roll number is required")
        
        # Check if student already exists
        existing_ref = db.collection(course_code).document(rollno)
        existing_doc = existing_ref.get()
        
        if existing_doc.exists:
            raise HTTPException(400, f"Student with roll number {rollno} already exists in this course")
        
        # Add student to course collection
        existing_ref.set(student_data)
        
        return {
            "status": "success",
            "message": f"Student {rollno} added successfully to course {course_code}",
            "student": student_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error adding student: {str(e)}")

@router.post("/update")
async def update_student_in_course(data: dict):
    """
    Update student information in a course
    """
    try:
        course_code = data.get("course_code")
        student_data = data.get("student")
        
        if not course_code or not student_data:
            raise HTTPException(400, "Course code and student data are required")
        
        rollno = student_data.get("rollno")
        if not rollno:
            raise HTTPException(400, "Student roll number is required")
        
        # Check if student exists
        student_ref = db.collection(course_code).document(rollno)
        existing_doc = student_ref.get()
        
        if not existing_doc.exists:
            raise HTTPException(404, f"Student {rollno} not found in course {course_code}")
        
        # Update student data (merge with existing)
        existing_data = existing_doc.to_dict()
        updated_data = {**existing_data, **student_data}
        
        student_ref.set(updated_data)
        
        return {
            "status": "success",
            "message": f"Student {rollno} updated successfully",
            "student": updated_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error updating student: {str(e)}")

@router.post("/delete")
async def delete_student_from_course(data: dict):
    """
    Delete a student from a course
    """
    try:
        course_code = data.get("course_code")
        rollno = data.get("rollno")
        
        if not course_code or not rollno:
            raise HTTPException(400, "Course code and roll number are required")
        
        # Check if student exists
        student_ref = db.collection(course_code).document(rollno)
        existing_doc = student_ref.get()
        
        if not existing_doc.exists:
            raise HTTPException(404, f"Student {rollno} not found in course {course_code}")
        
        # Delete student
        student_ref.delete()
        
        # Also delete from attendance records if needed
        attendance_ref = db.collection(f"attendance_{course_code}")
        attendance_docs = attendance_ref.stream()
        
        for doc in attendance_docs:
            attendance_data = doc.to_dict()
            if "attendance" in attendance_data and rollno in attendance_data["attendance"]:
                # Update attendance record to remove this student
                updated_attendance = attendance_data["attendance"]
                del updated_attendance[rollno]
                doc.reference.update({"attendance": updated_attendance})
        
        return {
            "status": "success",
            "message": f"Student {rollno} deleted successfully from course {course_code}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error deleting student: {str(e)}")

@router.get("/search/{course_code}")
async def search_students(course_code: str, query: str = ""):
    """
    Search students in a course by name or roll number
    """
    try:
        students_ref = db.collection(course_code)
        docs = students_ref.stream()
        
        results = []
        query_lower = query.lower()
        
        for doc in docs:
            student = doc.to_dict()
            student["rollno"] = doc.id
            
            # Search in name and roll number
            if (query_lower in student.get("name", "").lower() or 
                query_lower in student.get("rollno", "").lower()):
                results.append(student)
        
        return results
        
    except Exception as e:
        raise HTTPException(500, f"Error searching students: {str(e)}")
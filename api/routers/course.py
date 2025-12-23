# api/routers/course.py
from fastapi import APIRouter, HTTPException
from services.firebase import db, list_all_courses, get_course_info

router = APIRouter(prefix="/courses", tags=["Courses"])

@router.get("/")
async def list_courses():
    """
    Get list of all courses from _courses collection
    """
    try:
        courses = list_all_courses()
        
        if not courses:
            return []
        
        # Return just course names for compatibility
        return [course["name"] for course in courses]
        
    except Exception as e:
        print(f"Error listing courses: {e}")
        # Return empty array on error
        return []

@router.delete("/{course_code}")
async def delete_course(course_code: str):
    """
    Delete a course and all its data
    """
    try:
        # Check if course exists
        course_info = get_course_info(course_code)
        if not course_info:
            raise HTTPException(status_code=404, detail=f"Course '{course_code}' not found")
        
        # Delete students from course collection
        students_ref = db.collection(course_code)
        students_docs = students_ref.stream()
        
        deleted_students = 0
        for student in students_docs:
            student.reference.delete()
            deleted_students += 1
        
        # Delete attendance records (teacher portal format)
        attendance_ref = db.collection(f"attendance_{course_code}")
        attendance_docs = attendance_ref.stream()
        
        deleted_attendance = 0
        for doc in attendance_docs:
            doc.reference.delete()
            deleted_attendance += 1
        
        # Also delete from attendance logs (student portal format)
        attendance_logs_ref = db.collection("attendance").document(course_code).collection("logs")
        attendance_logs_docs = attendance_logs_ref.stream()
        
        for doc in attendance_logs_docs:
            doc.reference.delete()
        
        # Delete marks (student portal format)
        marks_ref = db.collection("marks").document(course_code).collection("students")
        marks_docs = marks_ref.stream()
        
        deleted_marks = 0
        for doc in marks_docs:
            doc.reference.delete()
            deleted_marks += 1
        
        # Delete results
        results_ref = db.collection(f"results_{course_code}")
        results_docs = results_ref.stream()
        
        deleted_results = 0
        for doc in results_docs:
            doc.reference.delete()
            deleted_results += 1
        
        # Finally delete from _courses
        db.collection("_courses").document(course_code).delete()
        
        return {
            "status": "deleted",
            "course": course_code,
            "deleted_students": deleted_students,
            "deleted_attendance": deleted_attendance,
            "deleted_marks": deleted_marks,
            "deleted_results": deleted_results,
            "message": f"Course '{course_code}' and all related data deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{course_code}/info")
async def get_course_info_endpoint(course_code: str):
    """
    Get detailed information about a course
    """
    try:
        # Get course info from _courses
        course_data = get_course_info(course_code)
        
        if not course_data:
            raise HTTPException(status_code=404, detail=f"Course '{course_code}' not found")
        
        # Count students in course collection
        students_ref = db.collection(course_code)
        students_count = len(list(students_ref.stream()))
        
        # Count attendance records (teacher portal)
        attendance_ref = db.collection(f"attendance_{course_code}")
        attendance_count = len(list(attendance_ref.stream()))
        
        # Get results count
        results_ref = db.collection(f"results_{course_code}")
        results_count = len(list(results_ref.stream()))
        
        # Get marks count
        marks_ref = db.collection(course_code)
        marks_docs = marks_ref.stream()
        marks_count = 0
        for doc in marks_docs:
            data = doc.to_dict()
            if any(key in data for key in ['mids_marks', 'finals_marks', 'sessional', 'assignment', 'quiz']):
                marks_count += 1
        
        return {
            "course_code": course_code,
            "created_at": course_data.get("created_at", ""),
            "student_count": students_count,
            "attendance_records": attendance_count,
            "results_count": results_count,
            "marks_count": marks_count,
            "description": course_data.get("description", ""),
            "total_students_in_file": course_data.get("student_count", 0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
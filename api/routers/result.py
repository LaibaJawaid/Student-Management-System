# api/routers/result.py
from fastapi import APIRouter, HTTPException
from services.firebase import db
from fastapi.responses import FileResponse
import pandas as pd
import tempfile
from datetime import datetime

router = APIRouter(prefix="/results", tags=["Results"])

# ============================================
# GPA CALCULATION FUNCTIONS (Directly in file)
# ============================================

def calculate_percentage(mids_marks=0.0, finals_marks=0.0, sessional=0.0, assignment=0.0, quiz=0.0):
    """
    Convert raw marks to percentage using max marks:
    Mids: 30
    Finals: 50
    Sessional: 10
    Assignment: 5
    Quiz: 5
    """

    mids_pct = (mids_marks / 30) * 30
    finals_pct = (finals_marks / 50) * 50
    sessional_pct = (sessional / 10) * 10
    assignment_pct = (assignment / 5) * 5
    quiz_pct = (quiz / 5) * 5

    total_percentage = (
        mids_pct +
        finals_pct +
        sessional_pct +
        assignment_pct +
        quiz_pct
    )

    return round(max(0, min(100, total_percentage)), 2)

def get_grade_from_percentage(percentage):
    """Convert percentage to grade based on standard scale"""
    if percentage >= 85:
        return "A+"
    elif percentage >= 80:
        return "A"
    elif percentage >= 75:
        return "A-"
    elif percentage >= 70:
        return "B+"
    elif percentage >= 65:
        return "B"
    elif percentage >= 60:
        return "B-"
    elif percentage >= 55:
        return "C+"
    elif percentage >= 50:
        return "C"
    elif percentage >= 45:
        return "C-"
    elif percentage >= 35:
        return "D"
    elif percentage >=30:
        return "D-"
    else:
        return "F"

def get_gpa_from_grade(grade):
    """Convert grade to GPA"""
    GRADE_TO_GPA = {
        'A+': 4.0, 'A': 3.7, 'A-': 3.5,
        'B+': 3.3, 'B': 3.0, 'B-': 2.7,
        'C+': 2.5, 'C': 2.3, 'C-': 2.0,
        'D': 1.7, 'D-': 1.5, 'F': 0.0
    }
    return GRADE_TO_GPA.get(grade, 0.0)

def get_status_from_grade(grade):
    """Determine pass/fail status"""
    return "Fail" if grade == "F" else "Pass"

def calculate_result(mids_marks=0.0, finals_marks=0.0, sessional=0.0, assignment=0.0, quiz=0.0):
    """
    Calculate complete result for a student
    """
    # Calculate percentage
    percentage = calculate_percentage(mids_marks, finals_marks, sessional, assignment, quiz)
    
    # Get grade
    grade = get_grade_from_percentage(percentage)
    
    # Get GPA
    gpa = get_gpa_from_grade(grade)
    
    # Get status
    status = get_status_from_grade(grade)
    
    # Calculate total marks
    total_marks = mids_marks + finals_marks + sessional + assignment + quiz
    
    return {
        "percentage": round(percentage, 2),
        "grade": grade,
        "gpa": gpa,
        "status": status,
        "total_marks": total_marks,
        "components": {
            "mids_marks": mids_marks,
            "finals_marks": finals_marks,
            "sessional": sessional,
            "assignment": assignment,
            "quiz": quiz
        }
    }

# ============================================
# API ENDPOINTS
# ============================================

@router.get("/{course_code}")
async def get_course_results(course_code: str):
    """
    Get calculated results for a course
    """
    try:
        results_ref = db.collection(f"results_{course_code}")
        docs = results_ref.stream()
        
        results = []
        for doc in docs:
            result = doc.to_dict()
            result["id"] = doc.id
            results.append(result)
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate/{course_code}")
async def calculate_course_results(course_code: str):
    """
    Calculate results for all students in a course
    """
    try:
        # Get students from course collection
        students_ref = db.collection(course_code)
        students_docs = students_ref.stream()
        
        if not students_docs:
            raise HTTPException(status_code=404, detail=f"No students found in course '{course_code}'")
        
        results = []
        results_ref = db.collection(f"results_{course_code}")
        
        # First clear existing results
        existing_results = results_ref.stream()
        for doc in existing_results:
            doc.reference.delete()
        
        for doc in students_docs:
            student_data = doc.to_dict()
            rollno = student_data.get("rollno", doc.id)
            
            # Skip if no rollno
            if not rollno:
                continue
            
            # Extract marks (convert to float, default to 0)
            mids_marks = float(student_data.get("mids_marks", 0))
            finals_marks = float(student_data.get("finals_marks", 0))
            sessional = float(student_data.get("sessional", 0))
            assignment = float(student_data.get("assignment", 0))
            quiz = float(student_data.get("quiz", 0))
            
            # Calculate result
            result = calculate_result(
                mids_marks=mids_marks,
                finals_marks=finals_marks,
                sessional=sessional,
                assignment=assignment,
                quiz=quiz
            )
            
            # Add student info
            result.update({
                "rollno": rollno,
                "name": student_data.get("name", ""),
                "section": student_data.get("section", ""),
                "batch": student_data.get("batch", ""),
                "course": course_code,
                "calculated_at": datetime.now().isoformat()
            })
            
            # Save to results collection
            results_ref.document(rollno).set(result)
            results.append(result)
        
        return {
            "status": "success",
            "course": course_code,
            "students_processed": len(results),
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/{course_code}")
async def export_results(course_code: str):
    """
    Export results as CSV
    """
    try:
        results_ref = db.collection(f"results_{course_code}")
        docs = results_ref.stream()
        
        rows = []
        for doc in docs:
            result = doc.to_dict()
            rows.append(result)
        
        if not rows:
            raise HTTPException(status_code=404, detail="No results found")
        
        # Create DataFrame
        df = pd.DataFrame(rows)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            df.to_csv(tmp.name, index=False)
            tmp_path = tmp.name
        
        return FileResponse(
            tmp_path,
            filename=f"{course_code}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            media_type='text/csv'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/student/{course_code}/{rollno}")
async def get_student_result(course_code: str, rollno: str):
    """
    Get result for specific student
    """
    try:
        result_ref = db.collection(f"results_{course_code}").document(rollno)
        result_doc = result_ref.get()
        
        if not result_doc.exists:
            # Try to calculate on the fly
            # Get student data
            student_ref = db.collection(course_code).document(rollno)
            student_doc = student_ref.get()
            
            if not student_doc.exists:
                raise HTTPException(status_code=404, detail=f"Student {rollno} not found in course {course_code}")
            
            student_data = student_doc.to_dict()
            
            # Extract marks
            mids_marks = float(student_data.get("mids_marks", 0))
            finals_marks = float(student_data.get("finals_marks", 0))
            sessional = float(student_data.get("sessional", 0))
            assignment = float(student_data.get("assignment", 0))
            quiz = float(student_data.get("quiz", 0))
            
            # Calculate result
            result = calculate_result(mids_marks, finals_marks, sessional, assignment, quiz)
            result.update({
                "rollno": rollno,
                "name": student_data.get("name", ""),
                "section": student_data.get("section", ""),
                "batch": student_data.get("batch", ""),
                "course": course_code
            })
            
            return result
        
        return result_doc.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{course_code}/stats")
async def get_course_stats(course_code: str):
    """
    Get statistics for a course
    """
    try:
        results_ref = db.collection(f"results_{course_code}")
        docs = results_ref.stream()
        
        results = []
        for doc in docs:
            results.append(doc.to_dict())
        
        if not results:
            raise HTTPException(status_code=404, detail="No results found. Calculate results first.")
        
        # Calculate statistics
        total_students = len(results)
        passing_students = sum(1 for r in results if r.get("status") == "Pass")
        failing_students = total_students - passing_students
        
        gpas = [r.get("gpa", 0) for r in results if r.get("gpa")]
        percentages = [r.get("percentage", 0) for r in results if r.get("percentage")]
        
        # Grade distribution
        grade_dist = {}
        for r in results:
            grade = r.get("grade", "Unknown")
            grade_dist[grade] = grade_dist.get(grade, 0) + 1
        
        return {
            "course": course_code,
            "total_students": total_students,
            "passing_students": passing_students,
            "failing_students": failing_students,
            "pass_rate": round((passing_students / total_students * 100), 2) if total_students > 0 else 0,
            "average_gpa": round(sum(gpas) / len(gpas), 2) if gpas else 0,
            "average_percentage": round(sum(percentages) / len(percentages), 2) if percentages else 0,
            "grade_distribution": grade_dist,
            "top_performer": max(results, key=lambda x: x.get("percentage", 0)) if results else None,
            "last_calculated": results[0].get("calculated_at", "") if results else ""
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
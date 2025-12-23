# api/routers/attendance.py
from fastapi import APIRouter, HTTPException
from services.firebase import db
from fastapi.responses import FileResponse
import pandas as pd
import tempfile
from datetime import datetime

router = APIRouter(prefix="/attendance", tags=["Attendance"])

@router.post("/mark/{course_code}")
async def mark_attendance(course_code: str, data: dict):
    """
    Expected payload:
    {
        "date": "2025-02-01",
        "time": "09:00",
        "attendance": { "20F-001": "present", "20F-002": "absent" }
    }
    """
    try:
        date = data.get("date")
        time = data.get("time")
        attendance_map = data.get("attendance", {})
        
        if not date or not attendance_map:
            raise HTTPException(400, "Date and attendance data are required")
        
        # Save attendance in teacher portal format
        attendance_ref = db.collection(f"attendance_{course_code}").document(date)
        
        attendance_data = {
            "date": date,
            "time": time,
            "course": course_code,
            "attendance": attendance_map,
            "timestamp": datetime.now().isoformat()
        }
        
        attendance_ref.set(attendance_data)
        
        return {
            "status": "success",
            "message": f"Attendance saved for {course_code} on {date}",
            "students_marked": len(attendance_map)
        }
        
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/view/{course_code}/{date}")
async def view_attendance(course_code: str, date: str):
    try:
        doc = db.collection(f"attendance_{course_code}").document(date).get()
        if not doc.exists:
            raise HTTPException(404, "No attendance found for this date")
        return doc.to_dict()
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/dates/{course_code}")
async def get_dates(course_code: str):
    try:
        docs = db.collection(f"attendance_{course_code}").stream()
        dates = []
        for doc in docs:
            dates.append({
                "date": doc.id,
                **doc.to_dict()
            })
        return dates
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/export/{course_code}")
async def export_attendance(course_code: str):
    """
    Export attendance as CSV
    """
    try:
        # Get attendance records
        attendance_ref = db.collection(f"attendance_{course_code}")
        docs = attendance_ref.stream()
        
        rows = []
        for doc in docs:
            data = doc.to_dict()
            date = data.get("date", doc.id)
            time = data.get("time", "")
            
            # Process each student's attendance
            if "attendance" in data:
                for rollno, status in data["attendance"].items():
                    rows.append({
                        "date": date,
                        "time": time,
                        "rollno": rollno,
                        "status": status,
                        "course": course_code
                    })
        
        if not rows:
            raise HTTPException(404, "No attendance records found")
        
        # Get student details for more informative export
        students_ref = db.collection(course_code)
        student_docs = students_ref.stream()
        
        student_info = {}
        for doc in student_docs:
            student_data = doc.to_dict()
            student_info[doc.id] = student_data
        
        # Enhance rows with student info
        enhanced_rows = []
        for row in rows:
            rollno = row["rollno"]
            if rollno in student_info:
                enhanced_rows.append({
                    **row,
                    "name": student_info[rollno].get("name", ""),
                    "section": student_info[rollno].get("section", ""),
                    "department": student_info[rollno].get("department", ""),
                    "semester": student_info[rollno].get("semester", "")
                })
            else:
                enhanced_rows.append(row)
        
        df = pd.DataFrame(enhanced_rows)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            df.to_csv(tmp.name, index=False)
            tmp_path = tmp.name
        
        filename = f"{course_code}_attendance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return FileResponse(
            tmp_path,
            filename=filename,
            media_type='text/csv'
        )
        
    except Exception as e:
        raise HTTPException(500, str(e))
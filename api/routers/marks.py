# api/routers/marks.py
from fastapi import APIRouter, HTTPException, UploadFile
from services.firebase import db
import pandas as pd
import tempfile
from fastapi.responses import FileResponse

router = APIRouter(prefix="/marks", tags=["Marks"])

@router.get("/{course_code}")
async def get_marks_for_course(course_code: str):
    """
    Get marks for all students in a course
    """
    try:
        marks_ref = db.collection(course_code)
        docs = marks_ref.stream()
        
        marks_list = []
        for doc in docs:
            data = doc.to_dict()
            # Check if this document has marks data (not just student info)
            if any(key in data for key in ['mids_marks', 'finals_marks', 'sessional', 'assignment', 'quiz']):
                marks_list.append(data)
        
        return marks_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/marks")
async def upload_marks(file: UploadFile, course_code: str):
    """
    Upload marks CSV/Excel file
    """
    try:
        # Read file
        if file.filename.endswith(".csv"):
            df = pd.read_csv(file.file)
        else:
            df = pd.read_excel(file.file)
        
        # Required column
        if 'rollno' not in df.columns:
            raise HTTPException(status_code=400, detail="CSV must contain 'rollno' column")
        
        df = df.fillna(0)
        
        marks_ref = db.collection(course_code)
        processed = 0
        
        for _, row in df.iterrows():
            rollno = str(row['rollno']).strip()
            if not rollno:
                continue
            
            # Prepare marks data
            marks_data = {
                "mids_marks": float(row.get('mids_marks', 0)),
                "finals_marks": float(row.get('finals_marks', 0)),
                "sessional": float(row.get('sessional', 0)),
                "assignment": float(row.get('assignment', 0)),
                "quiz": float(row.get('quiz', 0))
            }
            
            # Get existing student data
            student_ref = marks_ref.document(rollno)
            student_doc = student_ref.get()
            
            if student_doc.exists:
                # Update with marks
                existing_data = student_doc.to_dict()
                existing_data.update(marks_data)
                student_ref.set(existing_data)
            else:
                # Create new with basic info + marks
                student_data = {
                    "rollno": rollno,
                    "name": row.get('name', ''),
                    "section": row.get('section', ''),
                    "batch": row.get('batch', ''),
                    **marks_data
                }
                student_ref.set(student_data)
            
            processed += 1
        
        return {
            "status": "success",
            "students_processed": processed,
            "message": f"Marks uploaded for {processed} students"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/save")
async def save_marks(data: dict):
    """
    Save or update marks for a student
    """
    try:
        course_code = data.get('course_code')
        rollno = data.get('rollno')
        
        if not course_code or not rollno:
            raise HTTPException(status_code=400, detail="Course code and rollno are required")
        
        marks_ref = db.collection(course_code).document(rollno)
        
        # Get existing data
        existing_doc = marks_ref.get()
        if existing_doc.exists:
            # Update
            existing_data = existing_doc.to_dict()
            existing_data.update(data)
            marks_ref.set(existing_data)
        else:
            # Create new
            marks_ref.set(data)
        
        return {"status": "success", "message": "Marks saved successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update")
async def update_marks(data: dict):
    """
    Update specific field for a student
    """
    try:
        course_code = data.get('course_code')
        rollno = data.get('rollno')
        field = data.get('field')
        value = data.get('value')
        
        if not all([course_code, rollno, field]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        marks_ref = db.collection(course_code).document(rollno)
        marks_ref.update({field: value})
        
        return {"status": "success", "message": "Marks updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/delete")
async def delete_marks(data: dict):
    """
    Delete marks for a student
    """
    try:
        course_code = data.get('course_code')
        rollno = data.get('rollno')
        
        if not course_code or not rollno:
            raise HTTPException(status_code=400, detail="Course code and rollno are required")
        
        marks_ref = db.collection(course_code).document(rollno)
        
        # Get existing data
        existing_doc = marks_ref.get()
        if not existing_doc.exists:
            raise HTTPException(status_code=404, detail="Student marks not found")
        
        # Remove marks fields but keep student info
        existing_data = existing_doc.to_dict()
        
        # Remove marks fields
        marks_fields = ['mids_marks', 'finals_marks', 'sessional', 'assignment', 'quiz']
        for field in marks_fields:
            if field in existing_data:
                del existing_data[field]
        
        # Update document
        marks_ref.set(existing_data)
        
        return {"status": "success", "message": "Marks deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/{course_code}")
async def export_marks(course_code: str):
    """
    Export marks as CSV
    """
    try:
        marks_ref = db.collection(course_code)
        docs = marks_ref.stream()
        
        rows = []
        for doc in docs:
            data = doc.to_dict()
            rows.append(data)
        
        if not rows:
            raise HTTPException(status_code=404, detail="No marks data found")
        
        df = pd.DataFrame(rows)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            df.to_csv(tmp.name, index=False)
            tmp_path = tmp.name
        
        return FileResponse(
            tmp_path,
            filename=f"{course_code}_marks.csv",
            media_type='text/csv'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
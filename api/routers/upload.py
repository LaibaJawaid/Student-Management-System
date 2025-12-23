# api/routers/upload.py
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from services.firebase import db
from datetime import datetime

router = APIRouter(prefix="/upload", tags=["Upload"])

@router.post("/students")
async def upload_student_master(
    file: UploadFile = File(...),
    course_code: str = Form(...)
):
    """
    Upload students CSV/Excel.
    Creates a new collection with course_code as name.
    Also adds course to _courses collection.
    """
    
    if not course_code:
        raise HTTPException(status_code=400, detail="Course code is required")
    
    course_code = course_code.strip()
    
    try:
        # Read file based on extension
        content = await file.read()
        
        if file.filename.endswith(".csv"):
            df = pd.read_csv(pd.io.common.BytesIO(content))
        elif file.filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(pd.io.common.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
        
        # Check required columns
        required_cols = ["rollno", "name", "section", "batch", "department", "semester"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            # Try with different column name formats
            column_mapping = {
                "rollno": ["rollno", "roll_no", "Roll No", "RollNo", "Student ID"],
                "name": ["name", "Name", "Student Name", "student_name"],
                "section": ["section", "Section", "Sec"],
                "batch": ["batch", "Batch", "Class", "Year"],
                "department": ["department", "Department", "Dept", "Branch"],
                "semester": ["semester", "Semester", "Sem"]
            }
            
            # Try to find alternative column names
            for missing_col in missing_cols[:]:
                for alt_name in column_mapping.get(missing_col, []):
                    if alt_name in df.columns:
                        df.rename(columns={alt_name: missing_col}, inplace=True)
                        missing_cols.remove(missing_col)
                        break
        
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing columns in file: {', '.join(missing_cols)}. Required columns: {', '.join(required_cols)}"
            )
        
        # Fill NaN values
        df = df.fillna("")
        
        # Get collection references
        course_collection = db.collection(course_code)
        courses_list_ref = db.collection("_courses").document(course_code)
        
        inserted = 0
        errors = []
        
        # First, check if course already exists
        existing_course = courses_list_ref.get()
        if existing_course.exists:
            # Clear existing students
            existing_students = course_collection.stream()
            for student in existing_students:
                student.reference.delete()
        
        # Upload each student
        for index, row in df.iterrows():
            try:
                rollno = str(row["rollno"]).strip()
                if not rollno:
                    errors.append(f"Row {index + 2}: Empty roll number")
                    continue
                
                student_data = {
                    "rollno": rollno,
                    "name": str(row["name"]).strip(),
                    "section": str(row["section"]).strip(),
                    "batch": str(row["batch"]).strip(),
                    "department": str(row["department"]).strip(),
                    "semester": str(row["semester"]).strip(),
                    "course": course_code,
                    "uploaded_at": datetime.now().isoformat()
                }
                
                # Add additional columns if present
                for col in df.columns:
                    if col not in required_cols and col not in student_data:
                        student_data[col] = str(row[col]).strip()
                
                # Add to course collection (use rollno as document ID)
                course_collection.document(rollno).set(student_data)
                inserted += 1
                
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
        
        # Add/Update course in _courses collection
        courses_list_ref.set({
            "name": course_code,
            "created_at": datetime.now().isoformat(),
            "student_count": inserted,
            "description": f"Course created via upload with {inserted} students",
            "last_updated": datetime.now().isoformat(),
            "status": "active"
        })
        
        return {
            "status": "success",
            "course": course_code,
            "students_added": inserted,
            "total_rows": len(df),
            "errors": errors if errors else None,
            "message": f"Successfully uploaded {inserted} students to course '{course_code}'"
        }
        
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/marks")
async def upload_marks_file(
    file: UploadFile = File(...),
    course_code: str = Form(...)
):
    """
    Upload marks CSV/Excel file
    """
    try:
        # Read file
        content = await file.read()
        
        if file.filename.endswith(".csv"):
            df = pd.read_csv(pd.io.common.BytesIO(content))
        elif file.filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(pd.io.common.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
        
        # Check required columns
        if 'rollno' not in df.columns:
            raise HTTPException(status_code=400, detail="CSV must contain 'rollno' column")
        
        df = df.fillna(0)
        
        marks_ref = db.collection(course_code)
        processed = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                rollno = str(row['rollno']).strip()
                if not rollno:
                    errors.append(f"Row {index + 2}: Empty roll number")
                    continue
                
                # Prepare marks data
                marks_data = {}
                
                # Add all available marks columns
                marks_columns = ['mids_marks', 'finals_marks', 'sessional', 'assignment', 'quiz', 
                                'mid_marks', 'final_marks', 'sessional_marks', 'assignment_marks', 'quiz_marks']
                
                for col in df.columns:
                    if any(mark_col in col.lower() for mark_col in ['mid', 'final', 'sessional', 'assignment', 'quiz', 'marks']):
                        try:
                            value = row[col]
                            if pd.isna(value):
                                marks_data[col] = 0.0
                            else:
                                marks_data[col] = float(value)
                        except:
                            marks_data[col] = 0.0
                
                # Standardize column names
                standardized_data = {}
                for key, value in marks_data.items():
                    key_lower = key.lower()
                    if 'mid' in key_lower and 'final' not in key_lower:
                        standardized_data['mids_marks'] = value
                    elif 'final' in key_lower:
                        standardized_data['finals_marks'] = value
                    elif 'sessional' in key_lower:
                        standardized_data['sessional'] = value
                    elif 'assignment' in key_lower:
                        standardized_data['assignment'] = value
                    elif 'quiz' in key_lower:
                        standardized_data['quiz'] = value
                    else:
                        standardized_data[key] = value
                
                # Get existing student data
                student_ref = marks_ref.document(rollno)
                student_doc = student_ref.get()
                
                if student_doc.exists:
                    # Update with marks
                    existing_data = student_doc.to_dict()
                    existing_data.update(standardized_data)
                    existing_data['marks_updated_at'] = datetime.now().isoformat()
                    student_ref.set(existing_data)
                else:
                    # Create new with basic info + marks
                    student_data = {
                        "rollno": rollno,
                        "name": str(row.get('name', '')),
                        "section": str(row.get('section', '')),
                        "batch": str(row.get('batch', '')),
                        "department": str(row.get('department', '')),
                        "semester": str(row.get('semester', '')),
                        "course": course_code,
                        **standardized_data,
                        "marks_uploaded_at": datetime.now().isoformat()
                    }
                    student_ref.set(student_data)
                
                processed += 1
                
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
        
        return {
            "status": "success",
            "course": course_code,
            "students_processed": processed,
            "errors": errors if errors else None,
            "message": f"Marks uploaded for {processed} students"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
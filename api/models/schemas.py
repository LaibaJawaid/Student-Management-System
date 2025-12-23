# api/models/schemas.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

# Roster row
class RosterRow(BaseModel):
    rollno: str
    name: str
    section: Optional[str] = None
    batch: Optional[int] = None
    department: Optional[str] = None
    semester: Optional[int] = None

class MarksRow(BaseModel):
    rollno: str
    name: Optional[str] = None
    section: Optional[str] = None
    mid_marks: Optional[float] = None
    final_marks: Optional[float] = None
    assignment: Optional[float] = None
    quiz: Optional[float] = None
    sessional: Optional[float] = None
    total: Optional[float] = None
    percentage: Optional[float] = None
    grade: Optional[str] = None
    gpa: Optional[float] = None

class AttendancePayload(BaseModel):
    course_code: str
    date_iso: str
    time_iso: str
    attendance: Dict[str, str]  # rollno -> "present"/"absent"

# api/models/schemas.py (Add the following)

class CourseResult(BaseModel):
    # Core marks
    mid_marks: Optional[float] = Field(default=0.0)
    final_marks: Optional[float] = Field(default=0.0)
    assignment: Optional[float] = Field(default=0.0)
    quiz: Optional[float] = Field(default=0.0)
    sessional: Optional[float] = Field(default=0.0)
    
    # Calculated fields
    total_score: float
    percentage: float
    grade: str
    gpa: float
    credit_hours: int

class StudentReport(BaseModel):
    rollno: str
    name: str
    cgpa: float
    results: Dict[str, CourseResult] # Maps course_code -> CourseResult

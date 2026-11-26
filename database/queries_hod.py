from typing import List, Tuple, Dict, Any
from .connection import connect_to_db_sys, generate_next_pk
import oracledb

# Fetches Course List
# Called By: HOD Enroll Page, HOD Dashboard
# Returns: List of (ID, Name)
def get_all_courses() -> List[Tuple[str, str]]:
    conn = connect_to_db_sys()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT Course_ID, Course_Name FROM Course ORDER BY Course_Name")
        return [(row[0], row[1]) for row in cursor]
    except Exception as e:
        print(f"Fetch Courses Error: {e}")
        return []
    finally:
        if conn: conn.close()

# Fetches Students in a course
# Called By: HOD Enroll/Delist pages
# Returns: List of dicts {'id', 'name'}
def get_all_students(course_id: str) -> List[Dict[str, str]]:
    conn = connect_to_db_sys()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT Student_ID, Student_Name FROM Student WHERE Course_ID = :course_id ORDER BY Student_ID",
                       course_id=course_id)
        return [{'id': row[0], 'name': row[1]} for row in cursor]
    except Exception as e:
        print(f"Fetch Students Error: {e}")
        return []
    finally:
        if conn: conn.close()

# Inserts new student
# Called By: HOD Enroll Page
# Returns: Bool
def insert_new_student(student_id: str, student_name: str, course_id: str) -> bool:
    conn = connect_to_db_sys()
    if not conn: return False
    try:
        cursor = conn.cursor()
        query = "INSERT INTO Student (STUDENT_ID, STUDENT_NAME, Course_ID) VALUES (:id, :name, :cid)"
        cursor.execute(query, id=student_id, name=student_name, cid=course_id)
        conn.commit()
        return True
    except Exception as e:
        print(f"Insert Student Error: {e}")
        conn.rollback()
        return False
    finally:
        if conn: conn.close()

# Deletes student + related data
# Called By: HOD Delist Page
# Returns: Bool
def delete_student_record(student_id: str) -> bool:
    conn = connect_to_db_sys()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Grade WHERE Student_ID = :id", id=student_id)
        cursor.execute("DELETE FROM Attendance WHERE Student_ID = :id", id=student_id)
        cursor.execute("DELETE FROM Assignment WHERE Student_ID = :id", id=student_id)
        cursor.execute("DELETE FROM Student WHERE Student_ID = :id", id=student_id)
        conn.commit()
        return True
    except Exception as e:
        print(f"Delete Student Error: {e}")
        conn.rollback()
        return False
    finally:
        if conn: conn.close()

# Calcs next Student ID
# Called By: HOD Enroll Page (Auto-fill)
# Returns: Next ID String
def generate_next_student_id() -> str:
    conn = connect_to_db_sys()
    if not conn: return "101"
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(TO_NUMBER(Student_ID)) FROM Student WHERE REGEXP_LIKE(Student_ID, '^[0-9]+$')")
        result = cursor.fetchone()
        max_id = int(result[0]) + 1 if result and result[0] else 101
        return str(max_id)
    except Exception:
        return "101"
    finally:
        if conn: conn.close()

# Aggregates ALL academic data for ML
# Called By: HOD Prediction/What-If/Groups pages
# Returns: List of normalized student profiles
def fetch_aggregate_data_for_prediction(course_id: str) -> List[Dict[str, Any]]:
    conn = connect_to_db_sys()
    if not conn: return []

    students = get_all_students(course_id)
    if not students: return []

    student_data = {s['id']: {'Student_Name': s['name'], 'unit_test_marks': 0, 'unit_test_full': 0, 'mid_term_marks': 0,
                              'mid_term_full': 0, 'end_term_marks': 0, 'end_term_full': 0, 'attendance_days': 0,
                              'total_class_days': 0, 'assignments_submitted': 0, 'total_assignments': 0} for s in
                    students}

    try:
        cursor = conn.cursor()
        # Grades
        q_grade = """SELECT gt.Student_ID, gt.Grade_Type, gt.Grade_Marks,
                            CASE WHEN gt.Grade_Type = 'Unit Test' THEN ed.Unit_Full
                                 WHEN gt.Grade_Type = 'Mid Term' THEN ed.Mid_Full
                                 WHEN gt.Grade_Type = 'End Term' THEN ed.End_Full ELSE 0 END
                     FROM Grade gt JOIN Exam ed ON gt.Subject_ID = ed.Subject_ID
                     JOIN Subject sub ON gt.Subject_ID = sub.Subject_ID WHERE sub.Course_ID = :cid"""
        cursor.execute(q_grade, cid=course_id)
        for sid, gtype, marks, full in cursor:
            if sid in student_data and marks is not None:
                if gtype == 'Unit Test':
                    student_data[sid]['unit_test_marks'] += marks; student_data[sid]['unit_test_full'] += full
                elif gtype == 'Mid Term':
                    student_data[sid]['mid_term_marks'] += marks; student_data[sid]['mid_term_full'] += full
                elif gtype == 'End Term':
                    student_data[sid]['end_term_marks'] += marks; student_data[sid]['end_term_full'] += full

        # Attendance
        q_att = "SELECT at.Student_ID, SUM(at.Days), SUM(sd.Class_Days) FROM Attendance at JOIN Subject sd ON at.Subject_ID = sd.Subject_ID WHERE at.Attendance_Type='CLASS' AND sd.Course_ID = :cid GROUP BY at.Student_ID"
        cursor.execute(q_att, cid=course_id)
        for sid, days, total in cursor:
            if sid in student_data: student_data[sid]['attendance_days'] = days or 0; student_data[sid]['total_class_days'] = total or 0

        # Assignments
        q_ass = "SELECT ast.Student_ID, SUM(ast.Number_Of_Assignment), SUM(sd.Class_Assignment_Assigned) FROM Assignment ast JOIN Subject sd ON ast.Subject_ID = sd.Subject_ID WHERE ast.Submission_Type='Class' AND sd.Course_ID = :cid GROUP BY ast.Student_ID"
        cursor.execute(q_ass, cid=course_id)
        for sid, subm, total in cursor:
            if sid in student_data: student_data[sid]['assignments_submitted'] = subm or 0; student_data[sid]['total_assignments'] = total or 0

        final_data = []
        for sid, d in student_data.items():
            final_data.append({
                'Student_ID': sid, 'Student_Name': d['Student_Name'],
                'Unit_Test': (d['unit_test_marks'] / d['unit_test_full'] * 100) if d['unit_test_full'] else 0,
                'Mid_Term': (d['mid_term_marks'] / d['mid_term_full'] * 100) if d['mid_term_full'] else 0,
                'Pre_Board': (d['end_term_marks'] / d['end_term_full'] * 100) if d['end_term_full'] else 0,
                'Class_Attendance': (d['attendance_days'] / d['total_class_days'] * 100) if d['total_class_days'] else 0,
                'Assignment_Submission': (d['assignments_submitted'] / d['total_assignments'] * 100) if d['total_assignments'] else 0
            })
        return final_data
    except Exception as e:
        print(f"Fetch Prediction Data Error: {e}")
        return []
    finally:
        if conn: conn.close()

# Fetches total marks per student for HOD Pareto Chart
# Called By: HOD Reports Page
# Returns: List of (StudentName, Percentage)
def fetch_aggregate_grades_for_pareto(conn: oracledb.Connection, course_id: str, grade_type: str) -> List[Tuple[str, int]]:
    if not conn: return []
    data = []
    local_conn = connect_to_db_sys()
    if not local_conn: return []

    try:
        cursor = local_conn.cursor()
        # Updated Query: Calculates Percentage (Obtained / Full * 100) instead of raw SUM
        query = """
        SELECT s.Student_Name, 
               ROUND((SUM(g.Grade_Marks) / NULLIF(SUM(
                   CASE 
                       WHEN g.Grade_Type = 'Unit Test' THEN e.Unit_Full
                       WHEN g.Grade_Type = 'Mid Term' THEN e.Mid_Full
                       WHEN g.Grade_Type = 'End Term' THEN e.End_Full
                       ELSE 0
                   END
               ), 0)) * 100) AS Percentage
        FROM Grade g 
        JOIN Student s ON g.Student_ID = s.Student_ID 
        JOIN Subject sub ON g.Subject_ID = sub.Subject_ID
        JOIN Exam e ON g.Subject_ID = e.Subject_ID
        WHERE sub.Course_ID = :course_id AND g.Grade_Type = :grade_type
        GROUP BY s.Student_Name 
        ORDER BY Percentage DESC
        """
        cursor.execute(query, course_id=course_id, grade_type=grade_type)
        data = cursor.fetchall()
    except Exception as e:
        print(f"Fetch Aggregate Grades Error: {e}")
    finally:
        if local_conn: local_conn.close()

    return [(str(name), int(pct or 0)) for name, pct in data]


def fetch_exam_config(subject_id):
    """
    Retrieves the exam configuration (Full/Pass marks) for a specific subject.
    """
    conn = connect_to_db_sys()
    if not conn: return None

    try:
        cursor = conn.cursor()
        query = """
                SELECT Unit_Full, Unit_Pass, Mid_Full, Mid_Pass, End_Full, End_Pass
                FROM Exam
                WHERE Subject_ID = :sid \
                """
        cursor.execute(query, sid=subject_id)
        result = cursor.fetchone()

        if result:
            return {
                "Unit_Full": result[0], "Unit_Pass": result[1],
                "Mid_Full": result[2], "Mid_Pass": result[3],
                "End_Full": result[4], "End_Pass": result[5]
            }
        return None  # No config found for this subject
    except Exception as e:
        print(f"Error fetching exam config: {e}")
        return None
    finally:
        if conn: conn.close()
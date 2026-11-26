from typing import List, Dict, Any
from .connection import connect_to_db_sys, generate_next_pk
import oracledb

# Fetches Teacher details and Student list
# Called By: main.py (Dashboard Init)
# Returns: Dict (teacher_name, subject_name, students)
def fetch_all_teacher_data(subject_id: str) -> Dict[str, Any] | None:
    conn = connect_to_db_sys()
    if not conn: return None
    try:
        cursor = conn.cursor()
        q = """SELECT s.Staff_Name, sub.Subject_Name, s.Staff_ID, sub.Course_ID FROM Staff s 
            JOIN Subject sub ON s.Subject_ID = sub.Subject_ID WHERE s.Staff_ID = :sid AND s.Role = 'TEACHER'"""
        cursor.execute(q, sid=subject_id)
        res = cursor.fetchone()
        if not res: return None

        q_stu = "SELECT Student_ID, Student_Name FROM Student WHERE Course_ID = :cid ORDER BY Student_ID"
        cursor.execute(q_stu, cid=res[3])
        students = [{'id': r[0], 'name': r[1]} for r in cursor]

        return {'teacher_name': res[0], 'subject_name': res[1], 'teacher_id': res[2], 'subject_id': subject_id, 'students': students}
    except Exception as e:
        print(f"Fetch Teacher Data Error: {e}")
        return None
    finally:
        conn.close()

# Checks if subject has Lab
# Called By: Teacher Dashboard (Menu toggle)
# Returns: Bool
def get_subject_lab_status(subject_id: str) -> bool:
    conn = connect_to_db_sys()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT Lab_Status FROM Subject WHERE Subject_ID = :sid", sid=subject_id)
        res = cursor.fetchone()
        return res and res[0] == 'Y'
    finally:
        conn.close()

# --- EXAM / GRADES ---

# Gets Max Marks config
# Called By: Grades Page
# Returns: Dict (Unit_Full, etc)
def fetch_exam_details_for_subject(conn, subject_id):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT Unit_Full, Unit_Pass, Mid_Full, Mid_Pass, End_Full, End_Pass FROM Exam WHERE Subject_ID = :sid", sid=subject_id)
        res = cursor.fetchone()
        if res:
            return {'Unit_Full': res[0], 'Unit_Pass': res[1], 'Mid_Full': res[2], 'Mid_Pass': res[3], 'End_Full': res[4], 'End_Pass': res[5]}
        return {}
    except Exception as e:
        print(f"Fetch Exam Config Error: {e}")
        return {}

# Saves Max Marks config
# Called By: Grades Page (Save)
# Returns: Bool
def save_exam_details_to_db(conn, subject_id, data):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT Exam_Details_ID FROM Exam WHERE Subject_ID = :sid", sid=subject_id)
        res = cursor.fetchone()

        if res:
            sql = "UPDATE Exam SET Unit_Full=:uf, Unit_Pass=:up, Mid_Full=:mf, Mid_Pass=:mp, End_Full=:ef, End_Pass=:ep WHERE Subject_ID = :sid"
            cursor.execute(sql, uf=data['unit_full'], up=data['unit_pass'], mf=data['mid_full'], mp=data['mid_pass'], ef=data['end_full'], ep=data['end_pass'], sid=subject_id)
        else:
            pk = generate_next_pk(conn, "Exam_Details_ID", "Exam", "EXD")
            sql = "INSERT INTO Exam (Exam_Details_ID, Subject_ID, Unit_Full, Unit_Pass, Mid_Full, Mid_Pass, End_Full, End_Pass) VALUES (:pk, :sid, :uf, :up, :mf, :mp, :ef, :ep)"
            cursor.execute(sql, pk=pk, sid=subject_id, uf=data['unit_full'], up=data['unit_pass'], mf=data['mid_full'], mp=data['mid_pass'], ef=data['end_full'], ep=data['end_pass'])
        conn.commit()
        return True
    except Exception as e:
        print(f"Save Exam Config Error: {e}")
        conn.rollback()
        return False

# Gets student grades
# Called By: Grades Page, Teacher Analysis
# Returns: Dict {StudentID: Grades}
def fetch_student_grades_for_subject(conn, subject_id):
    data = {}
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT Student_ID, Grade_Type, Grade_Marks FROM Grade WHERE Subject_ID=:sid", sid=subject_id)
        for sid, gtype, marks in cursor:
            if sid not in data: data[sid] = {}
            data[sid][gtype] = str(int(marks)) if marks is not None else '0'
        return data
    except Exception as e:
        print(f"Fetch Grades Error: {e}")
        return {}

# Saves student grades
# Called By: Grades Page (Save)
# Returns: Bool
def save_grades_to_db(conn, grades_data):
    try:
        cursor = conn.cursor()
        check = "SELECT Grade_ID FROM Grade WHERE Student_ID=:sid AND Subject_ID=:sub AND Grade_Type=:typ"
        update = "UPDATE Grade SET Grade_Marks=:m WHERE Grade_ID=:gid"
        insert = "INSERT INTO Grade (Grade_ID, Student_ID, Subject_ID, Grade_Type, Grade_Marks) VALUES (:gid, :sid, :sub, :typ, :m)"

        for row in grades_data:
            for gtype in ['Unit Test', 'Mid Term', 'End Term']:
                key = gtype.lower().replace(' ', '_')
                if key in row:
                    cursor.execute(check, sid=row['student_id'], sub=row['subject_id'], typ=gtype)
                    res = cursor.fetchone()
                    if res:
                        cursor.execute(update, m=row[key], gid=res[0])
                    else:
                        pk = generate_next_pk(conn, "Grade_ID", "Grade", "GRA")
                        cursor.execute(insert, gid=pk, sid=row['student_id'], sub=row['subject_id'], typ=gtype, m=row[key])
        conn.commit()
        return True
    except Exception as e:
        print(f"Save Grades Error: {e}")
        conn.rollback()
        return False

# --- ATTENDANCE / ASSIGNMENT ---

# Gets Max Days/Assignment config
# Called By: Attendance/Assignment Pages
# Returns: String
def fetch_subject_config(conn, subject_id, table, column):
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT {column} FROM {table} WHERE Subject_ID = :sid", sid=subject_id)
        res = cursor.fetchone()
        return str(int(res[0])) if res and res[0] is not None else '0'
    except Exception:
        return '0'

# Saves Max Days/Assignment config
# Called By: Attendance/Assignment Pages
# Returns: Bool
def save_subject_config(conn, subject_id, table, column, value):
    try:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE {table} SET {column} = :val WHERE Subject_ID = :sid", val=value, sid=subject_id)
        conn.commit()
        return True
    except Exception as e:
        print(f"Save Config Error: {e}"); conn.rollback(); return False

# Gets Attendance/Assignment records
# Called By: Attendance/Assignment Pages
# Returns: Dict {StudentID: Value}
def fetch_student_records(conn, subject_id, table, type_col, type_val, value_col):
    data = {}
    try:
        cursor = conn.cursor()
        if type_col:
            cursor.execute(f"SELECT Student_ID, {value_col} FROM {table} WHERE Subject_ID=:sid AND {type_col}=:tv", sid=subject_id, tv=type_val)
        else:
            cursor.execute(f"SELECT Student_ID, {value_col} FROM {table} WHERE Subject_ID=:sid", sid=subject_id)
        for sid, val in cursor:
            data[sid] = str(int(val)) if val is not None else '0'
        return data
    except Exception as e:
        print(f"Fetch Records Error: {e}"); return {}

# Saves Attendance data
# Called By: Attendance Page (Save)
# Returns: Bool
def save_attendance_data(conn, data, att_type, subject_id):
    try:
        cursor = conn.cursor()
        check = "SELECT Attendance_ID FROM Attendance WHERE Student_ID=:sid AND Subject_ID=:sub AND Attendance_Type=:typ"
        update = "UPDATE Attendance SET Days=:d WHERE Attendance_ID=:aid"
        insert = "INSERT INTO Attendance (Attendance_ID, Student_ID, Subject_ID, Attendance_Type, Days) VALUES (:aid, :sid, :sub, :typ, :d)"

        for item in data:
            cursor.execute(check, sid=item['student_id'], sub=subject_id, typ=att_type)
            res = cursor.fetchone()
            if res:
                cursor.execute(update, d=item['total_days'], aid=res[0])
            else:
                pk = generate_next_pk(conn, "Attendance_ID", "Attendance", "ATN")
                cursor.execute(insert, aid=pk, sid=item['student_id'], sub=subject_id, typ=att_type, d=item['total_days'])
        conn.commit()
        return True
    except Exception as e:
        print(f"Save Attendance Error: {e}"); conn.rollback(); return False

# Saves Assignment data
# Called By: Assignment Page (Save)
# Returns: Bool
def save_assignment_data(conn, data, sub_type, subject_id):
    try:
        cursor = conn.cursor()
        check = "SELECT Assignment_ID FROM Assignment WHERE Student_ID=:sid AND Subject_ID=:sub AND Submission_Type=:typ"
        update = "UPDATE Assignment SET Number_Of_Assignment=:d WHERE Assignment_ID=:aid"
        insert = "INSERT INTO Assignment (Assignment_ID, Student_ID, Subject_ID, Submission_Type, Number_Of_Assignment) VALUES (:aid, :sid, :sub, :typ, :d)"

        for item in data:
            cursor.execute(check, sid=item['student_id'], sub=subject_id, typ=sub_type)
            res = cursor.fetchone()
            if res:
                cursor.execute(update, d=item['number_of_assignment'], aid=res[0])
            else:
                pk = generate_next_pk(conn, "Assignment_ID", "Assignment", "ASN")
                cursor.execute(insert, aid=pk, sid=item['student_id'], sub=subject_id, typ=sub_type, d=item['number_of_assignment'])
        conn.commit()
        return True
    except Exception as e:
        print(f"Save Assignment Error: {e}"); conn.rollback(); return False

# --- ANALYSIS ---

# Gets single exam type data for charts
# Called By: Teacher Analysis Page
# Returns: List of tuples
def fetch_grades_for_pareto(conn, subject_id, grade_type):
    try:
        cursor = conn.cursor()
        q = """SELECT s.Student_ID, s.Student_Name, g.Grade_Marks FROM Grade g JOIN Student s ON g.Student_ID = s.Student_ID
               WHERE g.Subject_ID = :sid AND g.Grade_Type = :typ ORDER BY g.Grade_Marks DESC"""
        cursor.execute(q, sid=subject_id, typ=grade_type)
        return cursor.fetchall()
    except Exception as e:
        print(f"Pareto Error: {e}")
        return []

# Aggregates all data for clustering
# Called By: Teacher Groups Page
# Returns: List of student profiles (normalized)
def fetch_data_for_teacher_groups(conn, subject_id):
    try:
        cursor = conn.cursor()
        # 1. Subject Details
        cursor.execute("SELECT Class_Days, Lab_Days, Class_Assignment_Assigned, Lab_Assignment_Assigned, Lab_Status FROM Subject WHERE Subject_ID = :sid", sid=subject_id)
        sub_res = cursor.fetchone()
        if not sub_res: return [], []
        cls_days, lab_days, cls_ass, lab_ass, lab_stat = sub_res
        has_lab = (lab_stat == 'Y')

        # 2. Exam Config
        cursor.execute("SELECT Unit_Full, Mid_Full, End_Full FROM Exam WHERE Subject_ID = :sid", sid=subject_id)
        exam_res = cursor.fetchone()
        unit_full, mid_full, end_full = exam_res if exam_res else (0, 0, 0)

        # 3. Students
        cursor.execute("SELECT Course_ID FROM Subject WHERE Subject_ID = :sid", sid=subject_id)
        cid_res = cursor.fetchone()
        if not cid_res: return [], []
        course_id = cid_res[0]
        cursor.execute("SELECT Student_ID, Student_Name FROM Student WHERE Course_ID = :cid", cid=course_id)
        students = {row[0]: {'Student_Name': row[1]} for row in cursor}

        # 4. Data
        cursor.execute("SELECT Student_ID, Grade_Type, Grade_Marks FROM Grade WHERE Subject_ID = :sid", sid=subject_id)
        for sid, gtype, marks in cursor:
            if sid in students: students[sid][gtype] = marks or 0

        cursor.execute("SELECT Student_ID, Attendance_Type, Days FROM Attendance WHERE Subject_ID = :sid", sid=subject_id)
        for sid, atype, days in cursor:
            if sid in students: students[sid][f"{atype}_Attendance"] = days or 0

        cursor.execute("SELECT Student_ID, Submission_Type, Number_Of_Assignment FROM Assignment WHERE Subject_ID = :sid", sid=subject_id)
        for sid, stype, num in cursor:
            if sid in students: students[sid][f"{stype}_Assignment"] = num or 0

        # 5. Calc %
        final_data = []
        features = ['Unit_Test', 'Mid_Term', 'End_Term', 'Class_Attendance', 'Class_Assignment']
        if has_lab: features.extend(['Lab_Attendance', 'Lab_Assignment'])

        for sid, data in students.items():
            row = {'Student_Name': data['Student_Name']}
            row['Unit_Test'] = (data.get('Unit Test', 0) / unit_full * 100) if unit_full else 0
            row['Mid_Term'] = (data.get('Mid Term', 0) / mid_full * 100) if mid_full else 0
            row['End_Term'] = (data.get('End Term', 0) / end_full * 100) if end_full else 0
            row['Class_Attendance'] = (data.get('CLASS_Attendance', 0) / cls_days * 100) if cls_days else 0
            row['Class_Assignment'] = (data.get('Class_Assignment', 0) / cls_ass * 100) if cls_ass else 0
            if has_lab:
                row['Lab_Attendance'] = (data.get('LAB_Attendance', 0) / lab_days * 100) if lab_days else 0
                row['Lab_Assignment'] = (data.get('Lab_Assignment', 0) / lab_ass * 100) if lab_ass else 0
            for f in features: row[f] = round(row.get(f, 0), 2)
            final_data.append(row)

        return final_data, features
    except Exception as e:
        print(f"Fetch Groups Error: {e}")
        return [], []
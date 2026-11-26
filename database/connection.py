import oracledb
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_HOST, DB_SERVICE, DB_USER_ADMIN, DB_PASSWORD_DEFAULT

# Connects to Oracle as Admin
# Called By: main.py (HOD Init), queries_auth.py, queries_hod.py
# Returns: Connection Object or None
def connect_to_db_sys() -> oracledb.Connection | None:
    dsn = f"{DB_HOST}/{DB_SERVICE}"
    try:
        return oracledb.connect(user=DB_USER_ADMIN, password=DB_PASSWORD_DEFAULT, dsn=dsn)
    except Exception as e:
        print(f"Admin Connection Error: {e}")
        return None

# Connects as Teacher and switches schema to Admin
# Called By: main.py (Teacher Init)
# Returns: Connection Object or None
def connect_to_db_teacher(db_user: str) -> oracledb.Connection | None:
    dsn = f"{DB_HOST}/{DB_SERVICE}"
    try:
        connection = oracledb.connect(user=db_user, password=DB_PASSWORD_DEFAULT, dsn=dsn)
        cursor = connection.cursor()
        cursor.execute(f"ALTER SESSION SET CURRENT_SCHEMA = {DB_USER_ADMIN}")
        cursor.close()
        return connection
    except Exception as e:
        print(f"Teacher Connection Error ({db_user}): {e}")
        return None

# Generates next PK (e.g., GRA101 -> GRA102)
# Called By: queries_teacher.py (Save), queries_hod.py (Enroll)
# Returns: New ID String
def generate_next_pk(conn: oracledb.Connection, pk_column: str, table_name: str, prefix: str, start_val: int = 101) -> str:
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        if cursor.fetchone()[0] == 0:
            return f"{prefix}{start_val}"

        query = f"SELECT MAX(TO_NUMBER(SUBSTR({pk_column}, LENGTH('{prefix}') + 1))) FROM {table_name} WHERE {pk_column} LIKE '{prefix}%'"
        cursor.execute(query)
        result = cursor.fetchone()
        max_id_num = 0
        if result and result[0] is not None:
            try:
                max_id_num = int(result[0])
            except ValueError:
                pass
        return f"{prefix}{max_id_num + 1 if max_id_num > 0 else start_val}"
    except Exception as e:
        print(f"PK Generation Error: {e}")
        return f"{prefix}{start_val}"
from .connection import connect_to_db_sys
from typing import List, Tuple, Dict

# Checks if Staff ID and Email match
# Called By: ui/auth/login_ui.py (Forgot Password Step 1)
# Returns: Bool
def verify_staff_identity(username: str, email: str) -> bool:
    conn = connect_to_db_sys()
    if not conn: return False
    try:
        cursor = conn.cursor()
        query = "SELECT Email FROM Staff WHERE Staff_ID = :id"
        cursor.execute(query, id=username)
        result = cursor.fetchone()
        return result and result[0].lower() == email.lower()
    except Exception as e:
        print(f"Identity Check Error: {e}")
        return False
    finally:
        conn.close()

# Updates password in DB
# Called By: ui/auth/login_ui.py (Forgot Password Step 3)
# Returns: Bool
def update_staff_password(username: str, new_password: str) -> bool:
    conn = connect_to_db_sys()
    if not conn: return False
    try:
        cursor = conn.cursor()
        query = "UPDATE Staff SET Password = :pw WHERE Staff_ID = :id"
        cursor.execute(query, pw=new_password, id=username)
        conn.commit()
        return True
    except Exception as e:
        print(f"Password Update Error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# Verifies Login Credentials
# Called By: main.py (AppController)
# Returns: Bool
def verify_staff_credentials(username: str, password: str) -> bool:
    conn = connect_to_db_sys()
    if not conn: return False
    try:
        cursor = conn.cursor()
        query = "SELECT Password FROM Staff WHERE Staff_ID = :id"
        cursor.execute(query, id=username)
        result = cursor.fetchone()

        if result:
            return password == result[0]
        return False
    except Exception as e:
        print(f"Credential Check Error: {e}")
        return False
    finally:
        conn.close()

# Gets User Role (HOD/TEACHER)
# Called By: main.py (Routing)
# Returns: String or None
def get_staff_role(username: str) -> str | None:
    conn = connect_to_db_sys()
    if not conn: return None
    try:
        cursor = conn.cursor()
        query = "SELECT Role FROM Staff WHERE Staff_ID = :id"
        cursor.execute(query, id=username)
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"Role Fetch Error: {e}")
        return None
    finally:
        conn.close()
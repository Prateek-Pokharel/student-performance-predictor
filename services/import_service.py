import pandas as pd

# Creates CSV with Student Names pre-filled
# Called By: Teacher Pages (Grades, Att, Assign)
# Returns: (Success_Bool, Message_Str)
def generate_template(file_path, students, data_columns):
    try:
        data = {
            'Student_ID': [s['id'] for s in students],
            'Student_Name': [s['name'] for s in students]
        }
        for col in data_columns:
            data[col] = ''

        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)
        return True, "Template created successfully."
    except Exception as e:
        return False, f"Failed to create template: {str(e)}"

# Creates Blank CSV with Headers only
# Called By: HOD Enroll Page
# Returns: (Success_Bool, Message_Str)
def generate_blank_template(file_path, headers):
    try:
        df = pd.DataFrame(columns=headers)
        df.to_csv(file_path, index=False)
        return True, "Template created successfully."
    except Exception as e:
        return False, f"Failed to create template: {str(e)}"

# Reads and Validates Uploaded CSV
# Logic: Checks file existence, 'Student_ID' column, and fills NaNs
# Called By: All Import Buttons (Teacher & HOD)
# Returns: (DataFrame, Error_Message_Str)
def parse_csv_data(file_path, required_columns):
    try:
        df = pd.read_csv(file_path)
        df.columns = [c.strip() for c in df.columns]

        if 'Student_ID' not in df.columns:
            return None, "Invalid CSV: Missing 'Student_ID' column."

        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            return None, f"Invalid CSV: Missing columns: {', '.join(missing)}"

        df.fillna(0, inplace=True)
        return df, None

    except FileNotFoundError:
        return None, "File not found."
    except pd.errors.EmptyDataError:
        return None, "The selected file is empty."
    except Exception as e:
        return None, f"Failed to read file: {str(e)}"
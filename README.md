# Student Performance Predictor

A Python desktop coursework project for managing student records and reviewing academic performance. The application has separate HOD and teacher dashboards, CSV import templates, attendance, assignment and grade tracking, charts, and a logistic-regression pass/fail prediction feature.

## Technology

- Python 3.10+
- PySide6 desktop UI
- Oracle Database through `python-oracledb`
- pandas, Matplotlib, and scikit-learn

## Requirements and setup

1. Install Python 3.10 or newer and Oracle Database XE (or a compatible Oracle database).
2. Create and configure the database schema expected by the application. **The supplied project archive does not include the Oracle schema or seed SQL**, so the application cannot connect to a fresh database until you provide that setup.
3. In PowerShell, open this project folder and create a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

4. Set environment variables for your own Oracle account. For example:

   ```powershell
   $env:DB_HOST = "127.0.0.1"
   $env:DB_SERVICE = "XE"
   $env:DB_USER_ADMIN = "PROJECT_ADMIN"
   $env:DB_PASSWORD_DEFAULT = "your-local-database-password"
   ```

   For password-recovery email, set `SENDER_EMAIL` and `SENDER_PASSWORD` to an email account and app password you control. Do not commit these values.

5. Start the application:

   ```powershell
   python main.py
   ```

## Model and sample templates

`logistic_regression_model.pkl` is the included prediction model. CSV templates under `ui/` show the expected import columns and contain example IDs and values; replace them with your own data.

## Current limitations

- A database schema/bootstrap script is not included, so setup is incomplete for new users until that is supplied.
- Oracle credentials and SMTP credentials must be configured locally through environment variables.
- This is an academic prototype, not a production student-information system. Review authentication, database permissions, and privacy controls before using real student records.

## Privacy

Do not upload real student records, database exports, passwords, email app passwords, or `.env` files. Keep any real student information in a private, access-controlled system.

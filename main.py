import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
from database.queries_auth import verify_staff_credentials, get_staff_role
from database.queries_teacher import fetch_all_teacher_data
from database.connection import connect_to_db_teacher, connect_to_db_sys
from ui.auth.login_ui import LoginPage
from ui.hod.dashboard import HODDashboardUI
from ui.teacher.dashboard import TeacherDashboardUI


def fetch_hod_data(staff_id):
    return {"teacher_name": "Head of Department", "staff_id": staff_id, "subject_name": "Admin"}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Student Performance Predictor")
        self.resize(1250, 800)  # One fixed window size for all views

        # The central widget is a Stack that holds [Login, Dashboard]
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # 1. Initialize Login Page
        self.login_page = LoginPage()
        # Connect login signal
        self.login_page.login_request.connect(self.handle_login_attempt)

        self.stack.addWidget(self.login_page)  # Index 0
        self.dashboard_widget = None

    def handle_login_attempt(self, user, pwd):
        """Called when user clicks Login on the Login Page"""
        if verify_staff_credentials(user, pwd):
            role = get_staff_role(user)

            # Prepare Dashboard Data
            dashboard = None
            if role == 'HOD':
                data = fetch_hod_data(user)
                conn = connect_to_db_sys()
                if conn:
                    dashboard = HODDashboardUI(data, conn)

            elif role == 'TEACHER':
                data = fetch_all_teacher_data(user)
                conn = connect_to_db_teacher(f"C##{user}")
                if conn:
                    dashboard = TeacherDashboardUI(data, conn)

            # Switch View if Dashboard created
            if dashboard:
                self.show_dashboard(dashboard)
            else:
                QMessageBox.critical(self, "Database Error", "Could not connect to database.")
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid Credentials. Please try again.")

    def show_dashboard(self, dashboard_widget):
        self.dashboard_widget = dashboard_widget
        # Listen for Logout
        self.dashboard_widget.logout_signal.connect(self.handle_logout)

        self.stack.addWidget(self.dashboard_widget)  # Add to stack
        self.stack.setCurrentWidget(self.dashboard_widget)  # Switch view

    def handle_logout(self):
        """Called when user clicks Logout on Dashboard"""
        if self.dashboard_widget:
            # 1. Close DB Connection if stored
            if hasattr(self.dashboard_widget, 'conn') and self.dashboard_widget.conn:
                self.dashboard_widget.conn.close()

            # 2. Remove from stack and delete
            self.stack.removeWidget(self.dashboard_widget)
            self.dashboard_widget.deleteLater()
            self.dashboard_widget = None

        # 3. Switch back to Login
        self.stack.setCurrentIndex(0)
        # Clear password fields
        self.login_page.login_widget.pass_input.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
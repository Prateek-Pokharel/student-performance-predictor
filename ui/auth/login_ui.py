from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QMessageBox, QStackedWidget)
from PySide6.QtCore import Qt, Signal, QThread, QObject
import sys
import os

# --- PATH SETUP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(root_dir)

from database.queries_auth import verify_staff_credentials, update_staff_password, verify_staff_identity
from services.auth_service import generate_otp, send_otp_email

# --- SHARED STYLES ---
STYLE_INPUT = "QLineEdit { border: 1px solid #d1d5db; border-radius: 6px; padding: 10px; font-size: 14px; color: #1e293b; }"

STYLE_BTN_PRIMARY = """
    QPushButton { background-color: #4f46e5; color: white; border-radius: 6px; padding: 10px; border: none; font-weight: 600; }
    QPushButton:hover { background-color: #4338ca; }
    QPushButton:pressed { background-color: #3730a3; }
"""

STYLE_BTN_SECONDARY = """
    QPushButton { background-color: #e5e7eb; color: #374151; border-radius: 6px; padding: 10px; border: none; font-weight: 500; }
    QPushButton:hover { background-color: #d1d5db; }
    QPushButton:pressed { background-color: #9ca3af; }
"""

# New Style for "Link" buttons like Forgot Password
STYLE_LINK_BTN = """
    QPushButton { color: #4f46e5; border: none; background: transparent; font-weight: 600; text-align: center; }
    QPushButton:hover { color: #3730a3; text-decoration: underline; }
    QPushButton:pressed { color: #1e1b4b; }
"""

STYLE_ERROR_LABEL = "color: #ef4444; font-weight: 500; font-size: 12px;"


# --- HELPER TO FORCE HOVER ---
def apply_hover(widget):
    """Forces the widget to track mouse hover events immediately."""
    widget.setAttribute(Qt.WA_Hover)


# ====================================================================
# WORKER & WAITING WIDGET
# ====================================================================
class EmailSenderWorker(QObject):
    finished = Signal(bool, str, str)

    def __init__(self, username, email, otp):
        super().__init__()
        self.username = username;
        self.email = email;
        self.otp = otp

    def run(self):
        body = f"Your OTP is: {self.otp}"
        success = send_otp_email("Password Reset OTP", body, self.email)
        self.finished.emit(success, self.username, self.otp)


class WaitingWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        lbl = QLabel("Sending OTP via Email...");
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #4f46e5;")
        sub = QLabel("Please wait. This may take a few moments.");
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("font-size: 16px; color: #64748b; margin-top: 10px;")
        layout.addStretch();
        layout.addWidget(lbl);
        layout.addWidget(sub);
        layout.addStretch()


# ====================================================================
# STEP 1: VERIFY IDENTITY
# ====================================================================
class VerifyIdentityWidget(QWidget):
    navigate = Signal(int)

    def __init__(self):
        super().__init__()
        self.username = None;
        self.email = None;
        self.thread = None;
        self.worker = None;
        self.otp = None
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self);
        layout.setContentsMargins(0, 0, 0, 0);
        layout.setSpacing(15)
        title = QLabel("Reset Password (1/3)");
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #2c3e50;")
        layout.addWidget(title)
        info = QLabel("Enter your username and registered email address to receive an OTP.")
        info.setWordWrap(True);
        info.setAlignment(Qt.AlignCenter);
        info.setStyleSheet("font-size: 14px; color: #5c6b73;")
        layout.addWidget(info);
        layout.addSpacing(10)

        self.user_in = QLineEdit();
        self.user_in.setPlaceholderText("Username (Staff ID)");
        self.user_in.setStyleSheet(STYLE_INPUT);
        layout.addWidget(self.user_in)
        self.email_in = QLineEdit();
        self.email_in.setPlaceholderText("Email Address");
        self.email_in.setStyleSheet(STYLE_INPUT);
        layout.addWidget(self.email_in)

        self.error_label = QLabel("");
        self.error_label.setStyleSheet(STYLE_ERROR_LABEL);
        self.error_label.setAlignment(Qt.AlignCenter);
        layout.addWidget(self.error_label)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Back to Login");
        self.btn_cancel.setCursor(Qt.PointingHandCursor);
        self.btn_cancel.setStyleSheet(STYLE_BTN_SECONDARY)
        apply_hover(self.btn_cancel)
        self.btn_cancel.clicked.connect(lambda: self.navigate.emit(0))

        self.btn_next = QPushButton("Send OTP");
        self.btn_next.setCursor(Qt.PointingHandCursor);
        self.btn_next.setStyleSheet(STYLE_BTN_PRIMARY)
        apply_hover(self.btn_next)
        self.btn_next.clicked.connect(self.handle_check_identity)

        btn_layout.addWidget(self.btn_cancel);
        btn_layout.addWidget(self.btn_next);
        layout.addLayout(btn_layout)

    def handle_check_identity(self):
        self.error_label.setText("");
        self.username = self.user_in.text().strip();
        self.email = self.email_in.text().strip()
        if not self.username or not self.email: self.error_label.setText(
            "Please fill in both Username and Email."); return

        # NOTE: Ensure verify_staff_identity exists in queries_auth.py
        if verify_staff_identity(self.username, self.email):
            self.start_email_thread()
        else:
            self.error_label.setText("Invalid Username or Email combination.")

    def start_email_thread(self):
        generated_otp = str(generate_otp());
        self.navigate.emit(4)
        self.thread = QThread();
        self.worker = EmailSenderWorker(self.username, self.email, generated_otp)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run);
        self.worker.finished.connect(self.on_email_finished)
        self.worker.finished.connect(self.thread.quit);
        self.worker.finished.connect(self.worker.deleteLater);
        self.thread.finished.connect(self.thread.deleteLater)
        self.otp = generated_otp;
        self.thread.start()

    def on_email_finished(self, success, username, otp):
        main_app_instance = self.window().findChild(QStackedWidget)
        if not main_app_instance: main_app_instance = self.parentWidget()

        if success:
            self.user_in.clear();
            self.email_in.clear()
            parent_page = self.parentWidget()
            parent_page.widget(2).username = username
            parent_page.widget(2).real_otp = otp
            parent_page.widget(3).username = username
            self.navigate.emit(2)
        else:
            self.error_label.setText("Failed to connect to email server.");
            self.navigate.emit(1)


# ====================================================================
# STEP 2: VERIFY OTP
# ====================================================================
class VerifyOTPWidget(QWidget):
    navigate = Signal(int)

    def __init__(self):
        super().__init__();
        self.username = None;
        self.real_otp = None;
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self);
        layout.setContentsMargins(0, 0, 0, 0);
        layout.setSpacing(15)
        title = QLabel("Verify OTP (2/3)");
        title.setAlignment(Qt.AlignCenter);
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #2c3e50;")
        layout.addWidget(title)
        info = QLabel("Please enter the 6-digit code sent to your email.");
        info.setWordWrap(True);
        info.setAlignment(Qt.AlignCenter);
        info.setStyleSheet("font-size: 14px; color: #5c6b73;")
        layout.addWidget(info);
        layout.addSpacing(10)
        self.otp_in = QLineEdit();
        self.otp_in.setPlaceholderText("______");
        self.otp_in.setAlignment(Qt.AlignCenter);
        self.otp_in.setStyleSheet(STYLE_INPUT + "font-size: 24px; letter-spacing: 8px; font-weight: bold;")
        layout.addWidget(self.otp_in)
        self.error_label = QLabel("");
        self.error_label.setStyleSheet(STYLE_ERROR_LABEL);
        self.error_label.setAlignment(Qt.AlignCenter);
        layout.addWidget(self.error_label)
        layout.addStretch()

        self.btn_verify = QPushButton("Verify Code");
        self.btn_verify.setCursor(Qt.PointingHandCursor);
        self.btn_verify.setStyleSheet(STYLE_BTN_PRIMARY)
        apply_hover(self.btn_verify)
        self.btn_verify.clicked.connect(self.handle_verify);
        layout.addWidget(self.btn_verify)

        btn_back = QPushButton("Back");
        btn_back.setCursor(Qt.PointingHandCursor);
        btn_back.setStyleSheet(STYLE_LINK_BTN)
        apply_hover(btn_back)
        btn_back.clicked.connect(lambda: self.navigate.emit(1));
        layout.addWidget(btn_back)

    def handle_verify(self):
        self.error_label.setText("")
        if self.otp_in.text().strip() == self.real_otp:
            self.navigate.emit(3)
        else:
            self.error_label.setText("Invalid OTP entered. Please try again.")


# ====================================================================
# STEP 3: RESET PASSWORD
# ====================================================================
class ResetPasswordWidget(QWidget):
    navigate = Signal(int, bool)

    def __init__(self):
        super().__init__();
        self.username = None;
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self);
        layout.setContentsMargins(0, 0, 0, 0);
        layout.setSpacing(10)
        title = QLabel("Set New Password (3/3)");
        title.setAlignment(Qt.AlignCenter);
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #2c3e50;")
        layout.addWidget(title)
        info = QLabel("Enter your new password below.");
        info.setAlignment(Qt.AlignCenter);
        info.setStyleSheet("font-size: 14px; color: #5c6b73;")
        layout.addWidget(info);
        layout.addSpacing(5)
        self.p1 = QLineEdit();
        self.p1.setPlaceholderText("New Password");
        self.p1.setEchoMode(QLineEdit.Password);
        self.p1.setStyleSheet(STYLE_INPUT);
        layout.addWidget(self.p1)
        self.p2 = QLineEdit();
        self.p2.setPlaceholderText("Confirm Password");
        self.p2.setEchoMode(QLineEdit.Password);
        self.p2.setStyleSheet(STYLE_INPUT);
        layout.addWidget(self.p2)
        self.error_label = QLabel("");
        self.error_label.setStyleSheet(STYLE_ERROR_LABEL);
        self.error_label.setAlignment(Qt.AlignCenter);
        layout.addWidget(self.error_label)
        layout.addStretch()

        self.btn_reset = QPushButton("Change Password");
        self.btn_reset.setCursor(Qt.PointingHandCursor);
        self.btn_reset.setStyleSheet(STYLE_BTN_PRIMARY)
        apply_hover(self.btn_reset)
        self.btn_reset.clicked.connect(self.handle_reset);
        layout.addWidget(self.btn_reset)

        btn_cancel = QPushButton("Cancel & Back to Login");
        btn_cancel.setCursor(Qt.PointingHandCursor);
        btn_cancel.setStyleSheet(STYLE_LINK_BTN)
        apply_hover(btn_cancel)
        btn_cancel.clicked.connect(lambda: self.navigate.emit(0, False));
        layout.addWidget(btn_cancel)

    def handle_reset(self):
        self.error_label.setText("");
        p1_text = self.p1.text();
        p2_text = self.p2.text()
        if not p1_text or not p2_text: self.error_label.setText("Please fill in both password fields."); return
        if p1_text == p2_text:
            if update_staff_password(self.username, p1_text):
                self.p1.clear(); self.p2.clear(); self.navigate.emit(0, True)
            else:
                self.error_label.setText("Database error occurred.")
        else:
            self.error_label.setText("Passwords do not match.")


# ====================================================================
# MAIN LOGIN WIDGET
# ====================================================================
class LoginWidget(QWidget):
    login_signal = Signal()
    forgot_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent);
        self.user_input = QLineEdit();
        self.pass_input = QLineEdit();
        self.message_label = QLabel();
        self.build_ui()

    def build_ui(self):
        inner = QVBoxLayout(self);
        inner.setContentsMargins(0, 0, 0, 0);
        inner.setSpacing(15)
        title = QLabel("Student Performance Predictor");
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #2c3e50;");
        title.setAlignment(Qt.AlignCenter);
        inner.addWidget(title)
        sub = QLabel("Sign in to your account");
        sub.setStyleSheet("font-size: 14px; color: #5c6b73;");
        sub.setAlignment(Qt.AlignCenter);
        inner.addWidget(sub);
        inner.addSpacing(10)
        self.message_label.setAlignment(Qt.AlignCenter);
        self.message_label.setStyleSheet(
            "color: #059669; font-weight: bold; background-color: #d1fae5; border-radius: 4px; padding: 8px;");
        self.message_label.setVisible(False);
        inner.addWidget(self.message_label)

        self.user_input.setPlaceholderText("Username");
        self.user_input.setStyleSheet(STYLE_INPUT);
        inner.addWidget(self.user_input)
        self.pass_input.setPlaceholderText("Password");
        self.pass_input.setEchoMode(QLineEdit.Password);
        self.pass_input.setStyleSheet(STYLE_INPUT);
        inner.addWidget(self.pass_input);
        inner.addSpacing(10)

        login_btn = QPushButton("Login");
        login_btn.setCursor(Qt.PointingHandCursor);
        login_btn.setStyleSheet(STYLE_BTN_PRIMARY)
        apply_hover(login_btn)
        login_btn.clicked.connect(self.login_signal.emit);
        inner.addWidget(login_btn)

        # --- FIX: Use STYLE_LINK_BTN for proper hover effect ---
        forgot_btn = QPushButton("Forgot Password?");
        forgot_btn.setCursor(Qt.PointingHandCursor)
        forgot_btn.setStyleSheet(STYLE_LINK_BTN)
        apply_hover(forgot_btn)
        # --------------------------------------------------------

        forgot_btn.clicked.connect(self.forgot_signal.emit);
        inner.addWidget(forgot_btn);
        inner.addStretch()

    def show_success_message(self):
        self.message_label.setText("Password Reset Successfully!");
        self.message_label.setVisible(True)


# ====================================================================
# MAIN LOGIN PAGE (QWidget Container)
# ====================================================================
class LoginPage(QWidget):
    login_request = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.login_widget = LoginWidget()
        self.id_widget = VerifyIdentityWidget()
        self.otp_widget = VerifyOTPWidget()
        self.reset_widget = ResetPasswordWidget()
        self.waiting_widget = WaitingWidget()
        self.build_ui()

    def build_ui(self):
        layout = QHBoxLayout(self)
        container = QWidget();
        layout.addWidget(container);
        container.setStyleSheet("background-color: #f5f7fa;")
        card = QWidget();
        card.setFixedWidth(450);
        card.setStyleSheet("background-color: white; border-radius: 12px;")
        card_layout = QVBoxLayout(container);
        card_layout.addStretch();
        card_layout.addWidget(card, 0, Qt.AlignCenter);
        card_layout.addStretch()
        self.stack = QStackedWidget(card);
        inner = QVBoxLayout(card);
        inner.setContentsMargins(32, 32, 32, 32);
        inner.addWidget(self.stack)

        self.login_widget.login_signal.connect(self.handle_login_click)
        self.login_widget.forgot_signal.connect(lambda: self.stack.setCurrentIndex(1))

        self.stack.addWidget(self.login_widget)
        self.stack.addWidget(self.id_widget)
        self.stack.addWidget(self.otp_widget)
        self.stack.addWidget(self.reset_widget)
        self.stack.addWidget(self.waiting_widget)

        self.id_widget.navigate.connect(self.stack.setCurrentIndex)
        self.otp_widget.navigate.connect(self.stack.setCurrentIndex)
        self.reset_widget.navigate.connect(self.handle_reset_navigation)
        self.stack.setCurrentIndex(0)

    def handle_reset_navigation(self, index, success):
        if success:
            self.login_widget.show_success_message()
        else:
            self.login_widget.message_label.setVisible(False)
        self.stack.setCurrentIndex(index)

    def handle_login_click(self):
        user = self.login_widget.user_input.text()
        pwd = self.login_widget.pass_input.text()
        self.login_request.emit(user, pwd)
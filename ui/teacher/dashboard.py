from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QStackedWidget, QFrame,
                               QGraphicsDropShadowEffect, QScrollArea, QComboBox, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPixmap
import sys, os

from .grades_page import GradePage
from .attendance_page import ClassAttendancePage, LabAttendancePage
from .assignment_page import ClassAssignmentPage, LabAssignmentPage
from .analysis_page import ParetoChartPage, TeacherFormGroupsPage

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.queries_teacher import get_subject_lab_status


class TeacherDashboardUI(QWidget):
    logout_signal = Signal()

    def __init__(self, user_info, teacher_conn):
        super().__init__()
        self.user_info = user_info
        self.conn = teacher_conn
        self.menu_buttons = {}

        # Main Layout (Directly on self)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. SIDEBAR
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(260)
        self.sidebar.setStyleSheet("background-color: #1e293b; color: white;")

        self.side_lay = QVBoxLayout(self.sidebar)
        self.side_lay.setContentsMargins(0, 0, 0, 0)
        self.side_lay.setSpacing(0)

        top_section = QWidget()
        top_lay = QVBoxLayout(top_section)
        top_lay.setContentsMargins(20, 30, 20, 10);
        top_lay.setSpacing(15)
        app_title = QLabel("🎓 TEACHER\nPORTAL");
        app_title.setStyleSheet("font-size: 22px; font-weight: 900; color: #38bdf8;")
        top_lay.addWidget(app_title)

        sub_card = QFrame()
        sub_card.setStyleSheet("background-color: #334155; border-radius: 8px; padding: 12px;")
        sub_lay = QVBoxLayout(sub_card);
        sub_lay.setContentsMargins(0, 0, 0, 0)
        lbl_sub_title = QLabel("CURRENT SUBJECT");
        lbl_sub_title.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        lbl_sub_name = QLabel(user_info.get('subject_name', 'Unknown').upper());
        lbl_sub_name.setStyleSheet("color: #e2e8f0; font-size: 13px; font-weight: bold; margin-top: 4px;");
        lbl_sub_name.setWordWrap(True)
        sub_lay.addWidget(lbl_sub_title);
        sub_lay.addWidget(lbl_sub_name);
        top_lay.addWidget(sub_card)
        top_lay.addWidget(QLabel("MAIN MENU"));
        self.side_lay.addWidget(top_section)

        self.menu_scroll = QScrollArea()
        self.menu_scroll.setWidgetResizable(True)
        self.menu_scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; } QScrollBar:vertical { width: 4px; background: #334155; }")
        self.menu_widget = QWidget();
        self.menu_widget.setStyleSheet("background: transparent;")
        self.menu_container = QVBoxLayout(self.menu_widget);
        self.menu_container.setContentsMargins(15, 0, 15, 20);
        self.menu_container.setSpacing(5);
        self.menu_container.addStretch()
        self.menu_scroll.setWidget(self.menu_widget)
        self.side_lay.addWidget(self.menu_scroll)

        bottom_section = QWidget()
        bottom_lay = QVBoxLayout(bottom_section);
        bottom_lay.setContentsMargins(20, 10, 20, 20)
        btn_logout = QPushButton("🚪  Logout");
        btn_logout.setCursor(Qt.PointingHandCursor)
        btn_logout.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.1); color: #f87171; 
                padding: 12px; border-radius: 8px; font-weight: bold; border: none; text-align: left; outline: none;
            }
            QPushButton:hover { background-color: #ef4444; color: white; }
        """)
        btn_logout.clicked.connect(self.logout_signal.emit)
        bottom_lay.addWidget(btn_logout);
        self.side_lay.addWidget(bottom_section)
        layout.addWidget(self.sidebar)

        # 2. TOGGLE STRIP
        toggle_strip = QWidget();
        toggle_strip.setFixedWidth(20);
        toggle_strip.setStyleSheet("background: transparent;")
        toggle_layout = QVBoxLayout(toggle_strip);
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.addSpacerItem(QSpacerItem(20, 150, QSizePolicy.Minimum, QSizePolicy.Fixed))
        self.btn_toggle = QPushButton("◀");
        self.btn_toggle.setFixedSize(20, 50);
        self.btn_toggle.setCursor(Qt.PointingHandCursor);
        self.btn_toggle.clicked.connect(self.toggle_sidebar)
        self.btn_toggle.setStyleSheet("""
            QPushButton {
                background-color: white; color: #64748b; border: 1px solid #cbd5e1;
                border-left: none; border-top-right-radius: 8px; border-bottom-right-radius: 8px; font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #f1f5f9; color: #334155; }
        """)
        shadow = QGraphicsDropShadowEffect();
        shadow.setBlurRadius(10);
        shadow.setColor(QColor(0, 0, 0, 30));
        shadow.setOffset(2, 2);
        self.btn_toggle.setGraphicsEffect(shadow)
        toggle_layout.addWidget(self.btn_toggle);
        toggle_layout.addStretch()
        layout.addWidget(toggle_strip)

        # 3. CONTENT AREA
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(10, 30, 30, 30);
        content_layout.setSpacing(20)

        top_bar = QHBoxLayout()
        welcome_text = f"Welcome, {user_info.get('teacher_name', 'Teacher')}"
        lbl_welcome = QLabel(welcome_text);
        lbl_welcome.setStyleSheet("font-size: 24px; font-weight: 800; color: #1e293b;")
        top_bar.addWidget(lbl_welcome);
        top_bar.addStretch();
        content_layout.addLayout(top_bar)

        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)
        layout.addWidget(content_area)

        self.create_menu()
        self.switch_page("home")

    def toggle_sidebar(self):
        width = self.sidebar.width()
        target_width = 0 if width == 260 else 260
        self.btn_toggle.setText("▶") if width > 0 else self.btn_toggle.setText("◀")
        self.anim = QPropertyAnimation(self.sidebar, b"minimumWidth");
        self.anim.setDuration(300);
        self.anim.setStartValue(width);
        self.anim.setEndValue(target_width);
        self.anim.setEasingCurve(QEasingCurve.InOutQuart);
        self.anim.start()
        self.anim_max = QPropertyAnimation(self.sidebar, b"maximumWidth");
        self.anim_max.setDuration(300);
        self.anim_max.setStartValue(width);
        self.anim_max.setEndValue(target_width);
        self.anim_max.setEasingCurve(QEasingCurve.InOutQuart);
        self.anim_max.start()

    def create_menu(self):
        self.pages = {}
        sid = self.user_info['subject_id']
        students = self.user_info['students']
        has_lab = get_subject_lab_status(sid)

        self.pages["home"] = self.create_home_page(has_lab)
        self.pages["grade"] = GradePage(students, sid, self.conn)
        self.pages["att_class"] = ClassAttendancePage(students, sid, self.conn)
        self.pages["ass_class"] = ClassAssignmentPage(students, sid, self.conn)
        self.pages["pareto"] = ParetoChartPage(sid, self.conn)
        self.pages["groups"] = TeacherFormGroupsPage(sid, self.conn)

        if self.menu_container.count() > 0: self.menu_container.takeAt(self.menu_container.count() - 1)
        self.add_menu_btn("🏠  Home", "home")
        self.add_menu_btn("📝  Enter Marks", "grade")
        self.add_menu_btn("📅  Daily Attendance", "att_class")
        self.add_menu_btn("📚  Assignments", "ass_class")

        if has_lab:
            self.pages["att_lab"] = LabAttendancePage(students, sid, self.conn)
            self.add_menu_btn("🧪  Lab Sessions", "att_lab")  # Was "Lab Attendance"
            self.pages["ass_lab"] = LabAssignmentPage(students, sid, self.conn)
            self.add_menu_btn("🔬  Lab Reports", "ass_lab")  # Was "Lab Assignments"

        self.menu_container.addSpacing(15)
        self.menu_container.addWidget(QLabel("INSIGHTS",
                                             styleSheet="color: #94a3b8; padding-left: 5px; font-size: 11px; font-weight: bold; letter-spacing: 1px;"))

        self.add_menu_btn("📊  Class Performance", "pareto")  # Was "Pareto Analysis"
        self.add_menu_btn("👥  Create Study Groups", "groups")  # Was "Form Groups"
        self.menu_container.addStretch()

        for name, widget in self.pages.items(): self.stack.addWidget(widget)

    def create_home_page(self, has_lab):
        page = QWidget()
        main_layout = QVBoxLayout(page);
        main_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea();
        scroll.setWidgetResizable(True);
        scroll.setStyleSheet("border: none; background: transparent;")
        container = QWidget();
        layout = QVBoxLayout(container);
        layout.setContentsMargins(0, 0, 20, 20);
        layout.setSpacing(30)

        hero = QFrame();
        hero.setFixedHeight(150)
        hero.setStyleSheet(
            "QFrame { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #2563eb); border-radius: 15px; }")
        hero_shadow = QGraphicsDropShadowEffect();
        hero_shadow.setBlurRadius(20);
        hero_shadow.setColor(QColor(59, 130, 246, 60));
        hero_shadow.setOffset(0, 8);
        hero.setGraphicsEffect(hero_shadow)
        h_layout = QVBoxLayout(hero);
        h_layout.setContentsMargins(30, 0, 30, 0);
        h_layout.setAlignment(Qt.AlignVCenter)
        h_layout.addWidget(QLabel("Subject Dashboard",
                                  styleSheet="font-size: 26px; font-weight: 800; color: white; background: transparent;"))
        h_layout.addWidget(QLabel("Manage grades, attendance, and view student insights.",
                                  styleSheet="font-size: 15px; color: #dbeafe; background: transparent; margin-top: 5px;"))
        layout.addWidget(hero)

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        logo_path = os.path.join(base_dir, "logo", "spp logo.png")
        layout.addWidget(self.create_logo_panel(logo_path))
        layout.addStretch()
        scroll.setWidget(container);
        main_layout.addWidget(scroll)
        return page

    def create_logo_panel(self, logo_path):
        logo_frame = QFrame();
        logo_frame.setMinimumHeight(250)
        logo_frame.setStyleSheet(
            "QFrame { background-color: #ffffff; border: 1px dashed #cbd5e1; border-radius: 15px; }")
        logo_layout = QVBoxLayout(logo_frame);
        logo_layout.setAlignment(Qt.AlignCenter)
        logo_label = QLabel();
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaledToHeight(240, Qt.SmoothTransformation); logo_label.setPixmap(pixmap)
        else:
            logo_label.setText(f"Error: Logo file not found"); logo_label.setStyleSheet("color: #ef4444;")
        logo_label.setStyleSheet("background: transparent; border: none;");
        logo_layout.addWidget(logo_label)
        return logo_frame

    def add_menu_btn(self, text, pid):
        btn = QPushButton(text);
        self.menu_buttons[pid] = btn;
        btn.setCursor(Qt.PointingHandCursor);
        btn.clicked.connect(lambda: self.switch_page(pid));
        self.menu_container.addWidget(btn)

    def update_menu_style(self, active_pid):
        base_style = "QPushButton { text-align: left; padding: 12px 15px; border: none; border-radius: 8px; color: #cbd5e1; font-size: 13px; font-weight: 600; outline: none; background: transparent; } QPushButton:hover { background-color: #334155; color: white; }"
        active_style = "QPushButton { text-align: left; padding: 12px 15px; border: none; border-radius: 8px; color: white; font-size: 13px; font-weight: 700; outline: none; background-color: #334155; border-left: 4px solid #38bdf8; }"
        for pid, btn in self.menu_buttons.items():
            btn.setStyleSheet(active_style if pid == active_pid else base_style)

    def switch_page(self, pid):
        if pid in self.pages:
            self.stack.setCurrentWidget(self.pages[pid])
            self.update_menu_style(pid)
            if hasattr(self.pages[pid], 'load_data'): self.pages[pid].load_data()
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QStackedWidget, QComboBox,
                               QFrame, QGraphicsDropShadowEffect, QScrollArea, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPixmap
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.queries_hod import get_all_courses
from .enroll_page import EnrollStudentPage
from .delist_page import DelistStudentPage
from .prediction_page import PredictStudentPerformancePage, FormGroupsPage
from .whatif_page import WhatIfAnalysisPage
from .reports_page import CourseParetoChartPage


class HODDashboardUI(QWidget):
    logout_signal = Signal()  # Signal to tell MainWindow to logout

    def __init__(self, user_info, db_conn):
        super().__init__()
        self.user_info = user_info
        self.conn = db_conn
        self.menu_buttons = {}

        # Main Layout (Directly on self, no CentralWidget)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. SIDEBAR
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(260)
        self.sidebar.setStyleSheet("background-color: #1a202c; color: white;")
        side_lay = QVBoxLayout(self.sidebar)
        side_lay.setContentsMargins(0, 0, 0, 0)
        side_lay.setSpacing(0)

        top_section = QWidget()
        top_lay = QVBoxLayout(top_section)
        top_lay.setContentsMargins(20, 30, 20, 20)
        app_title = QLabel("🎓 HOD\nPORTAL")
        app_title.setStyleSheet("font-size: 22px; font-weight: 900; color: #38bdf8;")
        top_lay.addWidget(app_title)
        side_lay.addWidget(top_section)

        self.menu_scroll = QScrollArea()
        self.menu_scroll.setWidgetResizable(True)
        self.menu_scroll.setStyleSheet("border: none; background: transparent;")
        self.menu_widget = QWidget()
        self.menu_widget.setStyleSheet("background: transparent;")
        self.menu_container = QVBoxLayout(self.menu_widget)
        self.menu_container.setContentsMargins(15, 0, 15, 20)
        self.menu_container.setSpacing(5)

        self.create_menu_btn("🏠  Home", "home")
        self.create_menu_btn("✨  Add New Student", "enroll")  # Was "Enroll Student"
        self.create_menu_btn("🗑️  Remove Student", "delist")  # Was "Delist Student"

        self.menu_container.addSpacing(10)
        self.menu_container.addWidget(QLabel("   INSIGHTS",
                                             styleSheet="color: #718096; font-size: 11px; font-weight: bold; letter-spacing: 1px; padding-left: 5px;"))

        self.create_menu_btn("📊  Course Overview", "reports")  # Was "Reports (Pareto)"
        self.create_menu_btn("🔮  Predict Results", "predict")  # Was "Prediction"
        self.create_menu_btn("🧪  Score Simulator", "whatif")  # Was "What-If Analysis"
        self.create_menu_btn("👥  Auto-Group Students", "groups")

        self.menu_container.addStretch()
        self.menu_scroll.setWidget(self.menu_widget)
        side_lay.addWidget(self.menu_scroll)

        bottom_section = QWidget()
        bottom_lay = QVBoxLayout(bottom_section)
        bottom_lay.setContentsMargins(20, 10, 20, 20)

        btn_logout = QPushButton("🚪  Logout")
        btn_logout.setCursor(Qt.PointingHandCursor)
        btn_logout.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.1); color: #f87171; 
                padding: 12px; border-radius: 8px; font-weight: bold; border: none; text-align: left; outline: none;
            }
            QPushButton:hover { background-color: #ef4444; color: white; }
        """)
        btn_logout.clicked.connect(self.logout_signal.emit)

        bottom_lay.addWidget(btn_logout)
        side_lay.addWidget(bottom_section)

        layout.addWidget(self.sidebar)

        # 2. TOGGLE STRIP
        toggle_strip = QWidget()
        toggle_strip.setFixedWidth(20)
        toggle_strip.setStyleSheet("background: transparent;")
        toggle_layout = QVBoxLayout(toggle_strip)
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.addSpacerItem(QSpacerItem(20, 150, QSizePolicy.Minimum, QSizePolicy.Fixed))

        self.btn_toggle = QPushButton("◀")
        self.btn_toggle.setFixedSize(20, 50)
        self.btn_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_toggle.clicked.connect(self.toggle_sidebar)
        self.btn_toggle.setStyleSheet("""
            QPushButton {
                background-color: white; color: #64748b; border: 1px solid #cbd5e1;
                border-left: none; border-top-right-radius: 8px; border-bottom-right-radius: 8px;
                font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #f1f5f9; color: #334155; }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10);
        shadow.setColor(QColor(0, 0, 0, 30));
        shadow.setOffset(2, 2)
        self.btn_toggle.setGraphicsEffect(shadow)
        toggle_layout.addWidget(self.btn_toggle)
        toggle_layout.addStretch()
        layout.addWidget(toggle_strip)

        # 3. CONTENT AREA
        content = QWidget()
        self.content_container = content  # Reference for switching
        cont_lay = QVBoxLayout(content)
        cont_lay.setContentsMargins(10, 30, 30, 30)
        cont_lay.setSpacing(20)

        top_bar = QHBoxLayout()
        welcome_lbl = QLabel(f"Welcome, {user_info.get('teacher_name', 'Admin')}")
        welcome_lbl.setStyleSheet("font-size: 24px; font-weight: 800; color: #1e293b;")
        top_bar.addWidget(welcome_lbl)
        top_bar.addStretch()

        self.course_selector_widget = QWidget()
        sel_lay = QHBoxLayout(self.course_selector_widget)
        sel_lay.setContentsMargins(0, 0, 0, 0)
        sel_lbl = QLabel("Current Session:")
        sel_lbl.setStyleSheet("font-weight: bold; color: #64748b; font-size: 14px;")
        self.course_select = QComboBox()
        self.course_select.setMinimumWidth(200)
        self.course_select.setCursor(Qt.PointingHandCursor)
        self.course_select.setStyleSheet(
            "QComboBox { border: 1px solid #cbd5e1; border-radius: 8px; padding: 8px 15px; background: white; color: #334155; font-weight: 600; } QComboBox::drop-down { border: 0px; }")
        self.course_select.currentIndexChanged.connect(self.on_course_changed)

        sel_lay.addWidget(sel_lbl)
        sel_lay.addWidget(self.course_select)
        top_bar.addWidget(self.course_selector_widget)
        cont_lay.addLayout(top_bar)

        self.stack = QStackedWidget()
        cont_lay.addWidget(self.stack)
        layout.addWidget(content)

        self.pages = {
            "home": self.create_home_page(),
            "enroll": EnrollStudentPage(),
            "delist": DelistStudentPage(),
            "reports": CourseParetoChartPage("", self.conn),
            "predict": PredictStudentPerformancePage(),
            "whatif": WhatIfAnalysisPage(),
            "groups": FormGroupsPage()
        }

        for pid, widget in self.pages.items():
            self.stack.addWidget(widget)

        self.load_courses()
        self.switch_page("home")

    def toggle_sidebar(self):
        width = self.sidebar.width()
        target_width = 0 if width == 260 else 260
        self.btn_toggle.setText("▶") if width > 0 else self.btn_toggle.setText("◀")

        self.anim = QPropertyAnimation(self.sidebar, b"minimumWidth")
        self.anim.setDuration(300);
        self.anim.setStartValue(width);
        self.anim.setEndValue(target_width)
        self.anim.setEasingCurve(QEasingCurve.InOutQuart);
        self.anim.start()

        self.anim_max = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self.anim_max.setDuration(300);
        self.anim_max.setStartValue(width);
        self.anim_max.setEndValue(target_width)
        self.anim_max.setEasingCurve(QEasingCurve.InOutQuart);
        self.anim_max.start()

    def create_home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page);
        layout.setContentsMargins(0, 0, 0, 0);
        layout.setSpacing(30)
        hero = QFrame();
        hero.setFixedHeight(160)
        hero.setStyleSheet(
            "QFrame { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #2563eb); border-radius: 15px; }")
        hero_shadow = QGraphicsDropShadowEffect();
        hero_shadow.setBlurRadius(20);
        hero_shadow.setColor(QColor(59, 130, 246, 60));
        hero_shadow.setOffset(0, 8);
        hero.setGraphicsEffect(hero_shadow)
        h_lay = QVBoxLayout(hero);
        h_lay.setAlignment(Qt.AlignVCenter);
        h_lay.setContentsMargins(40, 0, 40, 0)
        h1 = QLabel("Administrative Dashboard");
        h1.setStyleSheet("font-size: 28px; font-weight: 800; color: white; background: transparent;")
        h2 = QLabel("Manage student enrollments, courses, and analyze prediction models.");
        h2.setStyleSheet("font-size: 16px; color: #dbeafe; background: transparent; margin-top: 5px;")
        h_lay.addWidget(h1);
        h_lay.addWidget(h2);
        layout.addWidget(hero)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        logo_path = os.path.join(base_dir, "logo", "spp logo.png")
        layout.addWidget(self.create_logo_panel(logo_path));
        layout.addStretch()
        return page

    def create_logo_panel(self, logo_path):
        logo_frame = QFrame();
        logo_frame.setMinimumHeight(250)
        logo_frame.setStyleSheet(
            "QFrame { background-color: #ffffff; border: 2px dashed #e2e8f0; border-radius: 15px; }")
        logo_lay = QVBoxLayout(logo_frame);
        logo_lay.setAlignment(Qt.AlignCenter)
        logo_lbl = QLabel();
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaledToHeight(240, Qt.SmoothTransformation); logo_lbl.setPixmap(pixmap)
        else:
            logo_lbl.setText(f"Logo not found"); logo_lbl.setStyleSheet("color: #ef4444; font-weight: bold;")
        logo_lbl.setStyleSheet("background: transparent; border: none;");
        logo_lay.addWidget(logo_lbl)
        return logo_frame

    def create_menu_btn(self, text, pid, layout=None):
        target = layout if layout else self.menu_container
        btn = QPushButton(text)
        self.menu_buttons[pid] = btn
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self.switch_page(pid))
        target.addWidget(btn)

    def update_menu_style(self, active_pid):
        base_style = "QPushButton { text-align: left; padding: 12px 20px; border: none; background: transparent; color: #cbd5e1; font-weight: 600; } QPushButton:hover { background-color: #2d3748; color: white; }"
        active_style = "QPushButton { text-align: left; padding: 12px 20px; border: none; background-color: #2d3748; color: white; border-left: 4px solid #38bdf8; font-weight: 700; }"
        for pid, btn in self.menu_buttons.items():
            btn.setStyleSheet(active_style if pid == active_pid else base_style)

    def load_courses(self):
        courses = get_all_courses()
        for cid, cname in courses:
            self.course_select.addItem(cname, cid)

    def switch_page(self, pid):
        if pid in self.pages:
            self.stack.setCurrentWidget(self.pages[pid])
            self.update_menu_style(pid)
            if pid == "home":
                self.course_selector_widget.hide()
            else:
                self.course_selector_widget.show()
            self.on_course_changed(self.course_select.currentIndex())

    def on_course_changed(self, idx):
        cid = self.course_select.currentData()
        if not cid: return
        curr = self.stack.currentWidget()
        if hasattr(curr, 'load_data'): curr.load_data(cid)
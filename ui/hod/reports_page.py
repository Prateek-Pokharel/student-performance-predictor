from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                               QFrame, QScrollArea)
from PySide6.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

# IMPORTANT: Ensure these imports exist.
# We use fetch_exam_details_for_subject to calculate total course marks dynamically.
from database.queries_hod import fetch_aggregate_grades_for_pareto
from database.queries_teacher import fetch_exam_details_for_subject


class CourseParetoChartPage(QWidget):
    """
    Displays Course-wide Pareto Chart.
    Features:
    - Scrollable (No squashed bars)
    - Percentage-based (Standardized 0-100%)
    """

    def __init__(self, course_id: str, conn):
        super().__init__()
        self.course_id = course_id
        self.conn = conn
        self.grade_types = ["Unit Test", "Mid Term", "End Term"]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # --- Top Controls ---
        ctrl = QFrame()
        ctrl.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #e2e8f0;")
        cl = QHBoxLayout(ctrl)

        lbl = QLabel("Select Exam Term:")
        lbl.setStyleSheet("font-weight: bold; color: #1e293b;")

        self.combo = QComboBox()
        self.combo.addItems(["-- Select --"] + self.grade_types)
        self.combo.setFixedWidth(200)
        self.combo.setStyleSheet("""
            QComboBox { padding: 5px; border: 1px solid #cbd5e1; border-radius: 4px; background: #f8fafc; }
            QComboBox::drop-down { border: none; }
        """)
        self.combo.currentTextChanged.connect(self.plot)

        cl.addWidget(lbl)
        cl.addWidget(self.combo)
        cl.addStretch()
        layout.addWidget(ctrl)

        # --- Scrollable Chart Container ---
        chart_card = QFrame()
        chart_card.setStyleSheet(
            "background-color: white; border-radius: 10px; border: 1px solid #e2e8f0; padding-bottom: 15px;")

        # Use a layout for the card
        card_layout = QVBoxLayout(chart_card)
        card_layout.setContentsMargins(5, 5, 5, 15)

        # 1. Create Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")

        # 2. Create Figure & Canvas
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.fig.patch.set_facecolor('white')
        self.canvas = FigureCanvas(self.fig)

        # 3. Add Canvas to Scroll Area
        self.scroll.setWidget(self.canvas)
        card_layout.addWidget(self.scroll)

        layout.addWidget(chart_card)

        self.plot("-- Select --")

    def _calculate_course_total(self, exam_type):
        """
        Calculates the total possible marks for the entire course
        by summing the full marks of all subjects in this course.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT Subject_ID FROM Subject WHERE Course_ID = ?", (self.course_id,))
            subjects = cursor.fetchall()

            total_full_marks = 0
            for (sub_id,) in subjects:
                config = fetch_exam_details_for_subject(self.conn, sub_id)
                if config:
                    if exam_type == "Unit Test":
                        total_full_marks += int(config.get('Unit_Full', 20))
                    elif exam_type == "Mid Term":
                        total_full_marks += int(config.get('Mid_Full', 50))
                    elif exam_type == "End Term":
                        total_full_marks += int(config.get('End_Full', 100))

            return total_full_marks if total_full_marks > 0 else 100  # Fallback
        except Exception as e:
            print(f"Error calculating course total: {e}")
            return 100

    def plot(self, text):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor('white')

        # Reset canvas width
        self.canvas.setMinimumWidth(0)

        if text == "-- Select --":
            self._plot_initial_message(ax)
            self.canvas.draw()
            return

        # Fetch Aggregate Data: [(Student_Name, Total_Obtained_Marks), ...]
        data = fetch_aggregate_grades_for_pareto(self.conn, self.course_id, text)

        if not data:
            self._plot_no_data(ax, text)
            self.canvas.draw()
            return

        # --- 1. Dynamic Sizing ---
        num_students = len(data)
        bar_width_pixels = 60
        total_width = max(800, num_students * bar_width_pixels)
        self.canvas.setMinimumWidth(total_width)
        self.fig.set_figwidth(total_width / 100)

        # --- 2. Calculate Percentages ---
        course_full_marks = self._calculate_course_total(text)

        # Process data to percentages
        # data[i] = (Student_Name, Raw_Total_Marks)
        processed_data = []
        for row in data:
            name = str(row[0])
            raw_total = row[1]
            percentage = (raw_total / course_full_marks) * 100
            processed_data.append((name, percentage))

        # Sort by Percentage (High to Low)
        processed_data.sort(key=lambda x: x[1], reverse=True)

        student_names = [x[0] for x in processed_data]
        percentages = [x[1] for x in processed_data]
        x_pos = range(len(student_names))

        # --- 3. Draw Bars ---
        bars = ax.bar(x_pos, percentages, color='#8b5cf6', width=0.6, zorder=3)

        # Axis Settings
        ax.set_xticks(x_pos)
        ax.set_xticklabels(student_names, rotation=45, ha='right', rotation_mode='anchor', fontsize=9)
        ax.set_ylim(0, 105)  # Fixed 0-100% Scale

        # Pareto Line (Cumulative %)
        total_pct_sum = sum(percentages)
        if total_pct_sum > 0:
            cumulative = []
            curr = 0
            for p in percentages:
                curr += p
                cumulative.append((curr / total_pct_sum) * 100)

            ax2 = ax.twinx()
            ax2.plot(x_pos, cumulative, color='#ef4444', marker='o', linestyle='-', linewidth=2, markersize=4)
            ax2.set_ylabel("Cumulative %", color='#ef4444', fontsize=10)
            ax2.tick_params(axis='y', colors='#ef4444')
            ax2.set_ylim(0, 105)
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_color('#ef4444')

        # Styles
        self._apply_styles(ax, text)

        # Add Value Labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height + 1,
                    f'{int(height)}%', ha='center', va='bottom', fontsize=9, color='#334155')

        # Adjust margins for scrolling
        self.fig.subplots_adjust(left=0.08, bottom=0.35, right=0.92, top=0.88)

        self.canvas.draw()

    def _plot_initial_message(self, ax):
        ax.text(0.5, 0.5, "Select an exam type to view course-wide aggregated performance.", ha='center', va='center',
                fontsize=12, color='gray')
        ax.axis('off')

    def _plot_no_data(self, ax, text):
        ax.text(0.5, 0.5, f"No aggregated data found for {text} in this course.", ha='center',
                va='center', fontsize=12, color='red')
        ax.axis('off')

    def _apply_styles(self, ax, text):
        ax.grid(axis='y', linestyle='--', alpha=0.7, zorder=0)
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_color('#cbd5e1')
        ax.spines['bottom'].set_color('#cbd5e1')

        ax.set_title(f"Aggregated Course Performance (%) - {text}", fontsize=14, fontweight='bold', pad=20,
                     color='#1e293b')
        ax.set_ylabel("Percentage (%)", fontsize=10, color='#475569')
        ax.set_xlabel("Student Names (Sorted by Rank)", fontsize=10, color='#64748b', labelpad=10)

        ax.tick_params(axis='y', colors='#475569')
        ax.tick_params(axis='x', colors='#64748b')

    def load_data(self, course_id: str):
        self.course_id = course_id
        selected_text = self.combo.currentText()
        if selected_text and selected_text != "-- Select --":
            self.plot(selected_text)
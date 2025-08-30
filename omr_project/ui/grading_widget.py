import json
from datetime import datetime
from pathlib import Path
from utils.files import build_timestamped_filename

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QPushButton,
    QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem, QFileDialog, QSizePolicy
)

from core.pdf.report_generator import generate_class_report

from core.grading.grading_core import EXCEL_AVAILABLE
from utils.error_handling import ErrorHandler
from core.grading.grading_core import GradeResult, GradingSystem
from ui.table_manager import TableManager
from i18n import translator, get_option_letter
from config.logger_config import get_logger, GRADING_LOGGER_NAME
from config.app_config import AppConfig

class GradingWidget(QWidget):
    """Dedicated Grading & Reports tab with batch processing"""

    def __init__(self, parent):
        super().__init__()
        self.parent_app = parent
        self.log = get_logger(GRADING_LOGGER_NAME)
        # Grading system state
        self.grading_system = GradingSystem()
        self.current_grade_result = None
        self.scan_results = {}
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Main content layout
        main_layout = QHBoxLayout()

        # Left panel - Controls
        left_panel = self._create_control_panel()
        left_panel.setMaximumWidth(350)
        main_layout.addWidget(left_panel)

        # Right panel - Results display
        right_panel = self._create_results_panel()
        main_layout.addWidget(right_panel)

        layout.addLayout(main_layout)

    def _create_control_panel(self) -> QWidget:
        """Create left control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Title
        self.title_label = QLabel(translator.t('grading_title'))
        self.title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(self.title_label)

        # Load scan results
        self.load_group = QGroupBox(translator.t('load_scan_results'))
        load_layout = QVBoxLayout(self.load_group)

        self.load_results_btn = QPushButton(translator.t('load_results_btn'))
        self.load_results_btn.clicked.connect(self.load_scan_results)
        load_layout.addWidget(self.load_results_btn)

        self.scan_info = QLabel(translator.t('select_omr_results'))
        self.scan_info.setWordWrap(True)
        load_layout.addWidget(self.scan_info)

        layout.addWidget(self.load_group)

        # Student information
        self.student_group = QGroupBox(translator.t('student_info'))
        student_layout = QVBoxLayout(self.student_group)

        self.student_name_label = QLabel(translator.t('student_name_field'))
        student_layout.addWidget(self.student_name_label)
        self.student_name_edit = QLineEdit()
        self.student_name_edit.setPlaceholderText(translator.t('student_name_placeholder'))
        student_layout.addWidget(self.student_name_edit)

        self.student_id_label = QLabel(translator.t('student_id_field'))
        student_layout.addWidget(self.student_id_label)
        self.student_id_edit = QLineEdit()
        self.student_id_edit.setPlaceholderText(translator.t('student_id_placeholder'))
        student_layout.addWidget(self.student_id_edit)

        # Grade calculation
        self.calculate_grade_btn = QPushButton(translator.t('calculate_grade'))
        self.calculate_grade_btn.clicked.connect(self.calculate_grade)
        self.calculate_grade_btn.setEnabled(False)
        student_layout.addWidget(self.calculate_grade_btn)

        layout.addWidget(self.student_group)

        # Batch processing
        self.batch_group = QGroupBox(translator.t('batch_processing'))
        batch_layout = QVBoxLayout(self.batch_group)

        batch_btn_layout = QVBoxLayout()
        self.add_student_btn = QPushButton(translator.t('add_student'))
        self.add_student_btn.clicked.connect(self.add_current_student)
        self.add_student_btn.setEnabled(False)
        self.add_student_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        batch_btn_layout.addWidget(self.add_student_btn)

        self.remove_student_btn = QPushButton(translator.t('remove_student'))
        self.remove_student_btn.clicked.connect(self.remove_selected_student)
        self.remove_student_btn.setEnabled(False)
        self.remove_student_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        batch_btn_layout.addWidget(self.remove_student_btn)

        batch_layout.addLayout(batch_btn_layout)
        layout.addWidget(self.batch_group)

        # Class statistics
        self.stats_group = QGroupBox(translator.t('class_statistics'))
        stats_layout = QVBoxLayout(self.stats_group)

        self.stats_display = QTextEdit()
        self.stats_display.setMaximumHeight(150)
        self.stats_display.setReadOnly(True)
        stats_layout.addWidget(self.stats_display)

        layout.addWidget(self.stats_group)

        # Export controls
        self.export_group = QGroupBox(translator.t('export_results'))
        export_layout = QVBoxLayout(self.export_group)

        export_btn_layout = QHBoxLayout()

        self.export_csv_btn = QPushButton(translator.t('export_csv'))
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_csv_btn.setEnabled(False)
        export_btn_layout.addWidget(self.export_csv_btn)

        if EXCEL_AVAILABLE:
            self.export_excel_btn = QPushButton(translator.t('export_excel'))
            self.export_excel_btn.clicked.connect(self.export_excel)
            self.export_excel_btn.setEnabled(False)
            export_btn_layout.addWidget(self.export_excel_btn)

        export_layout.addLayout(export_btn_layout)

        self.export_class_btn = QPushButton(translator.t('export_class_report'))
        self.export_class_btn.clicked.connect(self.export_class_report)
        self.export_class_btn.setEnabled(False)
        export_layout.addWidget(self.export_class_btn)

        self.clear_results_btn = QPushButton(translator.t('clear_all_results'))
        self.clear_results_btn.clicked.connect(self.clear_all_results)
        self.clear_results_btn.setEnabled(False)
        export_layout.addWidget(self.clear_results_btn)

        layout.addWidget(self.export_group)

        layout.addStretch()
        return panel

    def _create_results_panel(self) -> QWidget:
        """Create right results panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Current student grade display
        self.current_group = QGroupBox(translator.t('grade_sheet'))
        current_layout = QVBoxLayout(self.current_group)

        self.grade_display = QTextEdit()
        # Let the grade display expand to fill available vertical space
        self.grade_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.grade_display.setReadOnly(True)
        current_layout.addWidget(self.grade_display)

        # Allow the whole group to expand within the right panel
        self.current_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.current_group, 1)

        # Students list
        self.students_group = QGroupBox(translator.t('students_processed_title'))
        students_layout = QVBoxLayout(self.students_group)

        self.students_table = QTableWidget()

        # Use centralized table configuration
        TableManager.configure_students_table(self.students_table)
        self._update_table_headers()

        students_layout.addWidget(self.students_table)

        # Give the students list more weight but still allow grade box to stretch
        self.students_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.students_group, 2)

        return panel

    def _update_table_headers(self) -> None:
        """Update table headers with current translations"""
        headers = TableManager.get_translated_headers()
        self.students_table.setHorizontalHeaderLabels(headers)

    def load_scan_results(self) -> None:
        """Load scan results from Scanner tab or file"""
        # First try to get current scan results from Scanner tab
        scanner_tab = self.parent_app.scanner_tab
        if scanner_tab.answers and scanner_tab.omr_data:
            self.scan_results = {
                'answers': scanner_tab.answers.copy(),
                'omr_data': scanner_tab.omr_data.copy()
            }
            self.scan_info.setText(translator.t('loaded_from_scanner_tab'))
            self.calculate_grade_btn.setEnabled(True)
            return

        # Otherwise, load from file (for future batch processing)
        file_path, _ = QFileDialog.getOpenFileName(
            self, translator.t('load_scan_results'), "",
            translator.t('file_filter_omr_json')
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.scan_results = json.load(f)

                filename = Path(file_path).name
                self.scan_info.setText(f"✅ {filename}")
                self.calculate_grade_btn.setEnabled(True)
                self.log.info("Loaded scan results file: %s", file_path)

            except Exception as e:
                ErrorHandler.show_error(self, translator.t('error'), translator.t('load_results_failed').format(str(e)))

    def calculate_grade(self) -> None:
        """Calculate and display grade for current student"""
        if not self.scan_results:
            ErrorHandler.show_warning(self, translator.t('warning'), translator.t('no_results_export'))
            return

        student_name = self.student_name_edit.text().strip()
        student_id = self.student_id_edit.text().strip()

        if not student_name or not student_id:
            ErrorHandler.show_warning(self, translator.t('warning'), translator.t('enter_student_info'))
            return

        # Extract data from scan results
        answers = self.scan_results.get('answers', {})
        omr_data = self.scan_results.get('omr_data', {})

        # Extract answer key and points
        questions_data = omr_data.get('questions', [])
        answer_key_int = {}
        points_per_question = {}

        for i, question_data in enumerate(questions_data):
            q_num = i + 1
            # Convert correct answer index to letter
            correct_index = question_data.get('correct_answer', 0)
            answer_key_int[q_num] = get_option_letter(correct_index)
            points_per_question[q_num] = question_data.get('points', 1)

        # Calculate grade
        self.current_grade_result = self.grading_system.calculate_grade(
            student_name, student_id, answers, answer_key_int, points_per_question
        )

        # Display results
        self.display_grade_result(self.current_grade_result)

        # Enable additional controls
        self.add_student_btn.setEnabled(True)
        self.update_class_statistics()
        self.update_students_table()
        self.enable_export_controls()

    def display_grade_result(self, result: GradeResult) -> None:
        """Display grade result in the grade display area"""
        text = f"""📊 {translator.t('grade_sheet')}

{translator.t('student_name_field')} {result.student_name}
{translator.t('student_id_field')} {result.student_id}

{translator.t('score_label')} {result.score}/{result.total_possible}
{translator.t('percentage_label')} {result.percentage:.1f}%
{translator.t('grade_label')} {self.grading_system.get_letter_grade(result.percentage)}

{translator.t('statistics_title')}:
{translator.t('correct_answers').format(result.correct_count)}
{translator.t('incorrect_answers').format(result.incorrect_count)}
{translator.t('blank_answers').format(result.blank_count)}
"""
        self.grade_display.setText(text)

    def add_current_student(self) -> None:
        """Add current student to batch processing list"""
        if self.current_grade_result:
            self.update_students_table()
            self.update_class_statistics()
            self.enable_export_controls()

            # Clear current student fields for next entry
            self.student_name_edit.clear()
            self.student_id_edit.clear()
            self.grade_display.clear()
            self.current_grade_result = None
            self.add_student_btn.setEnabled(False)

    def remove_selected_student(self) -> None:
        """Remove selected student from the list"""
        current_row = self.students_table.currentRow()
        if current_row >= 0 and current_row < len(self.grading_system.results):
            self.grading_system.results.pop(current_row)
            self.update_students_table()
            self.update_class_statistics()

            if not self.grading_system.results:
                self.disable_export_controls()

    def update_students_table(self) -> None:
        """Update the students table with current results"""
        self.students_table.setRowCount(len(self.grading_system.results))

        for row, result in enumerate(self.grading_system.results):
            self.students_table.setItem(row, 0, QTableWidgetItem(result.student_name))
            self.students_table.setItem(row, 1, QTableWidgetItem(result.student_id))
            self.students_table.setItem(row, 2, QTableWidgetItem(str(result.score)))
            self.students_table.setItem(row, 3, QTableWidgetItem(str(result.total_possible)))
            self.students_table.setItem(row, 4, QTableWidgetItem(f"{result.percentage:.1f}%"))
            self.students_table.setItem(row, 5, QTableWidgetItem(self.grading_system.get_letter_grade(result.percentage)))

        self.remove_student_btn.setEnabled(len(self.grading_system.results) > 0)

    def update_class_statistics(self) -> None:
        """Update class statistics display"""
        if not self.grading_system.results:
            self.stats_display.clear()
            return

        stats = self.grading_system.compute_stats()

        stats_text = f"""{translator.t('class_statistics')}

{translator.t('students_processed').format(len(self.grading_system.results))}
{translator.t('average_score').format(stats['average'])}
{translator.t('highest_score').format(stats['highest'])}
{translator.t('lowest_score').format(stats['lowest'])}
{translator.t('pass_rate').format(stats['pass_rate'])}
"""
        self.stats_display.setText(stats_text)

    def enable_export_controls(self) -> None:
        """Enable export controls when we have results"""
        has_results = len(self.grading_system.results) > 0
        self.export_csv_btn.setEnabled(has_results)
        if hasattr(self, 'export_excel_btn'):
            self.export_excel_btn.setEnabled(has_results)
        self.export_class_btn.setEnabled(has_results)
        self.clear_results_btn.setEnabled(has_results)

    def disable_export_controls(self) -> None:
        """Disable export controls when no results"""
        self.export_csv_btn.setEnabled(False)
        if hasattr(self, 'export_excel_btn'):
            self.export_excel_btn.setEnabled(False)
        self.export_class_btn.setEnabled(False)
        self.clear_results_btn.setEnabled(False)

    def export_csv(self) -> None:
        """Export results to CSV"""
        if not self.grading_system.results:
            ErrorHandler.show_warning(self, translator.t('warning'), translator.t('no_results_export'))
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, translator.t('export_csv'),
            build_timestamped_filename('omr_results', 'csv'),
            translator.t('file_filter_csv')
        )

        if filename:
            if self.grading_system.export_to_csv(filename):
                self.log.info("CSV export success: %s", filename)
                ErrorHandler.show_info(self, translator.t('success'), translator.t('export_success'))
            else:
                self.log.error("CSV export failed: %s", filename)
                ErrorHandler.show_error(self, translator.t('error'), translator.t('export_failed'))

    def export_excel(self) -> None:
        """Export results to Excel"""
        if not EXCEL_AVAILABLE:
            ErrorHandler.show_warning(self, translator.t('warning'),
                                      translator.t('excel_export_requires_libs'))
            return

        if not self.grading_system.results:
            ErrorHandler.show_warning(self, translator.t('warning'), translator.t('no_results_export'))
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, translator.t('export_excel'),
            build_timestamped_filename('omr_results', 'xlsx'),
            translator.t('file_filter_excel')
        )

        if filename:
            if self.grading_system.export_to_excel(filename):
                self.log.info("Excel export success: %s", filename)
                ErrorHandler.show_info(self, translator.t('success'), translator.t('export_success'))
            else:
                self.log.error("Excel export failed: %s", filename)
                ErrorHandler.show_error(self, translator.t('error'), translator.t('export_failed'))

    def export_class_report(self) -> None:
        """Export comprehensive class report as PDF"""
        if not self.grading_system.results:
            ErrorHandler.show_warning(self, translator.t('warning'), translator.t('no_results_export'))
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, translator.t('export_class_report'),
            build_timestamped_filename('class_report', 'pdf'),
            translator.t('file_filter_pdf')
        )

        if filename:
            if generate_class_report(self.grading_system, filename):
                self.log.info("Class report PDF generated: %s", filename)
                ErrorHandler.show_info(self, translator.t('success'), translator.t('export_success'))
            else:
                self.log.error("Class report PDF generation failed: %s", filename)
                ErrorHandler.show_error(self, translator.t('error'), translator.t('export_failed'))


    def clear_all_results(self) -> None:
        """Clear all results after confirmation"""
        if ErrorHandler.confirm(self, translator.t('clear_results_title'), translator.t('clear_results_confirm')):
            self.grading_system.results.clear()
            self.students_table.setRowCount(0)
            self.stats_display.clear()
            self.grade_display.clear()
            self.disable_export_controls()
            self.remove_student_btn.setEnabled(False)

    def refresh_ui(self) -> None:
        """Refresh UI elements with current language"""
        # Update group titles and labels
        self.title_label.setText(translator.t('grading_title'))
        if hasattr(self, "load_group"):
            self.load_group.setTitle(translator.t('load_scan_results'))
        if hasattr(self, "student_group"):
            self.student_group.setTitle(translator.t('student_info'))
        if hasattr(self, "batch_group"):
            self.batch_group.setTitle(translator.t('batch_processing'))
        if hasattr(self, "stats_group"):
            self.stats_group.setTitle(translator.t('class_statistics'))
        if hasattr(self, "export_group"):
            self.export_group.setTitle(translator.t('export_results'))
        if hasattr(self, "current_group"):
            self.current_group.setTitle(translator.t('grade_sheet'))
        if hasattr(self, "students_group"):
            self.students_group.setTitle(translator.t('students_processed_title'))
        self.student_name_label.setText(translator.t('student_name_field'))
        self.student_id_label.setText(translator.t('student_id_field'))
        # Update placeholders
        self.student_name_edit.setPlaceholderText(translator.t('student_name_placeholder'))
        self.student_id_edit.setPlaceholderText(translator.t('student_id_placeholder'))

        # Update buttons
        self.load_results_btn.setText(translator.t('load_results_btn'))
        self.calculate_grade_btn.setText(translator.t('calculate_grade'))
        self.add_student_btn.setText(translator.t('add_student'))
        self.remove_student_btn.setText(translator.t('remove_student'))
        self.export_csv_btn.setText(translator.t('export_csv'))
        if hasattr(self, 'export_excel_btn'):
            self.export_excel_btn.setText(translator.t('export_excel'))
        self.export_class_btn.setText(translator.t('export_class_report'))
        self.clear_results_btn.setText(translator.t('clear_all_results'))

        # Update table headers
        self._update_table_headers()

        # Refresh statistics if we have results
        if self.grading_system.results:
            self.update_class_statistics()
        # Update info label under Load Results when no file loaded
        if hasattr(self, 'scan_info') and not self.scan_results:
            self.scan_info.setText(translator.t('select_omr_results'))

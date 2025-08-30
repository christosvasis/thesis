from ui.ui_helpers import UIHelpers
from utils.error_handling import ErrorHandler
import csv
from typing import List
from PyQt6.QtWidgets import (
    QCheckBox, QDialog, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QVBoxLayout
)
from core.grading.grading_core import EXCEL_AVAILABLE
try:
    import pandas as pd  # type: ignore
except ImportError:  # pragma: no cover
    pd = None  # type: ignore
from core.models.question_model import Question
from i18n.translator import get_option_letter, translator
from config.logger_config import get_logger, UI_LOGGER_NAME


class ImportDialog(QDialog):
    """CSV/Excel import dialog with preview"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.imported_questions: List[Question] = []
        self.raw_data: List[List[str]] = []
        self.log = get_logger(UI_LOGGER_NAME)
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle(translator.t('import_title'))
        self.setModal(True)
        self.resize(800, 600)

        layout = QVBoxLayout()

        # Instructions
        layout.addWidget(QLabel(translator.t('import_expected')))

        # File selection
        file_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText(translator.t('import_file_placeholder'))
        self.file_path_edit.setReadOnly(True)
        browse_btn = UIHelpers.create_button(translator.t('browse_button'), "primary", self.browse_file)
        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(browse_btn)
        layout.addLayout(file_layout)

        # Preview
        self.preview_table = QTableWidget()
        layout.addWidget(self.preview_table)

        # Options
        self.has_headers_cb = QCheckBox(translator.t('has_headers'))
        self.has_headers_cb.setChecked(True)
        self.has_headers_cb.stateChanged.connect(self.refresh_preview)
        self.clear_existing_cb = QCheckBox(translator.t('clear_existing'))

        options_layout = QHBoxLayout()
        options_layout.addWidget(self.has_headers_cb)
        options_layout.addWidget(self.clear_existing_cb)
        layout.addLayout(options_layout)

        # Buttons
        button_layout = QHBoxLayout()
        cancel_btn = UIHelpers.create_button(translator.t('cancel_button'), callback=self.reject)
        self.import_btn = UIHelpers.create_button(translator.t('import_button'), "success", self.import_questions)
        self.import_btn.setEnabled(False)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.import_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def browse_file(self):
        filters = translator.t('file_filter_csv')
        if EXCEL_AVAILABLE:
            filters += f";;{translator.t('file_filter_excel_multi')}"

        filename, _ = QFileDialog.getOpenFileName(self, translator.t('select_file_title'), "", filters)
        if filename:
            self.file_path_edit.setText(filename)
            self.load_file_preview(filename)

    def load_file_preview(self, filename: str):
        try:
            ext = filename.lower()
            if ext.endswith('.csv'):
                self._load_csv_file(filename)
            elif EXCEL_AVAILABLE and ext.endswith(('.xlsx', '.xls')):
                self._load_excel_file(filename)
            else:
                ErrorHandler.show_warning(self, translator.t('error'), translator.t('unsupported_file_format'))
                return

            self.refresh_preview()
            self.import_btn.setEnabled(True)
            self.log.info("Import preview loaded: %s", filename)
        except Exception as e:
            ErrorHandler.show_error(self, translator.t('error'), translator.t('load_file_failed').format(str(e)))

    def _load_csv_file(self, filename: str):
        """Load CSV with multiple encoding attempts"""
        for encoding in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
            try:
                with open(filename, 'r', encoding=encoding) as f:
                    self.raw_data = list(csv.reader(f))
                return
            except UnicodeDecodeError:
                continue
            except Exception as e:
                if encoding == 'cp1252':
                    raise ValueError(f"Failed to read CSV file: {str(e)}")

        # Final fallback with error replacement
        try:
            with open(filename, 'r', encoding='utf-8', errors='replace') as f:
                self.raw_data = list(csv.reader(f))
        except Exception as e:
            raise ValueError(f"Unable to read CSV file: {str(e)}")

    def _load_excel_file(self, filename: str):
        """Load Excel file"""
        try:
            df = pd.read_excel(filename, header=None, engine='openpyxl')
            df = df.fillna('')  # Convert NaN to empty strings
            self.raw_data = df.values.tolist()
        except Exception as e:
            raise ValueError(f"Failed to read Excel file: {str(e)}")

    def refresh_preview(self):
        if not self.raw_data:
            return

        has_headers = self.has_headers_cb.isChecked()
        data = self.raw_data[1:] if has_headers and len(self.raw_data) > 1 else self.raw_data
        headers = (self.raw_data[0] if has_headers and len(self.raw_data) > 0
                  else [f"Column {i+1}" for i in range(len(self.raw_data[0]) if self.raw_data and self.raw_data[0] else 0)])

        self.preview_table.setRowCount(min(len(data), 10))
        self.preview_table.setColumnCount(len(headers))
        self.preview_table.setHorizontalHeaderLabels([str(h) for h in headers])

        for row in range(min(len(data), 10)):
            for col in range(len(headers)):
                item_text = str(data[row][col]) if row < len(data) and col < len(data[row]) and data[row][col] is not None else ""
                self.preview_table.setItem(row, col, QTableWidgetItem(item_text))

    def import_questions(self):
        try:
            self.imported_questions = self._parse_questions()
            if self.imported_questions:
                self.accept()
            else:
                ErrorHandler.show_warning(self, "Error", "No valid questions found")
        except Exception as e:
            ErrorHandler.show_error(self, "Error", f"Import failed: {str(e)}")

    def _parse_questions(self) -> List[Question]:
        """Parse raw data into Question objects"""
        if not self.raw_data:
            return []

        has_headers = self.has_headers_cb.isChecked()
        data = self.raw_data[1:] if has_headers and len(self.raw_data) > 1 else self.raw_data
        questions = []

        for row in data:
            if not row or len(row) < 1:
                continue

            question = Question()
            question.text = str(row[0]).strip() if len(row) > 0 else "Question"
            question.options = [str(row[i]).strip() if i < len(row) else f"Option {get_option_letter(i-1)}" for i in range(1, 5)]

            # Handle correct answer (English A,B,C,D or Greek Α,Β,Γ,Δ)
            correct = str(row[5]).strip() if len(row) > 5 else get_option_letter(0)
            correct_index = 0
            if correct.upper() in 'ABCD':
                correct_index = ord(correct.upper()) - ord('A')
            elif correct in 'ΑΒΓΔ':
                greek_map = {'Α': 0, 'Β': 1, 'Γ': 2, 'Δ': 3}
                correct_index = greek_map.get(correct, 0)

            valid_option_count = len([opt for opt in question.options if opt.strip()])
            question.correct = correct_index if correct_index < valid_option_count else 0

            # Handle points
            if len(row) > 6:
                try:
                    points_value = float(str(row[6]))
                    question.points = max(1, round(points_value))
                except (ValueError, TypeError):
                    question.points = 1

            if question.text and len([opt for opt in question.options if opt.strip()]) >= 2:
                questions.append(question)

        return questions

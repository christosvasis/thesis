#!/usr/bin/env python3
"""
OMR Form Designer
Clean, functional interface for creating optical mark recognition forms.
"""

import sys
import json
import os
import csv
import platform
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    import pandas as pd
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import *
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Constants
MAX_OPTIONS_COUNT = 4
DEFAULT_POINTS_RANGE = 10
BUBBLE_RADIUS = 10
BUBBLE_SPACING = 0.8
MIN_BOTTOM_MARGIN = 1.0
QUESTION_HEIGHT = 0.6
PREVIEW_TEXT_TRUNCATE_LENGTH = 40
SPLITTER_SIZES = [300, 600, 250]
PDF_MARGINS = {'right': 0.75, 'left': 0.75, 'top': 1.0, 'bottom': 1.0}
FONT_SIZES = {'title': 18, 'header': 16, 'normal': 12, 'instruction': 10, 'small': 8}


def get_font():
    """Get Unicode-compatible font"""
    try:
        font_paths = {
            "Darwin": ["/System/Library/Fonts/Geneva.ttf"],
            "Linux": ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
            "Windows": ["C:/Windows/Fonts/arial.ttf"]
        }
        
        for path in font_paths.get(platform.system(), []):
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont('UnicodeFont', path))
                    return 'UnicodeFont'
                except Exception:
                    continue
    except Exception:
        pass
    return 'Helvetica'

FONT = get_font()

def get_styles(dark_mode=False):
    c = {'bg': '#0f172a', 'panel': '#1e293b', 'text': '#e2e8f0', 'border': '#334155', 'input_border': '#475569', 'hover': '#334155', 'accent': '#3b82f6', 'button_bg': '#1e293b', 'button_hover': '#334155', 'input_bg': '#1e293b'} if dark_mode else {'bg': '#f7f9fc', 'panel': '#ffffff', 'text': '#1f2937', 'border': '#d1d5db', 'input_border': '#9ca3af', 'hover': '#e5e7eb', 'accent': '#2563eb', 'button_bg': '#f9fafb', 'button_hover': '#f3f4f6', 'input_bg': '#ffffff', 'secondary_text': '#6b7280', 'success': '#059669', 'warning': '#d97706', 'danger': '#dc2626'}
    
    return f"""QMainWindow{{background:{c['bg']};color:{c['text']};font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:13px}}
QFrame{{background:{c['panel']};border:1px solid {c['border']};border-radius:6px;padding:8px}}
QPushButton{{background:{c.get('button_bg',c['panel'])};color:{c['text']};border:1px solid {c['input_border']};border-radius:4px;padding:6px 12px;font-weight:500;min-height:26px}}
QPushButton:hover{{background:{c.get('button_hover',c['hover'])};border-color:{c['accent']}}}
QPushButton:pressed{{background:{c['hover']}}}
QPushButton[class="primary"]{{background:{c['accent']};color:white;border-color:{c['accent']}}}
QPushButton[class="primary"]:hover{{background:{'#1d4ed8' if not dark_mode else '#3b82f6'};border-color:{'#1d4ed8' if not dark_mode else '#3b82f6'}}}
QPushButton[class="success"]{{background:{c.get('success','#059669')};color:white;border-color:{c.get('success','#059669')}}}
QPushButton[class="success"]:hover{{background:{'#047857' if not dark_mode else '#10b981'}}}
QPushButton[class="danger"]{{background:{c.get('danger','#dc2626')};color:white;border-color:{c.get('danger','#dc2626')}}}
QPushButton[class="danger"]:hover{{background:{'#b91c1c' if not dark_mode else '#ef4444'}}}
QLineEdit,QTextEdit{{background:{c.get('input_bg',c['panel'])};color:{c['text']};border:1px solid {c['input_border']};border-radius:4px;padding:6px 8px;min-height:20px;selection-background-color:{c['accent']};selection-color:white}}
QLineEdit:focus,QTextEdit:focus{{border-color:{c['accent']};outline:0}}
QComboBox{{background:{c.get('input_bg',c['panel'])};color:{c['text']};border:1px solid {c['input_border']};border-radius:4px;padding:4px 8px;min-width:50px}}
QComboBox:focus{{border-color:{c['accent']}}}
QComboBox::drop-down{{subcontrol-origin:padding;subcontrol-position:top right;width:20px;border-left:1px solid {c['input_border']};border-top-right-radius:3px;border-bottom-right-radius:3px;background:{c.get('button_bg',c['panel'])}}}
QComboBox::down-arrow{{image:none;border:2px solid {c['text']};border-top:none;border-left:none;width:6px;height:6px;margin:4px}}
QComboBox QAbstractItemView{{background:{c['panel']};color:{c['text']};border:1px solid {c['input_border']};selection-background-color:{c['accent']};selection-color:white;outline:0}}
QListWidget{{background:{c['panel']};color:{c['text']};border:1px solid {c['border']};border-radius:4px;outline:0}}
QListWidget::item{{padding:4px 8px;border-bottom:1px solid {c['border']}}}
QListWidget::item:selected{{background:{c['accent']};color:white}}
QListWidget::item:hover{{background:{c['hover']}}}
QTabWidget::pane{{background:{c['panel']};border:1px solid {c['border']};border-radius:4px}}
QTabBar::tab{{background:{c['bg']};color:{c.get('secondary_text',c['text'])};border:1px solid {c['border']};padding:8px 16px;margin-right:2px}}
QTabBar::tab:selected{{background:{c['panel']};color:{c['accent']};font-weight:600;border-bottom-color:{c['panel']}}}
QTabBar::tab:hover{{background:{c['hover']}}}
QLabel{{color:{c['text']}}}
QGroupBox{{color:{c['text']};border:1px solid {c['border']};border-radius:4px;margin-top:8px;padding-top:8px}}
QGroupBox::title{{color:{c['text']};subcontrol-origin:margin;left:8px;padding:0 4px}}
QMenuBar{{background:{c['panel']};color:{c['text']};border-bottom:1px solid {c['border']}}}
QMenuBar::item{{background:transparent;padding:4px 8px;margin:2px;border-radius:3px}}
QMenuBar::item:selected{{background:{c['hover']};color:{c['text']}}}
QMenuBar::item:pressed{{background:{c['accent']};color:white}}
QMenu{{background:{c['panel']};color:{c['text']};border:1px solid {c['border']};border-radius:4px;padding:4px 0}}
QMenu::item{{padding:6px 12px;margin:1px 4px;border-radius:3px}}
QMenu::item:selected{{background:{c['accent']};color:white}}
QMenu::separator{{height:1px;background:{c['border']};margin:4px 8px}}
QStatusBar{{background:{c['panel']};color:{c['text']};border-top:1px solid {c['border']}}}"""

class UIHelpers:
    @staticmethod
    def create_button(text: str, style_class: Optional[str] = None, callback=None, tooltip: Optional[str] = None) -> QPushButton:
        btn = QPushButton(text)
        if style_class: btn.setProperty("class", style_class)
        if callback: btn.clicked.connect(callback)
        if tooltip: btn.setToolTip(tooltip)
        return btn
    
    @staticmethod
    def create_labeled_row(parent_layout: QLayout, label_text: str, widget: QWidget):
        row = QHBoxLayout()
        row.addWidget(QLabel(label_text))
        row.addWidget(widget)
        parent_layout.addLayout(row)
        return row
    
    @staticmethod
    def show_message(parent: QWidget, msg_type: str, title: str, message: str):
        icons = {"success": QMessageBox.Icon.Information, "error": QMessageBox.Icon.Critical, "warning": QMessageBox.Icon.Warning}
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icons.get(msg_type, QMessageBox.Icon.Information))
        msg_box.exec()
    
    @staticmethod
    def create_combo_with_items(items: List, callback=None, use_index=False) -> QComboBox:
        combo = QComboBox()
        combo.addItems([str(item) for item in items])
        if callback:
            if use_index:
                combo.currentIndexChanged.connect(callback)
            else:
                combo.currentTextChanged.connect(callback)
        return combo

class Translator:
    def __init__(self):
        self.current_language = 'en'
        en = {
            'app_title': 'OMR Form Designer', 'form_validation_valid': 'Form is valid', 'theme_light_mode': '🌙 Light Mode', 'theme_dark_mode': '🌞 Dark Mode', 'theme_tooltip': 'Click to toggle Dark/Light Mode',
            'menu_file': 'File', 'menu_new': 'New', 'menu_load': 'Load', 'menu_save': 'Save', 'menu_exit': 'Exit', 'menu_export': 'Export', 'menu_export_pdf': 'Export PDF', 'menu_export_omr': 'Export OMR Sheet', 'menu_export_scanner': 'Export for Scanner', 'menu_import': 'Import', 'menu_import_csv': 'Import CSV/Excel', 'menu_language': 'Language', 'menu_english': 'English', 'menu_greek': 'Ελληνικά',
            'title_label': 'Title:', 'instructions_label': 'Instructions:', 'preview_label': 'Preview', 'questions_panel': 'Questions', 'question_text_label': 'Question Text', 'answer_options_label': 'Answer Options', 'correct_label': 'Correct:', 'points_label': 'Points:', 'add_button': 'Add', 'delete_button': 'Delete', 'option': 'Option', 'preview_title': 'Title', 'preview_instructions': 'Instructions', 'preview_points': 'Points',
            'default_form_title': 'New Form', 'default_instructions': 'Select the best answer for each question.', 'default_option_a': 'Option A', 'default_option_b': 'Option B', 'default_option_c': 'Option C', 'default_option_d': 'Option D', 'default_question': 'Question', 'no_text': 'No text',
            'import_title': 'Import Questions', 'import_expected': 'Expected: Question, Option A, Option B, Option C, Option D, Correct Answer, Points', 'import_file_placeholder': 'Select CSV or Excel file...', 'browse_button': 'Browse', 'has_headers': 'First row contains headers', 'clear_existing': 'Clear existing questions', 'cancel_button': 'Cancel', 'import_button': 'Import',
            'success': 'Success', 'error': 'Error', 'warning': 'Warning', 'form_saved': 'Form saved!', 'form_loaded': 'Form loaded!', 'pdf_exported': 'PDF exported!', 'omr_exported': 'OMR sheet exported!', 'questions_imported': 'questions imported!', 'export_failed': 'Export failed:', 'save_failed': 'Save failed:', 'load_failed': 'Load failed:', 'critical_errors': 'Form has critical errors. Fix them first.', 'no_questions_export': 'No questions to export', 'exported_scanner': 'Exported for scanner:', 'new_form_confirm': 'Create new form? Unsaved changes will be lost.',
            'validation_title': 'Validation', 'form_valid': 'Form is valid!', 'issues_found': 'issue(s) found', 'click_details': '(click for details)', 'details_label': 'Details:', 'ok_button': 'OK',
            'answer_sheet': 'ANSWER SHEET', 'student_name': 'Name:', 'student_id': 'Student ID:', 'omr_instruction1': '• Fill in bubbles completely with dark pencil or pen', 'omr_instruction2': '• Make no stray marks on this sheet', 'total_questions': 'Total Questions:', 'total_points': 'Total Points:', 'continued': 'continued'
        }
        
        el = {
            'app_title': 'Σχεδιαστής Φορμών OMR', 'form_validation_valid': 'Η φόρμα είναι έγκυρη', 'theme_light_mode': '🌙 Φωτεινό Θέμα', 'theme_dark_mode': '🌞 Σκοτεινό Θέμα', 'theme_tooltip': 'Κάντε κλικ για εναλλαγή Σκοτεινού/Φωτεινού Θέματος',
            'menu_file': 'Αρχείο', 'menu_new': 'Νέο', 'menu_load': 'Φόρτωση', 'menu_save': 'Αποθήκευση', 'menu_exit': 'Έξοδος', 'menu_export': 'Εξαγωγή', 'menu_export_pdf': 'Εξαγωγή PDF', 'menu_export_omr': 'Εξαγωγή Φύλλου OMR', 'menu_export_scanner': 'Εξαγωγή για Σαρωτή', 'menu_import': 'Εισαγωγή', 'menu_import_csv': 'Εισαγωγή CSV/Excel', 'menu_language': 'Γλώσσα', 'menu_english': 'English', 'menu_greek': 'Ελληνικά',
            'title_label': 'Τίτλος:', 'instructions_label': 'Οδηγίες:', 'preview_label': 'Προεπισκόπηση', 'questions_panel': 'Ερωτήσεις', 'question_text_label': 'Κείμενο Ερώτησης', 'answer_options_label': 'Επιλογές Απαντήσεων', 'correct_label': 'Σωστή:', 'points_label': 'Βαθμοί:', 'add_button': 'Προσθήκη', 'delete_button': 'Διαγραφή', 'option': 'Επιλογή', 'preview_title': 'Τίτλος', 'preview_instructions': 'Οδηγίες', 'preview_points': 'Βαθμοί',
            'default_form_title': 'Νέα Φόρμα', 'default_instructions': 'Επιλέξτε την καλύτερη απάντηση για κάθε ερώτηση.', 'default_option_a': 'Επιλογή Α', 'default_option_b': 'Επιλογή Β', 'default_option_c': 'Επιλογή Γ', 'default_option_d': 'Επιλογή Δ', 'default_question': 'Ερώτηση', 'no_text': 'Χωρίς κείμενο',
            'import_title': 'Εισαγωγή Ερωτήσεων', 'import_expected': 'Αναμενόμενο: Ερώτηση, Επιλογή Α, Επιλογή Β, Επιλογή Γ, Επιλογή Δ, Σωστή Απάντηση, Βαθμοί', 'import_file_placeholder': 'Επιλέξτε αρχείο CSV ή Excel...', 'browse_button': 'Αναζήτηση', 'has_headers': 'Η πρώτη γραμμή περιέχει επικεφαλίδες', 'clear_existing': 'Διαγραφή υπαρχουσών ερωτήσεων', 'cancel_button': 'Ακύρωση', 'import_button': 'Εισαγωγή',
            'success': 'Επιτυχία', 'error': 'Σφάλμα', 'warning': 'Προειδοποίηση', 'form_saved': 'Η φόρμα αποθηκεύτηκε!', 'form_loaded': 'Η φόρμα φορτώθηκε!', 'pdf_exported': 'Το PDF εξήχθη!', 'omr_exported': 'Το φύλλο OMR εξήχθη!', 'questions_imported': 'ερωτήσεις εισήχθησαν!', 'export_failed': 'Η εξαγωγή απέτυχε:', 'save_failed': 'Η αποθήκευση απέτυχε:', 'load_failed': 'Η φόρτωση απέτυχε:', 'critical_errors': 'Η φόρμα έχει κρίσιμα σφάλματα. Διορθώστε τα πρώτα.', 'no_questions_export': 'Δεν υπάρχουν ερωτήσεις για εξαγωγή', 'exported_scanner': 'Εξήχθη για σαρωτή:', 'new_form_confirm': 'Δημιουργία νέας φόρμας; Οι μη αποθηκευμένες αλλαγές θα χαθούν.',
            'validation_title': 'Επικύρωση', 'form_valid': 'Η φόρμα είναι έγκυρη!', 'issues_found': 'ζήτημα(τα) βρέθηκε(αν)', 'click_details': '(κλικ για λεπτομέρειες)', 'details_label': 'Λεπτομέρειες:', 'ok_button': 'Εντάξει',
            'answer_sheet': 'ΦΥΛΛΟ ΑΠΑΝΤΗΣΕΩΝ', 'student_name': 'Όνομα:', 'student_id': 'Αρ. Μητρώου:', 'omr_instruction1': '• Συμπληρώστε πλήρως τις φυσαλίδες με σκούρο μολύβι ή στυλό', 'omr_instruction2': '• Μην κάνετε άλλα σημάδια σε αυτό το φύλλο', 'total_questions': 'Σύνολο Ερωτήσεων:', 'total_points': 'Σύνολο Βαθμών:', 'continued': 'συνέχεια'
        }
        
        self.translations = {'en': en, 'el': el}
    
    def set_language(self, lang_code: str):
        if lang_code in self.translations:
            self.current_language = lang_code
    
    def t(self, key: str) -> str:
        translation = self.translations[self.current_language].get(key)
        if translation is None:
            translation = self.translations['en'].get(key, f"[{key}]")
        return translation

translator = Translator()

def get_option_letter(index: int) -> str:
    """Get the appropriate option letter based on current language"""
    if translator.current_language == 'el':  # Greek
        greek_letters = ['Α', 'Β', 'Γ', 'Δ']
        return greek_letters[index] if index < len(greek_letters) else chr(65 + index)
    else:  # English and other languages
        return chr(65 + index)

class Question:
    def __init__(self):
        self.text: str = ""
        self.options: List[str] = ["Option A", "Option B", "Option C", "Option D"]
        self.correct: int = 0
        self.points: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            'text': self.text,
            'options': self.options.copy(),
            'correct': self.correct,
            'points': self.points
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Question':
        question = cls()
        question.text = data.get('text', '')
        question.options = data.get('options', ["Option A", "Option B", "Option C", "Option D"]).copy()
        question.correct = data.get('correct', 0)
        question.points = data.get('points', 1)
        return question

    def validate(self) -> List[str]:
        errors = []
        if not self.text.strip(): errors.append("Question text is empty")
        if len([opt.strip() for opt in self.options if opt.strip()]) < 2: errors.append("At least 2 answer options are required")
        if self.correct < 0 or self.correct >= len(self.options): errors.append("Invalid correct answer index")
        if self.points < 0: errors.append("Points cannot be negative")
        return errors

class Form:
    def __init__(self):
        self.title: str = "New Form"
        self.instructions: str = "Select the best answer for each question."
        self.questions: List[Question] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'instructions': self.instructions,
            'questions': [q.to_dict() for q in self.questions]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Form':
        form = cls()
        form.title = data.get('title', 'New Form')
        form.instructions = data.get('instructions', 'Select the best answer for each question.')
        form.questions = [Question.from_dict(q) for q in data.get('questions', [])]
        return form

    def validate(self) -> List[str]:
        errors = []
        if not self.title.strip(): errors.append("Form title is required")
        if not self.questions: errors.append("Form must have at least one question")
        for i, q in enumerate(self.questions):
            for error in q.validate(): errors.append(f"Question {i+1}: {error}")
        return errors

    def get_validation_summary(self) -> Dict[str, Any]:
        errors = self.validate()
        if not errors:
            return {"status": "valid", "message": "Form is ready", "errors": []}
        
        critical_keywords = ["required", "empty", "at least", "must have"]
        has_critical = any(any(k in e.lower() for k in critical_keywords) for e in errors)
        
        return {
            "status": "invalid" if has_critical else "warning",
            "message": f"{len(errors)} issue(s) found",
            "errors": errors
        }

class ImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.imported_questions: List[Question] = []
        self.raw_data: List[List[str]] = []
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
        filters = "CSV Files (*.csv)"
        if EXCEL_AVAILABLE:
            filters += ";;Excel Files (*.xlsx *.xls)"
        
        filename, _ = QFileDialog.getOpenFileName(self, "Select File", "", filters)
        if filename:
            self.file_path_edit.setText(filename)
            self.load_file_preview(filename)

    def load_file_preview(self, filename: str):
        try:
            ext = filename.lower()
            if ext.endswith('.csv'):
                self.load_csv_file(filename)
            elif EXCEL_AVAILABLE and ext.endswith(('.xlsx', '.xls')):
                self.load_excel_file(filename)
            else:
                QMessageBox.warning(self, "Error", "Unsupported file format")
                return
            
            self.refresh_preview()
            self.import_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")

    def load_csv_file(self, filename: str):
        for encoding in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
            try:
                with open(filename, 'r', encoding=encoding) as f:
                    self.raw_data = list(csv.reader(f))
                return
            except UnicodeDecodeError: continue
            except Exception as e:
                if encoding == 'cp1252': raise ValueError(f"Failed to read CSV file: {str(e)}")
        try:
            with open(filename, 'r', encoding='utf-8', errors='replace') as f:
                self.raw_data = list(csv.reader(f))
        except Exception as e: raise ValueError(f"Unable to read CSV file: {str(e)}")

    def load_excel_file(self, filename: str):
        try:
            df = pd.read_excel(filename, header=None, engine='openpyxl')
            # Convert NaN values to empty strings to prevent None issues
            df = df.fillna('')
            self.raw_data = df.values.tolist()
        except Exception as e:
            raise ValueError(f"Failed to read Excel file: {str(e)}")

    def refresh_preview(self):
        if not self.raw_data:
            return
        
        has_headers = self.has_headers_cb.isChecked()
        data = self.raw_data[1:] if has_headers and len(self.raw_data) > 1 else self.raw_data
        headers = self.raw_data[0] if has_headers and len(self.raw_data) > 0 else [f"Column {i+1}" for i in range(len(self.raw_data[0]) if len(self.raw_data) > 0 and len(self.raw_data[0]) > 0 else 0)]
        
        self.preview_table.setRowCount(min(len(data), 10))
        self.preview_table.setColumnCount(len(headers))
        self.preview_table.setHorizontalHeaderLabels([str(h) for h in headers])
        
        for row in range(min(len(data), 10)):
            for col in range(len(headers)):
                if row < len(data) and col < len(data[row]):
                    item_text = str(data[row][col]) if data[row][col] is not None else ""
                else:
                    item_text = ""
                item = QTableWidgetItem(item_text)
                self.preview_table.setItem(row, col, item)

    def import_questions(self):
        try:
            self.imported_questions = self.parse_questions()
            if self.imported_questions:
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "No valid questions found")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed: {str(e)}")

    def parse_questions(self) -> List[Question]:
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
            
            correct = str(row[5]).strip() if len(row) > 5 else get_option_letter(0)
            # Handle both English (A,B,C,D) and Greek (Α,Β,Γ,Δ) letters
            correct_index = 0
            if correct.upper() in 'ABCD':
                correct_index = ord(correct.upper()) - ord('A')
            elif correct in 'ΑΒΓΔ':
                greek_map = {'Α': 0, 'Β': 1, 'Γ': 2, 'Δ': 3}
                correct_index = greek_map.get(correct, 0)
            
            valid_option_count = len([opt for opt in question.options if opt.strip()])
            question.correct = correct_index if correct_index < valid_option_count else 0
            
            if len(row) > 6:
                try:
                    points_value = float(str(row[6]))
                    question.points = max(1, round(points_value))
                except (ValueError, TypeError):
                    question.points = 1
            
            if question.text and len([opt for opt in question.options if opt.strip()]) >= 2:
                questions.append(question)
        
        return questions

class QuestionEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.question: Optional[Question] = None
        self.parent_form = parent
        self.option_edits: List[QLineEdit] = []
        self.option_labels: List[QLabel] = []  # Store references to option labels
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Question text
        self.question_text_label = QLabel(translator.t('question_text_label'))
        layout.addWidget(self.question_text_label)
        self.text_edit = QTextEdit()
        self.text_edit.setMaximumHeight(100)
        self.text_edit.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.text_edit)
        
        # Options
        self.answer_options_label = QLabel(translator.t('answer_options_label'))
        layout.addWidget(self.answer_options_label)
        for i in range(MAX_OPTIONS_COUNT):
            row = QHBoxLayout()
            label = QLabel(get_option_letter(i))
            label.setFixedSize(30, 30)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("background: #1e40af; color: white; font-weight: bold;")
            self.option_labels.append(label)  # Store reference to label
            
            edit = QLineEdit()
            edit.setPlaceholderText(f"{translator.t('option')} {get_option_letter(i)}")
            edit.textChanged.connect(self.on_option_changed)
            self.option_edits.append(edit)
            
            row.addWidget(label)
            row.addWidget(edit)
            layout.addLayout(row)
        
        # Settings
        settings = QHBoxLayout()
        
        # Correct answer
        correct_row = QHBoxLayout()
        self.correct_label = QLabel(translator.t('correct_label'))
        correct_row.addWidget(self.correct_label)
        correct_row.addWidget(self.create_correct_combo())
        settings.addLayout(correct_row)
        
        # Points
        points_row = QHBoxLayout()
        self.points_label = QLabel(translator.t('points_label'))
        points_row.addWidget(self.points_label)
        points_row.addWidget(self.create_points_combo())
        settings.addLayout(points_row)
        
        settings.addStretch()
        layout.addLayout(settings)
        
        layout.addStretch()
        self.setLayout(layout)

    def create_correct_combo(self) -> QComboBox:
        self.correct_combo = UIHelpers.create_combo_with_items(
            [get_option_letter(i) for i in range(MAX_OPTIONS_COUNT)], 
            self.on_correct_changed,
            use_index=True
        )
        return self.correct_combo

    def create_points_combo(self) -> QComboBox:
        self.points_combo = UIHelpers.create_combo_with_items(
            list(range(1, DEFAULT_POINTS_RANGE + 1)), 
            self.on_points_changed
        )
        return self.points_combo

    def load_question(self, question: Optional[Question]):
        # Block signals to prevent updating the question during UI loading
        with SignalBlocker(self.text_edit, *self.option_edits, self.correct_combo, self.points_combo):
            self.question = question
            if question:
                self.text_edit.setPlainText(question.text)
                
                for i in range(MAX_OPTIONS_COUNT):
                    if i < len(question.options):
                        self.option_edits[i].setText(question.options[i])
                    else:
                        self.option_edits[i].setText("")
                
                self.correct_combo.setCurrentIndex(min(question.correct, MAX_OPTIONS_COUNT - 1))
                self.points_combo.setCurrentIndex(max(0, min(question.points - 1, self.points_combo.count() - 1)))
            else:
                self.clear()

    def clear(self):
        self.text_edit.clear()
        for edit in self.option_edits:
            edit.clear()
        self.correct_combo.setCurrentIndex(0)
        self.points_combo.setCurrentIndex(0)

    def on_text_changed(self):
        if self.question:
            self.question.text = self.text_edit.toPlainText()
            self.notify_parent()

    def on_option_changed(self):
        if self.question:
            for i, edit in enumerate(self.option_edits):
                if i < len(self.question.options):
                    self.question.options[i] = edit.text()
            self.notify_parent()

    def on_correct_changed(self, index: int):
        if self.question:
            self.question.correct = index
            self.notify_parent()

    def on_points_changed(self, points_str: str):
        if self.question:
            try: self.question.points = max(1, min(int(points_str), DEFAULT_POINTS_RANGE))
            except (ValueError, TypeError): self.question.points = 1
            self.notify_parent()

    def notify_parent(self):
        if self.parent_form and hasattr(self.parent_form, 'refresh_display'):
            self.parent_form.refresh_display()

    def refresh_option_letters(self):
        """Refresh option letters when language changes"""
        for attr, key in [('question_text_label', 'question_text_label'), ('answer_options_label', 'answer_options_label'), ('correct_label', 'correct_label'), ('points_label', 'points_label')]:
            if hasattr(self, attr): getattr(self, attr).setText(translator.t(key))
            
        if hasattr(self, 'option_labels'):
            for i, label in enumerate(self.option_labels[:MAX_OPTIONS_COUNT]): label.setText(get_option_letter(i))
        for i in range(min(MAX_OPTIONS_COUNT, len(self.option_edits))): self.option_edits[i].setPlaceholderText(f"{translator.t('option')} {get_option_letter(i)}")
        if hasattr(self, 'correct_combo'):
            current_index = self.correct_combo.currentIndex()
            self.correct_combo.clear()
            self.correct_combo.addItems([get_option_letter(i) for i in range(MAX_OPTIONS_COUNT)])
            self.correct_combo.setCurrentIndex(current_index)

class FormDesigner(QWidget):
    validation_changed = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.form = Form()
        self.form.title = translator.t('default_form_title')
        self.form.instructions = translator.t('default_instructions')
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Form info
        info_layout = QHBoxLayout()
        self.title_input = QLineEdit(self.form.title)
        self.title_input.textChanged.connect(self.on_title_changed)
        self.instructions_input = QLineEdit(self.form.instructions)
        self.instructions_input.textChanged.connect(self.on_instructions_changed)
        
        # Create title row
        title_row = QHBoxLayout()
        self.title_label = QLabel(translator.t('title_label'))
        title_row.addWidget(self.title_label)
        title_row.addWidget(self.title_input)
        info_layout.addLayout(title_row)
        
        # Create instructions row
        inst_row = QHBoxLayout()
        self.instructions_label = QLabel(translator.t('instructions_label'))
        inst_row.addWidget(self.instructions_label)
        inst_row.addWidget(self.instructions_input)
        info_layout.addLayout(inst_row)
        
        layout.addLayout(info_layout)
        
        # Main content
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Questions panel
        left = QWidget()
        left_layout = QVBoxLayout()
        self.questions_list = QListWidget()
        self.questions_list.currentRowChanged.connect(self.on_question_selected)
        left_layout.addWidget(self.questions_list)
        
        btn_layout = QHBoxLayout()
        self.add_question_btn = UIHelpers.create_button(translator.t('add_button'), "success", self.add_question)
        self.delete_question_btn = UIHelpers.create_button(translator.t('delete_button'), "danger", self.delete_question)
        btn_layout.addWidget(self.add_question_btn)
        btn_layout.addWidget(self.delete_question_btn)
        left_layout.addLayout(btn_layout)
        left.setLayout(left_layout)
        left.setMaximumWidth(300)
        
        # Editor
        self.editor = QuestionEditor(self)
        
        # Preview panel
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        # Preview header
        self.preview_label = QLabel(translator.t('preview_label'))
        
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setMinimumWidth(150)
        
        preview_layout.addWidget(self.preview_label)
        preview_layout.addWidget(self.preview)
        
        self.splitter.addWidget(left)
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(preview_widget)
        
        # Set initial splitter sizes: [questions=300, editor=flexible, preview=250]
        self.splitter.setSizes(SPLITTER_SIZES)
        layout.addWidget(self.splitter)
        
        self.setLayout(layout)
        self.refresh_display()

    def on_title_changed(self):
        self.form.title = self.title_input.text()
        self.refresh_display()

    def on_instructions_changed(self):
        self.form.instructions = self.instructions_input.text()
        self.refresh_display()

    def add_question(self):
        question = Question()
        question.text = f"{translator.t('default_question')} {len(self.form.questions) + 1}"
        question.options = [
            translator.t('default_option_a'), 
            translator.t('default_option_b'), 
            translator.t('default_option_c'), 
            translator.t('default_option_d')
        ]
        self.form.questions.append(question)
        self.update_question_list()
        self.questions_list.setCurrentRow(len(self.form.questions) - 1)

    def delete_question(self):
        row = self.questions_list.currentRow()
        if 0 <= row < len(self.form.questions):
            del self.form.questions[row]
            self.update_question_list()
            if self.form.questions:
                self.questions_list.setCurrentRow(min(row, len(self.form.questions) - 1))
            else:
                self.editor.clear()
            self.refresh_display()

    def on_question_selected(self, row: int):
        if 0 <= row < len(self.form.questions):
            self.editor.load_question(self.form.questions[row])
        else:
            self.editor.load_question(None)
        self.refresh_display()

    def update_question_list(self):
        current = self.questions_list.currentRow()
        self.questions_list.clear()
        for i, q in enumerate(self.form.questions):
            text = q.text if q.text else translator.t('no_text')
            text = text[:PREVIEW_TEXT_TRUNCATE_LENGTH] + "..." if len(text) > PREVIEW_TEXT_TRUNCATE_LENGTH else text
            self.questions_list.addItem(f"Q{i+1}: {text} ({q.points}pt)")
        if 0 <= current < len(self.form.questions): self.questions_list.setCurrentRow(current)

    def update_preview(self):
        text = f"{translator.t('preview_title')}: {self.form.title}\n{translator.t('preview_instructions')}: {self.form.instructions}\n\n"
        for i, q in enumerate(self.form.questions):
            text += f"Q{i+1}: {q.text}\n"
            for j, opt in enumerate(q.options):
                marker = "*" if j == q.correct else " "
                text += f"  {marker} {get_option_letter(j)}. {opt}\n"
            text += f"  {translator.t('preview_points')}: {q.points}\n\n"
        self.preview.setPlainText(text)

    def update_validation(self):
        summary = self.form.get_validation_summary()
        self.validation_changed.emit(summary)

    def refresh_display(self):
        """Combined method to update both preview and validation"""
        self.update_preview()
        self.update_validation()

    def show_validation_details(self):
        summary = self.form.get_validation_summary()
        
        # Create a custom resizable dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(translator.t('validation_title'))
        dialog.setMinimumSize(450, 250)
        
        layout = QVBoxLayout()
        
        # Icon and main message
        header_layout = QHBoxLayout()
        
        # Icon label
        icon_label = QLabel()
        if summary["status"] == "valid":
            icon_label.setText("ℹ️")  # Info icon
        elif summary["status"] == "warning":
            icon_label.setText("⚠️")  # Warning icon
        else:
            icon_label.setText("❌")  # Error icon
        icon_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        icon_label.setFixedSize(30, 30)
        header_layout.addWidget(icon_label)
        
        # Main message
        message_label = QLabel()
        if summary["status"] == "valid":
            message_label.setText(translator.t('form_valid'))
        else:
            message_label.setText(summary["message"])
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        header_layout.addWidget(message_label)
        
        layout.addLayout(header_layout)
        
        # Details text area (if there are errors)
        if summary["status"] != "valid" and summary["errors"]:
            details_label = QLabel(translator.t('details_label'))
            details_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            layout.addWidget(details_label)
            
            details_text = QTextEdit()
            error_text = "\n".join([f"• {e}" for e in summary["errors"]])
            details_text.setPlainText(error_text)
            details_text.setReadOnly(True)
            
            # Calculate dynamic height based on content
            doc = details_text.document()
            doc.setTextWidth(450)  # Set width to calculate proper height
            content_height = int(doc.size().height())
            
            # Set height with constraints: minimum 60px, maximum 300px
            min_height = 60
            max_height = 300
            optimal_height = max(min_height, min(content_height + 20, max_height))  # +20 for padding
            
            details_text.setFixedHeight(optimal_height)
            layout.addWidget(details_text)
        
        # OK button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        ok_button = QPushButton(translator.t('ok_button'))
        ok_button.clicked.connect(dialog.accept)
        ok_button.setDefault(True)
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        # Adjust dialog size based on content
        dialog.adjustSize()
        
        # Ensure dialog isn't too large
        screen_size = dialog.screen().availableGeometry()
        max_width = min(600, screen_size.width() - 100)
        max_height = min(500, screen_size.height() - 100)
        
        current_size = dialog.size()
        new_width = min(current_size.width(), max_width)
        new_height = min(current_size.height(), max_height)
        dialog.resize(new_width, new_height)
        
        dialog.exec()

    def _msg(self, type, text): UIHelpers.show_message(self, type, translator.t(type), text)
    
    def _handle_file_error(self, error: Exception, operation_key: str):
        """Common error handler for file operations"""
        msg = f"{translator.t(operation_key)} "
        if isinstance(error, PermissionError): msg += "Permission denied. Check file permissions."
        elif isinstance(error, OSError): msg += f"Disk error: {str(error)}"
        elif isinstance(error, json.JSONDecodeError): msg += f"Invalid JSON format: {str(error)}"
        elif isinstance(error, FileNotFoundError): msg += "File not found."
        else: msg += str(error)
        self._msg("error", msg)

    def save_form(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Form", "", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.form.to_dict(), f, indent=2, ensure_ascii=False)
                self._msg("success", translator.t('form_saved'))
            except Exception as e:
                self._handle_file_error(e, 'save_failed')

    def load_form(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Form", "", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.form = Form.from_dict(data)
                self.title_input.setText(self.form.title)
                self.instructions_input.setText(self.form.instructions)
                self.update_question_list()
                if self.form.questions:
                    self.questions_list.setCurrentRow(0)
                self.refresh_display()
                self._msg("success", translator.t('form_loaded'))
            except Exception as e:
                self._handle_file_error(e, 'load_failed')

    def import_questions(self):
        dialog = ImportDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.clear_existing_cb.isChecked():
                self.form.questions.clear()
            self.form.questions.extend(dialog.imported_questions)
            self.update_question_list()
            if self.form.questions:
                self.questions_list.setCurrentRow(len(self.form.questions) - 1)
            self.refresh_display()
            self._msg("success", f"{len(dialog.imported_questions)} {translator.t('questions_imported')}")

    def export_pdf(self):
        if not self._check_export():
            return
        filename, _ = QFileDialog.getSaveFileName(self, translator.t('menu_export_pdf'), f"{self.form.title}.pdf", "PDF Files (*.pdf)")
        if filename:
            try:
                self._generate_pdf(filename)
                self._msg("success", translator.t('pdf_exported'))
            except Exception as e:
                self._handle_file_error(e, 'export_failed')

    def export_omr_sheet(self):
        if not self._check_export():
            return
        filename, _ = QFileDialog.getSaveFileName(self, translator.t('menu_export_omr'), f"{self.form.title}_sheet.pdf", "PDF Files (*.pdf)")
        if filename:
            try:
                self._generate_omr_sheet(filename)
                self._msg("success", translator.t('omr_exported'))
            except Exception as e:
                self._handle_file_error(e, 'export_failed')

    def export_for_scanner(self):
        if not self.form.questions:
            QMessageBox.warning(self, translator.t('warning'), translator.t('no_questions_export'))
            return
        
        filename, _ = QFileDialog.getSaveFileName(self, "Export for Scanner", f"{self.form.title.replace(' ', '_')}.omr", "OMR Files (*.omr)")
        if filename:
            try:
                data = {
                    "format_version": "1.0",
                    "generator": "OMR Form Designer v1.0",
                    "generated_date": datetime.now().isoformat(),
                    "metadata": {
                        "form_id": f"FORM_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        "title": self.form.title,
                        "total_questions": len(self.form.questions),
                        "total_points": sum(q.points for q in self.form.questions)
                    },
                    "layout": {"page_size": "Letter", "orientation": "portrait", "bubble_style": "circle"},
                    "questions": [{"id": i+1, "text": q.text, "options": q.options, "correct_answer": q.correct, "points": q.points} for i, q in enumerate(self.form.questions)],
                    "answer_key": {str(i+1): q.correct for i, q in enumerate(self.form.questions)},
                    "grading_config": {"scoring_method": "points", "penalty_wrong": 0.25, "penalty_blank": 0}
                }
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                self._msg("success", f"{translator.t('exported_scanner')} {filename}")
            except Exception as e:
                self._msg("error", f"{translator.t('export_failed')} {str(e)}")

    def _check_export(self) -> bool:
        summary = self.form.get_validation_summary()
        if summary["status"] == "invalid":
            self._msg("error", translator.t('critical_errors'))
            return False
        return True

    def _generate_pdf(self, filename: str):
        doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=PDF_MARGINS['right']*inch, leftMargin=PDF_MARGINS['left']*inch, topMargin=PDF_MARGINS['top']*inch, bottomMargin=PDF_MARGINS['bottom']*inch)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=FONT_SIZES['title'], fontName=FONT, spaceAfter=12, alignment=1)
        story.append(Paragraph(str(self.form.title).replace('<', '&lt;').replace('>', '&gt;'), title_style))
        story.append(Spacer(1, 12))
        
        # Instructions
        if self.form.instructions:
            inst_style = ParagraphStyle('Instructions', parent=styles['Normal'], fontSize=FONT_SIZES['normal'], fontName=FONT, spaceAfter=18, alignment=1)
            story.append(Paragraph(self.form.instructions, inst_style))
            story.append(Spacer(1, 18))
        
        # Questions
        for i, q in enumerate(self.form.questions):
            elements = []
            q_style = ParagraphStyle('Question', parent=styles['Normal'], fontSize=FONT_SIZES['normal'], fontName=FONT, spaceAfter=8)
            elements.append(Paragraph(f"{i+1}. {q.text}", q_style))
            
            options = [[f"○ {get_option_letter(j)}.", opt] for j, opt in enumerate(q.options)]
            table = Table(options, colWidths=[0.5*inch, 5.5*inch])
            table.setStyle(TableStyle([
                ('FONTNAME', (0,0), (-1,-1), FONT),
                ('FONTSIZE', (0,0), (-1,-1), 11),
                ('LEFTPADDING', (0,0), (0,-1), 20),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ]))
            elements.append(table)
            
            story.append(KeepTogether(elements))
            if i < len(self.form.questions) - 1:  # Don't add spacer after last question
                story.append(Spacer(1, 18))
        
        doc.build(story)

    def _generate_omr_sheet(self, filename: str):
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        
        y = self._draw_omr_header(c, width, height)
        y = self._draw_student_info_section(c, width, y)
        y = self._draw_instructions_section(c, width, y)
        self._draw_questions_section(c, width, height, y)
        self._draw_omr_footer(c, width)
        
        c.save()

    def _draw_omr_header(self, c, width, height):
        """Draw the OMR sheet header with title and answer sheet label"""
        c.setFont(FONT, FONT_SIZES['title'])
        c.drawCentredString(width/2, height - 0.8*inch, self.form.title)
        c.setFont(FONT, FONT_SIZES['normal'] + 2)
        c.drawCentredString(width/2, height - 1.1*inch, translator.t('answer_sheet'))
        
        # Draw header separator line
        c.line(0.75*inch, height - 1.3*inch, width - 0.75*inch, height - 1.3*inch)
        
        return height - 1.7*inch

    def _draw_student_info_section(self, c, width, y):
        """Draw student name and ID fields with proper alignment"""
        c.setFont(FONT, FONT_SIZES['normal'] - 1)
        
        # Name field with aligned underline
        name_text = translator.t('student_name')
        name_x = 0.75*inch
        c.drawString(name_x, y, name_text)
        name_width = c.stringWidth(name_text, FONT, FONT_SIZES['normal'] - 1)
        c.line(name_x + name_width + 0.1*inch, y - 3, 4.5*inch, y - 3)
        
        # Student ID field with aligned underline  
        id_text = translator.t('student_id')
        id_x = 4.8*inch
        c.drawString(id_x, y, id_text)
        id_width = c.stringWidth(id_text, FONT, FONT_SIZES['normal'] - 1)
        c.line(id_x + id_width + 0.1*inch, y - 3, 7.5*inch, y - 3)
        
        return y - 0.4*inch

    def _draw_instructions_section(self, c, width, y):
        """Draw instructions for filling out the OMR sheet"""
        c.setFont(FONT, FONT_SIZES['instruction'])
        c.drawString(0.75*inch, y, translator.t('omr_instruction1'))
        y -= 0.2*inch
        c.drawString(0.75*inch, y, translator.t('omr_instruction2'))
        
        # Main separator line
        y -= 0.3*inch
        c.line(0.75*inch, y, width - 0.75*inch, y)
        
        return y - 0.5*inch

    def _draw_questions_section(self, c, width, height, y):
        """Draw all questions with bubbles and handle pagination"""
        min_bottom_margin = MIN_BOTTOM_MARGIN*inch
        question_height = QUESTION_HEIGHT*inch
        
        for i, q in enumerate(self.form.questions):
            # Check if we need a new page
            if y - question_height < min_bottom_margin:
                c.showPage()
                y = self._draw_continuation_header(c, width, height)
            
            y = self._draw_single_question(c, i, y, question_height)

    def _draw_continuation_header(self, c, width, height):
        """Draw header for continuation pages"""
        c.setFont(FONT, FONT_SIZES['header'])
        c.drawCentredString(width/2, height - 0.5*inch, f"{self.form.title} ({translator.t('continued')})")
        c.line(0.75*inch, height - 0.7*inch, width - 0.75*inch, height - 0.7*inch)
        return height - 1.2*inch

    def _draw_single_question(self, c, question_index, y, question_height):
        """Draw a single question with its bubbles"""
        # Question number
        c.setFont(FONT, FONT_SIZES['normal'])
        question_num = f"{question_index+1}."
        c.drawRightString(1.1*inch, y + 2, question_num)
        
        # Answer bubbles
        bubble_radius = BUBBLE_RADIUS
        bubble_spacing = BUBBLE_SPACING*inch
        start_x = 1.3*inch
        
        for j in range(MAX_OPTIONS_COUNT):
            x = start_x + j * bubble_spacing
            
            # Draw bubble circle
            c.circle(x, y + 5, bubble_radius, fill=0, stroke=1)
            
            # Draw option letter below bubble
            c.setFont(FONT, FONT_SIZES['instruction'])
            c.drawCentredString(x, y - 0.25*inch, get_option_letter(j))
        
        return y - question_height

    def _draw_omr_footer(self, c, width):
        """Draw footer with question and point totals"""
        c.setFont(FONT, FONT_SIZES['small'])
        footer_text = f"{translator.t('total_questions')} {len(self.form.questions)} | {translator.t('total_points')} {sum(q.points for q in self.form.questions)}"
        c.drawCentredString(width/2, 0.5*inch, footer_text)

    def refresh_ui(self):
        """Refresh UI elements with current language"""
        # Update form defaults if they contain default values
        if self.form.title in ["New Form", "Νέα Φόρμα"]:
            self.form.title = translator.t('default_form_title')
            self.title_input.setText(self.form.title)
        
        if self.form.instructions in ["Select the best answer for each question.", "Επιλέξτε την καλύτερη απάντηση για κάθε ερώτηση."]:
            self.form.instructions = translator.t('default_instructions')
            self.instructions_input.setText(self.form.instructions)
        
        # Update UI labels
        self.title_label.setText(translator.t('title_label'))
        self.instructions_label.setText(translator.t('instructions_label'))
        self.preview_label.setText(translator.t('preview_label'))
        
        # Update button texts
        if hasattr(self, 'add_question_btn'):
            self.add_question_btn.setText(translator.t('add_button'))
        if hasattr(self, 'delete_question_btn'):
            self.delete_question_btn.setText(translator.t('delete_button'))
        
        # Refresh the question editor to update option letters
        if hasattr(self, 'editor'):
            self.editor.refresh_option_letters()
        
        self.update_question_list()
        self.refresh_display()

class SignalBlocker:
    """Context manager for blocking multiple widget signals"""
    def __init__(self, *widgets):
        self.widgets = widgets
    
    def __enter__(self):
        for widget in self.widgets:
            widget.blockSignals(True)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for widget in self.widgets:
            widget.blockSignals(False)

class OMRFormDesigner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dark_mode = False
        self.current_validation_summary = {"status": "valid", "message": "", "errors": []}
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle(translator.t('app_title'))
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        self.setStyleSheet(get_styles(self.dark_mode))
        
        self.form_designer = FormDesigner()
        self.setCentralWidget(self.form_designer)
        
        self.create_menu()
        self.create_status_bar()

    def create_menu(self):
        self.menubar = self.menuBar()
        self.refresh_menu()

    def refresh_menu(self):
        """Refresh menu with current language"""
        self.menubar.clear()
        
        # File menu
        file_menu = self.menubar.addMenu(translator.t('menu_file'))
        
        new_action = file_menu.addAction(translator.t('menu_new'))
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_file)
        
        load_action = file_menu.addAction(translator.t('menu_load'))
        load_action.setShortcut('Ctrl+O')
        load_action.triggered.connect(self.form_designer.load_form)
        
        save_action = file_menu.addAction(translator.t('menu_save'))
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.form_designer.save_form)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction(translator.t('menu_exit'))
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        
        # Export menu
        export_menu = self.menubar.addMenu(translator.t('menu_export'))
        
        pdf_action = export_menu.addAction(translator.t('menu_export_pdf'))
        pdf_action.setShortcut('Ctrl+E')
        pdf_action.triggered.connect(self.form_designer.export_pdf)
        
        omr_action = export_menu.addAction(translator.t('menu_export_omr'))
        omr_action.setShortcut('Ctrl+Shift+E')
        omr_action.triggered.connect(self.form_designer.export_omr_sheet)
        
        scanner_action = export_menu.addAction(translator.t('menu_export_scanner'))
        scanner_action.setShortcut('Ctrl+Alt+E')
        scanner_action.triggered.connect(self.form_designer.export_for_scanner)
        
        # Import menu
        import_menu = self.menubar.addMenu(translator.t('menu_import'))
        
        import_action = import_menu.addAction(translator.t('menu_import_csv'))
        import_action.setShortcut('Ctrl+I')
        import_action.triggered.connect(self.form_designer.import_questions)
        
        # Language menu
        language_menu = self.menubar.addMenu(translator.t('menu_language'))
        
        english_action = language_menu.addAction(translator.t('menu_english'))
        english_action.triggered.connect(lambda: self.change_language('en'))
        
        greek_action = language_menu.addAction(translator.t('menu_greek'))
        greek_action.triggered.connect(lambda: self.change_language('el'))

    def create_status_bar(self):
        self.status_bar = self.statusBar()
        self.validation_label = QLabel(translator.t('form_validation_valid'))
        self.validation_label.setStyleSheet("color: #2f7d32; font-weight: bold; padding: 4px;")
        self.validation_label.mousePressEvent = lambda event: self.show_validation_details(event)
        
        self.status_bar.addWidget(self.validation_label)
        
        # Theme toggle label
        self.theme_label = QLabel(translator.t('theme_light_mode'))
        self.theme_label.setStyleSheet("color: #6b7280; font-weight: bold; padding: 4px; text-decoration: underline;")
        self.theme_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_label.setToolTip(translator.t('theme_tooltip'))
        self.theme_label.mousePressEvent = lambda event: self.toggle_theme(event)
        self.status_bar.addPermanentWidget(self.theme_label)
        
        self.form_designer.validation_changed.connect(self.update_validation)

    def update_validation(self, summary: Dict[str, Any]):
        self.current_validation_summary = summary
        if summary["status"] == "valid":
            self.validation_label.setText(translator.t('form_validation_valid'))
            self.validation_label.setStyleSheet("color: #2f7d32; font-weight: bold; padding: 4px;")
            self.validation_label.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.validation_label.setText(f"⚠ {summary['message']} {translator.t('click_details')}")
            color = "#c62828" if summary["status"] == "invalid" else "#f57c00"
            self.validation_label.setStyleSheet(f"color: {color}; font-weight: bold; padding: 4px; text-decoration: underline;")
            self.validation_label.setCursor(Qt.CursorShape.PointingHandCursor)

    def new_file(self):
        if QMessageBox.question(self, translator.t('menu_new'), translator.t('new_form_confirm')) == QMessageBox.StandardButton.Yes:
            self.form_designer.form = Form()
            self.form_designer.form.title = translator.t('default_form_title')
            self.form_designer.form.instructions = translator.t('default_instructions')
            self.form_designer.title_input.setText(translator.t('default_form_title'))
            self.form_designer.instructions_input.setText(translator.t('default_instructions'))
            self.form_designer.update_question_list()
            self.form_designer.update_preview()
            self.form_designer.update_validation()

    def show_validation_details(self, event=None):
        """Show validation details when label is clicked"""
        if self.current_validation_summary["status"] != "valid":
            self.form_designer.show_validation_details()

    def toggle_theme(self, event=None):
        """Toggle between dark and light mode"""
        self.dark_mode = not self.dark_mode
        self.setStyleSheet(get_styles(self.dark_mode))
        if self.dark_mode:
            self.theme_label.setText(translator.t('theme_dark_mode'))
            self.theme_label.setStyleSheet("color: #94a3b8; font-weight: bold; padding: 4px; text-decoration: underline;")
        else:
            self.theme_label.setText(translator.t('theme_light_mode'))
            self.theme_label.setStyleSheet("color: #6b7280; font-weight: bold; padding: 4px; text-decoration: underline;")

    def change_language(self, lang_code: str):
        """Change the application language"""
        translator.set_language(lang_code)
        
        # Update window title
        self.setWindowTitle(translator.t('app_title'))
        
        # Refresh menu
        self.refresh_menu()
        
        # Update status bar
        self.validation_label.setText(translator.t('form_validation_valid'))
        self.theme_label.setText(translator.t('theme_dark_mode') if self.dark_mode else translator.t('theme_light_mode'))
        self.theme_label.setToolTip(translator.t('theme_tooltip'))
        
        self.form_designer.refresh_ui()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("OMR Form Designer")
    window = OMRFormDesigner()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
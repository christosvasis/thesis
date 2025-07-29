#!/usr/bin/env python3
"""
OMR Unified Application - Clean Version
Combined Form Designer and Scanner with all original functionality preserved
"""

import sys
import json
import os
import csv
import io
import platform
from datetime import datetime
from typing import List, Dict, Any, Optional, NamedTuple, Tuple

# Optional imports with availability flags
try:
    import pandas as pd
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import fitz
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from PIL import Image, ImageDraw
import numpy as np

from PyQt6.QtCore import Qt, pyqtSignal, QThread, QPoint
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPixmap, QFont, QWheelEvent, QMouseEvent, QPainter, QImage

# Application Constants
class AppConfig:
    """Central configuration for the OMR application"""
    
    # Form Design Constants
    MAX_OPTIONS_COUNT = 4
    DEFAULT_POINTS_RANGE = 10
    PREVIEW_TEXT_TRUNCATE_LENGTH = 40
    
    # PDF Generation Constants
    PDF_MARGINS = {'right': 0.75, 'left': 0.75, 'top': 1.0, 'bottom': 1.0}
    FONT_SIZES = {'title': 18, 'header': 16, 'normal': 12, 'instruction': 10, 'small': 8}
    QUESTION_HEIGHT = 0.6
    MIN_BOTTOM_MARGIN = 1.0
    
    # Bubble Detection Constants
    BUBBLE_RADIUS = 10
    BUBBLE_SPACING = 0.8
    ANALYSIS_RADIUS = 18
    FILLED_THRESHOLD = 0.3
    
    # UI Layout Constants
    SPLITTER_SIZES = [300, 600, 250]
    TABLE_HEADER_HEIGHT = 40
    COLUMN_WIDTHS = {
        'student_name': 150,
        'student_id': 100,
        'score': 80,
        'total': 80,
        'percentage': 100
    }
    
    # File Format Constants
    SUPPORTED_IMAGE_FORMATS = ['*.png', '*.jpg', '*.jpeg', '*.tiff', '*.bmp']
    SUPPORTED_DOCUMENT_FORMATS = ['*.pdf']
    
    # Font Configuration
    FONT_PATHS = {
        "Darwin": ["/System/Library/Fonts/Geneva.ttf", "/Library/Fonts/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"],
        "Linux": ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/TTF/arial.ttf"],
        "Windows": ["C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/Arial.ttf", "C:/Windows/Fonts/calibri.ttf"]
    }

# Legacy constants for backward compatibility
MAX_OPTIONS_COUNT = AppConfig.MAX_OPTIONS_COUNT
DEFAULT_POINTS_RANGE = AppConfig.DEFAULT_POINTS_RANGE
BUBBLE_RADIUS = AppConfig.BUBBLE_RADIUS
BUBBLE_SPACING = AppConfig.BUBBLE_SPACING
MIN_BOTTOM_MARGIN = AppConfig.MIN_BOTTOM_MARGIN
QUESTION_HEIGHT = AppConfig.QUESTION_HEIGHT
PREVIEW_TEXT_TRUNCATE_LENGTH = AppConfig.PREVIEW_TEXT_TRUNCATE_LENGTH
SPLITTER_SIZES = AppConfig.SPLITTER_SIZES
PDF_MARGINS = AppConfig.PDF_MARGINS
FONT_SIZES = AppConfig.FONT_SIZES

def get_font():
    """Get Unicode-compatible font using configured paths"""
    
    try:
        for path in AppConfig.FONT_PATHS.get(platform.system(), []):
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

def get_color_scheme(dark_mode=False):
    """Get color scheme for themes"""
    if dark_mode:
        return {
            'bg': '#0f172a', 'panel': '#1e293b', 'text': '#e2e8f0', 'border': '#334155',
            'input_border': '#475569', 'hover': '#334155', 'accent': '#3b82f6',
            'button_bg': '#1e293b', 'button_hover': '#334155', 'input_bg': '#1e293b'
        }
    else:
        return {
            'bg': '#f7f9fc', 'panel': '#ffffff', 'text': '#1f2937', 'border': '#d1d5db',
            'input_border': '#9ca3af', 'hover': '#e5e7eb', 'accent': '#2563eb',
            'button_bg': '#f9fafb', 'button_hover': '#f3f4f6', 'input_bg': '#ffffff',
            'secondary_text': '#6b7280', 'success': '#059669', 'warning': '#d97706', 'danger': '#dc2626'
        }

def get_styles(dark_mode=False):
    """Generate complete stylesheet"""
    c = get_color_scheme(dark_mode)
    
    return f"""
QMainWindow{{background:{c['bg']};color:{c['text']};font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:13px}}
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
QStatusBar{{background:{c['panel']};color:{c['text']};border-top:1px solid {c['border']}}}
QDoubleSpinBox,QSpinBox{{background:{c.get('input_bg',c['panel'])};color:{c['text']};border:1px solid {c['input_border']};border-radius:4px;padding:4px 8px;min-height:20px}}
QScrollArea{{background:{c['panel']};border:1px solid {c['border']};border-radius:4px}}
QScrollBar:vertical{{background:{c['bg']};width:10px;border-radius:5px}}
QScrollBar::handle:vertical{{background:{c['hover']};border-radius:5px;min-height:20px}}
QScrollBar::handle:vertical:hover{{background:{c['accent']}}}
QTableWidget{{background:{c['panel']};color:{c['text']};border:1px solid {c['border']};border-radius:4px;gridline-color:{c['border']}}}
QTableWidget::item{{padding:4px 8px;border-bottom:1px solid {c['border']}}}
QTableWidget::item:selected{{background:{c['accent']};color:white}}
QTableWidget QHeaderView::section{{background:{c['bg']};color:{c['text']};border:1px solid {c['border']};padding:4px 8px}}
QCheckBox{{color:{c['text']}}}
QCheckBox::indicator{{width:16px;height:16px;border:1px solid {c['input_border']};border-radius:3px;background:{c.get('input_bg',c['panel'])}}}
QCheckBox::indicator:checked{{background:{c['accent']};color:white}}""".strip()

class FileManager:
    """Centralized file operations and dialog handling"""
    
    @staticmethod
    def get_supported_formats():
        """Get supported file formats string for dialogs"""
        image_formats = " ".join(AppConfig.SUPPORTED_IMAGE_FORMATS)
        if PDF_AVAILABLE:
            doc_formats = " ".join(AppConfig.SUPPORTED_DOCUMENT_FORMATS)
            return f"All Files ({doc_formats} {image_formats})"
        return f"Images ({image_formats})"
    
    @staticmethod
    def get_safe_filename(file_path: str) -> str:
        """Get normalized, safe filename from path"""
        return os.path.basename(os.path.normpath(file_path)) if file_path else ""
    
    @staticmethod
    def open_file_dialog(parent, title: str, file_filter: str = None):
        """Open file dialog with platform-specific optimizations"""
        if file_filter is None:
            file_filter = FileManager.get_supported_formats()
        
        options = QFileDialog.Option.DontUseNativeDialog if platform.system() == "Linux" else QFileDialog.Option(0)
        return QFileDialog.getOpenFileName(parent, title, "", file_filter, options=options)
    
    @staticmethod
    def save_file_dialog(parent, title: str, file_filter: str, default_suffix: str = ""):
        """Save file dialog with platform-specific optimizations"""
        options = QFileDialog.Option.DontUseNativeDialog if platform.system() == "Linux" else QFileDialog.Option(0)
        return QFileDialog.getSaveFileName(parent, title, "", file_filter, options=options)

class TableManager:
    """Utility class for table configuration and styling"""
    
    @staticmethod
    def configure_students_table(table: QTableWidget):
        """Apply standard configuration to students table"""
        table.setColumnCount(6)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        
        # Configure header
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        
        # Set column widths
        header.resizeSection(0, AppConfig.COLUMN_WIDTHS['student_name'])
        header.resizeSection(1, AppConfig.COLUMN_WIDTHS['student_id'])
        header.resizeSection(2, AppConfig.COLUMN_WIDTHS['score'])
        header.resizeSection(3, AppConfig.COLUMN_WIDTHS['total'])
        header.resizeSection(4, AppConfig.COLUMN_WIDTHS['percentage'])
        
        # Style header
        header_font = QFont()
        header_font.setPointSize(11)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setDefaultSectionSize(80)
        header.setMinimumSectionSize(60)
        header.setFixedHeight(AppConfig.TABLE_HEADER_HEIGHT)
    
    @staticmethod
    def get_translated_headers():
        """Get translated table headers"""
        headers = [
            translator.t('student_name_field').replace(':', ''),
            translator.t('student_id_field').replace(':', ''),
            translator.t('score_label').replace(':', ''),
            translator.t('total_label').replace(':', ''),
            translator.t('percentage_label').replace(':', ''),
            translator.t('grade_label').replace(':', '')
        ]
        
        # Fallback system
        fallback_headers = ["Name", "ID", "Score", "Total", "Percentage", "Grade"]
        return [h.strip() if h.strip() else fallback_headers[i] for i, h in enumerate(headers)]

class ErrorHandler:
    """Centralized error handling and user feedback"""
    
    @staticmethod
    def show_error(parent, title: str, message: str, details: str = None):
        """Show error dialog with optional details"""
        msg_box = QMessageBox.critical(parent, title, message)
        if details:
            msg_box.setDetailedText(details)
        return msg_box
    
    @staticmethod
    def show_warning(parent, title: str, message: str):
        """Show warning dialog"""
        return QMessageBox.warning(parent, title, message)
    
    @staticmethod
    def show_info(parent, title: str, message: str):
        """Show information dialog"""
        return QMessageBox.information(parent, title, message)
    
    @staticmethod
    def handle_file_error(parent, operation: str, file_path: str, error: Exception):
        """Handle file operation errors with user-friendly messages"""
        filename = FileManager.get_safe_filename(file_path)
        title = f"File {operation.title()} Error"
        message = f"Failed to {operation} file: {filename}"
        details = f"Error details: {str(error)}\nFile path: {file_path}"
        ErrorHandler.show_error(parent, title, message, details)
    
    @staticmethod
    def safe_execute(func, error_callback=None, *args, **kwargs):
        """Safely execute a function with error handling"""
        try:
            return func(*args, **kwargs), None
        except Exception as e:
            if error_callback:
                error_callback(e)
            return None, e

class UIHelpers:
    """Helper methods for creating UI elements"""
    
    @staticmethod
    def create_button(text: str, style_class: Optional[str] = None, callback=None, tooltip: Optional[str] = None) -> QPushButton:
        btn = QPushButton(text)
        if style_class: 
            btn.setProperty("class", style_class)
        if callback: 
            btn.clicked.connect(callback)
        if tooltip: 
            btn.setToolTip(tooltip)
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
        icons = {
            "success": QMessageBox.Icon.Information, 
            "error": QMessageBox.Icon.Critical, 
            "warning": QMessageBox.Icon.Warning
        }
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
    """Multi-language translation system"""
    
    def __init__(self):
        self.current_language = 'en'
        self.translations = self._initialize_translations()
    
    def _initialize_translations(self):
        """Initialize translation dictionaries"""
        en = {
            'app_title': 'OMR Unified Application', 'form_validation_valid': 'Form is valid', 
            'theme_light_mode': '🌙 Light Mode', 'theme_dark_mode': '🌞 Dark Mode', 
            'theme_tooltip': 'Click to toggle Dark/Light Mode',
            'menu_file': 'File', 'menu_new': 'New', 'menu_load': 'Load', 'menu_save': 'Save', 
            'menu_exit': 'Exit', 'menu_export': 'Export', 'menu_export_pdf': 'Export PDF', 
            'menu_export_omr': 'Export OMR Sheet', 'menu_export_scanner': 'Export for Scanner', 
            'menu_import': 'Import', 'menu_import_csv': 'Import CSV/Excel', 'menu_language': 'Language', 
            'menu_english': 'English', 'menu_greek': 'Ελληνικά',
            'title_label': 'Title:', 'instructions_label': 'Instructions:', 'preview_label': 'Preview', 
            'questions_panel': 'Questions', 'question_text_label': 'Question Text', 
            'answer_options_label': 'Answer Options', 'correct_label': 'Correct:', 'points_label': 'Points:', 
            'add_button': 'Add', 'delete_button': 'Delete', 'option': 'Option', 'preview_title': 'Title', 
            'preview_instructions': 'Instructions', 'preview_points': 'Points',
            'default_form_title': 'New Form', 'default_instructions': 'Select the best answer for each question.', 
            'default_option_a': 'Option A', 'default_option_b': 'Option B', 'default_option_c': 'Option C', 
            'default_option_d': 'Option D', 'default_question': 'Question', 'no_text': 'No text',
            'import_title': 'Import Questions', 
            'import_expected': 'Expected: Question, Option A, Option B, Option C, Option D, Correct Answer, Points', 
            'import_file_placeholder': 'Select CSV or Excel file...', 'browse_button': 'Browse', 
            'has_headers': 'First row contains headers', 'clear_existing': 'Clear existing questions', 
            'cancel_button': 'Cancel', 'import_button': 'Import',
            'success': 'Success', 'error': 'Error', 'warning': 'Warning', 'form_saved': 'Form saved!', 
            'form_loaded': 'Form loaded!', 'pdf_exported': 'PDF exported!', 'omr_exported': 'OMR sheet exported!', 
            'questions_imported': 'questions imported!', 'export_failed': 'Export failed:', 
            'save_failed': 'Save failed:', 'load_failed': 'Load failed:', 
            'critical_errors': 'Form has critical errors. Fix them first.', 
            'no_questions_export': 'No questions to export', 'exported_scanner': 'Exported for scanner:', 
            'new_form_confirm': 'Create new form? Unsaved changes will be lost.',
            'validation_title': 'Validation', 'form_valid': 'Form is valid!', 'issues_found': 'issue(s) found', 
            'click_details': '(click for details)', 'details_label': 'Details:', 'ok_button': 'OK',
            'answer_sheet': 'ANSWER SHEET', 'student_name': 'Name:', 'student_id': 'Student ID:', 
            'omr_instruction1': '• Fill in bubbles completely with dark pencil or pen', 
            'omr_instruction2': '• Make no stray marks on this sheet', 'total_questions': 'Total Questions:', 
            'total_points': 'Total Points:', 'continued': 'continued',
            'tab_designer': 'Form Designer', 'tab_scanner': 'Scanner', 'tab_grading': 'Grading & Reports',
            # Scanner translations
            'scanner_title': '🎯 OMR Scanner', 'step1_load': '1️⃣ Load Image', 'step2_process': '2️⃣ Process', 
            'step3_answer_key': '3️⃣ Answer Key', 'load_image_pdf': '📁 Load Image/PDF', 'no_image_loaded': 'No image loaded',
            'detect_analyze': '🔍 Detect & Analyze', 'load_omr_file': '📄 Load .omr File', 'no_answer_key': 'No answer key loaded',
            'settings_title': '⚙️ Settings', 'filled_threshold': 'Filled Threshold:', 'results_title': '📊 Results',
            'view_title': '👁️ View', 'show_positions': 'Show Positions', 'show_results': 'Show Results',
            'zoom_in': '🔍+', 'zoom_out': '🔍-', 'zoom_fit': '🖼️ Fit', 'zoom_100': '📏 100%', 'zoom_reset': '🔄 Reset',
            'no_image': 'No image', 'zoom_pan_info': '💡 Mouse wheel: Zoom | Middle-click/Ctrl+drag: Pan',
            'load_image_title': 'Load Image', 'detecting_anchors': '🔄 Detecting anchors...', 
            'anchors_detected': '✅ {0}', 'anchor_detection_failed': '❌ {0}', 'opencv_missing': 'Missing Dependency',
            'opencv_install': 'OpenCV not available. Install with:\npip install opencv-python',
            'load_answer_key': 'Load Answer Key', 'analyzing_bubbles': '🔄 Analyzing bubbles...',
            'analysis_complete': '✅ Analysis complete', 'analysis_failed': '❌ Analysis failed',
            'analysis_complete_text': '📊 ANALYSIS COMPLETE\nAnswered: {0}/{1}\n\n', 'question_prefix': 'Q{0}: {1}\n',
            'blank_answer': '(blank)', 'load_image_error': 'Failed to load image:\n{0}',
            # Grading and reporting
            'grading_title': '📋 Grading & Reports', 'student_info': 'Student Information',
            'student_name_field': 'Student Name:', 'student_id_field': 'Student ID:', 'grade_sheet': 'Grade Sheet',
            'export_results': 'Export Results', 'export_csv': '📊 Export CSV', 'export_excel': '📈 Export Excel',
            'export_pdf_report': '📄 Export PDF Report', 'calculate_grade': 'Calculate Grade',
            'score_label': 'Score:', 'percentage_label': 'Percentage:', 'grade_label': 'Grade:',
            'total_label': 'Total:',
            'correct_answers': 'Correct: {0}', 'incorrect_answers': 'Incorrect: {0}', 'blank_answers': 'Blank: {0}',
            'total_points': 'Total Points: {0}/{1}', 'statistics_title': 'Statistics',
            'question_analysis': 'Question Analysis', 'export_success': 'Results exported successfully!',
            'no_results_export': 'No analysis results to export', 'enter_student_info': 'Please enter student information',
            # Grading tab specific
            'load_scan_results': 'Load Scan Results', 'scan_results_file': 'Scan Results File',
            'select_omr_results': 'Select OMR results file...', 'load_results_btn': '📂 Load Results',
            'batch_processing': 'Batch Processing', 'add_student': '➕ Add Student', 'remove_student': '➖ Remove Student',
            'class_statistics': 'Class Statistics', 'average_score': 'Average Score: {0}%',
            'highest_score': 'Highest Score: {0}%', 'lowest_score': 'Lowest Score: {0}%',
            'pass_rate': 'Pass Rate: {0}%', 'students_processed': 'Students Processed: {0}',
            'export_class_report': '📋 Export Class Report', 'clear_all_results': '🗑️ Clear All Results'
        }
        
        el = {
            'app_title': 'Ενιαία Εφαρμογή OMR', 'form_validation_valid': 'Η φόρμα είναι έγκυρη', 
            'theme_light_mode': '🌙 Φωτεινό Θέμα', 'theme_dark_mode': '🌞 Σκοτεινό Θέμα', 
            'theme_tooltip': 'Κάντε κλικ για εναλλαγή Σκοτεινού/Φωτεινού Θέματος',
            'menu_file': 'Αρχείο', 'menu_new': 'Νέο', 'menu_load': 'Φόρτωση', 'menu_save': 'Αποθήκευση', 
            'menu_exit': 'Έξοδος', 'menu_export': 'Εξαγωγή', 'menu_export_pdf': 'Εξαγωγή PDF', 
            'menu_export_omr': 'Εξαγωγή Φύλλου OMR', 'menu_export_scanner': 'Εξαγωγή για Σαρωτή', 
            'menu_import': 'Εισαγωγή', 'menu_import_csv': 'Εισαγωγή CSV/Excel', 'menu_language': 'Γλώσσα', 
            'menu_english': 'English', 'menu_greek': 'Ελληνικά',
            'title_label': 'Τίτλος:', 'instructions_label': 'Οδηγίες:', 'preview_label': 'Προεπισκόπηση', 
            'questions_panel': 'Ερωτήσεις', 'question_text_label': 'Κείμενο Ερώτησης', 
            'answer_options_label': 'Επιλογές Απαντήσεων', 'correct_label': 'Σωστή:', 'points_label': 'Βαθμοί:', 
            'add_button': 'Προσθήκη', 'delete_button': 'Διαγραφή', 'option': 'Επιλογή', 
            'preview_title': 'Τίτλος', 'preview_instructions': 'Οδηγίες', 'preview_points': 'Βαθμοί',
            'default_form_title': 'Νέα Φόρμα', 'default_instructions': 'Επιλέξτε την καλύτερη απάντηση για κάθε ερώτηση.', 
            'default_option_a': 'Επιλογή Α', 'default_option_b': 'Επιλογή Β', 'default_option_c': 'Επιλογή Γ', 
            'default_option_d': 'Επιλογή Δ', 'default_question': 'Ερώτηση', 'no_text': 'Χωρίς κείμενο',
            'import_title': 'Εισαγωγή Ερωτήσεων', 
            'import_expected': 'Αναμενόμενο: Ερώτηση, Επιλογή Α, Επιλογή Β, Επιλογή Γ, Επιλογή Δ, Σωστή Απάντηση, Βαθμοί', 
            'import_file_placeholder': 'Επιλέξτε αρχείο CSV ή Excel...', 'browse_button': 'Αναζήτηση', 
            'has_headers': 'Η πρώτη γραμμή περιέχει επικεφαλίδες', 'clear_existing': 'Διαγραφή υπαρχουσών ερωτήσεων', 
            'cancel_button': 'Ακύρωση', 'import_button': 'Εισαγωγή',
            'success': 'Επιτυχία', 'error': 'Σφάλμα', 'warning': 'Προειδοποίηση', 'form_saved': 'Η φόρμα αποθηκεύτηκε!', 
            'form_loaded': 'Η φόρμα φορτώθηκε!', 'pdf_exported': 'Το PDF εξήχθη!', 'omr_exported': 'Το φύλλο OMR εξήχθη!', 
            'questions_imported': 'ερωτήσεις εισήχθησαν!', 'export_failed': 'Η εξαγωγή απέτυχε:', 
            'save_failed': 'Η αποθήκευση απέτυχε:', 'load_failed': 'Η φόρτωση απέτυχε:', 
            'critical_errors': 'Η φόρμα έχει κρίσιμα σφάλματα. Διορθώστε τα πρώτα.', 
            'no_questions_export': 'Δεν υπάρχουν ερωτήσεις για εξαγωγή', 'exported_scanner': 'Εξήχθη για σαρωτή:', 
            'new_form_confirm': 'Δημιουργία νέας φόρμας; Οι μη αποθηκευμένες αλλαγές θα χαθούν.',
            'validation_title': 'Επικύρωση', 'form_valid': 'Η φόρμα είναι έγκυρη!', 'issues_found': 'ζήτημα(τα) βρέθηκε(αν)', 
            'click_details': '(κλικ για λεπτομέρειες)', 'details_label': 'Λεπτομέρειες:', 'ok_button': 'Εντάξει',
            'answer_sheet': 'ΦΥΛΛΟ ΑΠΑΝΤΗΣΕΩΝ', 'student_name': 'Όνομα:', 'student_id': 'Αρ. Μητρώου:', 
            'omr_instruction1': '• Συμπληρώστε πλήρως τις φυσαλίδες με σκούρο μολύβι ή στυλό', 
            'omr_instruction2': '• Μην κάνετε άλλα σημάδια σε αυτό το φύλλο', 'total_questions': 'Σύνολο Ερωτήσεων:', 
            'total_points': 'Σύνολο Βαθμών:', 'continued': 'συνέχεια',
            'tab_designer': 'Σχεδιαστής Φορμών', 'tab_scanner': 'Σαρωτής', 'tab_grading': 'Βαθμολόγηση & Αναφορές',
            # Scanner translations (Greek)
            'scanner_title': '🎯 Σαρωτής OMR', 'step1_load': '1️⃣ Φόρτωση Εικόνας', 'step2_process': '2️⃣ Επεξεργασία', 
            'step3_answer_key': '3️⃣ Κλειδί Απαντήσεων', 'load_image_pdf': '📁 Φόρτωση Εικόνας/PDF', 'no_image_loaded': 'Δεν φορτώθηκε εικόνα',
            'detect_analyze': '🔍 Εντοπισμός & Ανάλυση', 'load_omr_file': '📄 Φόρτωση αρχείου .omr', 'no_answer_key': 'Δεν φορτώθηκε κλειδί απαντήσεων',
            'settings_title': '⚙️ Ρυθμίσεις', 'filled_threshold': 'Όριο Συμπλήρωσης:', 'results_title': '📊 Αποτελέσματα',
            'view_title': '👁️ Προβολή', 'show_positions': 'Εμφάνιση Θέσεων', 'show_results': 'Εμφάνιση Αποτελεσμάτων',
            'zoom_in': '🔍+', 'zoom_out': '🔍-', 'zoom_fit': '🖼️ Προσαρμογή', 'zoom_100': '📏 100%', 'zoom_reset': '🔄 Επαναφορά',
            'no_image': 'Χωρίς εικόνα', 'zoom_pan_info': '💡 Ροδάκι ποντικιού: Ζουμ | Μεσαίο κλικ/Ctrl+σύρσιμο: Μετακίνηση',
            'load_image_title': 'Φόρτωση Εικόνας', 'detecting_anchors': '🔄 Εντοπισμός αγκυρών...', 
            'anchors_detected': '✅ {0}', 'anchor_detection_failed': '❌ {0}', 'opencv_missing': 'Λείπει Εξάρτηση',
            'opencv_install': 'Το OpenCV δεν είναι διαθέσιμο. Εγκαταστήστε με:\npip install opencv-python',
            'load_answer_key': 'Φόρτωση Κλειδιού Απαντήσεων', 'analyzing_bubbles': '🔄 Ανάλυση φυσαλίδων...',
            'analysis_complete': '✅ Η ανάλυση ολοκληρώθηκε', 'analysis_failed': '❌ Η ανάλυση απέτυχε',
            'analysis_complete_text': '📊 ΑΝΑΛΥΣΗ ΟΛΟΚΛΗΡΩΘΗΚΕ\nΑπαντήθηκαν: {0}/{1}\n\n', 'question_prefix': 'Ε{0}: {1}\n',
            'blank_answer': '(κενό)', 'load_image_error': 'Αποτυχία φόρτωσης εικόνας:\n{0}',
            # Grading and reporting (Greek)
            'grading_title': '📋 Βαθμολόγηση & Αναφορές', 'student_info': 'Στοιχεία Μαθητή',
            'student_name_field': 'Όνομα Μαθητή:', 'student_id_field': 'Αρ. Μητρώου:', 'grade_sheet': 'Φύλλο Βαθμών',
            'export_results': 'Εξαγωγή Αποτελεσμάτων', 'export_csv': '📊 Εξαγωγή CSV', 'export_excel': '📈 Εξαγωγή Excel',
            'export_pdf_report': '📄 Εξαγωγή Αναφοράς PDF', 'calculate_grade': 'Υπολογισμός Βαθμού',
            'score_label': 'Βαθμός:', 'percentage_label': 'Ποσοστό:', 'grade_label': 'Βαθμολογία:',
            'total_label': 'Σύνολο:',
            'correct_answers': 'Σωστές: {0}', 'incorrect_answers': 'Λάθος: {0}', 'blank_answers': 'Κενές: {0}',
            'total_points': 'Σύνολο Βαθμών: {0}/{1}', 'statistics_title': 'Στατιστικά',
            'question_analysis': 'Ανάλυση Ερωτήσεων', 'export_success': 'Τα αποτελέσματα εξήχθησαν επιτυχώς!',
            'no_results_export': 'Δεν υπάρχουν αποτελέσματα ανάλυσης για εξαγωγή', 'enter_student_info': 'Παρακαλώ εισάγετε τα στοιχεία του μαθητή',
            # Grading tab specific (Greek)
            'load_scan_results': 'Φόρτωση Αποτελεσμάτων Σάρωσης', 'scan_results_file': 'Αρχείο Αποτελεσμάτων Σάρωσης',
            'select_omr_results': 'Επιλέξτε αρχείο αποτελεσμάτων OMR...', 'load_results_btn': '📂 Φόρτωση Αποτελεσμάτων',
            'batch_processing': 'Ομαδική Επεξεργασία', 'add_student': '➕ Προσθήκη Μαθητή', 'remove_student': '➖ Αφαίρεση Μαθητή',
            'class_statistics': 'Στατιστικά Τάξης', 'average_score': 'Μέσος Όρος: {0}%',
            'highest_score': 'Υψηλότερος Βαθμός: {0}%', 'lowest_score': 'Χαμηλότερος Βαθμός: {0}%',
            'pass_rate': 'Ποσοστό Επιτυχίας: {0}%', 'students_processed': 'Μαθητές που Επεξεργάστηκαν: {0}',
            'export_class_report': '📋 Εξαγωγή Αναφοράς Τάξης', 'clear_all_results': '🗑️ Εκκαθάριση Όλων των Αποτελεσμάτων'
        }
        
        return {'en': en, 'el': el}
    
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

# Core Data Models
class Question:
    """
    Represents a single question in an OMR form with validation capabilities.
    
    Attributes:
        text (str): The question text
        options (List[str]): List of answer options (typically A, B, C, D)
        correct (int): Index of the correct answer option (0-based)
        points (int): Point value awarded for correct answer
    """
    
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
        if not self.text.strip(): 
            errors.append("Question text is empty")
        if len([opt.strip() for opt in self.options if opt.strip()]) < 2: 
            errors.append("At least 2 answer options are required")
        if self.correct < 0 or self.correct >= len(self.options): 
            errors.append("Invalid correct answer index")
        if self.points < 0: 
            errors.append("Points cannot be negative")
        return errors

class Form:
    """
    Represents a complete OMR form containing multiple questions.
    
    Manages form metadata, questions collection, and provides validation
    functionality to ensure form integrity before PDF generation.
    
    Attributes:
        title (str): Form title displayed on generated PDF
        instructions (str): Instructions shown to students  
        questions (List[Question]): List of Question objects
    """
    
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
        if not self.title.strip(): 
            errors.append("Form title is required")
        if not self.questions: 
            errors.append("Form must have at least one question")
        for i, q in enumerate(self.questions):
            for error in q.validate(): 
                errors.append(f"Question {i+1}: {error}")
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

# Scanner Data Models
class BubbleAnalysisResult(NamedTuple):
    """Bubble analysis result"""
    darkness_score: float
    is_filled: bool
    confidence: float

class GradeResult(NamedTuple):
    """Complete grading result"""
    student_name: str
    student_id: str
    answers: Dict[int, str]
    correct_answers: Dict[int, str]
    points_per_question: Dict[int, int]
    score: int
    total_possible: int
    percentage: float
    correct_count: int
    incorrect_count: int
    blank_count: int
    question_results: Dict[int, bool]  # True if correct, False if wrong, None if blank

class GradingSystem:
    """
    Comprehensive grading and analytics system for OMR results.
    
    Manages grade calculations, student result tracking, statistical analysis,
    and provides various export formats. Handles scoring algorithms, percentage 
    calculations, letter grade assignments, and maintains collections of student
    results for batch processing and reporting.
    
    Attributes:
        results (List[GradeResult]): Collection of student grade results
        grade_scale (Dict): Letter grade thresholds and assignments
    """
    
    def __init__(self):
        self.results: List[GradeResult] = []
    
    def calculate_grade(self, student_name: str, student_id: str, 
                       student_answers: Dict[int, str], 
                       answer_key: Dict[int, str],
                       points_per_question: Dict[int, int]) -> GradeResult:
        """Calculate complete grade for a student"""
        
        question_results = {}
        score = 0
        total_possible = sum(points_per_question.values())
        correct_count = 0
        incorrect_count = 0
        blank_count = 0
        
        for q_num in answer_key.keys():
            student_answer = student_answers.get(q_num)
            correct_answer = answer_key[q_num]
            points = points_per_question[q_num]
            
            if student_answer is None:
                # Blank answer
                question_results[q_num] = None
                blank_count += 1
            elif student_answer == correct_answer:
                # Correct answer
                question_results[q_num] = True
                score += points
                correct_count += 1
            else:
                # Incorrect answer
                question_results[q_num] = False
                incorrect_count += 1
        
        percentage = (score / total_possible * 100) if total_possible > 0 else 0
        
        result = GradeResult(
            student_name=student_name,
            student_id=student_id,
            answers=student_answers.copy(),
            correct_answers=answer_key.copy(),
            points_per_question=points_per_question.copy(),
            score=score,
            total_possible=total_possible,
            percentage=percentage,
            correct_count=correct_count,
            incorrect_count=incorrect_count,
            blank_count=blank_count,
            question_results=question_results
        )
        
        self.results.append(result)
        return result
    
    def get_letter_grade(self, percentage: float) -> str:
        """Convert percentage to letter grade"""
        if percentage >= 90: return 'A'
        elif percentage >= 80: return 'B'  
        elif percentage >= 70: return 'C'
        elif percentage >= 60: return 'D'
        else: return 'F'
    
    def export_to_csv(self, filename: str) -> bool:
        """Export results to CSV"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                # Write header
                if self.results:
                    first_result = self.results[0]
                    questions = sorted(first_result.answers.keys())
                    
                    header = ['Student Name', 'Student ID', 'Score', 'Total Possible', 
                             'Percentage', 'Letter Grade', 'Correct', 'Incorrect', 'Blank']
                    
                    # Add question columns
                    for q_num in questions:
                        header.extend([f'Q{q_num} Answer', f'Q{q_num} Correct', f'Q{q_num} Points'])
                    
                    writer.writerow(header)
                    
                    # Write data rows
                    for result in self.results:
                        row = [
                            result.student_name, result.student_id, result.score, 
                            result.total_possible, f'{result.percentage:.1f}%',
                            self.get_letter_grade(result.percentage),
                            result.correct_count, result.incorrect_count, result.blank_count
                        ]
                        
                        # Add question details
                        for q_num in questions:
                            student_ans = result.answers.get(q_num, '')
                            correct_ans = result.correct_answers.get(q_num, '')
                            points = result.points_per_question.get(q_num, 0)
                            row.extend([student_ans, correct_ans, points])
                        
                        writer.writerow(row)
            
            return True
        except Exception as e:
            print(f"CSV export error: {e}")
            return False
    
    def export_to_excel(self, filename: str) -> bool:
        """Export results to Excel (requires pandas and openpyxl)"""
        if not EXCEL_AVAILABLE:
            return False
        
        try:
            data = []
            for result in self.results:
                row = {
                    'Student Name': result.student_name,
                    'Student ID': result.student_id,
                    'Score': result.score,
                    'Total Possible': result.total_possible,
                    'Percentage': result.percentage,
                    'Letter Grade': self.get_letter_grade(result.percentage),
                    'Correct': result.correct_count,
                    'Incorrect': result.incorrect_count,
                    'Blank': result.blank_count
                }
                
                # Add question details
                for q_num in sorted(result.answers.keys()):
                    row[f'Q{q_num} Answer'] = result.answers.get(q_num, '')
                    row[f'Q{q_num} Correct'] = result.correct_answers.get(q_num, '')
                    row[f'Q{q_num} Points'] = result.points_per_question.get(q_num, 0)
                
                data.append(row)
            
            df = pd.DataFrame(data)
            df.to_excel(filename, index=False, engine='openpyxl')
            return True
        except Exception as e:
            print(f"Excel export error: {e}")
            return False

class BubbleDetector:
    """
    Handles bubble detection and analysis for OMR scanning.
    
    Uses image processing techniques to determine if answer bubbles
    are filled based on darkness thresholds and confidence scoring.
    
    Attributes:
        analysis_radius (int): Pixel radius for bubble analysis
        filled_threshold (float): Darkness threshold for filled detection (0.0-1.0)
    """
    
    def __init__(self):
        self.analysis_radius = AppConfig.ANALYSIS_RADIUS
        self.filled_threshold = AppConfig.FILLED_THRESHOLD
    
    def analyze_bubble(self, image: Image.Image, center_x: int, center_y: int) -> BubbleAnalysisResult:
        """Analyze single bubble darkness"""
        try:
            img_array = np.array(image)
            gray = np.dot(img_array[...,:3], [0.299, 0.587, 0.114]) if len(img_array.shape) == 3 else img_array.astype(float)
            
            height, width = gray.shape
            if (center_x - self.analysis_radius < 0 or center_x + self.analysis_radius >= width or
                center_y - self.analysis_radius < 0 or center_y + self.analysis_radius >= height):
                return BubbleAnalysisResult(0.0, False, 0.0)
            
            # Sample circular area
            pixel_values = []
            for dy in range(-self.analysis_radius, self.analysis_radius + 1):
                for dx in range(-self.analysis_radius, self.analysis_radius + 1):
                    if dx*dx + dy*dy <= self.analysis_radius*self.analysis_radius:
                        pixel_values.append(gray[center_y + dy, center_x + dx])
            
            if not pixel_values:
                return BubbleAnalysisResult(0.0, False, 0.0)
            
            mean_intensity = np.mean(pixel_values)
            darkness_score = (255.0 - mean_intensity) / 255.0
            confidence = max(0.0, 1.0 - (np.std(pixel_values) / 100.0))
            is_filled = darkness_score >= self.filled_threshold
            
            return BubbleAnalysisResult(darkness_score, is_filled, min(1.0, confidence))
            
        except Exception:
            return BubbleAnalysisResult(0.0, False, 0.0)
    
    def analyze_all_bubbles(self, image: Image.Image, positions: Dict[int, Dict[str, Tuple[float, float]]]) -> Tuple[Dict, Dict]:
        """Analyze all bubbles and return results + answers"""
        results = {}
        answers = {}
        
        for q_num, options in positions.items():
            results[q_num] = {}
            filled_options = []
            
            for option, (x, y) in options.items():
                analysis = self.analyze_bubble(image, int(x), int(y))
                results[q_num][option] = analysis
                
                if analysis.is_filled and analysis.confidence >= 0.8:
                    filled_options.append((option, analysis.darkness_score))
            
            # Select answer: single filled bubble or darkest if multiple
            if len(filled_options) == 1:
                answers[q_num] = filled_options[0][0]
            elif len(filled_options) > 1:
                answers[q_num] = max(filled_options, key=lambda x: x[1])[0]
            else:
                answers[q_num] = None
        
        return results, answers

class WorkerThread(QThread):
    """Background processing thread"""
    
    result_ready = pyqtSignal(dict)
    
    def __init__(self, task_type, *args):
        super().__init__()
        self.task_type = task_type
        self.args = args
    
    def run(self):
        try:
            if self.task_type == 'anchors':
                result = self._detect_anchors(self.args[0])
            elif self.task_type == 'bubbles':
                result = self._analyze_bubbles(*self.args)
            else:
                result = {'success': False, 'message': 'Unknown task'}
            
            self.result_ready.emit(result)
        except Exception as e:
            self.result_ready.emit({'success': False, 'message': str(e)})
    
    def _detect_anchors(self, image: Image.Image) -> Dict:
        """Detect anchor points using OpenCV"""
        if not CV2_AVAILABLE:
            return {'success': False, 'message': 'OpenCV not available', 'anchors': {}}
        
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY) if len(img_array.shape) == 3 else img_array
        
        # Expected anchor positions
        margin, size = 75, 31
        expected = {
            'top_left': (margin, margin),
            'top_right': (image.width - margin - size, margin),
            'bottom_left': (margin, image.height - margin - size),
            'bottom_right': (image.width - margin - size, image.height - margin - size)
        }
        
        # Find contours
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Find square candidates
        candidates = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if 20 <= w <= 50 and 20 <= h <= 50 and 0.7 <= w/h <= 1.3:
                candidates.append((x, y, w, h))
        
        # Match to expected positions
        anchors = {}
        for name, (exp_x, exp_y) in expected.items():
            best_dist = float('inf')
            best_candidate = None
            
            for x, y, w, h in candidates:
                dist = np.sqrt((x - exp_x)**2 + (y - exp_y)**2)
                if dist < 100 and dist < best_dist:
                    best_dist = dist
                    best_candidate = (x, y, w, h)
            
            if best_candidate:
                x, y, w, h = best_candidate
                anchors[name] = {'x': x, 'y': y, 'width': w, 'height': h}
        
        return {
            'success': len(anchors) >= 3,
            'message': f"Detected {len(anchors)}/4 anchors",
            'anchors': anchors
        }
    
    def _analyze_bubbles(self, image, positions, detector):
        """Analyze all bubbles using detector"""
        results, answers = detector.analyze_all_bubbles(image, positions)
        return {
            'success': True,
            'results': results,
            'answers': answers
        }

# UI Components
class ZoomableImageLabel(QLabel):
    """Image display with zoom and pan capabilities"""
    
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("border: 2px solid #ccc;")
        self.setMinimumSize(800, 700)
        
        self.original_image = None
        self.current_pixmap = None
        self.zoom_factor = 1.0
        self.pan_offset = QPoint(0, 0)
        self.is_panning = False
        self.pan_start_point = QPoint()
        
        self.setMouseTracking(True)
        self.setText("Load an image to begin")
    
    def set_image(self, image: Image.Image):
        """Set image and fit to window"""
        try:
            # Ensure we have a proper PIL Image
            if not isinstance(image, Image.Image):
                print("ERROR: Invalid image type passed to set_image")
                return
            
            # Convert to RGB if needed for consistent display
            if image.mode not in ['RGB', 'RGBA']:
                print(f"DEBUG: Converting image from {image.mode} to RGB")
                self.original_image = image.convert('RGB')
            else:
                self.original_image = image
            
            self.zoom_factor = 1.0
            self.pan_offset = QPoint(0, 0)
            self.fit_to_window()
            
        except Exception as e:
            print(f"ERROR in set_image: {e}")
            self.original_image = None
    
    def fit_to_window(self):
        """Fit image to window maintaining aspect ratio"""
        if not self.original_image:
            return
        
        available_size = self.size()
        available_width = available_size.width() - 20
        available_height = available_size.height() - 20
        
        if available_width <= 0 or available_height <= 0:
            # Widget not yet properly sized, try again later
            return
        
        img_width, img_height = self.original_image.size
        if img_width <= 0 or img_height <= 0:
            return
            
        width_ratio = available_width / img_width
        height_ratio = available_height / img_height
        
        # Choose the smaller ratio to ensure the image fits completely
        self.zoom_factor = min(width_ratio, height_ratio)
        
        # Apply reasonable limits
        self.zoom_factor = min(self.zoom_factor, 5.0)  # Max 5x zoom
        self.zoom_factor = max(self.zoom_factor, 0.05)  # Min 0.05x zoom
        
        self.pan_offset = QPoint(0, 0)
        self.update_display()
    
    def zoom_in(self):
        if self.original_image and self.zoom_factor < 5.0:
            old_factor = self.zoom_factor
            self.zoom_factor = min(self.zoom_factor * 1.25, 5.0)
            
            # Check if the new zoom would create an image that's too large
            img_width, img_height = self.original_image.size
            new_width = int(img_width * self.zoom_factor)
            new_height = int(img_height * self.zoom_factor)
            
            if new_width > 10000 or new_height > 10000:
                # Revert to old zoom factor
                self.zoom_factor = old_factor
                print("WARNING: Maximum zoom reached to prevent memory issues")
                return
            
            self.update_display()
    
    def zoom_out(self):
        if self.original_image and self.zoom_factor > 0.05:  # Slightly lower minimum
            self.zoom_factor = max(self.zoom_factor / 1.25, 0.05)
            self.update_display()
    
    def zoom_100(self):
        if self.original_image:
            self.zoom_factor = 1.0
            self.pan_offset = QPoint(0, 0)
            self.update_display()
    
    def update_display(self):
        """Update displayed image"""
        if not self.original_image:
            return
        
        img_width, img_height = self.original_image.size
        new_width = int(img_width * self.zoom_factor)
        new_height = int(img_height * self.zoom_factor)
        
        # Ensure reasonable bounds to prevent memory issues
        if new_width <= 0 or new_height <= 0:
            return
        if new_width > 10000 or new_height > 10000:  # Limit max size
            return
        
        try:
            # Resize the image with high-quality resampling
            resized_image = self.original_image.resize(
                (new_width, new_height), Image.Resampling.LANCZOS
            )
            
            # Convert PIL image to QImage properly
            # First ensure the image is in RGB mode
            if resized_image.mode != 'RGB':
                resized_image = resized_image.convert('RGB')
            
            # Get image data with proper byte alignment
            width, height = resized_image.size
            rgb_data = resized_image.tobytes('raw', 'RGB')
            
            # Calculate bytes per line (Qt expects proper alignment)
            bytes_per_line = width * 3  # 3 bytes per pixel for RGB
            
            # Create QImage with proper parameters
            qimage = QImage(rgb_data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            
            # Ensure the QImage is valid
            if qimage.isNull():
                print("WARNING: Failed to create QImage from PIL data")
                return
            
            self.current_pixmap = QPixmap.fromImage(qimage)
            
            # Ensure the pixmap is valid
            if self.current_pixmap.isNull():
                print("WARNING: Failed to create QPixmap from QImage")
                return
            
            self.update()
            
        except Exception as e:
            print(f"ERROR in update_display: {e}")
            # Fall back to showing original image
            try:
                if self.original_image.mode != 'RGB':
                    fallback_image = self.original_image.convert('RGB')
                else:
                    fallback_image = self.original_image
                
                width, height = fallback_image.size
                rgb_data = fallback_image.tobytes('raw', 'RGB')
                bytes_per_line = width * 3
                qimage = QImage(rgb_data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
                
                if not qimage.isNull():
                    self.current_pixmap = QPixmap.fromImage(qimage)
                    self.update()
                    
            except Exception as fallback_error:
                print(f"ERROR in fallback display: {fallback_error}")
    
    def paintEvent(self, event):
        """Custom paint with pan support"""
        if self.current_pixmap and not self.current_pixmap.isNull():
            painter = QPainter(self)
            
            # Enable antialiasing for smoother appearance
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            
            widget_center = self.rect().center()
            pixmap_center = self.current_pixmap.rect().center()
            x = widget_center.x() - pixmap_center.x() + self.pan_offset.x()
            y = widget_center.y() - pixmap_center.y() + self.pan_offset.y()
            
            # Draw the pixmap
            painter.drawPixmap(x, y, self.current_pixmap)
        else:
            super().paintEvent(event)
    
    def wheelEvent(self, event: QWheelEvent):
        if self.original_image:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton or \
           (event.button() == Qt.MouseButton.LeftButton and 
            event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self.is_panning = True
            self.pan_start_point = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_panning:
            delta = event.position().toPoint() - self.pan_start_point
            self.pan_offset += delta
            self.pan_start_point = event.position().toPoint()
            self.update()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.is_panning:
            self.is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def get_zoom_info(self) -> str:
        return f"Zoom: {self.zoom_factor*100:.0f}%" if self.original_image else translator.t('no_image')

class ImportDialog(QDialog):
    """CSV/Excel import dialog with preview"""
    
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
                self._load_csv_file(filename)
            elif EXCEL_AVAILABLE and ext.endswith(('.xlsx', '.xls')):
                self._load_excel_file(filename)
            else:
                QMessageBox.warning(self, "Error", "Unsupported file format")
                return
            
            self.refresh_preview()
            self.import_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")

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
                QMessageBox.warning(self, "Error", "No valid questions found")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed: {str(e)}")

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

class QuestionEditor(QWidget):
    """Question editing widget"""
    
    def __init__(self, parent=None):
        super().__init__()
        self.question: Optional[Question] = None
        self.parent_form = parent
        self.option_edits: List[QLineEdit] = []
        self.option_labels: List[QLabel] = []
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
            self.option_labels.append(label)
            
            edit = QLineEdit()
            edit.setPlaceholderText(f"{translator.t('option')} {get_option_letter(i)}")
            edit.textChanged.connect(self.on_option_changed)
            self.option_edits.append(edit)
            
            row.addWidget(label)
            row.addWidget(edit)
            layout.addLayout(row)
        
        # Settings row
        settings = QHBoxLayout()
        
        # Correct answer
        correct_row = QHBoxLayout()
        self.correct_label = QLabel(translator.t('correct_label'))
        correct_row.addWidget(self.correct_label)
        self.correct_combo = UIHelpers.create_combo_with_items(
            [get_option_letter(i) for i in range(MAX_OPTIONS_COUNT)], 
            self.on_correct_changed, use_index=True
        )
        correct_row.addWidget(self.correct_combo)
        settings.addLayout(correct_row)
        
        # Points
        points_row = QHBoxLayout()
        self.points_label = QLabel(translator.t('points_label'))
        points_row.addWidget(self.points_label)
        self.points_combo = UIHelpers.create_combo_with_items(
            list(range(1, DEFAULT_POINTS_RANGE + 1)), 
            self.on_points_changed
        )
        points_row.addWidget(self.points_combo)
        settings.addLayout(points_row)
        
        settings.addStretch()
        layout.addLayout(settings)
        layout.addStretch()
        self.setLayout(layout)

    def load_question(self, question: Optional[Question]):
        """Load question data into editor"""
        with SignalBlocker(self.text_edit, *self.option_edits, self.correct_combo, self.points_combo):
            self.question = question
            if question:
                self.text_edit.setPlainText(question.text)
                
                for i in range(MAX_OPTIONS_COUNT):
                    text = question.options[i] if i < len(question.options) else ""
                    self.option_edits[i].setText(text)
                
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
            self._notify_parent()

    def on_option_changed(self):
        if self.question:
            for i, edit in enumerate(self.option_edits):
                if i < len(self.question.options):
                    self.question.options[i] = edit.text()
            self._notify_parent()

    def on_correct_changed(self, index: int):
        if self.question:
            self.question.correct = index
            self._notify_parent()

    def on_points_changed(self, points_str: str):
        if self.question:
            try: 
                self.question.points = max(1, min(int(points_str), DEFAULT_POINTS_RANGE))
            except (ValueError, TypeError): 
                self.question.points = 1
            self._notify_parent()

    def _notify_parent(self):
        if self.parent_form and hasattr(self.parent_form, 'refresh_display'):
            self.parent_form.refresh_display()

    def refresh_option_letters(self):
        """Refresh option letters when language changes"""
        # Update labels
        label_updates = [
            ('question_text_label', 'question_text_label'),
            ('answer_options_label', 'answer_options_label'),
            ('correct_label', 'correct_label'),
            ('points_label', 'points_label')
        ]
        
        for attr, key in label_updates:
            if hasattr(self, attr): 
                getattr(self, attr).setText(translator.t(key))
        
        # Update option labels and placeholders
        for i, label in enumerate(self.option_labels[:MAX_OPTIONS_COUNT]): 
            label.setText(get_option_letter(i))
        
        for i in range(min(MAX_OPTIONS_COUNT, len(self.option_edits))): 
            self.option_edits[i].setPlaceholderText(f"{translator.t('option')} {get_option_letter(i)}")
        
        # Update correct answer combo
        if hasattr(self, 'correct_combo'):
            current_index = self.correct_combo.currentIndex()
            self.correct_combo.clear()
            self.correct_combo.addItems([get_option_letter(i) for i in range(MAX_OPTIONS_COUNT)])
            self.correct_combo.setCurrentIndex(current_index)

# PDF Generation Mixins
class PDFGeneratorMixin:
    """Mixin for PDF generation functionality"""
    
    def _generate_pdf(self, filename: str):
        """Generate student answer PDF"""
        doc = SimpleDocTemplate(filename, pagesize=letter, 
                               rightMargin=PDF_MARGINS['right']*inch, leftMargin=PDF_MARGINS['left']*inch, 
                               topMargin=PDF_MARGINS['top']*inch, bottomMargin=PDF_MARGINS['bottom']*inch)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], 
                                   fontSize=FONT_SIZES['title'], fontName=FONT, spaceAfter=12, alignment=1)
        story.append(Paragraph(str(self.form.title).replace('<', '&lt;').replace('>', '&gt;'), title_style))
        story.append(Spacer(1, 12))
        
        # Instructions
        if self.form.instructions:
            inst_style = ParagraphStyle('Instructions', parent=styles['Normal'], 
                                      fontSize=FONT_SIZES['normal'], fontName=FONT, spaceAfter=18, alignment=1)
            story.append(Paragraph(self.form.instructions, inst_style))
            story.append(Spacer(1, 18))
        
        # Questions
        for i, q in enumerate(self.form.questions):
            elements = []
            q_style = ParagraphStyle('Question', parent=styles['Normal'], 
                                   fontSize=FONT_SIZES['normal'], fontName=FONT, spaceAfter=8)
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
            if i < len(self.form.questions) - 1:
                story.append(Spacer(1, 18))
        
        doc.build(story)

    def _generate_omr_sheet(self, filename: str):
        """Generate OMR answer sheet PDF"""
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        
        y = self._draw_omr_header(c, width, height)
        y = self._draw_student_info_section(c, width, y)
        y = self._draw_instructions_section(c, width, y)
        self._draw_questions_section(c, width, height, y)
        self._draw_omr_footer(c, width)
        
        c.save()

    def _draw_omr_header(self, c, width, height):
        """Draw OMR sheet header"""
        c.setFont(FONT, FONT_SIZES['title'])
        c.drawCentredString(width/2, height - 0.8*inch, self.form.title)
        c.setFont(FONT, FONT_SIZES['normal'] + 2)
        c.drawCentredString(width/2, height - 1.1*inch, translator.t('answer_sheet'))
        
        c.line(0.75*inch, height - 1.3*inch, width - 0.75*inch, height - 1.3*inch)
        self._draw_alignment_points(c, width, height)
        
        return height - 1.7*inch

    def _draw_student_info_section(self, c, width, y):
        """Draw student info fields"""
        c.setFont(FONT, FONT_SIZES['normal'] - 1)
        
        # Name field
        name_text = translator.t('student_name')
        name_x = 0.75*inch
        c.drawString(name_x, y, name_text)
        name_width = c.stringWidth(name_text, FONT, FONT_SIZES['normal'] - 1)
        c.line(name_x + name_width + 0.1*inch, y - 3, 4.5*inch, y - 3)
        
        # Student ID field
        id_text = translator.t('student_id')
        id_x = 4.8*inch
        c.drawString(id_x, y, id_text)
        id_width = c.stringWidth(id_text, FONT, FONT_SIZES['normal'] - 1)
        c.line(id_x + id_width + 0.1*inch, y - 3, 7.5*inch, y - 3)
        
        return y - 0.4*inch

    def _draw_instructions_section(self, c, width, y):
        """Draw OMR instructions"""
        c.setFont(FONT, FONT_SIZES['instruction'])
        c.drawString(0.75*inch, y, translator.t('omr_instruction1'))
        y -= 0.2*inch
        c.drawString(0.75*inch, y, translator.t('omr_instruction2'))
        
        y -= 0.3*inch
        c.line(0.75*inch, y, width - 0.75*inch, y)
        
        return y - 0.5*inch

    def _draw_questions_section(self, c, width, height, y):
        """Draw questions with bubbles"""
        min_bottom_margin = MIN_BOTTOM_MARGIN*inch
        question_height = QUESTION_HEIGHT*inch
        
        for i, q in enumerate(self.form.questions):
            if y - question_height < min_bottom_margin:
                c.showPage()
                y = self._draw_continuation_header(c, width, height)
            
            y = self._draw_single_question(c, i, y, question_height)

    def _draw_continuation_header(self, c, width, height):
        """Draw continuation page header"""
        c.setFont(FONT, FONT_SIZES['header'])
        c.drawCentredString(width/2, height - 0.5*inch, f"{self.form.title} ({translator.t('continued')})")
        c.line(0.75*inch, height - 0.7*inch, width - 0.75*inch, height - 0.7*inch)
        return height - 1.2*inch

    def _draw_single_question(self, c, question_index, y, question_height):
        """Draw single question with bubbles"""
        c.setFont(FONT, FONT_SIZES['normal'])
        question_num = f"{question_index+1}."
        c.drawRightString(1.1*inch, y + 2, question_num)
        
        bubble_radius = BUBBLE_RADIUS
        bubble_spacing = BUBBLE_SPACING*inch
        start_x = 1.3*inch
        
        for j in range(MAX_OPTIONS_COUNT):
            x = start_x + j * bubble_spacing
            c.circle(x, y + 5, bubble_radius, fill=0, stroke=1)
            c.setFont(FONT, FONT_SIZES['instruction'])
            c.drawCentredString(x, y - 0.25*inch, get_option_letter(j))
        
        return y - question_height

    def _draw_alignment_points(self, c, width, height):
        """Draw alignment squares for scanner"""
        square_size = 15
        
        positions = [
            (0.5*inch, height - 0.5*inch, "TL"),
            (width - 0.5*inch - square_size, height - 0.5*inch, "TR"),
            (0.5*inch, 0.5*inch + square_size, "BL"),
            (width - 0.5*inch - square_size, 0.5*inch + square_size, "BR")
        ]
        
        for x, y, label in positions:
            c.rect(x, y, square_size, -square_size, fill=1, stroke=1)
            c.setFont(FONT, 8)
            if label.endswith('L'):
                c.drawString(x + 20, y - 10 if label.startswith('T') else y + 5, label)
            else:
                c.drawRightString(x - 5, y - 10 if label.startswith('T') else y + 5, label)

    def _draw_omr_footer(self, c, width):
        """Draw footer with totals"""
        c.setFont(FONT, FONT_SIZES['small'])
        footer_text = f"{translator.t('total_questions')} {len(self.form.questions)} | {translator.t('total_points')} {sum(q.points for q in self.form.questions)}"
        c.drawCentredString(width/2, 0.5*inch, footer_text)

# Main Application Classes
class FormDesigner(QWidget, PDFGeneratorMixin):
    """Form designer with all functionality"""
    
    validation_changed = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.form = Form()
        self.form.title = translator.t('default_form_title')
        self.form.instructions = translator.t('default_instructions')
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Form header
        info_layout = QHBoxLayout()
        
        # Title row
        title_row = QHBoxLayout()
        self.title_label = QLabel(translator.t('title_label'))
        self.title_input = QLineEdit(self.form.title)
        self.title_input.textChanged.connect(self.on_title_changed)
        title_row.addWidget(self.title_label)
        title_row.addWidget(self.title_input)
        info_layout.addLayout(title_row)
        
        # Instructions row
        inst_row = QHBoxLayout()
        self.instructions_label = QLabel(translator.t('instructions_label'))
        self.instructions_input = QLineEdit(self.form.instructions)
        self.instructions_input.textChanged.connect(self.on_instructions_changed)
        inst_row.addWidget(self.instructions_label)
        inst_row.addWidget(self.instructions_input)
        info_layout.addLayout(inst_row)
        
        layout.addLayout(info_layout)
        
        # Main content splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Questions panel
        questions_widget = self._create_questions_panel()
        questions_widget.setMaximumWidth(300)
        
        # Editor panel
        self.editor = QuestionEditor(self)
        
        # Preview panel
        preview_widget = self._create_preview_panel()
        
        self.splitter.addWidget(questions_widget)
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(preview_widget)
        self.splitter.setSizes(SPLITTER_SIZES)
        
        layout.addWidget(self.splitter)
        self.setLayout(layout)
        self.refresh_display()

    def _create_questions_panel(self):
        """Create questions list panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.questions_list = QListWidget()
        self.questions_list.currentRowChanged.connect(self.on_question_selected)
        layout.addWidget(self.questions_list)
        
        btn_layout = QHBoxLayout()
        self.add_question_btn = UIHelpers.create_button(translator.t('add_button'), "success", self.add_question)
        self.delete_question_btn = UIHelpers.create_button(translator.t('delete_button'), "danger", self.delete_question)
        btn_layout.addWidget(self.add_question_btn)
        btn_layout.addWidget(self.delete_question_btn)
        layout.addLayout(btn_layout)
        
        return widget

    def _create_preview_panel(self):
        """Create preview panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.preview_label = QLabel(translator.t('preview_label'))
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setMinimumWidth(150)
        
        layout.addWidget(self.preview_label)
        layout.addWidget(self.preview)
        
        return widget

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
            translator.t('default_option_a'), translator.t('default_option_b'), 
            translator.t('default_option_c'), translator.t('default_option_d')
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
        
        if 0 <= current < len(self.form.questions): 
            self.questions_list.setCurrentRow(current)

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
        """Update preview and validation"""
        self.update_preview()
        self.update_validation()

    def show_validation_details(self):
        """Show detailed validation dialog"""
        summary = self.form.get_validation_summary()
        
        dialog = QDialog(self)
        dialog.setWindowTitle(translator.t('validation_title'))
        dialog.setMinimumSize(450, 250)
        
        layout = QVBoxLayout()
        
        # Header with icon and message
        header_layout = QHBoxLayout()
        
        icon_label = QLabel()
        if summary["status"] == "valid":
            icon_label.setText("ℹ️")
        elif summary["status"] == "warning":
            icon_label.setText("⚠️")
        else:
            icon_label.setText("❌")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        icon_label.setFixedSize(30, 30)
        header_layout.addWidget(icon_label)
        
        message_label = QLabel()
        if summary["status"] == "valid":
            message_label.setText(translator.t('form_valid'))
        else:
            message_label.setText(summary["message"])
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        header_layout.addWidget(message_label)
        
        layout.addLayout(header_layout)
        
        # Details if there are errors
        if summary["status"] != "valid" and summary["errors"]:
            details_label = QLabel(translator.t('details_label'))
            details_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            layout.addWidget(details_label)
            
            details_text = QTextEdit()
            error_text = "\n".join([f"• {e}" for e in summary["errors"]])
            details_text.setPlainText(error_text)
            details_text.setReadOnly(True)
            
            # Dynamic height calculation
            doc = details_text.document()
            doc.setTextWidth(450)
            content_height = int(doc.size().height())
            optimal_height = max(60, min(content_height + 20, 300))
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
        dialog.adjustSize()
        
        # Size constraints
        screen_size = dialog.screen().availableGeometry()
        max_width = min(600, screen_size.width() - 100)
        max_height = min(500, screen_size.height() - 100)
        current_size = dialog.size()
        dialog.resize(min(current_size.width(), max_width), min(current_size.height(), max_height))
        
        dialog.exec()

    # File operations
    def save_form(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Form", "", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.form.to_dict(), f, indent=2, ensure_ascii=False)
                UIHelpers.show_message(self, "success", translator.t('success'), translator.t('form_saved'))
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
                UIHelpers.show_message(self, "success", translator.t('success'), translator.t('form_loaded'))
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
            UIHelpers.show_message(self, "success", translator.t('success'), 
                                 f"{len(dialog.imported_questions)} {translator.t('questions_imported')}")

    def export_pdf(self):
        if not self._check_export():
            return
        filename, _ = QFileDialog.getSaveFileName(self, translator.t('menu_export_pdf'), 
                                                f"{self.form.title}.pdf", "PDF Files (*.pdf)")
        if filename:
            try:
                self._generate_pdf(filename)
                UIHelpers.show_message(self, "success", translator.t('success'), translator.t('pdf_exported'))
            except Exception as e:
                self._handle_file_error(e, 'export_failed')

    def export_omr_sheet(self):
        if not self._check_export():
            return
        filename, _ = QFileDialog.getSaveFileName(self, translator.t('menu_export_omr'), 
                                                f"{self.form.title}_sheet.pdf", "PDF Files (*.pdf)")
        if filename:
            try:
                self._generate_omr_sheet(filename)
                UIHelpers.show_message(self, "success", translator.t('success'), translator.t('omr_exported'))
            except Exception as e:
                self._handle_file_error(e, 'export_failed')

    def export_for_scanner(self):
        if not self.form.questions:
            QMessageBox.warning(self, translator.t('warning'), translator.t('no_questions_export'))
            return
        
        filename, _ = QFileDialog.getSaveFileName(self, "Export for Scanner", 
                                                f"{self.form.title.replace(' ', '_')}.omr", "OMR Files (*.omr)")
        if filename:
            try:
                bubble_coordinates = self._calculate_bubble_coordinates()
                data = {
                    "format_version": "2.0",
                    "generator": "OMR Unified Application v1.0",
                    "generated_date": datetime.now().isoformat(),
                    "metadata": {
                        "form_id": f"FORM_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        "title": self.form.title,
                        "total_questions": len(self.form.questions),
                        "total_points": sum(q.points for q in self.form.questions)
                    },
                    "layout": {
                        "page_size": "Letter", "orientation": "portrait", "bubble_style": "circle",
                        "page_width_inches": 8.5, "page_height_inches": 11.0, "dpi": 150
                    },
                    "questions": [{"id": i+1, "text": q.text, "options": q.options, 
                                 "correct_answer": q.correct, "points": q.points} 
                                for i, q in enumerate(self.form.questions)],
                    "answer_key": {str(i+1): q.correct for i, q in enumerate(self.form.questions)},
                    "bubble_coordinates": bubble_coordinates,
                    "alignment_points": self._calculate_alignment_points(),
                    "grading_config": {"scoring_method": "points", "penalty_wrong": 0.25, "penalty_blank": 0}
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                UIHelpers.show_message(self, "success", translator.t('success'), 
                                     f"{translator.t('exported_scanner')} {filename}")
            except Exception as e:
                UIHelpers.show_message(self, "error", translator.t('error'), 
                                     f"{translator.t('export_failed')} {str(e)}")

    def _calculate_bubble_coordinates(self):
        """Calculate exact bubble coordinates for scanner"""
        alignment = self._calculate_alignment_points()
        top_left_anchor = alignment["top_left"]
        
        # Empirically measured offsets
        anchor_to_first_bubble_x = 120
        anchor_to_first_bubble_y = 380
        bubble_spacing_x = 120
        bubble_spacing_y = 90
        
        bubble_coordinates = {}
        for i, question in enumerate(self.form.questions):
            question_num = i + 1
            bubble_coordinates[question_num] = {}
            
            for j in range(MAX_OPTIONS_COUNT):
                option_letter = get_option_letter(j)
                
                relative_x = anchor_to_first_bubble_x + (j * bubble_spacing_x)
                relative_y = anchor_to_first_bubble_y + (i * bubble_spacing_y)
                
                absolute_x = top_left_anchor["x"] + relative_x
                absolute_y = top_left_anchor["y"] + relative_y
                
                bubble_coordinates[question_num][option_letter] = {
                    "x": absolute_x, "y": absolute_y,
                    "radius": int((BUBBLE_RADIUS / 72) * 150),
                    "relative_to_anchor": {"x": relative_x, "y": relative_y, "anchor": "top_left"}
                }
        
        return bubble_coordinates
    
    def _calculate_alignment_points(self):
        """Calculate alignment point coordinates"""
        width, height = letter
        dpi = 150
        points_per_inch = 72
        
        page_width_px = int((width / points_per_inch) * dpi)
        page_height_px = int((height / points_per_inch) * dpi)
        square_size_px = int((15 / points_per_inch) * dpi)
        margin_px = int((0.5 * dpi))
        
        return {
            "top_left": {"x": margin_px, "y": margin_px},
            "top_right": {"x": page_width_px - margin_px - square_size_px, "y": margin_px},
            "bottom_left": {"x": margin_px, "y": page_height_px - margin_px - square_size_px},
            "bottom_right": {"x": page_width_px - margin_px - square_size_px, "y": page_height_px - margin_px - square_size_px},
            "size": square_size_px, "page_width": page_width_px, "page_height": page_height_px
        }

    def _check_export(self) -> bool:
        summary = self.form.get_validation_summary()
        if summary["status"] == "invalid":
            UIHelpers.show_message(self, "error", translator.t('error'), translator.t('critical_errors'))
            return False
        return True

    def _handle_file_error(self, error: Exception, operation_key: str):
        """Handle file operation errors"""
        msg = f"{translator.t(operation_key)} "
        if isinstance(error, PermissionError): 
            msg += "Permission denied. Check file permissions."
        elif isinstance(error, OSError): 
            msg += f"Disk error: {str(error)}"
        elif isinstance(error, json.JSONDecodeError): 
            msg += f"Invalid JSON format: {str(error)}"
        elif isinstance(error, FileNotFoundError): 
            msg += "File not found."
        else: 
            msg += str(error)
        UIHelpers.show_message(self, "error", translator.t('error'), msg)

    def refresh_ui(self):
        """Refresh UI for language changes"""
        # Update form defaults if they match translated defaults
        default_titles = ["New Form", "Νέα Φόρμα"]
        default_instructions = ["Select the best answer for each question.", 
                               "Επιλέξτε την καλύτερη απάντηση για κάθε ερώτηση."]
        
        if self.form.title in default_titles:
            self.form.title = translator.t('default_form_title')
            self.title_input.setText(self.form.title)
        
        if self.form.instructions in default_instructions:
            self.form.instructions = translator.t('default_instructions')
            self.instructions_input.setText(self.form.instructions)
        
        # Update UI labels
        self.title_label.setText(translator.t('title_label'))
        self.instructions_label.setText(translator.t('instructions_label'))
        self.preview_label.setText(translator.t('preview_label'))
        
        # Update buttons
        if hasattr(self, 'add_question_btn'):
            self.add_question_btn.setText(translator.t('add_button'))
        if hasattr(self, 'delete_question_btn'):
            self.delete_question_btn.setText(translator.t('delete_button'))
        
        # Refresh editor and display
        if hasattr(self, 'editor'):
            self.editor.refresh_option_letters()
        
        self.update_question_list()
        self.refresh_display()

class ScannerWidget(QWidget):
    """Scanner functionality widget"""
    
    def __init__(self, parent):
        super().__init__()
        self.parent_app = parent
        
        # Scanner state
        self.current_image = None
        self.anchors = {}
        self.omr_data = None
        self.bubble_positions = {}
        self.detector = BubbleDetector()
        self.analysis_results = {}
        self.answers = {}
        
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Left control panel
        left_panel = self._create_control_panel()
        left_panel.setMaximumWidth(320)
        layout.addWidget(left_panel)
        
        # Right image panel
        right_panel = self._create_image_panel()
        layout.addWidget(right_panel)
    
    def _create_control_panel(self):
        """Create left control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Title
        self.title_label = QLabel(translator.t('scanner_title'))
        self.title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(self.title_label)
        
        # Step 1: Load Image
        self.step1_group = QGroupBox(translator.t('step1_load'))
        step1_layout = QVBoxLayout(self.step1_group)
        
        self.load_btn = QPushButton(translator.t('load_image_pdf'))
        self.load_btn.clicked.connect(self.load_image)
        step1_layout.addWidget(self.load_btn)
        
        self.image_info = QLabel(translator.t('no_image_loaded'))
        self.image_info.setWordWrap(True)
        step1_layout.addWidget(self.image_info)
        layout.addWidget(self.step1_group)
        
        # Step 2: Process
        self.step2_group = QGroupBox(translator.t('step2_process'))
        step2_layout = QVBoxLayout(self.step2_group)
        
        self.process_btn = QPushButton(translator.t('detect_analyze'))
        self.process_btn.clicked.connect(self.process_image)
        self.process_btn.setEnabled(False)
        step2_layout.addWidget(self.process_btn)
        
        self.status_label = QLabel("")
        step2_layout.addWidget(self.status_label)
        layout.addWidget(self.step2_group)
        
        # Step 3: Answer Key
        self.step3_group = QGroupBox(translator.t('step3_answer_key'))
        step3_layout = QVBoxLayout(self.step3_group)
        
        self.load_omr_btn = QPushButton(translator.t('load_omr_file'))
        self.load_omr_btn.clicked.connect(self.load_omr)
        self.load_omr_btn.setEnabled(False)
        step3_layout.addWidget(self.load_omr_btn)
        
        self.omr_info = QLabel(translator.t('no_answer_key'))
        self.omr_info.setWordWrap(True)
        step3_layout.addWidget(self.omr_info)
        layout.addWidget(self.step3_group)
        
        # Settings
        self.settings_group = QGroupBox(translator.t('settings_title'))
        settings_layout = QVBoxLayout(self.settings_group)
        
        self.threshold_label = QLabel(translator.t('filled_threshold'))
        settings_layout.addWidget(self.threshold_label)
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.1, 0.9)
        self.threshold_spin.setValue(0.3)
        self.threshold_spin.setSingleStep(0.05)
        self.threshold_spin.valueChanged.connect(self.update_threshold)
        settings_layout.addWidget(self.threshold_spin)
        layout.addWidget(self.settings_group)
        
        # Results
        self.results_group = QGroupBox(translator.t('results_title'))
        results_layout = QVBoxLayout(self.results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(200)
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        layout.addWidget(self.results_group)
        
        # View Controls
        self.view_group = QGroupBox(translator.t('view_title'))
        view_layout = QVBoxLayout(self.view_group)
        
        self.show_positions_btn = QPushButton(translator.t('show_positions'))
        self.show_positions_btn.clicked.connect(self.show_positions)
        self.show_positions_btn.setEnabled(False)
        view_layout.addWidget(self.show_positions_btn)
        
        self.show_results_btn = QPushButton(translator.t('show_results'))
        self.show_results_btn.clicked.connect(self.show_results)
        self.show_results_btn.setEnabled(False)
        view_layout.addWidget(self.show_results_btn)
        layout.addWidget(self.view_group)
        
        layout.addStretch()
        return panel
    
    def _create_image_panel(self):
        """Create right image panel with zoom controls"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Zoom toolbar
        zoom_bar = QHBoxLayout()
        
        zoom_controls = [
            (translator.t('zoom_in'), self.zoom_in, "zoom_in_btn"),
            (translator.t('zoom_out'), self.zoom_out, "zoom_out_btn"),
            (translator.t('zoom_fit'), self.zoom_fit, "zoom_fit_btn"),
            (translator.t('zoom_100'), self.zoom_100, "zoom_100_btn"),
            (translator.t('zoom_reset'), self.reset_view, "reset_btn")
        ]
        
        for text, callback, attr_name in zoom_controls:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            btn.setEnabled(False)
            setattr(self, attr_name, btn)
            zoom_bar.addWidget(btn)
        
        zoom_bar.addStretch()
        
        self.zoom_info = QLabel(translator.t('no_image'))
        zoom_bar.addWidget(self.zoom_info)
        layout.addLayout(zoom_bar)
        
        # Zoomable image display
        self.image_display = ZoomableImageLabel()
        layout.addWidget(self.image_display)
        
        # Instructions
        self.zoom_info_label = QLabel(translator.t('zoom_pan_info'))
        self.zoom_info_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.zoom_info_label)
        
        return panel
    
    def load_image(self):
        """Load image or PDF file"""
        filter_str = ("All Files (*.pdf *.png *.jpg *.jpeg *.tiff *.bmp)" if PDF_AVAILABLE 
                     else "Images (*.png *.jpg *.jpeg *.tiff *.bmp)")
        
        # Use native file dialog on each platform for better integration
        options = QFileDialog.Option.DontUseNativeDialog if platform.system() == "Linux" else QFileDialog.Option(0)
        file_path, _ = QFileDialog.getOpenFileName(
            self, translator.t('load_image_title'), "", filter_str, options=options
        )
        if not file_path:
            return
        
        try:
            if file_path.lower().endswith('.pdf') and PDF_AVAILABLE:
                doc = fitz.open(file_path)
                page = doc[0]
                mat = fitz.Matrix(150.0/72.0, 150.0/72.0)  # 150 DPI
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("ppm")
                self.current_image = Image.open(io.BytesIO(img_data))
                doc.close()
            else:
                # Convert image to RGB if needed (handles CMYK, grayscale, etc.)
                temp_image = Image.open(file_path)
                if temp_image.mode not in ('RGB', 'RGBA'):
                    self.current_image = temp_image.convert('RGB')
                else:
                    self.current_image = temp_image
            
            # Update display
            self.image_display.set_image(self.current_image)
            filename = os.path.basename(os.path.normpath(file_path))
            self.image_info.setText(f"✅ {filename}\n{self.current_image.width}×{self.current_image.height}")
            
            # Enable controls
            self._enable_zoom_controls(True)
            self.process_btn.setEnabled(True)
            self.update_zoom_info()
            self._reset_analysis()
            
        except Exception as e:
            QMessageBox.critical(self, translator.t('error'), translator.t('load_image_error').format(str(e)))
    
    def process_image(self):
        """Process image for anchor detection"""
        if not self.current_image:
            return
        
        self.process_btn.setEnabled(False)
        self.status_label.setText(translator.t('detecting_anchors'))
        
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        
        self.worker = WorkerThread('anchors', self.current_image)
        self.worker.result_ready.connect(self.on_anchors_detected)
        self.worker.start()
    
    def on_anchors_detected(self, result):
        """Handle anchor detection completion"""
        self.process_btn.setEnabled(True)
        
        if result['success']:
            self.anchors = result['anchors']
            self.status_label.setText(translator.t('anchors_detected').format(result['message']))
            self.load_omr_btn.setEnabled(True)
        else:
            self.status_label.setText(translator.t('anchor_detection_failed').format(result['message']))
            if not CV2_AVAILABLE:
                QMessageBox.warning(self, translator.t('opencv_missing'), translator.t('opencv_install'))
    
    def load_omr(self):
        """Load OMR answer key file"""
        file_path, _ = QFileDialog.getOpenFileName(self, translator.t('load_answer_key'), "", 
                                                 "OMR Files (*.omr);;JSON Files (*.json)")
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.omr_data = json.load(f)
            
            self._transform_coordinates()
            
            filename = os.path.basename(os.path.normpath(file_path))
            questions = len(self.omr_data.get('questions', []))
            self.omr_info.setText(f"✅ {filename}\n{questions} questions")
            
            self._analyze_bubbles()
            
        except Exception as e:
            QMessageBox.critical(self, translator.t('error'), f"Failed to load OMR file:\n{str(e)}")
    
    def _transform_coordinates(self):
        """Transform bubble coordinates using detected anchors"""
        if not self.anchors or not self.omr_data:
            return
        
        bubble_coords = self.omr_data.get('bubble_coordinates', {})
        self.bubble_positions = {}
        
        for q_str, q_data in bubble_coords.items():
            q_num = int(q_str)
            self.bubble_positions[q_num] = {}
            
            for option in ['A', 'B', 'C', 'D']:
                if option in q_data:
                    rel_info = q_data[option].get('relative_to_anchor')
                    if rel_info and rel_info['anchor'] in self.anchors:
                        anchor = self.anchors[rel_info['anchor']]
                        x = anchor['x'] + rel_info['x']
                        y = anchor['y'] + rel_info['y']
                        self.bubble_positions[q_num][option] = (x, y)
    
    def _analyze_bubbles(self):
        """Analyze all bubbles"""
        if not self.current_image or not self.bubble_positions:
            return
        
        self.status_label.setText(translator.t('analyzing_bubbles'))
        
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        
        self.worker = WorkerThread('bubbles', self.current_image, self.bubble_positions, self.detector)
        self.worker.result_ready.connect(self.on_analysis_complete)
        self.worker.start()
    
    def on_analysis_complete(self, result):
        """Handle bubble analysis completion"""
        if result['success']:
            self.analysis_results = result['results']
            self.answers = result['answers']
            
            # Display results
            answered = sum(1 for ans in self.answers.values() if ans)
            total = len(self.answers)
            
            text = translator.t('analysis_complete_text').format(answered, total)
            for q_num in sorted(self.answers.keys()):
                answer = self.answers[q_num] or translator.t('blank_answer')
                text += translator.t('question_prefix').format(q_num, answer)
            
            self.results_text.setText(text)
            self.status_label.setText(translator.t('analysis_complete'))
            
            # Enable view buttons
            self.show_positions_btn.setEnabled(True)
            self.show_results_btn.setEnabled(True)
        else:
            self.status_label.setText(translator.t('analysis_failed'))
    
    def update_threshold(self):
        """Update bubble detection threshold"""
        self.detector.filled_threshold = self.threshold_spin.value()
        if self.bubble_positions:
            self._analyze_bubbles()
    
    def show_positions(self):
        """Show bubble positions overlay"""
        if not self.current_image or not self.bubble_positions:
            return
        
        try:
            overlay = self.current_image.copy()
            draw = ImageDraw.Draw(overlay)
            colors = {'A': 'red', 'B': 'green', 'C': 'blue', 'D': 'orange'}
            
            for q_num, options in self.bubble_positions.items():
                for option, (x, y) in options.items():
                    # Convert to integers and ensure valid coordinates
                    x, y = int(x), int(y)
                    color = colors.get(option, 'purple')
                    r = int(self.detector.analysis_radius)
                    
                    # Ensure coordinates are within image bounds
                    x1, y1 = max(0, x-r), max(0, y-r)
                    x2, y2 = min(overlay.width, x+r), min(overlay.height, y+r)
                    
                    if x2 > x1 and y2 > y1:  # Valid rectangle
                        draw.ellipse([x1, y1, x2, y2], outline=color, width=2)
                        # Ensure text coordinates are valid
                        text_x, text_y = max(0, x-5), max(0, y-8)
                        draw.text((text_x, text_y), option, fill=color)
                
                if 'A' in options:
                    x, y = int(options['A'][0]), int(options['A'][1])
                    text_x, text_y = max(0, x-30), max(0, y-8)
                    draw.text((text_x, text_y), f"Q{q_num}", fill='black')
            
            # Draw anchor rectangles if they exist
            if hasattr(self, 'anchors') and self.anchors:
                for anchor_name, anchor_data in self.anchors.items():
                    x = int(anchor_data['x'])
                    y = int(anchor_data['y'])
                    w = int(anchor_data['width'])
                    h = int(anchor_data['height'])
                    
                    # Ensure coordinates are within image bounds
                    x1, y1 = max(0, x), max(0, y)
                    x2, y2 = min(overlay.width, x + w), min(overlay.height, y + h)
                    
                    if x2 > x1 and y2 > y1:  # Valid rectangle
                        # Draw anchor rectangle with thick yellow outline
                        draw.rectangle([x1, y1, x2, y2], outline='yellow', width=3)
                        # Add anchor label
                        label_x, label_y = max(0, x1 + 2), max(0, y1 + 2)
                        draw.text((label_x, label_y), anchor_name.replace('_', ' ').title(), fill='yellow')
            
            self.image_display.set_image(overlay)
            self.update_zoom_info()
            
        except Exception as e:
            # Fallback - just show original image if drawing fails
            self.image_display.set_image(self.current_image)
            print(f"Error drawing positions overlay: {e}")
    
    def show_results(self):
        """Show analysis results overlay"""
        if not self.current_image or not self.analysis_results:
            return
        
        try:
            overlay = self.current_image.copy()
            draw = ImageDraw.Draw(overlay)
            colors = {'A': 'red', 'B': 'green', 'C': 'blue', 'D': 'orange'}
            
            for q_num, options in self.bubble_positions.items():
                for option, (x, y) in options.items():
                    if q_num in self.analysis_results and option in self.analysis_results[q_num]:
                        result = self.analysis_results[q_num][option]
                        color = colors.get(option, 'purple')
                        
                        # Convert to integers and ensure valid coordinates
                        x, y = int(x), int(y)
                        r = int(self.detector.analysis_radius)
                        
                        # Ensure coordinates are within image bounds
                        x1, y1 = max(0, x-r), max(0, y-r)
                        x2, y2 = min(overlay.width, x+r), min(overlay.height, y+r)
                        
                        if x2 > x1 and y2 > y1:  # Valid rectangle
                            # Circle thickness based on darkness
                            thickness = max(1, int(result.darkness_score * 5))
                            draw.ellipse([x1, y1, x2, y2], outline=color, width=thickness)
                            
                            # Fill if detected as filled
                            if result.is_filled:
                                fill_x1, fill_y1 = max(0, x-8), max(0, y-8)
                                fill_x2, fill_y2 = min(overlay.width, x+8), min(overlay.height, y+8)
                                if fill_x2 > fill_x1 and fill_y2 > fill_y1:
                                    draw.ellipse([fill_x1, fill_y1, fill_x2, fill_y2], fill=color)
            
            # Show selected answers
            for q_num, answer in self.answers.items():
                if answer and q_num in self.bubble_positions and answer in self.bubble_positions[q_num]:
                    x, y = int(self.bubble_positions[q_num][answer][0]), int(self.bubble_positions[q_num][answer][1])
                    text_x, text_y = max(0, x-50), max(0, y-8)
                    draw.text((text_x, text_y), f"Q{q_num}→{answer}", fill='black')
            
            self.image_display.set_image(overlay)
            self.update_zoom_info()
            
        except Exception as e:
            # Fallback - just show original image if drawing fails
            self.image_display.set_image(self.current_image)
            print(f"Error drawing results overlay: {e}")
    
    def reset_view(self):
        """Reset to original image"""
        if self.current_image:
            self.image_display.set_image(self.current_image)
            self.update_zoom_info()
    
    def _reset_analysis(self):
        """Reset analysis state"""
        self.anchors = {}
        self.omr_data = None
        self.bubble_positions = {}
        self.analysis_results = {}
        self.answers = {}
        
        self.status_label.clear()
        self.omr_info.setText(translator.t('no_answer_key'))
        self.results_text.clear()
        
        self.load_omr_btn.setEnabled(False)
        self.show_positions_btn.setEnabled(False)
        self.show_results_btn.setEnabled(False)
    
    def _enable_zoom_controls(self, enabled: bool):
        """Enable/disable zoom controls"""
        controls = [self.zoom_in_btn, self.zoom_out_btn, self.zoom_fit_btn, 
                   self.zoom_100_btn, self.reset_btn]
        for btn in controls:
            btn.setEnabled(enabled)
    
    # Zoom control methods
    def zoom_in(self):
        self.image_display.zoom_in()
        self.update_zoom_info()
    
    def zoom_out(self):
        self.image_display.zoom_out()
        self.update_zoom_info()
    
    def zoom_fit(self):
        self.image_display.fit_to_window()
        self.update_zoom_info()
    
    def zoom_100(self):
        self.image_display.zoom_100()
        self.update_zoom_info()
    
    def update_zoom_info(self):
        self.zoom_info.setText(self.image_display.get_zoom_info())
    
    
    def refresh_ui(self):
        """Refresh UI elements with current language"""
        # Update title and group boxes
        self.title_label.setText(translator.t('scanner_title'))
        self.step1_group.setTitle(translator.t('step1_load'))
        self.step2_group.setTitle(translator.t('step2_process'))
        self.step3_group.setTitle(translator.t('step3_answer_key'))
        self.settings_group.setTitle(translator.t('settings_title'))
        self.results_group.setTitle(translator.t('results_title'))
        self.view_group.setTitle(translator.t('view_title'))
        
        # Update buttons
        self.load_btn.setText(translator.t('load_image_pdf'))
        self.process_btn.setText(translator.t('detect_analyze'))
        self.load_omr_btn.setText(translator.t('load_omr_file'))
        self.show_positions_btn.setText(translator.t('show_positions'))
        self.show_results_btn.setText(translator.t('show_results'))
        
        # Update zoom controls
        self.zoom_in_btn.setText(translator.t('zoom_in'))
        self.zoom_out_btn.setText(translator.t('zoom_out'))
        self.zoom_fit_btn.setText(translator.t('zoom_fit'))
        self.zoom_100_btn.setText(translator.t('zoom_100'))
        self.reset_btn.setText(translator.t('zoom_reset'))
        
        # Update labels
        self.threshold_label.setText(translator.t('filled_threshold'))
        self.zoom_info_label.setText(translator.t('zoom_pan_info'))
        self.update_zoom_info()
        
        # Update info labels if no data loaded
        if not self.current_image:
            self.image_info.setText(translator.t('no_image_loaded'))
        if not self.omr_data:
            self.omr_info.setText(translator.t('no_answer_key'))

class GradingWidget(QWidget):
    """Dedicated Grading & Reports tab with batch processing"""
    
    def __init__(self, parent):
        super().__init__()
        self.parent_app = parent
        
        # Grading system
        self.grading_system = GradingSystem()
        self.current_grade_result = None
        self.scan_results = {}  # Store multiple scan results
        
        self.setup_ui()
    
    def setup_ui(self):
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
    
    def _create_control_panel(self):
        """Create left control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Title
        self.title_label = QLabel(translator.t('grading_title'))
        self.title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(self.title_label)
        
        # Load scan results
        load_group = QGroupBox(translator.t('load_scan_results'))
        load_layout = QVBoxLayout(load_group)
        
        self.load_results_btn = QPushButton(translator.t('load_results_btn'))
        self.load_results_btn.clicked.connect(self.load_scan_results)
        load_layout.addWidget(self.load_results_btn)
        
        self.scan_info = QLabel(translator.t('select_omr_results'))
        self.scan_info.setWordWrap(True)
        load_layout.addWidget(self.scan_info)
        
        layout.addWidget(load_group)
        
        # Student information
        student_group = QGroupBox(translator.t('student_info'))
        student_layout = QVBoxLayout(student_group)
        
        self.student_name_label = QLabel(translator.t('student_name_field'))
        student_layout.addWidget(self.student_name_label)
        self.student_name_edit = QLineEdit()
        self.student_name_edit.setPlaceholderText("Enter student name...")
        student_layout.addWidget(self.student_name_edit)
        
        self.student_id_label = QLabel(translator.t('student_id_field'))
        student_layout.addWidget(self.student_id_label)
        self.student_id_edit = QLineEdit()
        self.student_id_edit.setPlaceholderText("Enter student ID...")
        student_layout.addWidget(self.student_id_edit)
        
        # Grade calculation
        self.calculate_grade_btn = QPushButton(translator.t('calculate_grade'))
        self.calculate_grade_btn.clicked.connect(self.calculate_grade)
        self.calculate_grade_btn.setEnabled(False)
        student_layout.addWidget(self.calculate_grade_btn)
        
        layout.addWidget(student_group)
        
        # Batch processing
        batch_group = QGroupBox(translator.t('batch_processing'))
        batch_layout = QVBoxLayout(batch_group)
        
        batch_btn_layout = QHBoxLayout()
        self.add_student_btn = QPushButton(translator.t('add_student'))
        self.add_student_btn.clicked.connect(self.add_current_student)
        self.add_student_btn.setEnabled(False)
        batch_btn_layout.addWidget(self.add_student_btn)
        
        self.remove_student_btn = QPushButton(translator.t('remove_student'))
        self.remove_student_btn.clicked.connect(self.remove_selected_student)
        self.remove_student_btn.setEnabled(False)
        batch_btn_layout.addWidget(self.remove_student_btn)
        
        batch_layout.addLayout(batch_btn_layout)
        layout.addWidget(batch_group)
        
        # Class statistics
        stats_group = QGroupBox(translator.t('class_statistics'))
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_display = QTextEdit()
        self.stats_display.setMaximumHeight(150)
        self.stats_display.setReadOnly(True)
        stats_layout.addWidget(self.stats_display)
        
        layout.addWidget(stats_group)
        
        # Export controls
        export_group = QGroupBox(translator.t('export_results'))
        export_layout = QVBoxLayout(export_group)
        
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
        
        layout.addWidget(export_group)
        
        layout.addStretch()
        return panel
    
    def _create_results_panel(self):
        """Create right results panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Current student grade display
        current_group = QGroupBox(translator.t('grade_sheet'))
        current_layout = QVBoxLayout(current_group)
        
        self.grade_display = QTextEdit()
        self.grade_display.setMaximumHeight(200)
        self.grade_display.setReadOnly(True)
        current_layout.addWidget(self.grade_display)
        
        layout.addWidget(current_group)
        
        # Students list
        students_group = QGroupBox(translator.t('students_processed'))
        students_layout = QVBoxLayout(students_group)
        
        self.students_table = QTableWidget()
        
        # Use centralized table configuration
        TableManager.configure_students_table(self.students_table)
        self._update_table_headers()
        
        students_layout.addWidget(self.students_table)
        
        layout.addWidget(students_group)
        
        return panel
    
    def _update_table_headers(self):
        """Update table headers with current translations"""
        headers = TableManager.get_translated_headers()
        self.students_table.setHorizontalHeaderLabels(headers)
    
    def load_scan_results(self):
        """Load scan results from Scanner tab or file"""
        # First try to get current scan results from Scanner tab
        scanner_tab = self.parent_app.scanner_tab
        if scanner_tab.answers and scanner_tab.omr_data:
            self.scan_results = {
                'answers': scanner_tab.answers.copy(),
                'omr_data': scanner_tab.omr_data.copy()
            }
            self.scan_info.setText("✅ Loaded from Scanner tab")
            self.calculate_grade_btn.setEnabled(True)
            return
        
        # Otherwise, load from file (for future batch processing)
        file_path, _ = QFileDialog.getOpenFileName(
            self, translator.t('load_scan_results'), "",
            "OMR Results (*.json);;All Files (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.scan_results = json.load(f)
                
                filename = os.path.basename(os.path.normpath(file_path))
                self.scan_info.setText(f"✅ {filename}")
                self.calculate_grade_btn.setEnabled(True)
                
            except Exception as e:
                QMessageBox.critical(self, translator.t('error'), f"Failed to load results:\n{str(e)}")
    
    def calculate_grade(self):
        """Calculate and display grade for current student"""
        if not self.scan_results:
            QMessageBox.warning(self, translator.t('warning'), translator.t('no_results_export'))
            return
        
        student_name = self.student_name_edit.text().strip()
        student_id = self.student_id_edit.text().strip()
        
        if not student_name or not student_id:
            QMessageBox.warning(self, translator.t('warning'), translator.t('enter_student_info'))
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
            answer_key_int[q_num] = question_data.get('correct_answer', 'A')
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
    
    def display_grade_result(self, result: GradeResult):
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
    
    def add_current_student(self):
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
    
    def remove_selected_student(self):
        """Remove selected student from the list"""
        current_row = self.students_table.currentRow()
        if current_row >= 0 and current_row < len(self.grading_system.results):
            self.grading_system.results.pop(current_row)
            self.update_students_table()
            self.update_class_statistics()
            
            if not self.grading_system.results:
                self.disable_export_controls()
    
    def update_students_table(self):
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
    
    def update_class_statistics(self):
        """Update class statistics display"""
        if not self.grading_system.results:
            self.stats_display.clear()
            return
        
        percentages = [r.percentage for r in self.grading_system.results]
        avg_score = sum(percentages) / len(percentages)
        highest_score = max(percentages)
        lowest_score = min(percentages)
        pass_count = sum(1 for p in percentages if p >= 60)  # Assuming 60% is passing
        pass_rate = (pass_count / len(percentages)) * 100
        
        stats_text = f"""{translator.t('class_statistics')}

{translator.t('students_processed').format(len(self.grading_system.results))}
{translator.t('average_score').format(avg_score)}
{translator.t('highest_score').format(highest_score)}
{translator.t('lowest_score').format(lowest_score)}
{translator.t('pass_rate').format(pass_rate)}
"""
        self.stats_display.setText(stats_text)
    
    def enable_export_controls(self):
        """Enable export controls when we have results"""
        has_results = len(self.grading_system.results) > 0
        self.export_csv_btn.setEnabled(has_results)
        if hasattr(self, 'export_excel_btn'):
            self.export_excel_btn.setEnabled(has_results)
        self.export_class_btn.setEnabled(has_results)
        self.clear_results_btn.setEnabled(has_results)
    
    def disable_export_controls(self):
        """Disable export controls when no results"""
        self.export_csv_btn.setEnabled(False)
        if hasattr(self, 'export_excel_btn'):
            self.export_excel_btn.setEnabled(False)
        self.export_class_btn.setEnabled(False)
        self.clear_results_btn.setEnabled(False)
    
    def export_csv(self):
        """Export results to CSV"""
        if not self.grading_system.results:
            QMessageBox.warning(self, translator.t('warning'), translator.t('no_results_export'))
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, translator.t('export_csv'), 
            f"omr_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            "CSV Files (*.csv)"
        )
        
        if filename:
            if self.grading_system.export_to_csv(filename):
                QMessageBox.information(self, translator.t('success'), translator.t('export_success'))
            else:
                QMessageBox.critical(self, translator.t('error'), translator.t('export_failed'))
    
    def export_excel(self):
        """Export results to Excel"""
        if not EXCEL_AVAILABLE:
            QMessageBox.warning(self, translator.t('warning'), 
                              "Excel export requires pandas and openpyxl libraries")
            return
        
        if not self.grading_system.results:
            QMessageBox.warning(self, translator.t('warning'), translator.t('no_results_export'))
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, translator.t('export_excel'),
            f"omr_results_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            "Excel Files (*.xlsx)"
        )
        
        if filename:
            if self.grading_system.export_to_excel(filename):
                QMessageBox.information(self, translator.t('success'), translator.t('export_success'))
            else:
                QMessageBox.critical(self, translator.t('error'), translator.t('export_failed'))
    
    def export_class_report(self):
        """Export comprehensive class report as PDF"""
        if not self.grading_system.results:
            QMessageBox.warning(self, translator.t('warning'), translator.t('no_results_export'))
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, translator.t('export_class_report'),
            f"class_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            "PDF Files (*.pdf)"
        )
        
        if filename:
            if self.generate_class_report(filename):
                QMessageBox.information(self, translator.t('success'), translator.t('export_success'))
            else:
                QMessageBox.critical(self, translator.t('error'), translator.t('export_failed'))
    
    def generate_class_report(self, filename: str) -> bool:
        """Generate comprehensive class report PDF"""
        try:
            doc = SimpleDocTemplate(filename, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=20,
                spaceAfter=30,
                alignment=1  # Center
            )
            story.append(Paragraph("OMR Class Report", title_style))
            story.append(Spacer(1, 20))
            
            # Class Statistics
            story.append(Paragraph("Class Statistics", styles['Heading2']))
            
            percentages = [r.percentage for r in self.grading_system.results]
            avg_score = sum(percentages) / len(percentages)
            highest_score = max(percentages)
            lowest_score = min(percentages)
            pass_count = sum(1 for p in percentages if p >= 60)
            pass_rate = (pass_count / len(percentages)) * 100
            
            stats_info = [
                ["Total Students:", str(len(self.grading_system.results))],
                ["Average Score:", f"{avg_score:.1f}%"],
                ["Highest Score:", f"{highest_score:.1f}%"],
                ["Lowest Score:", f"{lowest_score:.1f}%"],
                ["Pass Rate (≥60%):", f"{pass_rate:.1f}%"],
                ["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M")]
            ]
            
            stats_table = Table(stats_info)
            stats_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, 'black'),
                ('BACKGROUND', (0, 0), (0, -1), '#f0f0f0'),
            ]))
            story.append(stats_table)
            story.append(Spacer(1, 20))
            
            # Student Results Table
            story.append(Paragraph("Individual Results", styles['Heading2']))
            
            student_data = [["Student Name", "Student ID", "Score", "Total", "Percentage", "Grade"]]
            
            for result in self.grading_system.results:
                student_data.append([
                    result.student_name,
                    result.student_id,
                    str(result.score),
                    str(result.total_possible),
                    f"{result.percentage:.1f}%",
                    self.grading_system.get_letter_grade(result.percentage)
                ])
            
            student_table = Table(student_data)
            student_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 1, 'black'),
                ('BACKGROUND', (0, 0), (-1, 0), '#cccccc'),  # Header
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ]))
            story.append(student_table)
            
            # Build PDF
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"Class report generation error: {e}")
            return False
    
    def clear_all_results(self):
        """Clear all results after confirmation"""
        reply = QMessageBox.question(
            self, "Clear Results", 
            "Are you sure you want to clear all results? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.grading_system.results.clear()
            self.students_table.setRowCount(0)
            self.stats_display.clear()
            self.grade_display.clear()
            self.disable_export_controls()
            self.remove_student_btn.setEnabled(False)
    
    def refresh_ui(self):
        """Refresh UI elements with current language"""
        # Update group titles and labels
        self.title_label.setText(translator.t('grading_title'))
        self.student_name_label.setText(translator.t('student_name_field'))
        self.student_id_label.setText(translator.t('student_id_field'))
        
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

class OMRUnifiedApp(QMainWindow):
    """Main unified application"""
    
    def __init__(self):
        super().__init__()
        
        self.dark_mode = False
        self.current_validation_summary = {"status": "valid", "message": "", "errors": []}
        
        self.setWindowTitle(translator.t('app_title'))
        self.setMinimumSize(1000, 700)
        self.setGeometry(100, 100, 1400, 900)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup main application UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tabbed interface
        self.tab_widget = QTabWidget()
        
        # Designer tab
        self.designer_tab = FormDesigner()
        self.designer_tab.validation_changed.connect(self.update_validation)
        self.tab_widget.addTab(self.designer_tab, translator.t('tab_designer'))
        
        # Scanner tab
        self.scanner_tab = ScannerWidget(self)
        self.tab_widget.addTab(self.scanner_tab, translator.t('tab_scanner'))
        
        # Grading tab
        self.grading_tab = GradingWidget(self)
        self.tab_widget.addTab(self.grading_tab, translator.t('tab_grading'))
        
        layout.addWidget(self.tab_widget)
        
        # Setup menu and status bar
        self.create_menu()
        self.create_status_bar()
        
        # Apply initial theme
        self.setStyleSheet(get_styles(self.dark_mode))
    
    def create_menu(self):
        """Create application menu"""
        self.menubar = self.menuBar()
        self.refresh_menu()

    def refresh_menu(self):
        """Refresh menu with current language"""
        self.menubar.clear()
        
        # File menu
        file_menu = self.menubar.addMenu(translator.t('menu_file'))
        
        menu_items = [
            (translator.t('menu_new'), 'Ctrl+N', self.new_file),
            (translator.t('menu_load'), 'Ctrl+O', self.designer_tab.load_form),
            (translator.t('menu_save'), 'Ctrl+S', self.designer_tab.save_form),
            None,  # Separator
            (translator.t('menu_exit'), 'Ctrl+Q', self.close)
        ]
        
        for item in menu_items:
            if item is None:
                file_menu.addSeparator()
            else:
                action = file_menu.addAction(item[0])
                action.setShortcut(item[1])
                action.triggered.connect(item[2])
        
        # Export menu
        export_menu = self.menubar.addMenu(translator.t('menu_export'))
        
        export_items = [
            (translator.t('menu_export_pdf'), 'Ctrl+E', self.designer_tab.export_pdf),
            (translator.t('menu_export_omr'), 'Ctrl+Shift+E', self.designer_tab.export_omr_sheet),
            (translator.t('menu_export_scanner'), 'Ctrl+Alt+E', self.designer_tab.export_for_scanner)
        ]
        
        for text, shortcut, callback in export_items:
            action = export_menu.addAction(text)
            action.setShortcut(shortcut)
            action.triggered.connect(callback)
        
        # Import menu
        import_menu = self.menubar.addMenu(translator.t('menu_import'))
        import_action = import_menu.addAction(translator.t('menu_import_csv'))
        import_action.setShortcut('Ctrl+I')
        import_action.triggered.connect(self.designer_tab.import_questions)
        
        # Language menu
        language_menu = self.menubar.addMenu(translator.t('menu_language'))
        
        english_action = language_menu.addAction(translator.t('menu_english'))
        english_action.triggered.connect(lambda: self.change_language('en'))
        
        greek_action = language_menu.addAction(translator.t('menu_greek'))
        greek_action.triggered.connect(lambda: self.change_language('el'))
    
    def create_status_bar(self):
        """Create status bar with validation and theme controls"""
        self.status_bar = self.statusBar()
        
        # Validation label
        self.validation_label = QLabel(translator.t('form_validation_valid'))
        self.validation_label.setStyleSheet("color: #2f7d32; font-weight: bold; padding: 4px;")
        self.validation_label.mousePressEvent = lambda event: self.show_validation_details(event)
        self.status_bar.addWidget(self.validation_label)
        
        # Theme toggle
        self.theme_label = QLabel(translator.t('theme_light_mode'))
        self.theme_label.setStyleSheet("color: #6b7280; font-weight: bold; padding: 4px; text-decoration: underline;")
        self.theme_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_label.setToolTip(translator.t('theme_tooltip'))
        self.theme_label.mousePressEvent = lambda event: self.toggle_theme(event)
        self.status_bar.addPermanentWidget(self.theme_label)
    
    def update_validation(self, summary: Dict[str, Any]):
        """Update validation display in status bar"""
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
        """Create new form"""
        if QMessageBox.question(self, translator.t('menu_new'), translator.t('new_form_confirm')) == QMessageBox.StandardButton.Yes:
            self.designer_tab.form = Form()
            self.designer_tab.form.title = translator.t('default_form_title')
            self.designer_tab.form.instructions = translator.t('default_instructions')
            self.designer_tab.title_input.setText(translator.t('default_form_title'))
            self.designer_tab.instructions_input.setText(translator.t('default_instructions'))
            self.designer_tab.update_question_list()
            self.designer_tab.update_preview()
            self.designer_tab.update_validation()
    
    def show_validation_details(self, event=None):
        """Show validation details dialog"""
        if self.current_validation_summary["status"] != "valid":
            self.designer_tab.show_validation_details()
    
    def toggle_theme(self, event=None):
        """Toggle between dark and light themes"""
        self.dark_mode = not self.dark_mode
        self.setStyleSheet(get_styles(self.dark_mode))
        
        if self.dark_mode:
            self.theme_label.setText(translator.t('theme_dark_mode'))
            self.theme_label.setStyleSheet("color: #94a3b8; font-weight: bold; padding: 4px; text-decoration: underline;")
        else:
            self.theme_label.setText(translator.t('theme_light_mode'))
            self.theme_label.setStyleSheet("color: #6b7280; font-weight: bold; padding: 4px; text-decoration: underline;")
    
    def change_language(self, lang_code: str):
        """Change application language"""
        translator.set_language(lang_code)
        
        # Update window and UI elements
        self.setWindowTitle(translator.t('app_title'))
        self.refresh_menu()
        
        # Update status bar
        self.validation_label.setText(translator.t('form_validation_valid'))
        theme_text = translator.t('theme_dark_mode') if self.dark_mode else translator.t('theme_light_mode')
        self.theme_label.setText(theme_text)
        self.theme_label.setToolTip(translator.t('theme_tooltip'))
        
        # Update tab titles
        self.tab_widget.setTabText(0, translator.t('tab_designer'))
        self.tab_widget.setTabText(1, translator.t('tab_scanner'))
        self.tab_widget.setTabText(2, translator.t('tab_grading'))
        
        # Refresh all tabs UI
        self.designer_tab.refresh_ui()
        self.scanner_tab.refresh_ui()
        self.grading_tab.refresh_ui()

def main():
    # Enable high DPI scaling on all platforms (PyQt6 syntax)
    import os
    os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
    
    app = QApplication(sys.argv)
    app.setApplicationName("OMR Unified Application")
    app.setStyle('Fusion')
    
    unified_app = OMRUnifiedApp()
    unified_app.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
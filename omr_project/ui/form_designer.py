from ui.ui_helpers import UIHelpers
from core.models.form_model import Form
from config.app_config import AppConfig
from utils.error_handling import ErrorHandler
from ui.import_dialog import ImportDialog  # ImportDialog now standalone module
from core.pdf.pdf_generator import PDFGeneratorMixin
from ui.question_editor import QuestionEditor
from core.models.question_model import Question
from i18n import translator, get_option_letter
from config.logger_config import get_logger, UI_LOGGER_NAME

# Standard library
import json
from datetime import datetime
from utils.files import build_timestamped_filename
from utils.page_size import get_page_size_inches

# PyQt6
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QListWidget, QTextEdit, QLabel,
    QLineEdit, QPushButton, QDialog, QFileDialog
)

# ReportLab (for page size constant)

class FormDesigner(QWidget, PDFGeneratorMixin):
    """Form designer with all functionality"""

    validation_changed = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.form = Form()
        self.form.title = translator.t('default_form_title')
        self.form.instructions = translator.t('default_instructions')
        self.log = get_logger(UI_LOGGER_NAME)
        self.setup_ui()

    def setup_ui(self) -> None:
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
        self.splitter.setSizes(AppConfig.SPLITTER_SIZES)

        layout.addWidget(self.splitter)
        self.setLayout(layout)
        self.refresh_display()

    def _create_questions_panel(self) -> QWidget:
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

    def _create_preview_panel(self) -> QWidget:
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

    def on_title_changed(self) -> None:
        self.form.title = self.title_input.text()
        self.refresh_display()

    def on_instructions_changed(self) -> None:
        self.form.instructions = self.instructions_input.text()
        self.refresh_display()

    def add_question(self) -> None:
        question = Question()
        question.text = f"{translator.t('default_question')} {len(self.form.questions) + 1}"
        question.options = [
            translator.t('default_option_a'), translator.t('default_option_b'),
            translator.t('default_option_c'), translator.t('default_option_d')
        ]
        self.form.questions.append(question)
        self.update_question_list()
        self.questions_list.setCurrentRow(len(self.form.questions) - 1)
        self.refresh_display()

    def delete_question(self) -> None:
        row = self.questions_list.currentRow()
        if 0 <= row < len(self.form.questions):
            del self.form.questions[row]
            self.update_question_list()
            if self.form.questions:
                self.questions_list.setCurrentRow(min(row, len(self.form.questions) - 1))
            else:
                self.editor.clear()
            self.refresh_display()

    def on_question_selected(self, row: int) -> None:
        if 0 <= row < len(self.form.questions):
            self.editor.load_question(self.form.questions[row])
        else:
            self.editor.load_question(None)
        self.refresh_display()

    def update_question_list(self) -> None:
        current = self.questions_list.currentRow()
        self.questions_list.clear()
        for i, q in enumerate(self.form.questions):
            text = q.text if q.text else translator.t('no_text')
            limit = AppConfig.PREVIEW_TEXT_TRUNCATE_LENGTH
            text = text[:limit] + "..." if len(text) > limit else text
            prefix = translator.t('question_prefix_inline').format(i+1, text)
            self.questions_list.addItem(f"{prefix} ({q.points}{translator.t('points_suffix')})")

        if 0 <= current < len(self.form.questions):
            self.questions_list.setCurrentRow(current)

    def _refresh_current_list_item(self) -> None:
        """Update the currently selected list item label without rebuilding the list.

        Keeps the left questions panel in sync while editing the question
        text or points, avoiding signal loops from clearing/resetting the list.
        """
        try:
            idx = self.questions_list.currentRow()
            if idx < 0 or idx >= len(self.form.questions):
                return
            item = self.questions_list.item(idx)
            if item is None:
                return
            q = self.form.questions[idx]
            text = q.text if q.text else translator.t('no_text')
            limit = AppConfig.PREVIEW_TEXT_TRUNCATE_LENGTH
            text = text[:limit] + "..." if len(text) > limit else text
            prefix = translator.t('question_prefix_inline').format(idx + 1, text)
            item.setText(f"{prefix} ({q.points}{translator.t('points_suffix')})")
        except Exception:
            # Non-fatal; UI update best-effort
            pass

    def update_preview(self) -> None:
        try:
            text = f"{translator.t('preview_title')}: {self.form.title}\n{translator.t('preview_instructions')}: {self.form.instructions}\n\n"
            for i, q in enumerate(self.form.questions):
                text += translator.t('question_prefix').format(i+1, q.text)
                non_empty_options = q.get_non_empty_options()

                # Get the correct answer text (handle empty options)
                correct_option = ""
                if q.correct < len(q.options) and q.options[q.correct].strip():
                    correct_option = q.options[q.correct].strip()

                for j, opt in enumerate(non_empty_options):
                    marker = "*" if opt == correct_option else " "
                    text += f"  {marker} {get_option_letter(j)}. {opt}\n"
                text += f"  {translator.t('preview_points')}: {q.points}\n\n"

            if hasattr(self, 'preview') and self.preview:
                self.preview.setPlainText(text)
            else:
                self.log.debug("Preview widget not found")
        except Exception as e:
            self.log.exception("Error in update_preview: %s", e)

    def update_validation(self) -> None:
        summary = self.form.get_validation_summary()
        self.validation_changed.emit(summary)

    def refresh_display(self) -> None:
        """Update preview and validation"""
        # Keep questions list label in sync while typing
        self._refresh_current_list_item()
        self.update_preview()
        self.update_validation()

    def show_validation_details(self) -> None:
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
    def save_form(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(self, translator.t('save_form_dialog'), "", translator.t('file_filter_json'))
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.form.to_dict(), f, indent=2, ensure_ascii=False)
                self.log.info("Form saved: %s", filename)
                ErrorHandler.show_info(self, translator.t('success'), translator.t('form_saved'))
            except Exception as e:
                self._handle_file_error(e, 'save_failed')

    def load_form(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, translator.t('load_form_dialog'), "", translator.t('file_filter_json'))
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
                self.log.info("Form loaded: %s", filename)
                ErrorHandler.show_info(self, translator.t('success'), translator.t('form_loaded'))
            except Exception as e:
                self._handle_file_error(e, 'load_failed')

    def import_questions(self) -> None:
        dialog = ImportDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.clear_existing_cb.isChecked():
                self.form.questions.clear()
            self.form.questions.extend(dialog.imported_questions)
            self.update_question_list()
            if self.form.questions:
                self.questions_list.setCurrentRow(len(self.form.questions) - 1)
            self.refresh_display()
            self.log.info("Questions imported: %d", len(dialog.imported_questions))
            ErrorHandler.show_info(self, translator.t('success'),
                                   f"{len(dialog.imported_questions)} {translator.t('questions_imported')}")

    def export_pdf(self) -> None:
        if not self._check_export():
            return
        filename, _ = QFileDialog.getSaveFileName(self, translator.t('menu_export_pdf'),
                                                build_timestamped_filename(self.form.title, 'pdf'), translator.t('file_filter_pdf'))
        if filename:
            try:
                self._generate_pdf(filename)
                self.log.info("PDF exported: %s", filename)
                ErrorHandler.show_info(self, translator.t('success'), translator.t('pdf_exported'))
            except Exception as e:
                self.log.exception("PDF export failed for '%s': %s", filename, e)
                self._handle_file_error(e, 'export_failed')

    def export_omr_sheet(self) -> None:
        if not self._check_export():
            return
        filename, _ = QFileDialog.getSaveFileName(self, translator.t('menu_export_omr'),
                                                build_timestamped_filename(f"{self.form.title}_sheet", 'pdf'), translator.t('file_filter_pdf'))
        if filename:
            try:
                self._generate_omr_sheet(filename)
                self.log.info("OMR sheet exported: %s", filename)
                ErrorHandler.show_info(self, translator.t('success'), translator.t('omr_exported'))
            except Exception as e:
                self.log.exception("OMR export failed for '%s': %s", filename, e)
                self._handle_file_error(e, 'export_failed')

    def export_for_scanner(self) -> None:
        if not self.form.questions:
            ErrorHandler.show_warning(self, translator.t('warning'), translator.t('no_questions_export'))
            return
        filename, _ = QFileDialog.getSaveFileName(self, translator.t('export_scanner_dialog'),
                                                  build_timestamped_filename(self.form.title.replace(' ', '_'), 'omr'), translator.t('file_filter_omr'))
        if filename:
            try:
                bubble_coordinates = self._calculate_bubble_coordinates()
                data = {
                    "format_version": AppConfig.EXPORT_FORMAT_VERSION,
                    "generator": AppConfig.APP_GENERATOR,
                    "generated_date": datetime.now().isoformat(),
                    "metadata": {
                        "form_id": f"FORM_{datetime.now().strftime(AppConfig.TIMESTAMP_FMT_SEC)}",
                        "title": self.form.title,
                        "total_questions": len(self.form.questions),
                        "total_points": sum(q.points for q in self.form.questions)
                    },
                    "layout": {
                        "page_size": (AppConfig.DEFAULT_PAGE_SIZE.value if hasattr(AppConfig.DEFAULT_PAGE_SIZE, "value") else str(AppConfig.DEFAULT_PAGE_SIZE)),
                        "orientation": (AppConfig.DEFAULT_PAGE_ORIENTATION.value if hasattr(AppConfig.DEFAULT_PAGE_ORIENTATION, "value") else str(AppConfig.DEFAULT_PAGE_ORIENTATION)),
                        "bubble_style": "circle",
                        "page_width_inches": get_page_size_inches()[0],
                        "page_height_inches": get_page_size_inches()[1],
                        "dpi": AppConfig.EXPORT_DPI
                    },
                    "questions": [{"id": i+1, "text": q.text, "options": q.get_non_empty_options(),
                                     "correct_answer": q.get_adjusted_correct_index(), "points": q.points}
                                    for i, q in enumerate(self.form.questions)],
                    "answer_key": {str(i+1): q.get_adjusted_correct_index() for i, q in enumerate(self.form.questions)},
                    "bubble_coordinates": bubble_coordinates,
                    "alignment_points": self._calculate_alignment_points(),
                    "grading_config": {
                        "scoring_method": "points",
                        "penalty_wrong": AppConfig.PENALTY_WRONG,
                        "penalty_blank": AppConfig.PENALTY_BLANK
                    }
                }

                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                self.log.info("Scanner export saved: %s", filename)
                ErrorHandler.show_info(self, translator.t('success'),
                                       f"{translator.t('exported_scanner')} {filename}")
            except Exception as e:
                self.log.exception("Scanner export failed for '%s': %s", filename, e)
                ErrorHandler.show_error(self, translator.t('error'),
                                        f"{translator.t('export_failed')} {str(e)}")

    def _calculate_bubble_coordinates(self):
        """Calculate exact bubble coordinates for scanner"""
        alignment = self._calculate_alignment_points()
        top_left_anchor = alignment["top_left"]

        # Layout parameters for exported scanner coordinates
        anchor_to_first_bubble_x = AppConfig.EXPORT_ANCHOR_TO_FIRST_BUBBLE_X
        anchor_to_first_bubble_y = AppConfig.EXPORT_ANCHOR_TO_FIRST_BUBBLE_Y
        bubble_spacing_x = AppConfig.EXPORT_BUBBLE_SPACING_X
        bubble_spacing_y = AppConfig.EXPORT_BUBBLE_SPACING_Y

        bubble_coordinates = {}
        for i, question in enumerate(self.form.questions):
            question_num = i + 1
            bubble_coordinates[question_num] = {}

            # Only create coordinates for non-empty options
            option_count = question.get_option_count()
            for j in range(option_count):
                option_letter = get_option_letter(j)

                relative_x = anchor_to_first_bubble_x + (j * bubble_spacing_x)
                relative_y = anchor_to_first_bubble_y + (i * bubble_spacing_y)

                absolute_x = top_left_anchor["x"] + relative_x
                absolute_y = top_left_anchor["y"] + relative_y

                bubble_coordinates[question_num][option_letter] = {
                    "x": absolute_x, "y": absolute_y,
                    "radius": int((AppConfig.BUBBLE_RADIUS / AppConfig.POINTS_PER_INCH) * AppConfig.EXPORT_DPI),
                    "relative_to_anchor": {"x": relative_x, "y": relative_y, "anchor": "top_left"}
                }

        return bubble_coordinates

    def _calculate_alignment_points(self):
        """Calculate alignment point coordinates"""
        dpi = AppConfig.EXPORT_DPI
        points_per_inch = AppConfig.POINTS_PER_INCH
        # Compute from configured page size in inches
        width_in, height_in = get_page_size_inches()
        page_width_px = int(width_in * dpi)
        page_height_px = int(height_in * dpi)
        square_size_px = int((AppConfig.PDF_ALIGNMENT_SQUARE_SIZE / points_per_inch) * dpi)
        margin_px = int(AppConfig.PDF_ALIGNMENT_SQUARE_OFFSET * dpi)

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
            ErrorHandler.show_error(self, translator.t('error'), translator.t('critical_errors'))
            return False
        return True

    def _handle_file_error(self, error: Exception, operation_key: str) -> None:
        """Handle file operation errors"""
        msg = f"{translator.t(operation_key)} "
        if isinstance(error, PermissionError):
            msg += translator.t('file_permission_denied')
        elif isinstance(error, OSError):
            msg += translator.t('file_disk_error').format(str(error))
        elif isinstance(error, json.JSONDecodeError):
            msg += translator.t('file_invalid_json').format(str(error))
        elif isinstance(error, FileNotFoundError):
            msg += translator.t('file_not_found')
        else:
            msg += str(error)
        self.log.error("File operation '%s' failed: %s", operation_key, error)
        ErrorHandler.show_error(self, translator.t('error'), msg)

    def refresh_ui(self) -> None:
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

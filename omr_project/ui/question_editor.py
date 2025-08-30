from ui.ui_helpers import UIHelpers
from config.app_config import AppConfig
from utils.qt_utils import SignalBlocker
from core.models.question_model import Question
from i18n import translator, get_option_letter

# Typing
from typing import Optional, List

# PyQt6
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QLineEdit, QSizePolicy
)

class QuestionEditor(QWidget):
    """Question editing widget"""

    def __init__(self, parent=None):
        super().__init__()
        self.question: Optional[Question] = None
        self.parent_form = parent
        self.option_edits: List[QLineEdit] = []
        self.option_labels: List[QLabel] = []
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QVBoxLayout()

        # Question text
        self.question_text_label = QLabel(translator.t('question_text_label'))
        layout.addWidget(self.question_text_label)
        self.text_edit = QTextEdit()
        # Make the question textbox a bit larger and allow expansion
        self.text_edit.setMinimumHeight(140)
        self.text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.text_edit.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.text_edit)

        # Options
        self.answer_options_label = QLabel(translator.t('answer_options_label'))
        layout.addWidget(self.answer_options_label)

        for i in range(AppConfig.MAX_OPTIONS_COUNT):
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

        # Settings row (after listing all options)
        settings = QHBoxLayout()

        # Correct answer selector
        correct_row = QHBoxLayout()
        self.correct_label = QLabel(translator.t('correct_label'))
        correct_row.addWidget(self.correct_label)
        self.correct_combo = UIHelpers.create_combo_with_items(
            [get_option_letter(i) for i in range(AppConfig.MAX_OPTIONS_COUNT)],
            self.on_correct_changed,
            use_index=True
        )
        correct_row.addWidget(self.correct_combo)
        settings.addLayout(correct_row)

        # Points selector
        points_row = QHBoxLayout()
        self.points_label = QLabel(translator.t('points_label'))
        points_row.addWidget(self.points_label)
        self.points_combo = UIHelpers.create_combo_with_items(
            list(range(1, AppConfig.DEFAULT_POINTS_RANGE + 1)),
            self.on_points_changed
        )
        points_row.addWidget(self.points_combo)
        settings.addLayout(points_row)

        settings.addStretch()
        layout.addLayout(settings)
        layout.addStretch()
        self.setLayout(layout)

    def load_question(self, question: Optional[Question]) -> None:
        """Load question data into editor"""
        with SignalBlocker(self.text_edit, *self.option_edits, self.correct_combo, self.points_combo):
            self.question = question
            if question:
                self.text_edit.setPlainText(question.text)

                for i in range(AppConfig.MAX_OPTIONS_COUNT):
                    text = question.options[i] if i < len(question.options) else ""
                    self.option_edits[i].setText(text)

                self.correct_combo.setCurrentIndex(min(question.correct, AppConfig.MAX_OPTIONS_COUNT - 1))
                self.points_combo.setCurrentIndex(max(0, min(question.points - 1, self.points_combo.count() - 1)))
            else:
                self.clear()

    def clear(self) -> None:
        self.text_edit.clear()
        for edit in self.option_edits:
            edit.clear()
        self.correct_combo.setCurrentIndex(0)
        self.points_combo.setCurrentIndex(0)

    def on_text_changed(self) -> None:
        if self.question:
            self.question.text = self.text_edit.toPlainText()
            self._notify_parent()

    def on_option_changed(self) -> None:
        if self.question:
            for i, edit in enumerate(self.option_edits):
                if i < len(self.question.options):
                    self.question.options[i] = edit.text()
            self._notify_parent()

    def on_correct_changed(self, index: int) -> None:
        if self.question:
            self.question.correct = index
            self._notify_parent()

    def on_points_changed(self, points_str: str) -> None:
        if self.question:
            try:
                self.question.points = max(1, min(int(points_str), AppConfig.DEFAULT_POINTS_RANGE))
            except (ValueError, TypeError):
                self.question.points = 1
            self._notify_parent()

    def _notify_parent(self) -> None:
        if self.parent_form and hasattr(self.parent_form, 'refresh_display'):
            self.parent_form.refresh_display()

    def refresh_option_letters(self) -> None:
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
        for i, label in enumerate(self.option_labels[:AppConfig.MAX_OPTIONS_COUNT]):
            label.setText(get_option_letter(i))

        for i in range(min(AppConfig.MAX_OPTIONS_COUNT, len(self.option_edits))):
            self.option_edits[i].setPlaceholderText(f"{translator.t('option')} {get_option_letter(i)}")

        # Update correct answer combo
        if hasattr(self, 'correct_combo'):
            current_index = self.correct_combo.currentIndex()
            self.correct_combo.clear()
            self.correct_combo.addItems([get_option_letter(i) for i in range(AppConfig.MAX_OPTIONS_COUNT)])
            self.correct_combo.setCurrentIndex(current_index)

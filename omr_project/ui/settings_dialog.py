from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDialogButtonBox
from PyQt6.QtCore import QSettings

from i18n import translator
from config.app_config import AppConfig


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(translator.t('preferences_title'))
        self.resize(380, 220)

        self.lang_combo = QComboBox()
        self.lang_combo.addItem('English', 'en')
        self.lang_combo.addItem('Ελληνικά', 'el')

        self.theme_combo = QComboBox()
        self.theme_combo.addItem(translator.t('settings_theme_light'), 'light')
        self.theme_combo.addItem(translator.t('settings_theme_dark'), 'dark')

        self.page_size_combo = QComboBox()
        self.page_size_combo.addItem('Letter', AppConfig.PageSize.LETTER.value)
        self.page_size_combo.addItem('A4', AppConfig.PageSize.A4.value)

        self.orientation_combo = QComboBox()
        self.orientation_combo.addItem('Portrait', AppConfig.Orientation.PORTRAIT.value)
        self.orientation_combo.addItem('Landscape', AppConfig.Orientation.LANDSCAPE.value)

        self._load_current()

        layout = QVBoxLayout(self)
        # Language
        row = QHBoxLayout()
        row.addWidget(QLabel(translator.t('settings_language')))
        row.addWidget(self.lang_combo)
        layout.addLayout(row)
        # Theme
        row = QHBoxLayout()
        row.addWidget(QLabel(translator.t('settings_theme')))
        row.addWidget(self.theme_combo)
        layout.addLayout(row)
        # Page size
        row = QHBoxLayout()
        row.addWidget(QLabel(translator.t('settings_page_size')))
        row.addWidget(self.page_size_combo)
        layout.addLayout(row)
        # Orientation
        row = QHBoxLayout()
        row.addWidget(QLabel(translator.t('settings_orientation')))
        row.addWidget(self.orientation_combo)
        layout.addLayout(row)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_current(self):
        s = QSettings()
        # Language
        lang = s.value('language', 'en')
        idx = self.lang_combo.findData(lang)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        # Theme
        dark = str(s.value('dark_mode', 'false')).lower() in ('1', 'true', 'yes')
        self.theme_combo.setCurrentIndex(1 if dark else 0)
        # Page size
        size_val = s.value('page_size', AppConfig.DEFAULT_PAGE_SIZE.value if hasattr(AppConfig.DEFAULT_PAGE_SIZE, 'value') else str(AppConfig.DEFAULT_PAGE_SIZE))
        idx = self.page_size_combo.findData(str(size_val).lower())
        if idx >= 0:
            self.page_size_combo.setCurrentIndex(idx)
        # Orientation
        orient_val = s.value('page_orientation', AppConfig.DEFAULT_PAGE_ORIENTATION.value if hasattr(AppConfig.DEFAULT_PAGE_ORIENTATION, 'value') else str(AppConfig.DEFAULT_PAGE_ORIENTATION))
        idx = self.orientation_combo.findData(str(orient_val).lower())
        if idx >= 0:
            self.orientation_combo.setCurrentIndex(idx)

    def save(self):
        s = QSettings()
        s.setValue('language', self.lang_combo.currentData())
        s.setValue('dark_mode', 'true' if self.theme_combo.currentData() == 'dark' else 'false')
        s.setValue('page_size', self.page_size_combo.currentData())
        s.setValue('page_orientation', self.orientation_combo.currentData())


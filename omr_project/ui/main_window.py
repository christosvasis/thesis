from ui.app_style import get_styles
from ui.form_designer import FormDesigner
from ui.settings_dialog import SettingsDialog
from core.models.form_model import Form
from ui.grading_widget import GradingWidget
from ui.scanner_widget import ScannerWidget
from i18n import translator

from typing import Dict, Any
import sys

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QLabel, QHBoxLayout, QPushButton
)
from PyQt6.QtCore import Qt, QSettings
from utils.error_handling import ErrorHandler


class OMRUnifiedApp(QMainWindow):
    """Main unified application window with tabbed UI."""

    # Style constants
    VALIDATION_VALID_STYLE = "color: #2f7d32; font-weight: bold; padding: 4px;"
    THEME_LABEL_STYLE = "color: #6b7280; font-weight: bold; padding: 4px; text-decoration: underline;"
    THEME_LABEL_DARK_STYLE = "color: #94a3b8; font-weight: bold; padding: 4px; text-decoration: underline;"
    VALIDATION_ERROR_STYLE = "font-weight: bold; padding: 4px; text-decoration: underline;"

    def __init__(self):
        super().__init__()

        self.dark_mode = False
        self.current_validation_summary = {"status": "valid", "message": "", "errors": []}

        self.setWindowTitle(translator.t('app_title'))
        self.setMinimumSize(1000, 700)
        self.setGeometry(100, 100, 1400, 900)

        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup main application UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        # Reduce vertical gaps between header and content
        try:
            layout.setContentsMargins(3, 3, 3, 3)
            layout.setSpacing(0)
        except Exception:
            pass

        # Create tabbed interface
        self.tab_widget = QTabWidget()
        try:
            self.tab_widget.setContentsMargins(0, 0, 0, 0)
            if self.tab_widget.layout() is not None:
                self.tab_widget.layout().setContentsMargins(0, 0, 0, 0)
                self.tab_widget.layout().setSpacing(0)
        except Exception:
            pass
        # Hide the default tab bar; we'll provide a centered header with buttons
        try:
            self.tab_widget.tabBar().hide()
        except Exception:
            pass

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

        # Build centered tab header with buttons
        self._build_centered_tab_header(layout)
        # Keep buttons in sync when current tab changes
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        layout.addWidget(self.tab_widget)

        # Setup menu and status bar
        self.create_menu()
        self.create_status_bar()

        # Apply initial theme
        self.setStyleSheet(get_styles(self.dark_mode))
        QSettings().setValue('dark_mode', self.dark_mode)

    def _build_centered_tab_header(self, parent_layout: QVBoxLayout) -> None:
        """Create a centered header with buttons acting as tabs."""
        header = QWidget()
        hlayout = QHBoxLayout(header)
        try:
            header.setContentsMargins(0, 0, 0, 0)
            hlayout.setContentsMargins(0, 0, 0, 0)
            hlayout.setSpacing(0)
        except Exception:
            pass
        hlayout.addStretch()

        titles = [translator.t('tab_designer'), translator.t('tab_scanner'), translator.t('tab_grading')]
        self.tab_buttons: list[QPushButton] = []
        for idx, title in enumerate(titles):
            btn = QPushButton(title)
            btn.setCheckable(True)
            # First button checked initially
            if idx == 0:
                btn.setChecked(True)
            # Capture index in lambda default
            btn.clicked.connect(lambda checked=False, i=idx: self.tab_widget.setCurrentIndex(i))
            self.tab_buttons.append(btn)
            hlayout.addWidget(btn)

        hlayout.addStretch()
        parent_layout.addWidget(header)

    def _on_tab_changed(self, index: int) -> None:
        """Sync button checked state when tab changes."""
        try:
            for i, btn in enumerate(getattr(self, 'tab_buttons', [])):
                btn.setChecked(i == index)
        except Exception:
            pass

    def create_menu(self) -> None:
        """Create application menu"""
        self.menubar = self.menuBar()
        self.refresh_menu()

    def refresh_menu(self) -> None:
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

        # Language menu removed; language is controlled via Settings

        # Platform-specific Settings/Preferences wiring
        if sys.platform == 'darwin':
            # On macOS, expose a Preferences action in the App menu and avoid a visible Settings menu
            try:
                from PyQt6.QtGui import QAction, QKeySequence
                pref_action = QAction('Preferences…', self)
                pref_action.setMenuRole(QAction.MenuRole.PreferencesRole)
                try:
                    pref_action.setShortcut(QKeySequence.StandardKey.Preferences)
                except Exception:
                    pref_action.setShortcut('Ctrl+,')
                pref_action.triggered.connect(self.open_settings)
                file_menu.addAction(pref_action)  # add to any menu; macOS will relocate it
            except Exception:
                # Fallback: simple action
                action = self.menubar.addAction('Preferences…')
                action.triggered.connect(self.open_settings)
        else:
            # Other platforms: show a Settings menu with a single Settings… action
            settings_menu = self.menubar.addMenu(translator.t('menu_settings'))
            settings_action = settings_menu.addAction(translator.t('preferences_title') + '…')
            try:
                settings_action.setShortcut('Ctrl+,')
            except Exception:
                pass
            settings_action.setEnabled(True)
            settings_action.triggered.connect(self.open_settings)

    def open_settings(self) -> None:
        dlg = SettingsDialog(self)
        if dlg.exec() == dlg.DialogCode.Accepted:
            dlg.save()
            self.apply_preferences()

    def apply_preferences(self) -> None:
        from utils.config_check import validate_config as _validate
        from config.app_config import AppConfig as _Cfg
        from ui.app_style import get_styles as _styles
        from PyQt6.QtCore import QSettings
        s = QSettings()
        lang = s.value('language')
        if lang:
            translator.set_language(str(lang))
        if (ps := s.value('page_size')):
            try:
                _Cfg.DEFAULT_PAGE_SIZE = _Cfg.PageSize(str(ps).lower())
            except Exception:
                pass
        if (po := s.value('page_orientation')):
            try:
                _Cfg.DEFAULT_PAGE_ORIENTATION = _Cfg.Orientation(str(po).lower())
            except Exception:
                pass
        _validate()
        dm = s.value('dark_mode')
        if dm is not None:
            val = str(dm).lower() in ('1', 'true', 'yes')
            self.dark_mode = val
            self.setStyleSheet(_styles(self.dark_mode))
        self.setWindowTitle(translator.t('app_title'))
        self.refresh_menu()
        self.validation_label.setText(translator.t('form_validation_valid'))
        # Theme label is removed from status bar; nothing to update here
        self.tab_widget.setTabText(0, translator.t('tab_designer'))
        self.tab_widget.setTabText(1, translator.t('tab_scanner'))
        self.tab_widget.setTabText(2, translator.t('tab_grading'))
        self._update_tab_header_labels()
        self.designer_tab.refresh_ui()
        self.scanner_tab.refresh_ui()
        self.grading_tab.refresh_ui()

    def create_status_bar(self) -> None:
        """Create status bar with validation and theme controls"""
        self.status_bar = self.statusBar()

        # Validation label
        self.validation_label = QLabel(translator.t('form_validation_valid'))
        self.validation_label.setStyleSheet(self.VALIDATION_VALID_STYLE)
        self.validation_label.mousePressEvent = lambda event: self.show_validation_details(event)
        self.status_bar.addWidget(self.validation_label)

        # Theme toggle removed; menu View -> Toggle Theme controls theme

    def update_validation(self, summary: Dict[str, Any]) -> None:
        """Update validation display in status bar"""
        self.current_validation_summary = summary
        if summary["status"] == "valid":
            self.validation_label.setText(translator.t('form_validation_valid'))
            self.validation_label.setStyleSheet(self.VALIDATION_VALID_STYLE)
            self.validation_label.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.validation_label.setText(f"⚠ {summary['message']} {translator.t('click_details')}")
            color = "#c62828" if summary["status"] == "invalid" else "#f57c00"
            self.validation_label.setStyleSheet(f"color: {color}; {self.VALIDATION_ERROR_STYLE}")
            self.validation_label.setCursor(Qt.CursorShape.PointingHandCursor)

    def new_file(self) -> None:
        """Create new form"""
        if ErrorHandler.confirm(self, translator.t('menu_new'), translator.t('new_form_confirm')):
            self.designer_tab.form = Form()
            self.designer_tab.form.title = translator.t('default_form_title')
            self.designer_tab.form.instructions = translator.t('default_instructions')
            self.designer_tab.title_input.setText(translator.t('default_form_title'))
            self.designer_tab.instructions_input.setText(translator.t('default_instructions'))
            self.designer_tab.update_question_list()
            self.designer_tab.update_preview()
            self.designer_tab.update_validation()

    def show_validation_details(self, event=None) -> None:
        """Show validation details dialog"""
        if self.current_validation_summary["status"] != "valid":
            self.designer_tab.show_validation_details()

    def toggle_theme(self, event=None) -> None:
        """Toggle between dark and light themes"""
        self.dark_mode = not self.dark_mode
        self.setStyleSheet(get_styles(self.dark_mode))
        QSettings().setValue('dark_mode', self.dark_mode)
        if hasattr(self, 'toggle_theme_action'):
            try:
                self.toggle_theme_action.setChecked(self.dark_mode)
            except Exception:
                pass

        # Theme label removed from status bar; no direct label updates

    def set_theme_checked(self, enabled: bool) -> None:
        """Apply theme directly from a checkable action state."""
        self.dark_mode = enabled
        self.setStyleSheet(get_styles(self.dark_mode))
        QSettings().setValue('dark_mode', self.dark_mode)
        # Theme label removed from status bar; no direct label updates

    def change_language(self, lang_code: str) -> None:
        """Change application language"""
        translator.set_language(lang_code)
        QSettings().setValue('language', lang_code)

        # Update window and UI elements
        self.setWindowTitle(translator.t('app_title'))
        self.refresh_menu()

        # Update status bar
        self.validation_label.setText(translator.t('form_validation_valid'))
        # Theme label is removed from status bar; nothing to update here

        # Update tab titles
        self.tab_widget.setTabText(0, translator.t('tab_designer'))
        self.tab_widget.setTabText(1, translator.t('tab_scanner'))
        self.tab_widget.setTabText(2, translator.t('tab_grading'))
        self._update_tab_header_labels()

        # Refresh all tabs UI
        self.designer_tab.refresh_ui()
        self.scanner_tab.refresh_ui()
        self.grading_tab.refresh_ui()
        # Persist normalized page settings for future preferences UI
        try:
            from config.app_config import AppConfig as _Cfg
            QSettings().setValue('page_size', (_Cfg.DEFAULT_PAGE_SIZE.value if hasattr(_Cfg.DEFAULT_PAGE_SIZE, "value") else str(_Cfg.DEFAULT_PAGE_SIZE)))
            QSettings().setValue('page_orientation', (_Cfg.DEFAULT_PAGE_ORIENTATION.value if hasattr(_Cfg.DEFAULT_PAGE_ORIENTATION, "value") else str(_Cfg.DEFAULT_PAGE_ORIENTATION)))
        except Exception:
            pass

    def _update_tab_header_labels(self) -> None:
        """Refresh the centered tab header button labels for current language."""
        try:
            titles = [translator.t('tab_designer'), translator.t('tab_scanner'), translator.t('tab_grading')]
            for btn, title in zip(getattr(self, 'tab_buttons', []), titles):
                btn.setText(title)
        except Exception:
            pass

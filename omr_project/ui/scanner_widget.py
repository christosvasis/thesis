import json
from pathlib import Path
import io
import platform
from typing import Dict, Any

from config.logger_config import get_logger, SCAN_LOGGER_NAME
from PIL import Image, ImageDraw

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QGroupBox,
    QTextEdit, QDoubleSpinBox, QFileDialog
)

try:  # PDF support
    import fitz  # type: ignore
    PDF_AVAILABLE = True
except ImportError:  # pragma: no cover
    PDF_AVAILABLE = False

from utils.error_handling import ErrorHandler
from core.scanning.worker_threads import WorkerThread, AnchorDetectionCommand, BubbleAnalysisCommand
from ui.zoomable_image import ZoomableImageLabel
from core.scanning.scanner_model import BubbleDetector
from config.app_config import AppConfig
from i18n import translator
from core.scanning.opencv import CV2_AVAILABLE


class ScannerWidget(QWidget):
    """Scanner functionality widget (reconstructed clean version)"""

    def __init__(self, parent):
        super().__init__()
        self.log = get_logger(SCAN_LOGGER_NAME)
        self.parent_app = parent

        # State containers
        self.current_image = None
        self.anchors: Dict[str, Dict[str, Any]] = {}
        self.omr_data: Dict[str, Any] | None = None
        self.bubble_positions: Dict[int, Dict[str, tuple]] = {}
        self.detector = BubbleDetector()
        self.analysis_results: Dict[int, Dict[str, Any]] = {}
        self.answers: Dict[int, str | None] = {}

        self.setup_ui()

    # ================= UI Construction =================
    def setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        left_panel = self._create_control_panel()
        left_panel.setMaximumWidth(340)
        layout.addWidget(left_panel)

        right_panel = self._create_image_panel()
        layout.addWidget(right_panel, 1)

    def _create_control_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Title
        self.title_label = QLabel(translator.t('scanner_title'))
        self.title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(self.title_label)

        # Step 1
        self.step1_group = QGroupBox(translator.t('step1_load'))
        step1_layout = QVBoxLayout(self.step1_group)
        self.load_btn = QPushButton(translator.t('load_image_pdf'))
        self.load_btn.clicked.connect(self.load_image)
        step1_layout.addWidget(self.load_btn)
        self.image_info = QLabel(translator.t('no_image_loaded'))
        self.image_info.setWordWrap(True)
        step1_layout.addWidget(self.image_info)
        layout.addWidget(self.step1_group)

        # Step 2
        self.step2_group = QGroupBox(translator.t('step2_process'))
        step2_layout = QVBoxLayout(self.step2_group)
        self.process_btn = QPushButton(translator.t('detect_analyze'))
        self.process_btn.clicked.connect(self.process_image)
        self.process_btn.setEnabled(False)
        step2_layout.addWidget(self.process_btn)
        self.status_label = QLabel("")
        step2_layout.addWidget(self.status_label)
        layout.addWidget(self.step2_group)

        # Step 3
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
        self.drag_mode_btn = QPushButton(translator.t('enable_drag_mode'))
        self.drag_mode_btn.clicked.connect(self.toggle_drag_mode)
        self.drag_mode_btn.setEnabled(False)
        self.drag_mode_btn.setCheckable(True)
        view_layout.addWidget(self.drag_mode_btn)
        layout.addWidget(self.view_group)

        layout.addStretch()
        return panel

    def _create_image_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Zoom toolbar
        zoom_bar = QHBoxLayout()
        zoom_controls = [
            (translator.t('zoom_in'), self.zoom_in, 'zoom_in_btn'),
            (translator.t('zoom_out'), self.zoom_out, 'zoom_out_btn'),
            (translator.t('zoom_fit'), self.zoom_fit, 'zoom_fit_btn'),
            (translator.t('zoom_100'), self.zoom_100, 'zoom_100_btn'),
            (translator.t('zoom_reset'), self.reset_view, 'reset_btn')
        ]
        for text, callback, attr in zoom_controls:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            btn.setEnabled(False)
            setattr(self, attr, btn)
            zoom_bar.addWidget(btn)
        zoom_bar.addStretch()
        self.zoom_info = QLabel(translator.t('no_image'))
        zoom_bar.addWidget(self.zoom_info)
        layout.addLayout(zoom_bar)

        # Image display
        self.image_display = ZoomableImageLabel()
        self.image_display.set_bubble_update_callback(self.on_bubble_coordinates_updated)
        layout.addWidget(self.image_display, 1)

        # Instructions
        self.zoom_info_label = QLabel(translator.t('zoom_pan_info'))
        self.zoom_info_label.setStyleSheet("color:#666;font-style:italic;")
        layout.addWidget(self.zoom_info_label)
        return panel

    # ================= Actions =================
    def load_image(self) -> None:
        filter_str = (translator.t('file_filter_all_with_pdf') if PDF_AVAILABLE
                      else translator.t('file_filter_images'))
        options = (QFileDialog.Option.DontUseNativeDialog
                   if platform.system() == "Linux" else QFileDialog.Option(0))
        file_path, _ = QFileDialog.getOpenFileName(
            self, translator.t('load_image_title'), '', filter_str, options=options
        )
        if not file_path:
            return
        try:
            if file_path.lower().endswith('.pdf') and PDF_AVAILABLE:
                doc = fitz.open(file_path)
                page = doc[0]
                mat = fitz.Matrix(AppConfig.EXPORT_DPI / AppConfig.POINTS_PER_INCH,
                                   AppConfig.EXPORT_DPI / AppConfig.POINTS_PER_INCH)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("ppm")
                self.current_image = Image.open(io.BytesIO(img_data))
                doc.close()
                self.log.info("Loaded PDF first page: %s", file_path)
            else:
                temp_image = Image.open(file_path)
                self.current_image = temp_image.convert('RGB') if temp_image.mode not in ('RGB', 'RGBA') else temp_image
                self.log.info("Loaded image: %s", file_path)
            self.image_display.set_image(self.current_image)
            filename = Path(file_path).name
            self.image_info.setText(f"✅ {filename}\n{self.current_image.width}×{self.current_image.height}")
            self._enable_zoom_controls(True)
            self.process_btn.setEnabled(True)
            self.update_zoom_info()
            self._reset_analysis()
        except Exception as e:  # pragma: no cover
            ErrorHandler.show_error(self, translator.t('error'), translator.t('load_image_error').format(str(e)))

    def process_image(self) -> None:
        if not self.current_image:
            return
        self.process_btn.setEnabled(False)
        self.status_label.setText(translator.t('detecting_anchors'))
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.quit(); self.worker.wait()
        self.worker = WorkerThread(AnchorDetectionCommand(self.current_image))
        self.worker.result_ready.connect(self.on_anchors_detected)
        self.worker.start()

    def on_anchors_detected(self, result) -> None:
        self.process_btn.setEnabled(True)
        if result['success']:
            self.anchors = result['anchors']
            self.status_label.setText(translator.t('anchors_detected').format(result['message']))
            self.load_omr_btn.setEnabled(True)
        else:
            self.status_label.setText(translator.t('anchor_detection_failed').format(result['message']))
            if not CV2_AVAILABLE:
                ErrorHandler.show_warning(self, translator.t('opencv_missing'), translator.t('opencv_install'))

    def load_omr(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, translator.t('load_answer_key'), '', translator.t('file_filter_omr_json')
        )
        if not file_path:
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.omr_data = json.load(f)
            self._transform_coordinates()
            filename = Path(file_path).name
            questions = len(self.omr_data.get('questions', []))
            self.omr_info.setText(f"✅ {filename}\n{questions} {translator.t('questions_word')}")
            self._analyze_bubbles()
        except Exception as e:  # pragma: no cover
            ErrorHandler.show_error(self, translator.t('error'), translator.t('load_omr_failed').format(str(e)))

    # ================= Processing =================
    def _transform_coordinates(self) -> None:
        if not self.anchors or not self.omr_data:
            return
        bubble_coords = self.omr_data.get('bubble_coordinates', {})
        self.bubble_positions = {}
        for q_str, q_data in bubble_coords.items():
            q_num = int(q_str)
            self.bubble_positions[q_num] = {}
            for option, option_data in q_data.items():
                if isinstance(option_data, dict):
                    rel = option_data.get('relative_to_anchor')
                    if rel and rel['anchor'] in self.anchors:
                        anchor = self.anchors[rel['anchor']]
                        x = anchor['x'] + rel['x']
                        y = anchor['y'] + rel['y']
                        self.bubble_positions[q_num][option] = (x, y)

    def _analyze_bubbles(self) -> None:
        if not self.current_image or not self.bubble_positions:
            return
        self.status_label.setText(translator.t('analyzing_bubbles'))
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.quit(); self.worker.wait()
        self.worker = WorkerThread(BubbleAnalysisCommand(self.detector, self.current_image, self.bubble_positions))
        self.worker.result_ready.connect(self.on_analysis_complete)
        self.worker.start()

    def on_analysis_complete(self, result) -> None:
        if result['success']:
            self.analysis_results = result['results']
            self.answers = result['answers']
            answered = sum(1 for a in self.answers.values() if a)
            total = len(self.answers)
            text = translator.t('analysis_complete_text').format(answered, total)
            for q_num in sorted(self.answers.keys()):
                answer = self.answers[q_num] or translator.t('blank_answer')
                text += translator.t('question_prefix').format(q_num, answer)
            self.results_text.setText(text)
            self.status_label.setText(translator.t('analysis_complete'))
            self.show_positions_btn.setEnabled(True)
            self.show_results_btn.setEnabled(True)
            self.drag_mode_btn.setEnabled(True)
        else:
            self.status_label.setText(translator.t('analysis_failed'))

    # ================= Overlays & Display =================
    def update_threshold(self) -> None:
        self.detector.filled_threshold = self.threshold_spin.value()
        if self.bubble_positions:
            self._analyze_bubbles()

    def show_positions(self) -> None:
        if not self.current_image or not self.bubble_positions:
            return
        try:
            overlay = self.current_image.copy()
            draw = ImageDraw.Draw(overlay)
            colors = {'A': 'red', 'B': 'green', 'C': 'blue', 'D': 'orange'}
            for q_num, options in self.bubble_positions.items():
                for option, (x, y) in options.items():
                    x, y = int(x), int(y)
                    r = int(self.detector.analysis_radius)
                    x1, y1 = max(0, x-r), max(0, y-r)
                    x2, y2 = min(overlay.width, x+r), min(overlay.height, y+r)
                    if x2 > x1 and y2 > y1:
                        draw.ellipse([x1, y1, x2, y2], outline=colors.get(option, 'purple'), width=AppConfig.OVERLAY_CIRCLE_OUTLINE_WIDTH)
                        tx, ty = max(0, x-AppConfig.OVERLAY_TEXT_OFFSET_SMALL), max(0, y-AppConfig.OVERLAY_TEXT_OFFSET_VERTICAL)
                        draw.text((tx, ty), option, fill=colors.get(option, 'purple'))
                if 'A' in options:
                    x, y = options['A']
                    x, y = int(x), int(y)
                    tx, ty = max(0, x-AppConfig.OVERLAY_LABEL_OFFSET_X), max(0, y-AppConfig.OVERLAY_TEXT_OFFSET_VERTICAL)
                    draw.text((tx, ty), f"Q{q_num}", fill='black')
            if self.anchors:
                for name, data in self.anchors.items():
                    x = int(data['x']); y = int(data['y']); w = int(data['width']); h = int(data['height'])
                    x1, y1 = max(0, x), max(0, y)
                    x2, y2 = min(overlay.width, x+w), min(overlay.height, y+h)
                    if x2 > x1 and y2 > y1:
                        draw.rectangle([x1, y1, x2, y2], outline='yellow', width=AppConfig.OVERLAY_ANCHOR_OUTLINE_WIDTH)
                        draw.text((x1+2, y1+2), name.replace('_', ' ').title(), fill='yellow')
            self.image_display.set_image(overlay)
            self.update_zoom_info()
        except Exception as e:  # pragma: no cover
            self.image_display.set_image(self.current_image)
            self.log.exception("Error drawing positions overlay: %s", e)

    def show_results(self) -> None:
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
                        x, y = int(x), int(y)
                        r = int(self.detector.analysis_radius)
                        x1, y1 = max(0, x-r), max(0, y-r)
                        x2, y2 = min(overlay.width, x+r), min(overlay.height, y+r)
                        if x2 > x1 and y2 > y1:
                            thickness = max(1, int(result.darkness_score * AppConfig.BUBBLE_THICKNESS_SCALE))
                            draw.ellipse([x1, y1, x2, y2], outline=colors.get(option, 'purple'), width=thickness)
                            if result.is_filled:
                                fx1, fy1 = max(0, x-AppConfig.BUBBLE_FILL_HALF_SIZE), max(0, y-AppConfig.BUBBLE_FILL_HALF_SIZE)
                                fx2, fy2 = min(overlay.width, x+AppConfig.BUBBLE_FILL_HALF_SIZE), min(overlay.height, y+AppConfig.BUBBLE_FILL_HALF_SIZE)
                                if fx2 > fx1 and fy2 > fy1:
                                    draw.ellipse([fx1, fy1, fx2, fy2], fill=colors.get(option, 'purple'))
            for q_num, answer in self.answers.items():
                if answer and q_num in self.bubble_positions and answer in self.bubble_positions[q_num]:
                    x, y = self.bubble_positions[q_num][answer]
                    x, y = int(x), int(y)
                    draw.text((max(0, x-50), max(0, y-8)), f"Q{q_num}→{answer}", fill='black')
            self.image_display.set_image(overlay)
            self.update_zoom_info()
        except Exception as e:  # pragma: no cover
            self.image_display.set_image(self.current_image)
            self.log.exception("Error drawing results overlay: %s", e)

    # ================= View helpers =================
    def reset_view(self) -> None:
        if self.current_image:
            self.image_display.set_image(self.current_image)
            self.update_zoom_info()

    def _reset_analysis(self) -> None:
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
        self.drag_mode_btn.setEnabled(False)
        self.drag_mode_btn.setChecked(False)

    def _enable_zoom_controls(self, enabled: bool) -> None:
        for btn in [self.zoom_in_btn, self.zoom_out_btn, self.zoom_fit_btn, self.zoom_100_btn, self.reset_btn]:
            btn.setEnabled(enabled)

    def zoom_in(self) -> None:
        self.image_display.zoom_in(); self.update_zoom_info()
    def zoom_out(self) -> None:
        self.image_display.zoom_out(); self.update_zoom_info()
    def zoom_fit(self) -> None:
        self.image_display.fit_to_window(); self.update_zoom_info()
    def zoom_100(self) -> None:
        self.image_display.zoom_100(); self.update_zoom_info()
    def update_zoom_info(self) -> None:
        self.zoom_info.setText(self.image_display.get_zoom_info())

    # ================= Drag Mode =================
    def toggle_drag_mode(self) -> None:
        try:
            enabled = self.drag_mode_btn.isChecked()
            self.image_display.set_drag_mode(enabled)
            if enabled:
                self.drag_mode_btn.setText(translator.t('disable_drag_mode'))
                if self.bubble_positions:
                    drag_coordinates = {}
                    for q_num, opts in self.bubble_positions.items():
                        drag_coordinates[q_num] = {opt: {'x': x, 'y': y, 'radius': AppConfig.DRAG_BUBBLE_DEFAULT_RADIUS} for opt, (x, y) in opts.items()}
                    self.image_display.set_bubble_coordinates(drag_coordinates)
                elif self.omr_data and 'bubble_coordinates' in self.omr_data:
                    self._transform_coordinates()
                    drag_coordinates = {}
                    for q_num, opts in self.bubble_positions.items():
                        drag_coordinates[q_num] = {opt: {'x': x, 'y': y, 'radius': AppConfig.DRAG_BUBBLE_DEFAULT_RADIUS} for opt, (x, y) in opts.items()}
                    self.image_display.set_bubble_coordinates(drag_coordinates)
            else:
                self.drag_mode_btn.setText(translator.t('enable_drag_mode'))
        except Exception as e:  # pragma: no cover
            self.log.exception("Error in toggle_drag_mode: %s", e)
            self.drag_mode_btn.setChecked(False)
            self.drag_mode_btn.setText(translator.t('enable_drag_mode'))

    def on_bubble_coordinates_updated(self, new_coordinates) -> None:
        try:
            converted = {}
            for q_num, bubbles in new_coordinates.items():
                converted[q_num] = {opt: (data['x'], data['y']) for opt, data in bubbles.items() if isinstance(data, dict) and 'x' in data and 'y' in data}
            self.bubble_positions = converted
            if self.omr_data and 'bubble_coordinates' in self.omr_data:
                for q_num, bubbles in new_coordinates.items():
                    if str(q_num) in self.omr_data['bubble_coordinates']:
                        for opt, data in bubbles.items():
                            if opt in self.omr_data['bubble_coordinates'][str(q_num)]:
                                self.omr_data['bubble_coordinates'][str(q_num)][opt].update(data)
        except Exception as e:  # pragma: no cover
            self.log.exception("Error in on_bubble_coordinates_updated: %s", e)

    def closeEvent(self, event):  # noqa: N802
        """Ensure worker thread is stopped when the widget is closing."""
        try:
            if hasattr(self, 'worker') and getattr(self, 'worker') is not None and self.worker.isRunning():
                self.worker.quit()
                self.worker.wait(1000)
        except Exception:
            pass
        super().closeEvent(event)

    # ================= i18n Refresh =================
    def refresh_ui(self) -> None:
        self.title_label.setText(translator.t('scanner_title'))
        self.step1_group.setTitle(translator.t('step1_load'))
        self.step2_group.setTitle(translator.t('step2_process'))
        self.step3_group.setTitle(translator.t('step3_answer_key'))
        self.settings_group.setTitle(translator.t('settings_title'))
        self.results_group.setTitle(translator.t('results_title'))
        self.view_group.setTitle(translator.t('view_title'))
        self.load_btn.setText(translator.t('load_image_pdf'))
        self.process_btn.setText(translator.t('detect_analyze'))
        self.load_omr_btn.setText(translator.t('load_omr_file'))
        self.show_positions_btn.setText(translator.t('show_positions'))
        self.show_results_btn.setText(translator.t('show_results'))
        self.zoom_in_btn.setText(translator.t('zoom_in'))
        self.zoom_out_btn.setText(translator.t('zoom_out'))
        self.zoom_fit_btn.setText(translator.t('zoom_fit'))
        self.zoom_100_btn.setText(translator.t('zoom_100'))
        self.reset_btn.setText(translator.t('zoom_reset'))
        self.threshold_label.setText(translator.t('filled_threshold'))
        self.zoom_info_label.setText(translator.t('zoom_pan_info'))
        if not self.current_image:
            self.image_info.setText(translator.t('no_image_loaded'))
        if not self.omr_data:
            self.omr_info.setText(translator.t('no_answer_key'))

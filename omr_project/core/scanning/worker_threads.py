from typing import Dict, Protocol, Any

import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal
from PIL import Image
from config.app_config import AppConfig
from core.scanning.opencv import CV2_AVAILABLE, cv2

class TaskCommand(Protocol):  # pragma: no cover - structural typing aid
    def execute(self) -> Dict[str, Any]: ...


class AnchorDetectionCommand:
    def __init__(self, image: Image.Image):
        self.image = image

    def execute(self) -> Dict[str, Any]:  # noqa: D401
        return WorkerThread._detect_anchors_static(self.image)


class BubbleAnalysisCommand:
    def __init__(self, detector, image: Image.Image, positions):
        self.detector = detector
        self.image = image
        self.positions = positions

    def execute(self) -> Dict[str, Any]:  # noqa: D401
        try:
            results, answers = self.detector.analyze_all_bubbles(self.image, self.positions)
            return {'success': True, 'results': results, 'answers': answers}
        except Exception as e:  # noqa: BLE001
            return {'success': False, 'message': str(e), 'results': {}, 'answers': {}}


class WorkerThread(QThread):
    """Generic background worker executing a TaskCommand."""
    result_ready = pyqtSignal(dict)

    def __init__(self, command: TaskCommand):
        super().__init__()
        self._command = command

    def run(self):  # noqa: D401
        try:
            result = self._command.execute()
            self.result_ready.emit(result)
        except Exception as e:  # noqa: BLE001
            self.result_ready.emit({'success': False, 'message': str(e)})

    @staticmethod
    def _detect_anchors_static(image: Image.Image) -> Dict:
        if not CV2_AVAILABLE:
            return {'success': False, 'message': 'OpenCV not available', 'anchors': {}}
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY) if len(img_array.shape) == 3 else img_array
        margin, size = AppConfig.ANCHOR_MARGIN, AppConfig.ANCHOR_SIZE
        expected = {
            'top_left': (margin, margin),
            'top_right': (image.width - margin - size, margin),
            'bottom_left': (margin, image.height - margin - size),
            'bottom_right': (image.width - margin - size, image.height - margin - size)
        }
        _, binary = cv2.threshold(gray, AppConfig.ANCHOR_THRESHOLD, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if (AppConfig.ANCHOR_CONTOUR_MIN <= w <= AppConfig.ANCHOR_CONTOUR_MAX and
                AppConfig.ANCHOR_CONTOUR_MIN <= h <= AppConfig.ANCHOR_CONTOUR_MAX and
                AppConfig.ANCHOR_ASPECT_MIN <= w / h <= AppConfig.ANCHOR_ASPECT_MAX):
                candidates.append((x, y, w, h))
        anchors = {}
        for name, (exp_x, exp_y) in expected.items():
            best_dist = float('inf')
            best_candidate = None
            for x, y, w, h in candidates:
                center_x, center_y = x + w/2, y + h/2
                dist = (center_x - (exp_x + size/2))**2 + (center_y - (exp_y + size/2))**2
                if dist < best_dist:
                    best_dist = dist
                    best_candidate = (x, y, w, h)
            if best_candidate:
                bx, by, bw, bh = best_candidate
                anchors[name] = {"x": int(bx), "y": int(by), "width": int(bw), "height": int(bh)}
        if len(anchors) < 4:
            return {'success': False, 'message': 'Failed to detect all anchors', 'anchors': anchors}
        return {'success': True, 'message': 'Anchors detected', 'anchors': anchors}

    # Legacy method names retained for backward compatibility (optional)
    def _detect_anchors(self, image: Image.Image) -> Dict:  # pragma: no cover
        return self._detect_anchors_static(image)

    def _analyze_bubbles(self, detector, image: Image.Image, positions):  # pragma: no cover
        return BubbleAnalysisCommand(detector, image, positions).execute()

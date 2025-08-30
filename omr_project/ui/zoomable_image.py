from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QBrush, QPen, QColor, QImage, QWheelEvent, QMouseEvent
from PyQt6.QtWidgets import QLabel
from PIL import Image
from i18n import translator
from config.logger_config import get_logger, UI_LOGGER_NAME
from config.app_config import AppConfig


class ZoomableImageLabel(QLabel):
    """Image display with zoom, pan, and draggable bubble capabilities."""

    def __init__(self):
        super().__init__()
        self.log = get_logger(UI_LOGGER_NAME)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("border: 2px solid #ccc;")
        self.setMinimumSize(800, 700)
        self.original_image = None
        self.current_pixmap = None
        self.zoom_factor = 1.0
        self.pan_offset = QPoint(0, 0)
        self.is_panning = False
        self.pan_start_point = QPoint()
        # Bubble manipulation
        self.drag_mode_enabled = False
        self.bubble_coordinates = {}
        self.dragging_bubble = None
        self.drag_start_point = QPoint()
        self.hover_bubble = None
        self.bubble_update_callback = None
        self.setMouseTracking(True)
        try:
            self.setText(translator.t('load_image_prompt'))
        except Exception:
            self.setText("Load an image to begin")

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        if self.original_image:
            self.fit_to_window()

    def set_image(self, image: Image.Image):
        try:
            if not isinstance(image, Image.Image):
                self.log.error("Invalid image type passed to set_image: %s", type(image))
                return
            if image.mode not in ['RGB', 'RGBA']:
                self.original_image = image.convert('RGB')
            else:
                self.original_image = image
            self.zoom_factor = 1.0
            self.pan_offset = QPoint(0, 0)
            self.fit_to_window()
        except Exception as e:  # noqa: BLE001
            self.log.exception("Error in set_image: %s", e)
            self.original_image = None

    def fit_to_window(self):
        if not self.original_image:
            return
        available_size = self.size()
        available_width = available_size.width() - 20
        available_height = available_size.height() - 20
        if available_width <= 0 or available_height <= 0:
            return
        img_width, img_height = self.original_image.size
        if img_width <= 0 or img_height <= 0:
            return
        width_ratio = available_width / img_width
        height_ratio = available_height / img_height
        self.zoom_factor = min(width_ratio, height_ratio)
        self.zoom_factor = min(self.zoom_factor, AppConfig.ZOOM_MAX_FACTOR)
        self.zoom_factor = max(self.zoom_factor, AppConfig.ZOOM_MIN_FACTOR)
        self.pan_offset = QPoint(0, 0)
        self.update_display()

    def zoom_in(self):
        if self.original_image and self.zoom_factor < AppConfig.ZOOM_MAX_FACTOR:
            old_factor = self.zoom_factor
            self.zoom_factor = min(self.zoom_factor * AppConfig.ZOOM_STEP_FACTOR, AppConfig.ZOOM_MAX_FACTOR)
            img_width, img_height = self.original_image.size
            if (int(img_width * self.zoom_factor) > AppConfig.ZOOM_LARGE_DIM_LIMIT or
                    int(img_height * self.zoom_factor) > AppConfig.ZOOM_LARGE_DIM_LIMIT):
                self.zoom_factor = old_factor
                self.log.warning("Maximum zoom reached to prevent memory issues")
                return
            self.update_display()

    def zoom_out(self):
        if self.original_image and self.zoom_factor > AppConfig.ZOOM_MIN_FACTOR:
            self.zoom_factor = max(self.zoom_factor / AppConfig.ZOOM_STEP_FACTOR, AppConfig.ZOOM_MIN_FACTOR)
            self.update_display()

    def zoom_100(self):
        if self.original_image:
            self.zoom_factor = 1.0
            self.pan_offset = QPoint(0, 0)
            self.update_display()

    def update_display(self):
        if not self.original_image:
            return
        img_width, img_height = self.original_image.size
        new_width = int(img_width * self.zoom_factor)
        new_height = int(img_height * self.zoom_factor)
        if new_width <= 0 or new_height <= 0:
            return
        if new_width > AppConfig.ZOOM_LARGE_DIM_LIMIT or new_height > AppConfig.ZOOM_LARGE_DIM_LIMIT:
            return
        try:
            resized_image = self.original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            if resized_image.mode != 'RGB':
                resized_image = resized_image.convert('RGB')
            width, height = resized_image.size
            rgb_data = resized_image.tobytes('raw', 'RGB')
            bytes_per_line = width * 3
            qimage = QImage(rgb_data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            if qimage.isNull():
                self.log.warning("Failed to create QImage from PIL data")
                return
            self.current_pixmap = QPixmap.fromImage(qimage)
            if self.current_pixmap.isNull():
                self.log.warning("Failed to create QPixmap from QImage")
                return
            self.update()
        except Exception as e:  # noqa: BLE001
            self.log.exception("Error in update_display: %s", e)
            try:
                fallback = self.original_image.convert('RGB') if self.original_image.mode != 'RGB' else self.original_image
                width, height = fallback.size
                rgb_data = fallback.tobytes('raw', 'RGB')
                qimage = QImage(rgb_data, width, height, width * 3, QImage.Format.Format_RGB888)
                if not qimage.isNull():
                    self.current_pixmap = QPixmap.fromImage(qimage)
                    self.update()
            except Exception as fe:  # noqa: BLE001
                self.log.exception("Error in fallback display: %s", fe)

    def paintEvent(self, event):  # noqa: N802
        if self.current_pixmap and not self.current_pixmap.isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            widget_center = self.rect().center()
            pixmap_center = self.current_pixmap.rect().center()
            x = widget_center.x() - pixmap_center.x() + self.pan_offset.x()
            y = widget_center.y() - pixmap_center.y() + self.pan_offset.y()
            painter.drawPixmap(x, y, self.current_pixmap)
            if self.drag_mode_enabled and self.bubble_coordinates:
                for q_num, question_bubbles in self.bubble_coordinates.items():
                    if not isinstance(question_bubbles, dict):
                        continue
                    for option, bubble_data in question_bubbles.items():
                        if not isinstance(bubble_data, dict):
                            continue
                        try:
                            bubble_x = float(bubble_data.get('x', 0))
                            bubble_y = float(bubble_data.get('y', 0))
                            radius = float(bubble_data.get('radius', AppConfig.DRAG_BUBBLE_DEFAULT_RADIUS))
                        except (ValueError, TypeError):
                            continue
                        try:
                            screen_pos = self.image_to_screen_coords(QPoint(int(bubble_x), int(bubble_y)))
                            screen_radius = max(1, int(radius * self.zoom_factor))
                        except Exception:
                            continue
                        if (self.hover_bubble and len(self.hover_bubble) >= 2 and
                                self.hover_bubble[0] == q_num and self.hover_bubble[1] == option):
                            color = QColor(255, 165, 0, 150)
                        elif (self.dragging_bubble and len(self.dragging_bubble) >= 2 and
                              self.dragging_bubble[0] == q_num and self.dragging_bubble[1] == option):
                            color = QColor(255, 0, 0, 150)
                        else:
                            color = QColor(0, 255, 0, 100)
                        try:
                            painter.setPen(QPen(color.darker(), 2))
                            painter.setBrush(QBrush(color))
                            painter.drawEllipse(screen_pos.x() - screen_radius, screen_pos.y() - screen_radius,
                                                screen_radius * 2, screen_radius * 2)
                            painter.setPen(QPen(QColor(0, 0, 0), 1))
                            painter.drawText(screen_pos.x() - 5, screen_pos.y() + 5, str(option))
                        except Exception:
                            continue
        else:
            super().paintEvent(event)

    def wheelEvent(self, event: QWheelEvent):  # noqa: N802
        if self.original_image:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()

    def mousePressEvent(self, event: QMouseEvent):  # noqa: N802
        try:
            if self.drag_mode_enabled and event.button() == Qt.MouseButton.LeftButton:
                bubble = self.get_bubble_at_position(event.position().toPoint())
                if bubble:
                    self.dragging_bubble = bubble
                    self.drag_start_point = event.position().toPoint()
                    self.setCursor(Qt.CursorShape.ClosedHandCursor)
                    return
            if event.button() == Qt.MouseButton.MiddleButton or \
                    (event.button() == Qt.MouseButton.LeftButton and
                     event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                self.is_panning = True
                self.pan_start_point = event.position().toPoint()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
        except Exception as e:  # noqa: BLE001
            self.log.exception("Error in mousePressEvent: %s", e)

    def mouseMoveEvent(self, event: QMouseEvent):  # noqa: N802
        try:
            if self.dragging_bubble:
                delta = event.position().toPoint() - self.drag_start_point
                if not isinstance(self.dragging_bubble, tuple) or len(self.dragging_bubble) != 3:
                    self.dragging_bubble = None
                    return
                q_num, option, bubble_data = self.dragging_bubble
                if not isinstance(bubble_data, dict) or 'x' not in bubble_data or 'y' not in bubble_data:
                    self.dragging_bubble = None
                    return
                if self.zoom_factor <= 0:
                    self.zoom_factor = 1.0
                try:
                    current_x = float(bubble_data['x'])
                    current_y = float(bubble_data['y'])
                    bubble_data['x'] = current_x + (delta.x() / self.zoom_factor)
                    bubble_data['y'] = current_y + (delta.y() / self.zoom_factor)
                except (ValueError, TypeError, KeyError):
                    self.dragging_bubble = None
                    return
                self.drag_start_point = event.position().toPoint()
                self.update()
                return
            if self.drag_mode_enabled:
                bubble = self.get_bubble_at_position(event.position().toPoint())
                if bubble != self.hover_bubble:
                    self.hover_bubble = bubble
                    if bubble:
                        self.setCursor(Qt.CursorShape.OpenHandCursor)
                    else:
                        self.setCursor(Qt.CursorShape.ArrowCursor)
                    self.update()
            if self.is_panning:
                delta = event.position().toPoint() - self.pan_start_point
                self.pan_offset += delta
                self.pan_start_point = event.position().toPoint()
                self.update()
        except Exception as e:  # noqa: BLE001
            self.log.exception("Error in mouseMoveEvent: %s", e)
            self.dragging_bubble = None

    def mouseReleaseEvent(self, event: QMouseEvent):  # noqa: N802
        try:
            if self.dragging_bubble:
                if self.bubble_update_callback:
                    try:
                        self.bubble_update_callback(self.bubble_coordinates)
                    except Exception as e:  # noqa: BLE001
                        self.log.exception("Error in bubble_update_callback: %s", e)
                self.dragging_bubble = None
                self.setCursor(Qt.CursorShape.OpenHandCursor if self.drag_mode_enabled else Qt.CursorShape.ArrowCursor)
                return
        except Exception as e:  # noqa: BLE001
            self.log.exception("Error in mouseReleaseEvent: %s", e)
            self.dragging_bubble = None
        if self.is_panning:
            self.is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def get_zoom_info(self) -> str:
        if not self.original_image:
            return translator.t('no_image')
        try:
            return translator.t('zoom_label').format(int(self.zoom_factor * 100))
        except Exception:
            return f"Zoom: {self.zoom_factor*100:.0f}%"

    def set_drag_mode(self, enabled: bool):
        self.drag_mode_enabled = enabled
        self.setCursor(Qt.CursorShape.OpenHandCursor if enabled else Qt.CursorShape.ArrowCursor)
        self.update()

    def set_bubble_coordinates(self, coordinates: dict):
        self.bubble_coordinates = coordinates
        self.update()

    def set_bubble_update_callback(self, callback):
        self.bubble_update_callback = callback

    def get_bubble_at_position(self, pos: QPoint):
        try:
            if not self.bubble_coordinates:
                return None
            image_pos = self.screen_to_image_coords(pos)
            for q_num, question_bubbles in self.bubble_coordinates.items():
                for option, bubble_data in question_bubbles.items():
                    if not isinstance(bubble_data, dict):
                        continue
                    try:
                        bubble_x = float(bubble_data.get('x', 0))
                        bubble_y = float(bubble_data.get('y', 0))
                        radius = float(bubble_data.get('radius', AppConfig.DRAG_BUBBLE_DEFAULT_RADIUS))
                    except (ValueError, TypeError):
                        continue
                    distance = ((image_pos.x() - bubble_x) ** 2 + (image_pos.y() - bubble_y) ** 2) ** 0.5
                    if distance <= radius:
                        return (q_num, option, bubble_data)
            return None
        except Exception as e:  # noqa: BLE001
            self.log.exception("Error in get_bubble_at_position: %s", e)
            return None

    def screen_to_image_coords(self, screen_pos: QPoint):
        try:
            if not self.original_image or not self.current_pixmap:
                return screen_pos
            if self.zoom_factor <= 0:
                self.zoom_factor = 1.0
            pixmap_rect = self.current_pixmap.rect()
            widget_rect = self.rect()
            x_offset = (widget_rect.width() - pixmap_rect.width()) // 2 + self.pan_offset.x()
            y_offset = (widget_rect.height() - pixmap_rect.height()) // 2 + self.pan_offset.y()
            image_x = (screen_pos.x() - x_offset) / self.zoom_factor
            image_y = (screen_pos.y() - y_offset) / self.zoom_factor
            return QPoint(int(image_x), int(image_y))
        except Exception as e:  # noqa: BLE001
            self.log.exception("Error in screen_to_image_coords: %s", e)
            return screen_pos

    def image_to_screen_coords(self, image_pos: QPoint):
        try:
            if not self.original_image or not self.current_pixmap:
                return image_pos
            if self.zoom_factor <= 0:
                self.zoom_factor = 1.0
            pixmap_rect = self.current_pixmap.rect()
            widget_rect = self.rect()
            x_offset = (widget_rect.width() - pixmap_rect.width()) // 2 + self.pan_offset.x()
            y_offset = (widget_rect.height() - pixmap_rect.height()) // 2 + self.pan_offset.y()
            screen_x = image_pos.x() * self.zoom_factor + x_offset
            screen_y = image_pos.y() * self.zoom_factor + y_offset
            return QPoint(int(screen_x), int(screen_y))
        except Exception as e:  # noqa: BLE001
            self.log.exception("Error in image_to_screen_coords: %s", e)
            return image_pos

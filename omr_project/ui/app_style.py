from pathlib import Path


def get_color_scheme(dark_mode=False):
    """
    Generate a consistent color palette for the application interface.
    
    Provides carefully selected colors that ensure good contrast and readability
    across both light and dark theme variations. Colors are chosen to meet
    accessibility standards while maintaining visual appeal.
    
    Args:
        dark_mode (bool): Whether to return dark theme colors
        
    Returns:
        dict: Color scheme dictionary with semantic color names
    """
    if dark_mode:
        # Dark theme optimized for reduced eye strain in low-light conditions
        return {
            'bg': '#0f172a',           # Primary background
            'panel': '#1e293b',        # Panel and card backgrounds
            'text': '#e2e8f0',         # Primary text color
            'border': '#334155',       # Border and separator lines
            'input_border': '#475569', # Input field borders
            'hover': '#334155',        # Hover state background
            'accent': '#3b82f6',       # Primary accent color
            'button_bg': '#1e293b',    # Button backgrounds
            'button_hover': '#334155', # Button hover state
            'input_bg': '#1e293b'      # Input field backgrounds
        }
    else:
        # Light theme with high contrast for optimal readability
        return {
            'bg': '#f7f9fc',          # Clean primary background
            'panel': '#ffffff',        # Panel and card backgrounds
            'text': '#1f2937',         # High contrast text
            'border': '#d1d5db',       # Subtle border lines
            'input_border': '#9ca3af', # Visible input borders
            'hover': '#e5e7eb',        # Gentle hover feedback
            'accent': '#2563eb',       # Primary accent color
            'button_bg': '#f9fafb',    # Button backgrounds
            'button_hover': '#f3f4f6', # Button hover state
            'input_bg': '#ffffff',     # Input field backgrounds
            'secondary_text': '#6b7280', # Secondary text elements
            'success': '#059669',      # Success state indicator
            'warning': '#d97706',      # Warning state indicator
            'danger': '#dc2626'        # Error state indicator
        }

def _load_qss_from_file(dark_mode: bool) -> str | None:
    """Optionally load a .qss file if present.

    Looks for ui/style/dark.qss or ui/style/light.qss (relative to this file).
    Returns file contents if found, otherwise None.
    """
    style_dir = Path(__file__).parent / "style"
    candidate = style_dir / ("dark.qss" if dark_mode else "light.qss")
    try:
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")
    except Exception:
        # Silently fall back to generated stylesheet
        return None
    return None


def get_styles(dark_mode=False):
    """
    Generate a giant CSS-like stylesheet for the entire app.
    
    Qt apps need styling just like web pages, but with more weird syntax.
    This creates one massive style string that makes everything look
    consistent and not like it came from 1995.
    
    Args:
        dark_mode (bool): Whether to make it dark and brooding
        
    Returns:
        str: One enormous stylesheet that covers every widget type
    """
    # Prefer external QSS if available for theme flexibility
    qss = _load_qss_from_file(dark_mode)
    if qss is not None:
        return qss

    # Fallback: generate stylesheet from color scheme
    c = get_color_scheme(dark_mode)

    # Here's the mother of all stylesheets - covers every Qt widget we use
    radius_large = 8
    radius_med = 6
    radius_small = 4
    return f"""
QMainWindow{{background:{c['bg']};color:{c['text']};font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:13px}}
QFrame{{background:{c['panel']};border:1px solid {c['border']};border-radius:{radius_large}px;padding:8px}}
QPushButton{{background:{c.get('button_bg',c['panel'])};color:{c['text']};border:1px solid {c['input_border']};border-radius:{radius_med}px;padding:6px 12px;font-weight:500;min-height:26px}}
QPushButton:hover{{background:{c.get('button_hover',c['hover'])};border-color:{c['accent']}}}
QPushButton:pressed{{background:{c['hover']}}}
QPushButton[class="primary"]{{background:{c['accent']};color:white;border-color:{c['accent']}}}
QPushButton[class="primary"]:hover{{background:{'#1d4ed8' if not dark_mode else '#3b82f6'};border-color:{'#1d4ed8' if not dark_mode else '#3b82f6'}}}
QPushButton[class="success"]{{background:{c.get('success','#059669')};color:white;border-color:{c.get('success','#059669')}}}
QPushButton[class="success"]:hover{{background:{'#047857' if not dark_mode else '#10b981'}}}
QPushButton[class="danger"]{{background:{c.get('danger','#dc2626')};color:white;border-color:{c.get('danger','#dc2626')}}}
QPushButton[class="danger"]:hover{{background:{'#b91c1c' if not dark_mode else '#ef4444'}}}
QLineEdit,QTextEdit{{background:{c.get('input_bg',c['panel'])};color:{c['text']};border:1px solid {c['input_border']};border-radius:{radius_med}px;padding:6px 8px;min-height:20px;selection-background-color:{c['accent']};selection-color:white}}
QLineEdit:focus,QTextEdit:focus{{border-color:{c['accent']};outline:0}}
QComboBox{{background:{c.get('input_bg',c['panel'])};color:{c['text']};border:1px solid {c['input_border']};border-radius:{radius_med}px;padding:4px 8px;min-width:50px}}
QComboBox:focus{{border-color:{c['accent']}}}
QComboBox::drop-down{{subcontrol-origin:padding;subcontrol-position:top right;width:20px;border-left:1px solid {c['input_border']};border-top-right-radius:{radius_small}px;border-bottom-right-radius:{radius_small}px;background:{c.get('button_bg',c['panel'])}}}
QComboBox::down-arrow{{image:none;border:2px solid {c['text']};border-top:none;border-left:none;width:6px;height:6px;margin:4px}}
QComboBox QAbstractItemView{{background:{c['panel']};color:{c['text']};border:1px solid {c['input_border']};border-radius:{radius_med}px;selection-background-color:{c['accent']};selection-color:white;outline:0}}
QListWidget{{background:{c['panel']};color:{c['text']};border:1px solid {c['border']};border-radius:{radius_med}px;outline:0}}
QListWidget::item{{padding:4px 8px;border-bottom:1px solid {c['border']}}}
QListWidget::item:selected{{background:{c['accent']};color:white}}
QListWidget::item:hover{{background:{c['hover']}}}
QTabWidget::pane{{background:{c['panel']};border:1px solid {c['border']};border-radius:{radius_large}px}}
QTabBar::tab{{background:{c['bg']};color:{c.get('secondary_text',c['text'])};border:1px solid {c['border']};padding:8px 16px;margin-right:2px;border-radius:{radius_small}px}}
QTabBar::tab:selected{{background:{c['panel']};color:{c['accent']};font-weight:600;border-bottom-color:{c['panel']}}}
QTabBar::tab:hover{{background:{c['hover']}}}
QLabel{{color:{c['text']}}}
QGroupBox{{color:{c['text']};border:1px solid {c['border']};border-radius:{radius_large}px;margin-top:8px;padding-top:8px}}
QGroupBox::title{{color:{c['text']};subcontrol-origin:margin;left:8px;padding:0 4px}}
QMenuBar{{background:{c['panel']};color:{c['text']};border-bottom:1px solid {c['border']}}}
QMenuBar::item{{background:transparent;padding:4px 8px;margin:2px;border-radius:{radius_small}px}}
QMenuBar::item:selected{{background:{c['hover']};color:{c['text']}}}
QMenuBar::item:pressed{{background:{c['accent']};color:white}}
QMenu{{background:{c['panel']};color:{c['text']};border:1px solid {c['border']};border-radius:{radius_med}px;padding:4px 0}}
QMenu::item{{padding:6px 12px;margin:1px 4px;border-radius:{radius_small}px}}
QMenu::item:selected{{background:{c['accent']};color:white}}
QMenu::separator{{height:1px;background:{c['border']};margin:4px 8px}}
QStatusBar{{background:{c['panel']};color:{c['text']};border-top:1px solid {c['border']}}}
QDoubleSpinBox,QSpinBox{{background:{c.get('input_bg',c['panel'])};color:{c['text']};border:1px solid {c['input_border']};border-radius:{radius_med}px;padding:4px 8px;min-height:20px}}
QScrollArea{{background:{c['panel']};border:1px solid {c['border']};border-radius:{radius_large}px}}
QScrollBar:vertical{{background:{c['bg']};width:10px;border-radius:5px}}
QScrollBar::handle:vertical{{background:{c['hover']};border-radius:5px;min-height:20px}}
QScrollBar::handle:vertical:hover{{background:{c['accent']}}}
QTableWidget{{background:{c['panel']};color:{c['text']};border:1px solid {c['border']};border-radius:{radius_med}px;gridline-color:{c['border']}}}
QTableWidget::item{{padding:4px 8px;border-bottom:1px solid {c['border']}}}
QTableWidget::item:selected{{background:{c['accent']};color:white}}
QTableWidget QHeaderView::section{{background:{c['bg']};color:{c['text']};border:1px solid {c['border']};padding:4px 8px}}
QCheckBox{{color:{c['text']}}}
QCheckBox::indicator{{width:16px;height:16px;border:1px solid {c['input_border']};border-radius:{radius_small}px;background:{c.get('input_bg',c['panel'])}}}
QCheckBox::indicator:checked{{background:{c['accent']};color:white}}""".strip()

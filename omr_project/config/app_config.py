# ============================================================================
# APPLICATION CONFIGURATION AND CONSTANTS
# ============================================================================

from enum import Enum


class AppConfig:
    """
    Centralized configuration management for application settings.
    
    This class consolidates all configuration parameters, magic numbers, and 
    default values used throughout the application. Centralizing these values
    makes maintenance easier and provides a single source of truth for 
    application behavior.
    """

    # Form design constraints and defaults
    MAX_OPTIONS_COUNT = 4                    # Maximum answer choices per question (A, B, C, D)
    DEFAULT_POINTS_RANGE = 10               # Default range for question point values (1-10)
    PREVIEW_TEXT_TRUNCATE_LENGTH = 40       # Character limit for question preview text

    # PDF layout and formatting specifications
    PDF_MARGINS = {                         # Page margins in inches for consistent printing
        'right': 0.75,                      # Right margin
        'left': 0.75,                       # Left margin  
        'top': 1.0,                         # Top margin for headers
        'bottom': 1.0                       # Bottom margin for footers
    }
    FONT_SIZES = {                          # Typography scale for consistent text hierarchy
        'title': 18,                        # Main form titles
        'header': 16,                       # Section headers
        'normal': 12,                       # Body text and questions
        'instruction': 10,                  # Instructional text
        'small': 8                          # Fine print and metadata
    }
    QUESTION_HEIGHT = 0.6                   # Height allocation per question in inches
    MIN_BOTTOM_MARGIN = 1.0                 # Minimum bottom margin to prevent content cutoff

    # Bubble detection and image processing parameters
    BUBBLE_RADIUS = 10                      # Expected bubble radius in pixels
    BUBBLE_SPACING = 0.8                    # Spacing between bubbles as fraction of bubble size
    ANALYSIS_RADIUS = 18                    # Analysis area around each bubble in pixels
    FILLED_THRESHOLD = 0.3                  # Darkness threshold for filled bubble detection (0-1)
    # Anchor detection parameters (used in image scanning)
    ANCHOR_MARGIN = 75                      # Expected margin from page border to anchor square (px)
    ANCHOR_SIZE = 31                        # Expected anchor square side length (px)
    ANCHOR_CONTOUR_MIN = 20                 # Min width/height of contour to be considered anchor (px)
    ANCHOR_CONTOUR_MAX = 50                 # Max width/height of contour to be considered anchor (px)
    ANCHOR_ASPECT_MIN = 0.7                 # Min aspect ratio (w/h) for anchor square candidacy
    ANCHOR_ASPECT_MAX = 1.3                 # Max aspect ratio (w/h) for anchor square candidacy
    ANCHOR_THRESHOLD = 127                  # Threshold value for binary inversion in anchor detection
    # Zoom / image interaction parameters
    ZOOM_MIN_FACTOR = 0.05                  # Minimum zoom level
    ZOOM_MAX_FACTOR = 5.0                   # Maximum zoom level
    ZOOM_LARGE_DIM_LIMIT = 10000            # Max allowed dimension in pixels after scaling to avoid memory issues
    DRAG_BUBBLE_DEFAULT_RADIUS = 20         # Default bubble radius used in drag mode editing
    BUBBLE_FILL_HALF_SIZE = 8               # Half-size in pixels for filled bubble overlay highlight
    BUBBLE_THICKNESS_SCALE = 5              # Multiplier for drawing outline thickness based on darkness score
    ZOOM_STEP_FACTOR = 1.25                 # Multiplicative step for zoom in/out operations
    OVERLAY_CIRCLE_OUTLINE_WIDTH = 2        # Outline width for bubble position circles
    OVERLAY_ANCHOR_OUTLINE_WIDTH = 3        # Outline width for anchor rectangles
    OVERLAY_LABEL_OFFSET_X = 30             # Horizontal offset for question label text positioning
    OVERLAY_TEXT_OFFSET_SMALL = 5           # Small x offset for text centering tweaks
    OVERLAY_TEXT_OFFSET_VERTICAL = 8        # Vertical offset for text alignment above bubble center
    
    # Export-for-scanner layout (pixel offsets at 150 DPI)
    EXPORT_ANCHOR_TO_FIRST_BUBBLE_X = 120   # px from top-left anchor to first bubble (X)
    EXPORT_ANCHOR_TO_FIRST_BUBBLE_Y = 380   # px from top-left anchor to first bubble (Y)
    EXPORT_BUBBLE_SPACING_X = 120           # px horizontal spacing between bubbles
    EXPORT_BUBBLE_SPACING_Y = 90            # px vertical spacing between questions
    # PDF layout fine-tuning
    PDF_HEADER_TITLE_Y_OFFSET = 0.8  # inches from top for main title baseline
    PDF_HEADER_SUBTITLE_Y_OFFSET = 1.1  # inches from top for subtitle / sheet label
    PDF_HEADER_SEPARATOR_Y_OFFSET = 1.3  # inches from top for header separator line
    PDF_HEADER_RETURN_Y_OFFSET = 1.7  # inches from top for content start after header
    PDF_CONTINUATION_HEADER_Y_OFFSET = 0.5  # inches from top for continuation header title
    PDF_CONTINUATION_SEPARATOR_Y_OFFSET = 0.7  # inches from top for continuation header separator
    PDF_CONTINUATION_RETURN_Y_OFFSET = 1.2  # inches from top for continuation page content start
    PDF_QUESTION_NUMBER_RIGHT_X = 1.1  # inches x-position for right-aligned question number
    PDF_QUESTION_BUBBLE_START_X = 1.3  # inches starting x-position for first bubble
    PDF_ALIGNMENT_SQUARE_SIZE = 15  # pixels size of alignment squares
    PDF_SIDE_MARGIN_INCH = 0.75  # Common left/right margin for lines and blocks
    PDF_STUDENT_ID_X = 4.8       # inches x-position start for student ID label
    PDF_STUDENT_NAME_UNDERLINE_END = 4.5  # inches underline end for student name
    PDF_STUDENT_ID_UNDERLINE_END = 7.5    # inches underline end for student id
    PDF_STUDENT_LABEL_LINE_OFFSET = 0.1   # inches gap between label and underline start
    PDF_STUDENT_SECTION_Y_REDUCTION = 0.4 # inches vertical reduction after student info line
    PDF_INSTRUCTION_LINE_SPACING1 = 0.2   # inches spacing after first instruction line
    PDF_INSTRUCTION_LINE_SPACING2 = 0.3   # inches spacing after second instruction line
    PDF_INSTRUCTION_SECTION_SPACING = 0.5 # inches spacing after instructions block
    PDF_FOOTER_Y = 0.5                    # inches from bottom for footer text
    PDF_ALIGNMENT_SQUARE_OFFSET = 0.5     # inches offset of alignment squares from page edges

    # Export rendering configuration
    EXPORT_DPI = 150                      # Target DPI for exported coordinates/rasterization
    POINTS_PER_INCH = 72                  # ReportLab points per inch conversion
    class PageSize(str, Enum):
        LETTER = 'letter'
        A4 = 'a4'

    class Orientation(str, Enum):
        PORTRAIT = 'portrait'
        LANDSCAPE = 'landscape'

    DEFAULT_PAGE_SIZE: 'AppConfig.PageSize' = PageSize.LETTER
    DEFAULT_PAGE_ORIENTATION: 'AppConfig.Orientation' = Orientation.PORTRAIT
    TIMESTAMP_FMT = "%Y%m%d_%H%M"         # Default timestamp format for filenames
    TIMESTAMP_FMT_SEC = "%Y%m%d_%H%M%S"   # Timestamp format with seconds (for IDs)

    # Grading thresholds
    PASSING_PERCENTAGE = 60.0             # Passing threshold percentage

    # Export metadata
    EXPORT_FORMAT_VERSION = "2.0"         # .omr format version
    APP_GENERATOR = "OMR Unified Application v1.0"  # Generator identifier

    # User interface layout configuration
    SPLITTER_SIZES = [300, 600, 250]       # Default panel widths for main interface
    TABLE_HEADER_HEIGHT = 40               # Header height for data tables
    COLUMN_WIDTHS = {                       # Optimal column widths for data display
        'student_name': 150,                # Student name column
        'student_id': 100,                  # Student ID column
        'score': 80,                        # Score column
        'total': 80,                        # Total points column
        'percentage': 100                   # Percentage column
    }

    # Grading penalties (used in .omr export)
    PENALTY_WRONG = 0.25
    PENALTY_BLANK = 0.0

    # Page size configuration (single source of truth)
    # Keys must be lowercase canonical names; values are (width, height) in inches.
    PAGE_SIZES_INCHES = {
        'letter': (8.5, 11.0),
        'a4': (8.27, 11.69),
    }
    SUPPORTED_PAGE_SIZES = tuple(PAGE_SIZES_INCHES.keys())
    SUPPORTED_PAGE_ORIENTATIONS = (Orientation.PORTRAIT.value, Orientation.LANDSCAPE.value)

    # Supported file formats for import/export operations
    SUPPORTED_IMAGE_FORMATS = ['*.png', '*.jpg', '*.jpeg', '*.tiff', '*.bmp']  # Accepted image types
    SUPPORTED_DOCUMENT_FORMATS = ['*.pdf']  # Accepted document formats
    
    # File dialog filters are localized via i18n now

    # System font paths for cross-platform compatibility
    FONT_PATHS = {
        "Darwin": [                         # macOS font locations
            "/System/Library/Fonts/Geneva.ttf", 
            "/Library/Fonts/Arial.ttf", 
            "/System/Library/Fonts/Helvetica.ttc"
        ],
        "Linux": [                          # Linux font locations
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 
            "/usr/share/fonts/TTF/arial.ttf"
        ],
        "Windows": [                        # Windows font locations
            "C:/Windows/Fonts/arial.ttf", 
            "C:/Windows/Fonts/Arial.ttf", 
            "C:/Windows/Fonts/calibri.ttf"
        ]
    }

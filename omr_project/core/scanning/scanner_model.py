import numpy as np
from typing import NamedTuple, Tuple, Dict
from PIL import Image
from config.app_config import AppConfig

class BubbleAnalysisResult(NamedTuple):
    """
    Result of analyzing a single answer bubble.
    
    Contains the computed metrics for determining if a bubble is filled,
    including darkness score, binary fill determination, and confidence level.
    
    Attributes:
        darkness_score (float): Normalized darkness value (0.0-1.0, higher = darker)
        is_filled (bool): Whether bubble is considered filled based on threshold
        confidence (float): Confidence level of the analysis (0.0-1.0)
    """
    darkness_score: float
    is_filled: bool
    confidence: float

class BubbleDetector:
    """
    Handles bubble detection and analysis for OMR scanning.
    
    This class implements image processing algorithms to analyze answer bubbles
    on scanned OMR sheets. It determines whether bubbles are filled based on
    darkness analysis and provides confidence scoring for the results.

    The detection process involves:
    1. Converting images to grayscale for analysis
    2. Sampling pixel values within a circular area around each bubble
    3. Computing darkness scores and confidence levels
    4. Applying thresholds to determine if bubbles are filled

    Attributes:
        analysis_radius (int): Pixel radius for bubble analysis area
        filled_threshold (float): Darkness threshold for filled detection (0.0-1.0)
    """

    def __init__(self):
        """Initialize bubble detector with configuration from AppConfig."""
        self.analysis_radius = AppConfig.ANALYSIS_RADIUS    # Size of analysis area
        self.filled_threshold = AppConfig.FILLED_THRESHOLD  # Darkness threshold

    def analyze_bubble(self, image: Image.Image, center_x: int, center_y: int) -> BubbleAnalysisResult:
        """
        Analyze a single bubble to determine if it's filled.
        
        Performs image analysis on a circular region around the specified center
        point to determine bubble fill status. Uses RGB to grayscale conversion
        and statistical analysis of pixel intensities.
        
        Args:
            image (Image.Image): Input image containing the bubble
            center_x (int): X coordinate of bubble center
            center_y (int): Y coordinate of bubble center
            
        Returns:
            BubbleAnalysisResult: Analysis result with darkness score, fill status, and confidence
        """
        try:
            # Convert PIL image to numpy array for processing
            img_array = np.array(image)
            
            # Convert to grayscale using standard RGB weights if needed
            if len(img_array.shape) == 3:
                # RGB to grayscale conversion using standard luminance weights
                gray = np.dot(img_array[...,:3], [0.299, 0.587, 0.114])
            else:
                gray = img_array.astype(float)

            height, width = gray.shape
            
            # Check if analysis area is within image bounds
            if (center_x - self.analysis_radius < 0 or center_x + self.analysis_radius >= width or
                center_y - self.analysis_radius < 0 or center_y + self.analysis_radius >= height):
                return BubbleAnalysisResult(0.0, False, 0.0)

            # Sample pixel values within circular area around bubble center
            pixel_values = []
            for dy in range(-self.analysis_radius, self.analysis_radius + 1):
                for dx in range(-self.analysis_radius, self.analysis_radius + 1):
                    # Only include pixels within the circular radius
                    if dx*dx + dy*dy <= self.analysis_radius*self.analysis_radius:
                        pixel_values.append(gray[center_y + dy, center_x + dx])

            # Handle edge case of no valid pixels
            if not pixel_values:
                return BubbleAnalysisResult(0.0, False, 0.0)

            # Calculate statistics for bubble analysis
            mean_intensity = np.mean(pixel_values)
            darkness_score = (255.0 - mean_intensity) / 255.0  # Convert to 0-1 scale (higher = darker)
            
            # Confidence based on pixel value consistency (lower std dev = higher confidence)
            confidence = max(0.0, 1.0 - (np.std(pixel_values) / 100.0))
            
            # Determine if bubble is filled based on threshold
            is_filled = darkness_score >= self.filled_threshold

            return BubbleAnalysisResult(darkness_score, is_filled, min(1.0, confidence))

        except Exception:
            # Return safe defaults if analysis fails
            return BubbleAnalysisResult(0.0, False, 0.0)

    def analyze_all_bubbles(self, image: Image.Image, positions: Dict[int, Dict[str, Tuple[float, float]]]) -> Tuple[Dict, Dict]:
        """
        Analyze all bubbles in an image and determine student answers.
        
        Processes all bubble positions for all questions and determines the
        most likely answer for each question based on bubble fill analysis.
        Handles cases where multiple bubbles are filled or no bubbles are filled.
        
        Args:
            image (Image.Image): Scanned OMR sheet image
            positions (Dict): Bubble positions by question number and option
            
        Returns:
            tuple: (analysis_results, student_answers)
                - analysis_results: Detailed analysis for each bubble
                - student_answers: Determined answer for each question
        """
        results = {}
        answers = {}

        # Process each question
        for q_num, options in positions.items():
            results[q_num] = {}
            filled_options = []

            # Analyze each option bubble for this question
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

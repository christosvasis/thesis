try:
    import cv2  # type: ignore
    CV2_AVAILABLE = True
except ImportError:  # pragma: no cover
    CV2_AVAILABLE = False
    cv2 = None  # type: ignore

__all__ = ["CV2_AVAILABLE", "cv2"]


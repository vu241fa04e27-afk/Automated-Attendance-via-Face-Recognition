"""
Face Detection Module for Automated Attendance System.
Supports both MTCNN (deep learning based) and OpenCV Haar Cascade with automatic fallback.
Performs face localization, bounding box extraction, face cropping, and preprocessing.
"""

import os
import cv2
import numpy as np
from PIL import Image
from typing import List, Tuple, Dict, Any, Optional
import config

# Try to import MTCNN from facenet_pytorch
MTCNN_AVAILABLE = False
try:
    from facenet_pytorch import MTCNN
    import torch
    MTCNN_AVAILABLE = True
except ImportError:
    MTCNN_AVAILABLE = False


class FaceDetector:
    """Handles face detection using either MTCNN or OpenCV Haar Cascade."""

    def __init__(self, method: Optional[str] = None):
        """
        Initialize the detector.
        Args:
            method: "mtcnn" or "haar". If None, defaults to config.DEFAULT_DETECTOR.
        """
        self.method = (method or config.DEFAULT_DETECTOR).lower()

        # Initialize Haar Cascade classifier if supported by OpenCV build
        self.haar_cascade = None
        has_cascade = hasattr(cv2, "CascadeClassifier")

        if has_cascade:
            if os.path.exists(config.HAAR_CASCADE_PATH):
                self.haar_cascade = cv2.CascadeClassifier(str(config.HAAR_CASCADE_PATH))
            else:
                default_cv2_path = os.path.join(
                    getattr(cv2, "data", None).haarcascades
                    if hasattr(cv2, "data") and hasattr(cv2.data, "haarcascades")
                    else "",
                    "haarcascade_frontalface_default.xml",
                )
                if os.path.exists(default_cv2_path):
                    self.haar_cascade = cv2.CascadeClassifier(default_cv2_path)
        elif self.method == "haar":
            print(
                "[Notice] cv2.CascadeClassifier is not available in this OpenCV build. "
                "Automatically using deep learning MTCNN detector."
            )
            self.method = "mtcnn"

        # Initialize MTCNN if requested or as fallback
        self.mtcnn = None
        if self.method == "mtcnn":
            if MTCNN_AVAILABLE:
                try:
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                    self.mtcnn = MTCNN(
                        keep_all=True,
                        min_face_size=config.MTCNN_MIN_FACE_SIZE,
                        thresholds=config.MTCNN_THRESHOLDS,
                        select_largest=False,
                        device=device,
                        post_process=False,
                    )
                except Exception as e:
                    print(f"[Warning] Failed to initialize MTCNN: {e}.")
                    if has_cascade and self.haar_cascade:
                        print("Falling back to Haar Cascade.")
                        self.method = "haar"
            elif has_cascade and self.haar_cascade:
                print("[Notice] facenet-pytorch MTCNN is not installed. Falling back to Haar Cascade.")
                self.method = "haar"

        if self.method == "haar" and (not has_cascade or self.haar_cascade is None):
            if MTCNN_AVAILABLE and self.mtcnn is not None:
                self.method = "mtcnn"
            else:
                raise RuntimeError(
                    "No functional face detector available. "
                    "Please install facenet-pytorch or use an OpenCV version with CascadeClassifier."
                )

    def detect_faces(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect faces in an input BGR or RGB image.
        Returns a list of dictionaries with:
            - 'box': (x, y, w, h) bounding box coordinates
            - 'confidence': confidence score (1.0 for Haar, [0, 1] for MTCNN)
            - 'cropped_face': resized (160x160) normalized RGB face numpy array
        """
        if image is None or image.size == 0:
            return []

        h_img, w_img = image.shape[:2]
        detections = []

        if self.method == "mtcnn" and self.mtcnn is not None:
            # MTCNN expects RGB image
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if len(image.shape) == 3 else image
            pil_img = Image.fromarray(rgb_image)
            boxes, probs = self.mtcnn.detect(pil_img)

            if boxes is not None:
                for box, prob in zip(boxes, probs):
                    if prob is not None and prob < 0.60:
                        continue
                    x1, y1, x2, y2 = box
                    x1 = max(0, int(round(x1)))
                    y1 = max(0, int(round(y1)))
                    x2 = min(w_img, int(round(x2)))
                    y2 = min(h_img, int(round(y2)))

                    w = x2 - x1
                    h = y2 - y1
                    if w < 15 or h < 15:
                        continue

                    # Crop and process face
                    cropped = self._crop_and_preprocess(image, (x1, y1, w, h))
                    detections.append(
                        {
                            "box": (x1, y1, w, h),
                            "confidence": float(prob) if prob is not None else 1.0,
                            "cropped_face": cropped,
                        }
                    )
        else:
            # Haar Cascade detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            # Equalize histogram to improve detection under varying lighting conditions
            gray = cv2.equalizeHist(gray)

            faces = self.haar_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE,
            )

            for (x, y, w, h) in faces:
                cropped = self._crop_and_preprocess(image, (x, y, w, h))
                detections.append(
                    {
                        "box": (int(x), int(y), int(w), int(h)),
                        "confidence": 1.0,
                        "cropped_face": cropped,
                    }
                )

        return detections

    def _crop_and_preprocess(self, image: np.ndarray, box: Tuple[int, int, int, int]) -> np.ndarray:
        """
        Crop face region with a margin, resize to 160x160, and convert to RGB.
        """
        x, y, w, h = box
        img_h, img_w = image.shape[:2]

        # Add 10% padding margin around the face bounding box
        margin_x = int(w * 0.10)
        margin_y = int(h * 0.10)
        x1 = max(0, x - margin_x)
        y1 = max(0, y - margin_y)
        x2 = min(img_w, x + w + margin_x)
        y2 = min(img_h, y + h + margin_y)

        face_roi = image[y1:y2, x1:x2]

        # If face ROI is empty or corrupted, fallback to the exact box
        if face_roi.size == 0:
            face_roi = image[y : y + h, x : x + w]

        # Convert to RGB if currently BGR
        if len(face_roi.shape) == 3 and face_roi.shape[2] == 3:
            face_roi_rgb = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)
        else:
            face_roi_rgb = cv2.cvtColor(face_roi, cv2.COLOR_GRAY2RGB)

        # Resize to standard FaceNet resolution (160x160)
        resized_face = cv2.resize(
            face_roi_rgb,
            config.FACE_IMAGE_SIZE,
            interpolation=cv2.INTER_AREA if (w > 160 and h > 160) else cv2.INTER_CUBIC,
        )

        return resized_face

    @staticmethod
    def draw_detections(
        image: np.ndarray,
        detections: List[Dict[str, Any]],
        labels: Optional[List[str]] = None,
        colors: Optional[List[Tuple[int, int, int]]] = None,
    ) -> np.ndarray:
        """
        Draw bounding boxes and labels around detected faces on the image.
        Returns a new annotated copy of the image.
        """
        annotated = image.copy()
        for idx, det in enumerate(detections):
            x, y, w, h = det["box"]
            label = labels[idx] if (labels and idx < len(labels)) else "Face"
            color = colors[idx] if (colors and idx < len(colors)) else (0, 255, 0)

            # Draw rectangle
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)

            # Draw label background for clean readability
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.55
            thickness = 1
            (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)

            text_y = max(y - 8, text_h + 5)
            cv2.rectangle(
                annotated,
                (x, text_y - text_h - 4),
                (x + text_w + 6, text_y + baseline - 2),
                color,
                cv2.FILLED,
            )
            # Text in contrasting black or white
            text_color = (0, 0, 0) if color == (0, 255, 0) or color == (255, 255, 0) else (255, 255, 255)
            cv2.putText(
                annotated,
                label,
                (x + 3, text_y - 2),
                font,
                font_scale,
                text_color,
                thickness,
                lineType=cv2.LINE_AA,
            )

        return annotated

    @staticmethod
    def display_or_save(
        image: np.ndarray,
        window_title: str = "Processed Image",
        save_filename: Optional[str] = None,
        auto_close_ms: int = 0,
    ) -> Optional[str]:
        """
        Display image with OpenCV GUI. If headless/unsupported or window is closed,
        save to the output directory.
        Returns saved file path.
        """
        saved_path = None
        if save_filename:
            saved_path = os.path.join(config.OUTPUT_DIR, save_filename)
            cv2.imwrite(saved_path, image)
            print(f"[Result Saved]: {saved_path}")

        # Attempt graphical display if DISPLAY/GUI is available
        try:
            cv2.imshow(window_title, image)
            print(f"[Display] Showing '{window_title}'. Press any key to close the window...")
            cv2.waitKey(auto_close_ms)
            cv2.destroyAllWindows()
        except cv2.error as e:
            # OpenCV GUI error (e.g. running in headless or SSH terminal)
            if not saved_path:
                saved_path = os.path.join(config.OUTPUT_DIR, "output_display.jpg")
                cv2.imwrite(saved_path, image)
                print(f"[Notice] Display unavailable ({e}). Annotated image saved to: {saved_path}")

        return saved_path

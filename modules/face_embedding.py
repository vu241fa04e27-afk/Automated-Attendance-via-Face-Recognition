"""
Face Embedding Module for Automated Attendance System.
Uses pretrained InceptionResnetV1 (FaceNet architecture) trained on VGGFace2.
Extracts 512-dimensional L2-normalized facial embeddings for identity representation.
"""

import os
import numpy as np
import torch
from typing import Union, List, Optional
import config

try:
    from facenet_pytorch import InceptionResnetV1
except ImportError:
    InceptionResnetV1 = None


class FaceEmbeddingExtractor:
    """Extracts deep facial feature embeddings using pretrained FaceNet InceptionResnetV1."""

    _instance = None  # Singleton pattern to avoid reloading heavy model weights multiple times

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(FaceEmbeddingExtractor, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, pretrained: Optional[str] = None):
        if self._initialized:
            return

        if InceptionResnetV1 is None:
            raise ImportError(
                "facenet-pytorch is required for facial embedding extraction. "
                "Please run: pip install facenet-pytorch"
            )

        self.pretrained = pretrained or config.FACENET_PRETRAINED_DATASET
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        print(f"[Model Init] Loading FaceNet InceptionResnetV1 ({self.pretrained}) on {self.device}...")
        try:
            self.model = InceptionResnetV1(pretrained=self.pretrained).eval().to(self.device)
            print("[Model Init] Pretrained FaceNet model loaded successfully.")
        except Exception as e:
            raise RuntimeError(
                f"Failed to load FaceNet pretrained weights: {e}\n"
                "Please ensure internet connectivity on initial run or provide local weights."
            )

        self._initialized = True

    def preprocess_face(self, face_rgb: np.ndarray) -> torch.Tensor:
        """
        Preprocess a cropped face image for FaceNet:
        1. Ensures 160x160 resolution.
        2. Normalizes pixel values using fixed standard FaceNet formula: (x - 127.5) / 128.0
        3. Permutes dimensions to (channels, height, width) -> (3, 160, 160).
        4. Converts to float32 tensor on target device.
        """
        import cv2

        if face_rgb.shape[:2] != config.FACE_IMAGE_SIZE:
            face_rgb = cv2.resize(face_rgb, config.FACE_IMAGE_SIZE, interpolation=cv2.INTER_LINEAR)

        # Standard FaceNet normalization: scale [0, 255] to [-1, 1]
        face_normalized = (face_rgb.astype(np.float32) - 127.5) / 128.0

        # Transpose from (H, W, C) to (C, H, W)
        tensor = torch.from_numpy(face_normalized).permute(2, 0, 1).float()
        return tensor.to(self.device)

    def extract_embedding(self, face_rgb: np.ndarray) -> np.ndarray:
        """
        Extract 512-dimensional facial embedding vector from a cropped RGB face.
        Returns 1D numpy array of float32, L2-normalized.
        """
        tensor = self.preprocess_face(face_rgb).unsqueeze(0)  # Shape: (1, 3, 160, 160)

        with torch.no_grad():
            embedding_tensor = self.model(tensor)  # Shape: (1, 512)
            # Ensure unit length (L2 normalization)
            norm = torch.norm(embedding_tensor, p=2, dim=1, keepdim=True)
            normalized_tensor = embedding_tensor / torch.clamp(norm, min=1e-10)

        embedding = normalized_tensor.squeeze(0).cpu().numpy().astype(np.float32)
        return embedding

    def extract_batch_embeddings(self, faces_rgb: List[np.ndarray]) -> List[np.ndarray]:
        """
        Extract embeddings for a batch of face images simultaneously.
        """
        if not faces_rgb:
            return []

        tensors = [self.preprocess_face(f) for f in faces_rgb]
        batch_tensor = torch.stack(tensors).to(self.device)

        with torch.no_grad():
            embeddings_tensor = self.model(batch_tensor)
            norm = torch.norm(embeddings_tensor, p=2, dim=1, keepdim=True)
            normalized_tensor = embeddings_tensor / torch.clamp(norm, min=1e-10)

        return [vec.cpu().numpy().astype(np.float32) for vec in normalized_tensor]


"""
Face Matching Module for Automated Attendance System.
Implements identity verification using Euclidean Distance and Cosine Similarity.
Includes configurable recognition thresholds, confidence checks, and ambiguity rejection.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import config


class FaceMatcher:
    """Matches facial embeddings against enrolled student database records."""

    def __init__(
        self,
        metric: Optional[str] = None,
        euclidean_threshold: Optional[float] = None,
        cosine_threshold: Optional[float] = None,
        ambiguity_margin: Optional[float] = None,
    ):
        """
        Initialize the FaceMatcher.
        Args:
            metric: "euclidean" or "cosine"
            euclidean_threshold: Maximum distance to consider a positive identity match
            cosine_threshold: Minimum similarity to consider a positive identity match
            ambiguity_margin: Margin below which two close student matches are rejected as ambiguous
        """
        self.metric = (metric or config.DEFAULT_MATCHING_METRIC).lower()
        self.euclidean_threshold = (
            euclidean_threshold if euclidean_threshold is not None else config.EUCLIDEAN_THRESHOLD
        )
        self.cosine_threshold = (
            cosine_threshold if cosine_threshold is not None else config.COSINE_THRESHOLD
        )
        self.ambiguity_margin = (
            ambiguity_margin if ambiguity_margin is not None else config.AMBIGUITY_MARGIN
        )

    @staticmethod
    def compute_euclidean_distance(emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Calculate Euclidean distance (L2 norm) between two embedding vectors.
        Formula: d = sqrt( sum( (u_i - v_i)^2 ) )
        """
        diff = emb1.astype(np.float32) - emb2.astype(np.float32)
        return float(np.linalg.norm(diff))

    @staticmethod
    def compute_cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Calculate Cosine similarity between two embedding vectors.
        Formula: cos(theta) = (u . v) / ( ||u|| * ||v|| )
        """
        dot_product = np.dot(emb1.astype(np.float32), emb2.astype(np.float32))
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        if norm1 < 1e-10 or norm2 < 1e-10:
            return 0.0
        return float(dot_product / (norm1 * norm2))

    def match_face(
        self,
        query_embedding: np.ndarray,
        enrolled_records: List[Dict[str, Any]],
        metric_override: Optional[str] = None,
        threshold_override: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Compare query face embedding against enrolled student embeddings.
        Supports multi-sample enrollment (takes the closest matching sample for each student).

        Args:
            query_embedding: 1D numpy array of the detected face embedding.
            enrolled_records: List of enrolled embedding records containing:
                              'student_id', 'student_name', 'embedding'.
            metric_override: Optional "euclidean" or "cosine" override.
            threshold_override: Optional threshold override.

        Returns:
            Dict containing:
                - 'is_recognized': bool
                - 'student_id': str ('UNKNOWN' if not matched)
                - 'student_name': str ('UNKNOWN' if not matched)
                - 'distance': float (or similarity)
                - 'status': 'RECOGNIZED', 'UNKNOWN', or 'AMBIGUOUS'
                - 'metric': str
        """
        active_metric = (metric_override or self.metric).lower()

        # Handle empty enrollment case
        if not enrolled_records:
            return {
                "is_recognized": False,
                "student_id": "UNKNOWN",
                "student_name": "UNKNOWN",
                "distance": 999.0 if active_metric == "euclidean" else 0.0,
                "status": "UNKNOWN (No enrolled students)",
                "metric": active_metric,
            }

        # Group matches per student to find each student's best sample score
        student_scores: Dict[str, Dict[str, Any]] = {}

        for rec in enrolled_records:
            sid = rec["student_id"]
            sname = rec["student_name"]
            ref_emb = rec["embedding"]

            if active_metric == "euclidean":
                score = self.compute_euclidean_distance(query_embedding, ref_emb)
                if sid not in student_scores or score < student_scores[sid]["score"]:
                    student_scores[sid] = {"name": sname, "score": score}
            else:
                score = self.compute_cosine_similarity(query_embedding, ref_emb)
                if sid not in student_scores or score > student_scores[sid]["score"]:
                    student_scores[sid] = {"name": sname, "score": score}

        # Sort students by matching quality
        # For Euclidean: lowest distance is best
        # For Cosine: highest similarity is best
        if active_metric == "euclidean":
            threshold = (
                threshold_override if threshold_override is not None else self.euclidean_threshold
            )
            sorted_candidates = sorted(
                student_scores.items(), key=lambda item: item[1]["score"]
            )
        else:
            threshold = (
                threshold_override if threshold_override is not None else self.cosine_threshold
            )
            sorted_candidates = sorted(
                student_scores.items(), key=lambda item: item[1]["score"], reverse=True
            )

        best_sid, best_data = sorted_candidates[0]
        best_score = best_data["score"]
        best_name = best_data["name"]

        # Evaluate threshold
        passes_threshold = False
        if active_metric == "euclidean":
            passes_threshold = best_score <= threshold
        else:
            passes_threshold = best_score >= threshold

        if not passes_threshold:
            return {
                "is_recognized": False,
                "student_id": "UNKNOWN",
                "student_name": "UNKNOWN",
                "distance": round(best_score, 4),
                "status": "UNKNOWN (Below Confidence)",
                "metric": active_metric,
            }

        # Check for ambiguity if multiple distinct students are enrolled
        if len(sorted_candidates) > 1:
            runner_up_sid, runner_up_data = sorted_candidates[1]
            runner_up_score = runner_up_data["score"]

            score_margin = abs(best_score - runner_up_score)
            if score_margin < self.ambiguity_margin:
                # Two different students are too close to call - mark UNKNOWN rather than guessing
                return {
                    "is_recognized": False,
                    "student_id": "UNKNOWN",
                    "student_name": "UNKNOWN",
                    "distance": round(best_score, 4),
                    "status": f"UNKNOWN (Ambiguous between {best_name} and {runner_up_data['name']})",
                    "metric": active_metric,
                }

        # Confirmed match
        return {
            "is_recognized": True,
            "student_id": best_sid,
            "student_name": best_name,
            "distance": round(best_score, 4),
            "status": "RECOGNIZED",
            "metric": active_metric,
        }


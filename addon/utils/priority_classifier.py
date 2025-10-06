"""
Email Priority Classifier Wrapper
"""

import pickle
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.embeddings import EmailEmbedder


class PriorityClassifier:
    """Wrapper for trained priority classification model."""

    def __init__(self, model_path):
        """
        Initialize classifier.

        Args:
            model_path: Path to trained model pickle file
        """
        self.model_path = model_path
        self.model_data = None
        self.model = None
        self.embedder = None
        self._load_model()

    def _load_model(self):
        """Load model and embedder from pickle file."""
        try:
            with open(self.model_path, 'rb') as f:
                self.model_data = pickle.load(f)

            self.model = self.model_data['model']

            # Initialize embedder with same config as training
            self.embedder = EmailEmbedder(
                provider=self.model_data['embedder_provider'],
                model=self.model_data['embedder_model']
            )

            print(f"Model loaded successfully from {self.model_path}")
            print(f"  Model type: {type(self.model).__name__}")
            print(f"  Training accuracy: {self.model_data.get('accuracy', 'N/A')}")

        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")

    def predict_priority(self, email):
        """
        Predict priority for a single email.

        Args:
            email: Email dictionary with 'subject' and 'body'

        Returns:
            Dictionary with 'priority' and 'confidence'
        """
        try:
            # Generate embedding
            email_text = f"Subject: {email['subject']}\n\nBody: {email['body']}"
            embedding = self.embedder.embed_text(email_text)

            # Predict
            priority = self.model.predict([embedding])[0]

            # Get confidence
            if hasattr(self.model, 'predict_proba'):
                probs = self.model.predict_proba([embedding])[0]
                class_to_idx = {cls: idx for idx, cls in enumerate(self.model.classes_)}
                confidence = probs[class_to_idx[priority]]
            else:
                confidence = 1.0

            return {
                'priority': priority,
                'confidence': float(confidence)
            }

        except Exception as e:
            print(f"Error predicting priority: {e}")
            return {
                'priority': 'MEDIUM',
                'confidence': 0.5
            }

    def predict_batch(self, emails):
        """
        Predict priorities for multiple emails.

        Args:
            emails: List of email dictionaries

        Returns:
            List of dictionaries with 'priority' and 'confidence'
        """
        results = []
        for email in emails:
            result = self.predict_priority(email)
            results.append(result)
        return results

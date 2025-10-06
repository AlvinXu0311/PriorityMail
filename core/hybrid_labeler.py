"""
Hybrid Priority Labeler

Combines rule-based heuristics with embedding-based similarity matching.
No LLM required - uses local embeddings and deterministic rules.
"""

import numpy as np
from typing import Dict, Tuple
import logging
from .reference_examples import get_reference_set, get_references_by_priority

logger = logging.getLogger(__name__)


class HybridPriorityLabeler:
    """
    Hybrid approach combining rules and embeddings for priority classification.
    """

    def __init__(self, embedder=None):
        """
        Initialize hybrid labeler.

        Args:
            embedder: EmailEmbedder instance (optional, will use rules-only if None)
        """
        self.embedder = embedder
        self.reference_emails = get_reference_set()
        self.reference_embeddings = None

        # Initialize reference embeddings if embedder provided
        if self.embedder:
            self._initialize_reference_embeddings()

        # Priority keywords (enhanced from existing system)
        self.high_keywords = [
            'urgent', 'asap', 'immediately', 'critical', 'emergency', 'deadline',
            'important', 'priority', 'action required', 'time sensitive',
            'escalation', 'ceo', 'president', 'director', 'crisis', 'breach',
            'outage', 'down', 'broken', 'failed', 'failure', 'issue',
            'approve', 'signature', 'sign', 'contract', 'today', 'now',
            'meeting today', 'call now', 'respond immediately'
        ]

        self.low_keywords = [
            'newsletter', 'unsubscribe', 'webinar', 'invitation', 'register',
            'fyi only', 'no action', 'automated', 'notification', 'noreply',
            'no-reply', 'spam', 'promotional', 'advertisement', 'marketing',
            'social event', 'happy hour', 'congratulations', 'winner', 'prize',
            'click here', 'act now', 'free', 'offer expires', 'backup completed'
        ]

    def _initialize_reference_embeddings(self):
        """Pre-compute embeddings for reference emails."""
        logger.info("Initializing reference embeddings...")
        ref_texts = []
        for email in self.reference_emails:
            combined = f"{email['subject']} {email['body']}"
            ref_texts.append(combined)

        self.reference_embeddings = self.embedder.embed_batch(ref_texts)
        logger.info(f"Reference embeddings initialized: {self.reference_embeddings.shape}")

    def _calculate_rule_scores(self, email: Dict) -> Tuple[float, float, float]:
        """
        Calculate rule-based priority scores.

        Args:
            email: Email dictionary

        Returns:
            Tuple of (high_score, medium_score, low_score) and confidence
        """
        subject = str(email.get('subject', '')).lower()
        body = str(email.get('body', ''))[:1500].lower()
        from_field = str(email.get('from', '')).lower()
        to_field = str(email.get('to', '')).lower()

        high_score = 0.0
        low_score = 0.0

        # HIGH priority indicators
        for keyword in self.high_keywords:
            if keyword in subject:
                high_score += 3.0  # Subject weighted more
            if keyword in body:
                high_score += 1.0

        # LOW priority indicators
        for keyword in self.low_keywords:
            if keyword in subject:
                low_score += 3.0
            if keyword in body:
                low_score += 1.0

        # Structural analysis
        # Multiple recipients = likely mass email (lower priority)
        if ',' in to_field:
            recipient_count = to_field.count(',') + 1
            if recipient_count > 15:
                low_score += 4.0
            elif recipient_count > 8:
                low_score += 2.0

        # Very short emails might be quick requests
        body_len = len(body)
        if 10 < body_len < 300 and len(subject) < 50:
            high_score += 1.5

        # Reply/Forward patterns
        if subject.startswith('re:'):
            high_score += 1.0  # Replies need attention
        elif subject.startswith(('fw:', 'fwd:', 'fwd fwd')):
            low_score += 2.0  # Forwards often informational

        # Automated senders
        auto_indicators = ['noreply', 'no-reply', 'system', 'automated', 'notification', 'donotreply']
        if any(indicator in from_field for indicator in auto_indicators):
            low_score += 3.0

        # Executive indicators
        exec_keywords = ['ceo', 'president', 'director', 'vp', 'vice president', 'manager']
        if any(keyword in from_field or keyword in body for keyword in exec_keywords):
            high_score += 1.5

        # Calculate confidence based on score difference
        max_score = max(high_score, low_score)
        total_score = high_score + low_score
        confidence = max_score / (total_score + 1.0)  # Avoid division by zero

        # Normalize scores
        medium_score = 1.0 - (high_score + low_score) / 20.0  # Baseline medium
        if medium_score < 0:
            medium_score = 0

        return (high_score, medium_score, low_score), confidence

    def _calculate_embedding_similarity(self, email: Dict) -> Tuple[str, float]:
        """
        Calculate priority based on embedding similarity to references.

        Args:
            email: Email dictionary

        Returns:
            Tuple of (predicted_priority, confidence)
        """
        if self.embedder is None or self.reference_embeddings is None:
            return 'MEDIUM', 0.0

        # Generate embedding for email
        combined_text = f"{email.get('subject', '')} {email.get('body', '')[:1000]}"
        email_embedding = self.embedder.embed_text(combined_text)

        # Calculate cosine similarities
        similarities = []
        for ref_emb in self.reference_embeddings:
            # Cosine similarity
            similarity = np.dot(email_embedding, ref_emb) / (
                np.linalg.norm(email_embedding) * np.linalg.norm(ref_emb) + 1e-10
            )
            similarities.append(similarity)

        # Get top-3 most similar references
        top_indices = np.argsort(similarities)[-3:][::-1]
        top_similarities = [similarities[i] for i in top_indices]

        # Weighted voting from top-3
        priority_votes = {'HIGH': 0.0, 'MEDIUM': 0.0, 'LOW': 0.0}
        for idx, sim in zip(top_indices, top_similarities):
            priority = self.reference_emails[idx]['priority']
            priority_votes[priority] += sim

        # Determine final priority
        predicted_priority = max(priority_votes, key=priority_votes.get)
        confidence = priority_votes[predicted_priority] / sum(priority_votes.values())

        return predicted_priority, confidence

    def label_email_detailed(self, email: Dict, use_embeddings: bool = True) -> Dict:
        """
        Label email priority and return detailed method info.

        Args:
            email: Email dictionary with 'subject', 'body', 'from', 'to'
            use_embeddings: Whether to use embedding similarity (default: True)

        Returns:
            Dictionary with 'priority', 'confidence', 'method' used
        """
        result = self.label_email(email, use_embeddings)
        return {
            'priority': result['priority'],
            'confidence': result['confidence'],
            'method': result['method']
        }

    def label_email(self, email: Dict, use_embeddings: bool = True) -> Dict:
        """
        Label email priority using hybrid approach.

        Args:
            email: Email dictionary with 'subject', 'body', 'from', 'to'
            use_embeddings: Whether to use embedding similarity (default: True)

        Returns:
            Dictionary with 'priority', 'confidence', 'method' used
        """
        # Step 1: Try rule-based classification
        (high_score, medium_score, low_score), rule_confidence = self._calculate_rule_scores(email)

        # Decision thresholds
        HIGH_THRESHOLD = 5.0
        LOW_THRESHOLD = 5.0
        CONFIDENT_THRESHOLD = 0.7

        # Check for clear rule-based decision
        if high_score >= HIGH_THRESHOLD and rule_confidence > CONFIDENT_THRESHOLD:
            return {
                'priority': 'HIGH',
                'confidence': rule_confidence,
                'method': 'rules',
                'scores': {'high': high_score, 'medium': medium_score, 'low': low_score}
            }

        if low_score >= LOW_THRESHOLD and rule_confidence > CONFIDENT_THRESHOLD:
            return {
                'priority': 'LOW',
                'confidence': rule_confidence,
                'method': 'rules',
                'scores': {'high': high_score, 'medium': medium_score, 'low': low_score}
            }

        # Step 2: Try embedding-based if uncertain
        if use_embeddings and self.embedder is not None:
            embedding_priority, embedding_confidence = self._calculate_embedding_similarity(email)

            # If embedding is confident, use it
            if embedding_confidence > 0.5:
                return {
                    'priority': embedding_priority,
                    'confidence': embedding_confidence,
                    'method': 'embeddings',
                    'scores': {'high': high_score, 'medium': medium_score, 'low': low_score}
                }

        # Step 3: Fall back to rule-based decision (even if not confident)
        if high_score > low_score and high_score >= 2:
            priority = 'HIGH'
        elif low_score > high_score and low_score >= 2:
            priority = 'LOW'
        else:
            priority = 'MEDIUM'

        return {
            'priority': priority,
            'confidence': max(rule_confidence, 0.3),  # Minimum confidence
            'method': 'rules_fallback',
            'scores': {'high': high_score, 'medium': medium_score, 'low': low_score}
        }

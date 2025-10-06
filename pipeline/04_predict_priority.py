#!/usr/bin/env python3
"""
STEP 4: PREDICT EMAIL PRIORITIES (Production)

Uses trained classifier to predict priorities for new emails.

Input:
- New emails CSV (unlabeled): data/raw/new_emails.csv
- Trained model: data/models/priority_classifier.pkl

Output: data/predictions/predicted_emails.csv

Columns in output CSV:
- email_id, subject, body, sender, timestamp, folder (original)
- predicted_priority: Predicted class (HIGH/MEDIUM/LOW)
- confidence: Prediction confidence (0-1)
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
import pickle
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.embeddings import EmailEmbedder


def load_model(model_path):
    """Load trained classifier and embedder config."""
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)

    print(f"Loaded model from {model_path}")
    print(f"  Model type: {type(model_data['model']).__name__}")
    print(f"  Training accuracy: {model_data['accuracy']:.4f}")
    print(f"  Embedder: {model_data['embedder_provider']} ({model_data['embedder_model']})")

    return model_data


def load_new_emails(input_path):
    """Load new unlabeled emails from CSV or JSON."""
    if input_path.endswith('.json'):
        df = pd.read_json(input_path)
    else:
        df = pd.read_csv(input_path)

    # Ensure required columns exist
    if 'email_id' not in df.columns:
        df['email_id'] = range(1, len(df) + 1)
    if 'timestamp' not in df.columns:
        df['timestamp'] = ''
    if 'folder' not in df.columns:
        df['folder'] = ''
    if 'sender' not in df.columns:
        df['sender'] = ''

    print(f"\nLoaded {len(df)} new emails from {input_path}")
    return df


def predict_priorities(df, model_data):
    """Predict priorities for new emails."""
    print(f"\n{'='*80}")
    print("STEP 4: PREDICTING EMAIL PRIORITIES")
    print(f"{'='*80}")

    # Initialize embedder with same config as training
    embedder = EmailEmbedder(
        provider=model_data['embedder_provider'],
        model=model_data['embedder_model']
    )

    model = model_data['model']

    print(f"\nGenerating embeddings and predictions...")

    predictions = []
    for _, row in df.iterrows():
        email_text = f"Subject: {row['subject']}\n\nBody: {row['body']}"
        embedding = embedder.embed_text(email_text)

        # Predict
        pred_class = model.predict([embedding])[0]

        # Get confidence (probability of predicted class)
        if hasattr(model, 'predict_proba'):
            probs = model.predict_proba([embedding])[0]
            class_to_idx = {cls: idx for idx, cls in enumerate(model.classes_)}
            confidence = probs[class_to_idx[pred_class]]
        else:
            confidence = 1.0  # No probability available

        predictions.append({
            'email_id': row['email_id'],
            'subject': row['subject'],
            'body': row['body'],
            'sender': row['sender'],
            'timestamp': row['timestamp'],
            'folder': row.get('folder', ''),
            'predicted_priority': pred_class,
            'confidence': round(confidence, 3)
        })

    return pd.DataFrame(predictions)


def save_predictions(df, output_path):
    """Save predictions to CSV."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False)

    print(f"\n{'='*80}")
    print("PREDICTION COMPLETE")
    print(f"{'='*80}")

    print(f"\nPredicted priority distribution:")
    for priority, count in df['predicted_priority'].value_counts().items():
        percentage = count / len(df) * 100
        print(f"  {priority:6s}: {count:4d} ({percentage:5.1f}%)")

    print(f"\nAverage confidence: {df['confidence'].mean():.3f}")

    print(f"\nTop 5 HIGH priority emails:")
    high_priority = df[df['predicted_priority'] == 'HIGH'].sort_values('confidence', ascending=False)
    for i in range(min(5, len(high_priority))):
        row = high_priority.iloc[i]
        print(f"  {i+1}. [Conf: {row['confidence']:.3f}] {row['subject'][:60]}")

    print(f"\nSaved to: {output_path}")
    print(f"File size: {output_path.stat().st_size / 1024:.1f} KB")


def main():
    parser = argparse.ArgumentParser(
        description="Step 4: Predict priorities for new emails"
    )

    parser.add_argument(
        '--input', type=str,
        default='data/raw/new_emails.csv',
        help='Input CSV file (new unlabeled emails)'
    )

    parser.add_argument(
        '--model', type=str,
        default='data/models/priority_classifier.pkl',
        help='Trained classification model'
    )

    parser.add_argument(
        '--output', type=str,
        default='data/predictions/predicted_emails.csv',
        help='Output CSV file (predictions)'
    )

    args = parser.parse_args()

    # Load model
    model_data = load_model(args.model)

    # Load new emails
    df_new = load_new_emails(args.input)

    # Predict priorities
    df_predictions = predict_priorities(df_new, model_data)

    # Save results
    save_predictions(df_predictions, args.output)


if __name__ == "__main__":
    main()

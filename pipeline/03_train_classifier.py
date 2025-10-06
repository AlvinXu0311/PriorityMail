#!/usr/bin/env python3
"""
STEP 3: TRAIN CLASSIFICATION MODEL

Trains a multi-class classifier to predict email priority (HIGH/MEDIUM/LOW).

Input:  data/labeled/emails_labeled.csv (auto-labeled emails)
Output: data/models/priority_classifier.pkl (trained model)

The model learns: "Given an email, what is its priority class?"
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.embeddings import EmailEmbedder


def load_labeled_emails(input_path):
    """Load auto-labeled emails from CSV."""
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} labeled emails from {input_path}")
    return df


def prepare_features(df, embedder):
    """Generate embeddings for emails."""
    print("\nGenerating embeddings for training...")

    embeddings = []
    for _, row in df.iterrows():
        email_text = f"Subject: {row['subject']}\n\nBody: {row['body']}"
        embedding = embedder.embed_text(email_text)
        embeddings.append(embedding)

    X = np.array(embeddings)
    y = df['priority'].values

    return X, y


def train_classifier(X, y, model_type='svm'):
    """Train multi-class classifier."""
    print(f"\nTraining {model_type} classifier...")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Initialize model
    if model_type == 'svm':
        model = SVC(kernel='rbf', C=1.0, probability=True, random_state=42)
    elif model_type == 'random_forest':
        model = RandomForestClassifier(n_estimators=100, random_state=42)
    elif model_type == 'gradient_boost':
        model = GradientBoostingClassifier(n_estimators=100, random_state=42)
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    # Train
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\n{'='*80}")
    print("TRAINING RESULTS")
    print(f"{'='*80}")
    print(f"\nAccuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['HIGH', 'LOW', 'MEDIUM']))

    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred, labels=['HIGH', 'MEDIUM', 'LOW'])
    print("             Predicted")
    print("           H    M    L")
    for i, label in enumerate(['HIGH', 'MEDIUM', 'LOW']):
        print(f"Actual {label[0]}  {cm[i][0]:4d} {cm[i][1]:4d} {cm[i][2]:4d}")

    return model, accuracy


def save_model(model, embedder, output_path, accuracy):
    """Save trained model and embedder configuration."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save model + embedder config
    model_data = {
        'model': model,
        'embedder_provider': embedder.provider,
        'embedder_model': embedder.model_name,
        'accuracy': accuracy
    }

    with open(output_path, 'wb') as f:
        pickle.dump(model_data, f)

    print(f"\n{'='*80}")
    print("MODEL TRAINING COMPLETE")
    print(f"{'='*80}")
    print(f"\nModel saved to: {output_path}")
    print(f"Model size: {output_path.stat().st_size / 1024:.1f} KB")
    print(f"\nNext step: Predict priorities for new emails")
    print(f"  python pipeline/04_predict_priority.py --model {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Step 3: Train priority classification model"
    )

    parser.add_argument(
        '--input', type=str,
        default='data/labeled/emails_labeled.csv',
        help='Input CSV file (auto-labeled emails)'
    )

    parser.add_argument(
        '--output', type=str,
        default='data/models/priority_classifier.pkl',
        help='Output model file'
    )

    parser.add_argument(
        '--model-type', type=str,
        default='svm',
        choices=['svm', 'random_forest', 'gradient_boost'],
        help='Classifier type'
    )

    parser.add_argument(
        '--embedder', type=str,
        default='ollama',
        choices=['ollama', 'openai', 'sentence-transformers'],
        help='Embedding provider'
    )

    parser.add_argument(
        '--embedding-model', type=str,
        default='qwen3-embedding',
        help='Embedding model name'
    )

    args = parser.parse_args()

    print(f"\n{'='*80}")
    print("STEP 3: TRAINING CLASSIFICATION MODEL")
    print(f"{'='*80}")

    # Load labeled emails
    df = load_labeled_emails(args.input)

    # Initialize embedder
    print(f"\nInitializing embedder: {args.embedder} ({args.embedding_model})")
    embedder = EmailEmbedder(provider=args.embedder, model=args.embedding_model)

    # Prepare features
    X, y = prepare_features(df, embedder)

    # Train classifier
    model, accuracy = train_classifier(X, y, args.model_type)

    # Save model
    save_model(model, embedder, args.output, accuracy)


if __name__ == "__main__":
    main()

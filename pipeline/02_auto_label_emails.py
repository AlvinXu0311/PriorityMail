#!/usr/bin/env python3
"""
STEP 2: AUTO-LABEL EMAILS

Auto-labels emails using hybrid approach (rules + embeddings).
NO manual labels required - fully automatic!

Input:  data/raw/emails_raw.csv (unlabeled)
Output: data/labeled/emails_labeled.csv (with priority labels)

New columns added:
- priority: AUTO-LABELED priority (HIGH/MEDIUM/LOW)
- confidence: Labeling confidence (0-1)
- label_method: How it was labeled (rules/embedding/fallback)
"""

import sys
import os
import csv
import argparse
from pathlib import Path
import pandas as pd
from tqdm import tqdm

# Add parent directory to path to import core modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.hybrid_labeler import HybridPriorityLabeler
from core.embeddings import EmailEmbedder


def load_raw_emails(input_path):
    """Load raw emails from CSV."""
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} raw emails from {input_path}")
    return df


def auto_label_emails(df, embedder):
    """Auto-label emails using hybrid approach."""
    print(f"\n{'='*80}")
    print("STEP 2: AUTO-LABELING EMAILS")
    print(f"{'='*80}")
    print("\nUsing hybrid labeling approach:")
    print("  1. Rule-based: Keywords (urgent, critical, asap...)")
    print("  2. Embedding-based: Similarity to reference examples")
    print("  3. Fallback: Rule scores if neither works\n")

    labeler = HybridPriorityLabeler(embedder=embedder)

    labeled_emails = []

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Auto-labeling"):
        email = {
            'subject': row['subject'],
            'body': row['body']
        }

        # Get priority label with confidence and method
        result = labeler.label_email_detailed(email)

        labeled_emails.append({
            'email_id': row['email_id'],
            'subject': row['subject'],
            'body': row['body'],
            'sender': row['sender'],
            'timestamp': row['timestamp'],
            'folder': row['folder'],
            'priority': result['priority'],
            'confidence': result['confidence'],
            'label_method': result['method']
        })

    return pd.DataFrame(labeled_emails)


def save_labeled_emails(df, output_path):
    """Save labeled emails to CSV."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False)

    # Print statistics
    print(f"\n{'='*80}")
    print("AUTO-LABELING COMPLETE")
    print(f"{'='*80}")

    print(f"\nPriority distribution:")
    for priority, count in df['priority'].value_counts().items():
        percentage = count / len(df) * 100
        print(f"  {priority:6s}: {count:4d} ({percentage:5.1f}%)")

    print(f"\nLabeling methods used:")
    for method, count in df['label_method'].value_counts().items():
        percentage = count / len(df) * 100
        print(f"  {method:10s}: {count:4d} ({percentage:5.1f}%)")

    print(f"\nAverage confidence: {df['confidence'].mean():.3f}")

    print(f"\nSaved to: {output_path}")
    print(f"File size: {output_path.stat().st_size / 1024:.1f} KB")

    print(f"\nNext step: Train classification model")
    print(f"  python pipeline/03_train_classifier.py --input {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Step 2: Auto-label emails with priority"
    )

    parser.add_argument(
        '--input', type=str,
        default='data/raw/emails_raw.csv',
        help='Input CSV file (raw unlabeled emails)'
    )

    parser.add_argument(
        '--output', type=str,
        default='data/labeled/emails_labeled.csv',
        help='Output CSV file (labeled emails)'
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

    parser.add_argument(
        '--balance', action='store_true',
        help='Balance dataset (equal HIGH/MEDIUM/LOW samples)'
    )

    args = parser.parse_args()

    # Load raw emails
    df_raw = load_raw_emails(args.input)

    # Initialize embedder
    print(f"\nInitializing embedder: {args.embedder} ({args.embedding_model})")
    embedder = EmailEmbedder(provider=args.embedder, model=args.embedding_model)

    # Auto-label emails
    df_labeled = auto_label_emails(df_raw, embedder)

    # Balance if requested
    if args.balance:
        print("\nBalancing dataset...")
        min_count = df_labeled['priority'].value_counts().min()
        df_balanced = df_labeled.groupby('priority').sample(n=min_count, random_state=42)
        df_labeled = df_balanced.reset_index(drop=True)
        print(f"Balanced to {len(df_labeled)} emails ({min_count} per class)")

    # Save labeled emails
    save_labeled_emails(df_labeled, args.output)


if __name__ == "__main__":
    main()

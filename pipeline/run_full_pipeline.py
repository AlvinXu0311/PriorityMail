#!/usr/bin/env python3
"""
MASTER PIPELINE RUNNER

Runs the complete email priority prediction pipeline in one command.

Pipeline stages:
1. Extract raw emails → data/raw/emails_raw.csv
2. Auto-label emails → data/labeled/emails_labeled.csv
3. Train classifier → data/models/priority_classifier.pkl
4. Predict priorities → data/predictions/predicted_emails.csv

Usage:
    python pipeline/run_full_pipeline.py --source path/to/emails --limit 1500
"""

import subprocess
import argparse
import time
from pathlib import Path


def run_command(command, description):
    """Run a pipeline step and track time."""
    print(f"\n{'='*80}")
    print(f"RUNNING: {description}")
    print(f"{'='*80}")
    print(f"Command: {' '.join(command)}\n")

    start_time = time.time()

    result = subprocess.run(command, capture_output=False, text=True)

    elapsed_time = time.time() - start_time

    if result.returncode != 0:
        print(f"\n[ERROR] Step failed: {description}")
        print(f"Exit code: {result.returncode}")
        exit(1)

    print(f"\n[OK] Completed in {elapsed_time:.1f} seconds")

    return elapsed_time


def main():
    parser = argparse.ArgumentParser(
        description="Run complete email priority pipeline"
    )

    parser.add_argument(
        '--source', type=str,
        default='data/raw/enron_mail_20150507',
        help='Path to email source'
    )

    parser.add_argument(
        '--limit', type=int,
        default=1500,
        help='Number of emails to extract'
    )

    parser.add_argument(
        '--balance', action='store_true',
        help='Balance labeled dataset'
    )

    parser.add_argument(
        '--embedder', type=str,
        default='ollama',
        help='Embedding provider'
    )

    parser.add_argument(
        '--embedding-model', type=str,
        default='qwen3-embedding',
        help='Embedding model'
    )

    parser.add_argument(
        '--model-type', type=str,
        default='svm',
        choices=['svm', 'random_forest', 'gradient_boost'],
        help='Classification model type'
    )

    parser.add_argument(
        '--skip-steps', type=str,
        default='',
        help='Comma-separated steps to skip (e.g., "1,2")'
    )

    args = parser.parse_args()

    skip_steps = set(args.skip_steps.split(',')) if args.skip_steps else set()

    print(f"\n{'='*80}")
    print("EMAIL PRIORITY PREDICTION - FULL PIPELINE")
    print(f"{'='*80}")
    print(f"\nConfiguration:")
    print(f"  Source: {args.source}")
    print(f"  Email limit: {args.limit}")
    print(f"  Embedder: {args.embedder} ({args.embedding_model})")
    print(f"  Model type: {args.model_type}")
    print(f"  Balance dataset: {args.balance}")

    total_start = time.time()
    step_times = []

    # Step 1: Extract emails
    if '1' not in skip_steps:
        cmd = [
            'python', 'pipeline/01_extract_emails.py',
            '--source', args.source,
            '--output', 'data/raw/emails_raw.csv',
            '--limit', str(args.limit)
        ]
        step_times.append(run_command(cmd, "Step 1: Extract emails"))
    else:
        print("\n[SKIP] Step 1: Extract emails")

    # Step 2: Auto-label emails (COMMENTED OUT - Use manual labeling)
    # if '2' not in skip_steps:
    #     cmd = [
    #         'python', 'pipeline/02_auto_label_emails.py',
    #         '--input', 'data/raw/emails_raw.csv',
    #         '--output', 'data/labeled/emails_labeled.csv',
    #         '--embedder', args.embedder,
    #         '--embedding-model', args.embedding_model
    #     ]
    #     if args.balance:
    #         cmd.append('--balance')
    #     step_times.append(run_command(cmd, "Step 2: Auto-label emails"))
    # else:
    #     print("\n[SKIP] Step 2: Auto-label emails")
    print("\n[COMMENTED OUT] Step 2: Auto-label emails - Please manually label emails instead")

    # Step 3: Train classifier
    if '3' not in skip_steps:
        cmd = [
            'python', 'pipeline/03_train_classifier.py',
            '--input', 'data/labeled/emails_labeled.csv',
            '--output', 'data/models/priority_classifier.pkl',
            '--model-type', args.model_type,
            '--embedder', args.embedder,
            '--embedding-model', args.embedding_model
        ]
        step_times.append(run_command(cmd, "Step 3: Train classification model"))
    else:
        print("\n[SKIP] Step 3: Train classifier")

    # Step 4: Predict priorities
    if '4' not in skip_steps:
        # Use a subset of raw emails as "new" emails for demo
        cmd = [
            'python', 'pipeline/04_predict_priority.py',
            '--input', 'data/raw/emails_raw.csv',
            '--model', 'data/models/priority_classifier.pkl',
            '--output', 'data/predictions/predicted_emails.csv'
        ]
        step_times.append(run_command(cmd, "Step 4: Predict email priorities"))
    else:
        print("\n[SKIP] Step 4: Predict priorities")

    total_time = time.time() - total_start

    # Summary
    print(f"\n{'='*80}")
    print("PIPELINE COMPLETE")
    print(f"{'='*80}")

    print(f"\nStep execution times:")
    step_names = [
        "Extract emails",
        "Train classifier",
        "Predict priorities"
    ]
    for i, step_time in enumerate(step_times):
        print(f"  {step_names[i]}: {step_time:.1f}s")

    print(f"\nTotal time: {total_time:.1f}s ({total_time/60:.1f} minutes)")

    print(f"\nOutput files:")
    print(f"  Raw emails:        data/raw/emails_raw.csv")
    print(f"  Labeled emails:    data/labeled/emails_labeled.csv")
    print(f"  Trained model:     data/models/priority_classifier.pkl")
    print(f"  Final predictions: data/predictions/predicted_emails.csv")

    print(f"\nTo predict priorities for new emails:")
    print(f"  python pipeline/04_predict_priority.py \\")
    print(f"    --input your_new_emails.csv \\")
    print(f"    --model data/models/priority_classifier.pkl")


if __name__ == "__main__":
    main()

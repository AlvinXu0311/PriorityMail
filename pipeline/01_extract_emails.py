#!/usr/bin/env python3
"""
STEP 1: EXTRACT RAW EMAILS

Extracts emails from mailbox/folders and saves to CSV format (unlabeled).

Input:  Email folders/mailbox files
Output: data/raw/emails_raw.csv

Columns in output CSV:
- email_id: Unique identifier
- subject: Email subject
- body: Email body text
- sender: Sender email address
- timestamp: Received timestamp
- folder: Original folder location
"""

import os
import csv
import argparse
from pathlib import Path
from email import message_from_file
from email.utils import parsedate_to_datetime
import email
from tqdm import tqdm


def extract_email_from_file(file_path):
    """Extract email data from a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            msg = message_from_file(f)

            subject = msg.get('Subject', '')
            sender = msg.get('From', '')
            date_str = msg.get('Date', '')

            # Parse timestamp
            try:
                timestamp = parsedate_to_datetime(date_str).isoformat() if date_str else ''
            except:
                timestamp = ''

            # Extract body
            body = ''
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == 'text/plain':
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
            else:
                body = msg.get_payload(decode=True)
                if body:
                    body = body.decode('utf-8', errors='ignore')
                else:
                    body = ''

            return {
                'subject': subject,
                'body': body,
                'sender': sender,
                'timestamp': timestamp
            }
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None


def extract_emails_from_enron(enron_path, limit=1500):
    """
    Extract emails from Enron dataset.

    Args:
        enron_path: Path to maildir folder
        limit: Maximum number of emails to extract
    """
    emails = []
    email_id = 1

    # Walk through all user folders
    maildir_path = Path(enron_path) / 'maildir'

    if not maildir_path.exists():
        raise ValueError(f"Maildir not found: {maildir_path}")

    print(f"\n{'='*80}")
    print("STEP 1: EXTRACTING RAW EMAILS")
    print(f"{'='*80}")
    print(f"\nScanning: {maildir_path}")

    # Collect all email files
    email_files = []
    for user_folder in maildir_path.iterdir():
        if user_folder.is_dir():
            for folder in user_folder.iterdir():
                if folder.is_dir() and folder.name in ['inbox', 'sent', 'sent_items', '_sent_mail']:
                    # Windows extended path support
                    folder_path_abs = os.path.abspath(str(folder))
                    if os.name == 'nt':
                        folder_path_abs = '\\\\?\\' + folder_path_abs

                    try:
                        filenames = os.listdir(folder_path_abs)
                        for filename in filenames:
                            file_path = os.path.join(folder_path_abs, filename)
                            if os.path.isfile(file_path):
                                email_files.append((file_path, user_folder.name, folder.name))

                                if len(email_files) >= limit:
                                    break
                    except Exception as e:
                        print(f"Error accessing {folder}: {e}")
                        continue

                if len(email_files) >= limit:
                    break

        if len(email_files) >= limit:
            break

    print(f"\nFound {len(email_files)} email files")
    print(f"Extracting {min(limit, len(email_files))} emails...\n")

    # Extract email content
    for file_path, user, folder in tqdm(email_files[:limit], desc="Extracting"):
        email_data = extract_email_from_file(file_path)

        if email_data:
            emails.append({
                'email_id': email_id,
                'subject': email_data['subject'],
                'body': email_data['body'][:1000],  # Limit body to 1000 chars
                'sender': email_data['sender'],
                'timestamp': email_data['timestamp'],
                'folder': f"{user}/{folder}"
            })
            email_id += 1

    return emails


def save_to_csv(emails, output_path):
    """Save emails to CSV file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['email_id', 'subject', 'body', 'sender', 'timestamp', 'folder']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(emails)

    print(f"\n{'='*80}")
    print(f"EXTRACTION COMPLETE")
    print(f"{'='*80}")
    print(f"\nSaved {len(emails)} emails to: {output_path}")
    print(f"File size: {output_path.stat().st_size / 1024:.1f} KB")
    print(f"\nNext step: Auto-label emails")
    print(f"  python pipeline/02_auto_label_emails.py --input {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Step 1: Extract raw emails to CSV"
    )

    parser.add_argument(
        '--source', type=str,
        default='data/raw/enron_mail_20150507',
        help='Path to email source (Enron dataset)'
    )

    parser.add_argument(
        '--output', type=str,
        default='data/raw/emails_raw.csv',
        help='Output CSV file path'
    )

    parser.add_argument(
        '--limit', type=int,
        default=1500,
        help='Maximum number of emails to extract'
    )

    args = parser.parse_args()

    # Extract emails
    emails = extract_emails_from_enron(args.source, args.limit)

    # Save to CSV
    save_to_csv(emails, args.output)


if __name__ == "__main__":
    main()

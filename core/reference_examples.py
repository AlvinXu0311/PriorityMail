"""
Reference Email Examples for Priority Classification

Hard-coded reference emails with clear priority characteristics.
Used for embedding-based similarity matching.
"""

REFERENCE_EMAILS = {
    'HIGH': [
        {
            'subject': 'URGENT: Server outage affecting production',
            'body': 'We have a critical server outage that is impacting all production systems. Need immediate response from the infrastructure team. This is affecting customer transactions.',
            'priority': 'HIGH',
            'reason': 'Critical system issue requiring immediate action'
        },
        {
            'subject': 'Meeting with CEO tomorrow at 9am',
            'body': 'Please confirm your attendance for tomorrow\'s meeting with the CEO at 9am. We need to discuss Q4 strategy and your input is crucial.',
            'priority': 'HIGH',
            'reason': 'Executive meeting requiring confirmation'
        },
        {
            'subject': 'Contract deadline TODAY - need signature',
            'body': 'The vendor contract must be signed by end of day today. Please review and sign ASAP. Legal has approved all terms.',
            'priority': 'HIGH',
            'reason': 'Same-day deadline requiring action'
        },
        {
            'subject': 'Client escalation - they are threatening to cancel',
            'body': 'Our largest client just called and they are very unhappy with the recent service issues. They mentioned canceling their contract. Can you call them immediately?',
            'priority': 'HIGH',
            'reason': 'Client emergency requiring immediate response'
        },
        {
            'subject': 'Action required: Approve budget request by EOD',
            'body': 'I need your approval on the $50K budget request by end of day so we can process it this quarter. Please review attached proposal.',
            'priority': 'HIGH',
            'reason': 'Time-sensitive approval needed'
        },
        {
            'subject': 'Emergency: Data breach detected',
            'body': 'Security team has detected unauthorized access to customer database. We need to convene emergency response team NOW.',
            'priority': 'HIGH',
            'reason': 'Security emergency'
        },
    ],

    'MEDIUM': [
        {
            'subject': 'Project status update for Q2',
            'body': 'Here is the monthly status update for the infrastructure project. We are on track for Q2 delivery. Please review and let me know if you have any questions.',
            'priority': 'MEDIUM',
            'reason': 'Regular project update'
        },
        {
            'subject': 'Meeting request: Planning session next week',
            'body': 'I would like to schedule a planning session for next week to discuss the roadmap. Please let me know your availability on Tuesday or Wednesday.',
            'priority': 'MEDIUM',
            'reason': 'Non-urgent meeting request'
        },
        {
            'subject': 'Question about the new process',
            'body': 'I have a question about the new approval process we discussed last week. When you get a chance, can you clarify the escalation path?',
            'priority': 'MEDIUM',
            'reason': 'Question that can wait'
        },
        {
            'subject': 'FYI: Updated guidelines document',
            'body': 'Attached are the updated guidelines for the project. Please review when you have time. No immediate action needed, but please read before our next team meeting.',
            'priority': 'MEDIUM',
            'reason': 'Information sharing with future deadline'
        },
        {
            'subject': 'Feedback on proposal draft',
            'body': 'I have reviewed the proposal draft you sent. Overall looks good, I have a few suggestions. Let\'s discuss when you have time.',
            'priority': 'MEDIUM',
            'reason': 'Feedback on ongoing work'
        },
        {
            'subject': 'Team lunch next Friday?',
            'body': 'Hey team, I was thinking we could do a team lunch next Friday to celebrate the project completion. Let me know if you are interested.',
            'priority': 'MEDIUM',
            'reason': 'Team coordination, not urgent'
        },
    ],

    'LOW': [
        {
            'subject': 'Newsletter: Weekly Tech Digest',
            'body': 'Welcome to this week\'s tech newsletter! Featured articles: 10 productivity tips, new cloud services, and industry trends. Click here to read more.',
            'priority': 'LOW',
            'reason': 'Newsletter - informational only'
        },
        {
            'subject': 'Invitation: Webinar on Cloud Computing',
            'body': 'You are invited to our upcoming webinar on cloud computing best practices. Register now! This email was sent to you because you subscribed to our mailing list.',
            'priority': 'LOW',
            'reason': 'Marketing/promotional content'
        },
        {
            'subject': 'SPAM: Congratulations! You have won!',
            'body': 'Click here to claim your prize! You have been selected as a winner in our monthly drawing. Act now before this offer expires!',
            'priority': 'LOW',
            'reason': 'Obvious spam'
        },
        {
            'subject': 'Automatic notification: Backup completed',
            'body': 'This is an automated message. Your scheduled backup completed successfully at 2:00 AM. No action required.',
            'priority': 'LOW',
            'reason': 'Automated notification'
        },
        {
            'subject': 'Social event: Happy hour this Friday',
            'body': 'Join us for happy hour this Friday at 5pm! It will be at the usual spot. Hope to see you there! RSVP optional.',
            'priority': 'LOW',
            'reason': 'Social/casual event'
        },
        {
            'subject': 'FWD: FWD: FWD: Funny cat video',
            'body': 'Check out this hilarious video! Thought you might enjoy it.',
            'priority': 'LOW',
            'reason': 'Forwarded casual content'
        },
        {
            'subject': 'Unsubscribe confirmation',
            'body': 'You have successfully unsubscribed from our mailing list. You will no longer receive promotional emails from us.',
            'priority': 'LOW',
            'reason': 'Automated confirmation'
        },
    ]
}


def get_reference_set():
    """
    Get all reference emails as a list.

    Returns:
        List of reference email dictionaries
    """
    references = []
    for priority, emails in REFERENCE_EMAILS.items():
        references.extend(emails)
    return references


def get_references_by_priority(priority: str):
    """
    Get reference emails for a specific priority.

    Args:
        priority: 'HIGH', 'MEDIUM', or 'LOW'

    Returns:
        List of reference emails for that priority
    """
    return REFERENCE_EMAILS.get(priority.upper(), [])


def print_reference_examples():
    """Print all reference examples for review."""
    for priority, emails in REFERENCE_EMAILS.items():
        print(f"\n{'='*70}")
        print(f"{priority} PRIORITY EXAMPLES ({len(emails)} examples)")
        print('='*70)
        for i, email in enumerate(emails, 1):
            print(f"\n{i}. Subject: {email['subject']}")
            print(f"   Body: {email['body'][:100]}...")
            print(f"   Reason: {email['reason']}")

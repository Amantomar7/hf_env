EMAILS = {
    "easy": [
        {
            "id": "easy_001",
            "email_from": "deals@shopnow.com",
            "subject": "50% OFF this weekend only!!!",
            "body": "Don't miss our biggest sale. Click here to shop now. Unsubscribe anytime.",
            "answer": {
                "category": "spam",
                "priority": "low",
                "action_type": "archive"
            }
        },
        {
            "id": "easy_002",
            "email_from": "john.smith@gmail.com",
            "subject": "Quick question about my invoice",
            "body": "Hi, I received invoice #1234 but the amount seems wrong. Can you check?",
            "answer": {
                "category": "billing",
                "priority": "medium",
                "action_type": "respond"
            }
        },
    ],
    "medium": [
        {
            "id": "med_001",
            "email_from": "angry.customer@gmail.com",
            "subject": "Charged twice this month!!",
            "body": "I was billed $99 twice in October. This is unacceptable. I want a refund immediately or I will dispute with my bank.",
            "answer": {
                "category": "billing",
                "priority": "high",
                "action_type": "escalate"
            }
        },
        {
            "id": "med_002",
            "email_from": "newuser@company.com",
            "subject": "Cannot log into my account",
            "body": "I just signed up yesterday but I cannot log in. I tried resetting my password but the email never arrived.",
            "answer": {
                "category": "support",
                "priority": "high",
                "action_type": "respond"
            }
        },
        {
            "id": "med_003",
            "email_from": "newsletter@techblog.io",
            "subject": "Your weekly digest is here",
            "body": "This week in tech: AI breakthroughs, new framework releases, and more. Click to read.",
            "answer": {
                "category": "spam",
                "priority": "low",
                "action_type": "archive"
            }
        },
    ],
    "hard": [
        {
            "id": "hard_001",
            "email_from": "james.k@enterprise.com",
            "subject": "Following up on our call",
            "body": "Hi, following up from our call last week. We are interested in the enterprise plan but need custom pricing for 500 seats. Also our legal team has questions about the data processing agreement.",
            "answer": {
                "category": "sales",
                "priority": "high",
                "action_type": "escalate"
            }
        },
        {
            "id": "hard_002",
            "email_from": "mary@smallbiz.com",
            "subject": "Not happy",
            "body": "Things are not working as expected. We have been trying for two weeks now with no resolution.",
            "answer": {
                "category": "support",
                "priority": "high",
                "action_type": "escalate"
            }
        },
        {
            "id": "hard_003",
            "email_from": "accounts@vendor.com",
            "subject": "Invoice INV-2024-089 due",
            "body": "Please find attached invoice INV-2024-089 for $4,500 due on November 30th for consulting services rendered in October.",
            "answer": {
                "category": "billing",
                "priority": "medium",
                "action_type": "respond"
            }
        },
    ]
}
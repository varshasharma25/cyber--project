
# Identity Trust System

A privacy-first AI-powered Identity Trust Framework designed to detect suspicious banking activity and dynamically trigger verification only when risk is elevated.

The system continuously evaluates user behavior, device information, and account activity to reduce fraud while maintaining a seamless experience for legitimate users.


Traditional authentication systems apply the same verification process to every user regardless of risk level. This creates friction for legitimate users while still allowing sophisticated fraud attempts such as account takeover attacks.

This project addresses that challenge by using machine learning to continuously assess identity trust and trigger verification only when necessary.

## Risks Addressed

- Account Takeover (ATO)
- Behavioral Anomalies
- New Device Risk

## Proposed Solution

The system follows a risk-based authentication approach:

1. Monitor user behavior and activity such as
   - Typing speed
   - Click patterns
   - Login timing
   - Device information

2. Generate a risk score using a machine learning model

3. Apply adaptive verification based on risk level

| Risk Score | Action |
|------------|---------|
| 0 - 29 | Allow access without verification |
| 30 - 59 | Require SMS verification |
| 60 - 100 | Require Biometric Verification + 2FA |

This approach minimizes user friction while providing stronger protection against fraud and unauthorized access.

## Features

- AI-powered risk scoring
- Behavioral anomaly detection
- Device trust analysis
- JWT-based authentication
- OAuth 2.0 integration
- Risk-based verification flow
- REST API backend
- Interactive dashboard

## Project Structure

```text
BOB-IDENTITY-TRUST/
│
├── backend/
│   ├── ml/
│   │   └── idk tbh
│   │
│   ├── models/
│   │   ├── behavior_log.py
│   │   ├── risk_score.py
│   │   └── user.py
│   │
│   ├── routes/
│   │   ├── auth.py
│   │   ├── risk.py
│   │   └── verify.py
│   │
│   ├── utils/
│   │   ├── jwt_auth.py
│   │   └── oauth.py
│   │
│   ├── app.py
│   └── database/
│       ├── sample_data.sql
│       └── schema.sql
│
├── frontend/
│   ├── css/
│   ├── js/
│   ├── dashboard.html
│   ├── index.html
│   └── verify.html
│
├── myenv/
├── .env
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Workflow

1. User logs in
2. Behavioral and device data are collected
3. Machine learning model calculates a risk score
4. Risk engine determines required verification level
5. User is granted access or challenged with additional verification
6. Risk events are logged for future analysis

## API Modules

### Authentication
Handles login, JWT generation, and OAuth integration.

### Risk Engine
Calculates risk scores using behavioral and contextual signals.

### Verification Service
Applies adaptive verification based on calculated risk.

### Behavioral Logging
Stores user activity patterns for anomaly detection.

## Privacy First Design

- Collects only necessary behavioral signals
- Uses risk-based verification instead of constant challenges
- Minimizes exposure of sensitive user information
- Supports secure authentication standards

## Future Improvements

- Real-time anomaly detection
- Device fingerprinting
- Continuous authentication
- Explainable AI risk scoring
- Biometric verification integration
- Advanced fraud analytics

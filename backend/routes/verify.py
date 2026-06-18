# POST /verify/sms, /verify/biometric, /verify/2fa: each endpoint validates the submitted proof,
# logs to verification_logs, and returns a verified JWT or an error.
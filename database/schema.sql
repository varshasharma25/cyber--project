SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS behavior_logs;
DROP TABLE IF EXISTS risk_scores;
DROP TABLE IF EXISTS verification_logs;
DROP TABLE IF EXISTS device_fingerprints;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE IF NOT EXISTS users (
    id            INT PRIMARY KEY AUTO_INCREMENT,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL COMMENT 'werkzeug generate_password_hash() output, never plaintext',
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS behavior_logs (
    id         INT PRIMARY KEY AUTO_INCREMENT,
    user_id    INT NOT NULL,
    event_type VARCHAR(50) NOT NULL COMMENT "'typing' | 'click' | 'navigation' | 'transaction' etc.",
    event_data JSON NOT NULL COMMENT 'raw behavioral payload from the frontend (speed, coords, timing...)',
    timestamp  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_behavior_logs_timestamp ON behavior_logs (timestamp);

CREATE TABLE IF NOT EXISTS risk_scores (
    id            INT PRIMARY KEY AUTO_INCREMENT,
    user_id       INT NOT NULL,
    risk_score    INT NOT NULL COMMENT '0-100',
    risk_level    VARCHAR(20) NOT NULL COMMENT "'low' | 'medium' | 'high'",
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_risk_score_range CHECK (risk_score BETWEEN 0 AND 100),
    CONSTRAINT chk_risk_level_valid CHECK (risk_level IN ('low', 'medium', 'high'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_risk_scores_calculated_at ON risk_scores (calculated_at);

CREATE TABLE IF NOT EXISTS verification_logs (
    id                   INT PRIMARY KEY AUTO_INCREMENT,
    user_id              INT NOT NULL,
    verification_method  VARCHAR(50) NOT NULL COMMENT "'sms' | '2fa' | 'biometric'",
    status               VARCHAR(20) NOT NULL COMMENT "'success' | 'failed'",
    timestamp            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_verification_method_valid CHECK (verification_method IN ('sms', '2fa', 'biometric')),
    CONSTRAINT chk_verification_status_valid CHECK (status IN ('success', 'failed'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_verification_logs_timestamp ON verification_logs (timestamp);

CREATE TABLE IF NOT EXISTS device_fingerprints (
    id            INT PRIMARY KEY AUTO_INCREMENT,
    user_id       INT NOT NULL,
    fingerprint   VARCHAR(64) NOT NULL COMMENT 'sha256 hash of client device signals',
    first_seen_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_device_fingerprints_user_id ON device_fingerprints (user_id);
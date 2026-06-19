SET FOREIGN_KEY_CHECKS = 0;

-- resets the tables and adds the following 6 sample users

--   alice@boi-trust.com   > [pass] Test1234!   (low-risk profile)
--   bob@boi-trust.com     > [pass] Test1234!   (medium-risk profile)
--   charlie@boi-trust.com > [pass] Test1234!   (low-risk profile)
--   dana@boi-trust.com    > [pass] Test1234!   (medium-risk profile)
--   eve@boi-trust.com     > [pass] Test1234!   (high-risk profile)
--   admin@boi-trust.com   > [pass] Admin1234!  (high-risk profile)

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

INSERT INTO users (email, password_hash) VALUES
('alice@boi-trust.com',   'pbkdf2:sha256:1000000$dRTVf3Dk8DSxWQyY$b2affedd3421b878de94ee6faf5364ec3d598e14c3f8011a9d75dbf157bdf932'),
('bob@boi-trust.com',     'pbkdf2:sha256:1000000$ixScKJJ8wr3M1tRc$9b91acfd97e2e26e6956e9683768716c8640a0d1fb86d31a41c5edf55c4164f3'),
('charlie@boi-trust.com', 'pbkdf2:sha256:1000000$jS8Vwo9FXjh28qqU$a0d39d5d9e46f3236d48703c442555dd76694fa5a25d8286f4b6bb474f38e076'),
('dana@boi-trust.com',    'pbkdf2:sha256:1000000$cJxGseXZy9z1wbJi$a4a844bd7e0c207215fcfe5be2df1d5e89289b0ec893da1a4b14540a2115ccab'),
('eve@boi-trust.com',     'pbkdf2:sha256:1000000$17umI0vmp36yGCNj$92bbc8dc893afed1a938bf086903ea31341558ad1be02b5a01b77f2fc99ed016'),
('admin@boi-trust.com',   'pbkdf2:sha256:1000000$X54smpK7DFoEwQxp$010c63ab60f09154aea4cd7e0f0baa0b44c2cacee91105d18312dffedb982a1f');

INSERT INTO risk_scores (user_id, risk_score, risk_level) VALUES
(1, 14, 'low'),
(2, 42, 'medium'),
(3, 91, 'high'),
(4, 18, 'low'),
(5, 48, 'medium'),
(6, 87, 'high');

ALTER TABLE users
    ADD COLUMN balance DECIMAL(12,2) NOT NULL DEFAULT 0.00
    COMMENT 'available funds, in account currency';

CREATE TABLE IF NOT EXISTS transactions (
    id                  INT PRIMARY KEY AUTO_INCREMENT,
    sender_id           INT NOT NULL,
    recipient_id        INT NOT NULL,
    amount              DECIMAL(12,2) NOT NULL,
    status              VARCHAR(20) NOT NULL COMMENT "'success' | 'failed' | 'blocked'",
    reason              VARCHAR(255) NULL,
    risk_score_at_time  INT NULL,
    risk_level_at_time  VARCHAR(20) NULL,
    timestamp           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_transaction_amount_positive CHECK (amount > 0),
    CONSTRAINT chk_transaction_status_valid CHECK (status IN ('success', 'failed', 'blocked'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_transactions_timestamp ON transactions (timestamp);
CREATE INDEX idx_transactions_sender ON transactions (sender_id);
CREATE INDEX idx_transactions_recipient ON transactions (recipient_id);

-- optional: seed some starting balances for your demo accounts
UPDATE users SET balance = 1000.00 WHERE email = 'alice@boi-trust.com';
UPDATE users SET balance = 500.00  WHERE email = 'bob@boi-trust.com';
UPDATE users SET balance = 750.00  WHERE email = 'charlie@boi-trust.com';
UPDATE users SET balance = 300.00  WHERE email = 'dana@boi-trust.com';
UPDATE users SET balance = 2000.00 WHERE email = 'eve@boi-trust.com';
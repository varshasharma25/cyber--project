-- (dev/demo only, (temporary)
--   alice@boi-trust.com > [pass] Test1234!   (low-risk profile)
--   bob@boi-trust.com   > [pass] Test1234!   (medium-risk profile)
--   admin@boi-trust.com > [pass] Admin1234!  (high-risk profile)

INSERT INTO users (email, password_hash) VALUES
('alice@boi-trust.com', 'pbkdf2:sha256:1000000$dRTVf3Dk8DSxWQyY$b2affedd3421b878de94ee6faf5364ec3d598e14c3f8011a9d75dbf157bdf932'),
('bob@boi-trust.com',   'pbkdf2:sha256:1000000$ixScKJJ8wr3M1tRc$9b91acfd97e2e26e6956e9683768716c8640a0d1fb86d31a41c5edf55c4164f3'),
('admin@boi-trust.com', 'pbkdf2:sha256:1000000$X54smpK7DFoEwQxp$010c63ab60f09154aea4cd7e0f0baa0b44c2cacee91105d18312dffedb982a1f');

INSERT INTO behavior_logs (user_id, event_type, event_data) VALUES
(1, 'login', '{"typing_speed": 320, "new_device": false, "login_hour": 14}'),
(2, 'login', '{"typing_speed": 95, "new_device": false, "login_hour": 22}'),
(3, 'transaction', '{"typing_speed": 700, "new_device": true, "login_hour": 3, "transaction_amount": 75000}');

INSERT INTO risk_scores (user_id, risk_score, risk_level) VALUES
(1, 14, 'low'),
(2, 42, 'medium'),
(3, 91, 'high');

INSERT INTO verification_logs (user_id, verification_method, status) VALUES
(2, 'sms', 'success'),
(3, 'biometric', 'failed'),
(3, '2fa', 'success');
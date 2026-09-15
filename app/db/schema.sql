CREATE DATABASE IF NOT EXISTS enterprise_ops DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE enterprise_ops;

CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(64) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(16) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sales (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sale_date DATE NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    region VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(64) NOT NULL,
    user_id INT NULL,
    event_type VARCHAR(32) NOT NULL,
    content_json JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_agent_logs_session (session_id),
    INDEX idx_agent_logs_created (created_at)
);

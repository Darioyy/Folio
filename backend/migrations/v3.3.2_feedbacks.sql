-- v3.3.2 feedbacks table migration

CREATE TABLE IF NOT EXISTS feedbacks (
  id         INT PRIMARY KEY AUTO_INCREMENT,
  user_id    INT NULL,
  type       ENUM('suggestion', 'bug', 'other') NOT NULL DEFAULT 'suggestion',
  content    TEXT NOT NULL,
  status     ENUM('pending', 'resolved') NOT NULL DEFAULT 'pending',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_fb_user    (user_id),
  INDEX idx_fb_status  (status),
  INDEX idx_fb_created (created_at),
  CONSTRAINT fk_feedbacks_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

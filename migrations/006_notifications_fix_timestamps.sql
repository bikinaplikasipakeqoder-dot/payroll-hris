-- Fix missing created_at/updated_at columns on the notifications table.
-- The Notification model inherits TimestampMixin, but the table created on
-- Turso was missing these columns, causing 500 errors on every dashboard page.
-- Turso does not support ALTER TABLE ADD COLUMN with CURRENT_TIMESTAMP defaults,
-- so we recreate the table and copy the existing data.

CREATE TABLE IF NOT EXISTS notifications_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    user_id INTEGER,
    employee_id INTEGER,
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT,
    link VARCHAR(500),
    is_read BOOLEAN DEFAULT FALSE,
    read_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT ck_notifications_type CHECK (notification_type IN ('PAYSLIP_READY', 'BULK_COMPLETE', 'BULK_FAILED')),
    FOREIGN KEY(company_id) REFERENCES companies (id),
    FOREIGN KEY(user_id) REFERENCES users (id),
    FOREIGN KEY(employee_id) REFERENCES employees (id)
);

CREATE INDEX idx_notifications_employee_read_new ON notifications_new (employee_id, is_read);
CREATE INDEX idx_notifications_user_read_new ON notifications_new (user_id, is_read);

INSERT INTO notifications_new (
    id, company_id, user_id, employee_id, notification_type, title, message, link, is_read, read_at
)
SELECT
    id, company_id, user_id, employee_id, notification_type, title, message, link, is_read, read_at
FROM notifications;

DROP TABLE notifications;

ALTER TABLE notifications_new RENAME TO notifications;

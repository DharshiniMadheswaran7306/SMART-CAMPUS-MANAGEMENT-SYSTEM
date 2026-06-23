-- fix_emails.sql
-- Run this to update the fake student emails in your existing database.
-- Replace the email addresses below with real ones, then run:
--   sqlite3 smart_campus.db < fix_emails.sql

UPDATE students SET email = 'dharsh7306@gmail.com' WHERE user_id = 'STU001';
UPDATE students SET email = 'dharsh7306@gmail.com' WHERE user_id = 'STU002';
UPDATE students SET email = 'dharsh7306@gmail.com' WHERE user_id = 'STU003';

-- Verify
SELECT user_id, name, email FROM students;

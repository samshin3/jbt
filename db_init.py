import sqlite3
import pandas as pd

# Only run this once to generate all the tables, this is just to log what tables have been created and their names
command = """
-- 1. Users Table
CREATE TABLE users (
    username TEXT PRIMARY KEY,
    email TEXT,
    profile_picture TEXT,
    verified BOOLEAN
);

-- 2. Group Info Table
CREATE TABLE group_info (
    group_id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT,
    description TEXT,
    status_flag TEXT DEFAULT 'active',
    created_by TEXT,
    modified_date DATETIME,
    creation_date DATETIME DEFAULT (datetime('now')),
    start_date DATE,
    end_date DATE,
    location TEXT,
    FOREIGN KEY (created_by) REFERENCES users (username)
);

-- 3. Group Members Table
CREATE TABLE group_members (
    group_id INTEGER,
    username TEXT,
    date_joined DATETIME DEFAULT (datetime('now')),
    PRIMARY KEY (group_id, username),
    FOREIGN KEY (group_id) REFERENCES group_info (group_id),
    FOREIGN KEY (username) REFERENCES users (username)
);

-- 4. Events Table
CREATE TABLE events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER,
    event_name TEXT,
    description TEXT,
    uploaded_by TEXT,
    upload_date DATETIME DEFAULT (datetime('now')),
    currency TEXT,
    paid_by TEXT,
    FOREIGN KEY (group_id) REFERENCES group_info (group_id),
    FOREIGN KEY (uploaded_by) REFERENCES users (username),
    FOREIGN KEY (paid_by) REFERENCES users (username)
);

-- 5. Transactions Table
CREATE TABLE transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER,
    event_id INTEGER,
    item_name TEXT,
    category TEXT DEFAULT 'General',
    amount_due DECIMAL(19,4),
    owed_by TEXT,
    modified_date DATETIME,
    FOREIGN KEY (group_id) REFERENCES group_info (group_id),
    FOREIGN KEY (event_id) REFERENCES events (event_id),
    FOREIGN KEY (owed_by) REFERENCES users (username)
);

-- 6. User Paid Amounts Table
CREATE TABLE user_paid_amounts (
    group_id INTEGER,
    paid_by TEXT,
    owed_by TEXT,
    total_paid_for DECIMAL(19,4),
    PRIMARY KEY (group_id, paid_by, owed_by),
    FOREIGN KEY (group_id) REFERENCES group_info (group_id),
    FOREIGN KEY (paid_by) REFERENCES users (username),
    FOREIGN KEY (owed_by) REFERENCES users (username)
);   

"""

if __name__ == "__main__":
    session = sqlite3.connect("jbt_database.db")
    cursor = session.cursor()
    cursor.executescript(command)


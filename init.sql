CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
INSERT INTO messages (text) VALUES ('Hello from XyOps Sample App!'), ('DB connection works!');

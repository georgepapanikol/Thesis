-- Drop tables if they exist
DROP TABLE IF EXISTS resumes CASCADE;
DROP TABLE IF EXISTS categories CASCADE;

-- Create categories table
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
); 

-- Create resumes table
CREATE TABLE resumes (
    id SERIAL PRIMARY KEY,
    source_id VARCHAR(50) UNIQUE NOT NULL,
    source_name VARCHAR(100),
    resume_content TEXT NOT NULL,
    category_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
);

-- Create indexes for better query performance
CREATE INDEX idx_resumes_category_id ON resumes(category_id);
CREATE INDEX idx_categories_name ON categories(category_name);
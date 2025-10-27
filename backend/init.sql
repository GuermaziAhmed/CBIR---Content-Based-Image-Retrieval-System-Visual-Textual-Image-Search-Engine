-- Initialize CBIR Database

CREATE TABLE IF NOT EXISTS images (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) UNIQUE NOT NULL,
    url VARCHAR(512) NOT NULL,
    tags TEXT,
    caption TEXT,
    descriptors_json JSONB,
    file_size INTEGER,
    width INTEGER,
    height INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for faster search
CREATE INDEX IF NOT EXISTS idx_images_filename ON images(filename);
CREATE INDEX IF NOT EXISTS idx_images_tags ON images USING GIN(to_tsvector('english', tags));
CREATE INDEX IF NOT EXISTS idx_images_caption ON images USING GIN(to_tsvector('english', caption));
CREATE INDEX IF NOT EXISTS idx_images_descriptors ON images USING GIN(descriptors_json);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_images_updated_at BEFORE UPDATE ON images
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data (optional)
-- INSERT INTO images (filename, url, tags, caption, descriptors_json)
-- VALUES 
--     ('sample1.jpg', '/data/images/sample1.jpg', 'cat animal pet', 'A cute orange cat', '{"color": true, "lbp": true}'),
--     ('sample2.jpg', '/data/images/sample2.jpg', 'dog animal pet', 'A happy dog running', '{"color": true, "lbp": true}');

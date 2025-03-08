CREATE INDEX IF NOT EXISTS favicons_hash_idx ON favicons (image_hash);
CREATE UNIQUE INDEX IF NOT EXISTS favicons_domain_idx ON favicons (domain);
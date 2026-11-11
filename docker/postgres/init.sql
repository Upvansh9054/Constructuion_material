-- Initialize PostgreSQL extensions for Demolition Intelligence & Material Recovery
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE demolition_intelligence TO demolition_user;

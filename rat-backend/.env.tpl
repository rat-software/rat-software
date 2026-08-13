# Database Connection (Production target database)
SQLALCHEMY_DATABASE_URI=postgresql://user:password@localhost:5432/db

# Core Security
SECRET_KEY=generate-a-random-string-here
SECURITY_PASSWORD_SALT=another-random-string

# Domain URL Handling
SERVER_NAME=your_server.com

# Form Verification Checks
RECAPTCHA_PUBLIC_KEY=RECAPTCHA_PUBLIC_KEY
RECAPTCHA_PRIVATE_KEY=RECAPTCHA_PRIVATE_KEY=

# Mail Operations Engine
MAIL_SERVER=smtp.resend.com
MAIL_PORT=465
MAIL_USERNAME=resend
MAIL_PASSWORD=your-resend-api-key
RESEND_API_KEY=your-resend-api-key
SECURITY_EMAIL_SENDER=admin@yourdomain.com

# Storage Endpoint Links
STORAGE_BASE_URL=https://storage.yourdomain.com
API_UPLOAD_KEY=test_api
STORAGE_FOLDER=/var/www/rat/storage

# Application Parameters
DEBUG=True

# LLM SECRET_KEY
LLM_SECRET_KEY="LLM KEY"
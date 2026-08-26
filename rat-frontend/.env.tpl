# Database
SQLALCHEMY_DATABASE_URI=postgresql://user:password@localhost:5432/db

# Security
SECRET_KEY=generate-a-random-string-here
SECURITY_PASSWORD_SALT=another-random-string

# Domain URL Handling
SERVER_NAME=your_server.com

# Form Verification Checks
RECAPTCHA_PUBLIC_KEY=RECAPTCHA_PUBLIC_KEY
RECAPTCHA_PRIVATE_KEY=RECAPTCHA_PRIVATE_KEY=

# Mail Settings
MAIL_SERVER=smtp.resend.com
MAIL_PORT=465
MAIL_PASSWORD=your-resend-api-key
MAIL_USERNAME=resend
RESEND_API_KEY=re_B6Ru7a5t_CbkSKpU9EMwbV4QF9eDBA4Yk
SECURITY_EMAIL_SENDER=admin@yourdomain.com

# Storage
STORAGE_BASE_URL=https://storage.yourdomain.com
API_UPLOAD_KEY=your_api_key
STORAGE_FOLDER=/var/www/rat/storage

# App Settings
DEBUG=True

# LLM SECRET_KEY
LLM_SECRET_KEY="LLM KEY"
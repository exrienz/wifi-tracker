# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask-based WiFi network scanner management application designed for home use. The application allows:
- Admin users to create and manage wireless scan environments
- Users to upload CSV files containing wireless network scan data
- Deduplication of scan data based on BSSID and SSID
- Adding remarks/notes to individual scan entries

## Architecture

### Tech Stack
- **Backend**: Flask with SQLAlchemy ORM
- **Database**: SQLite (single file, suitable for home use)
- **Authentication**: Flask-Login with bcrypt password hashing
- **Frontend**: Jinja2 templates with Bootstrap styling
- **Security**: Flask-WTF for CSRF protection and form validation
- **Containerization**: Docker with Python 3.9+ base

### Project Structure
```
/app
  /src
    __init__.py           # Flask app initialization
    models.py             # SQLAlchemy models (User, Environment, WirelessScan)
    routes.py             # Main Flask routes
    auth.py               # Authentication helpers
    forms.py              # WTForms for form validation
    utils.py              # CSV parsing and deduplication logic
  /templates              # Jinja2 HTML templates
  /uploads                # Temporary CSV upload storage
  requirements.txt        # Python dependencies
  Dockerfile              # Container configuration
  docker-compose.yml      # Multi-container setup (optional)
  .env                    # Environment variables (not in version control)
```

### Database Schema
- **User**: id, username (unique), password_hash, is_admin, is_approved
- **Environment**: id, name (unique per admin), created_by, created_at
- **WirelessScan**: id, environment_id (FK), bssid, ssid, quality, signal, channel, encryption, timestamp, remarks, uploaded_by, uploaded_at

Key constraint: Unique on (environment_id, bssid, ssid) for deduplication.

## Development Commands

### Initial Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### Running the Application
```bash
# Development server
flask run

# Production with Gunicorn
gunicorn -b 0.0.0.0:5000 "src:app"
```

### Docker Commands
```bash
# Build image
docker build -t wifi-scanner .

# Run container
docker run -p 5000:5000 --env-file .env wifi-scanner

# Using docker-compose
docker-compose up --build
```

### Testing
```bash
# Run tests (when implemented)
python -m pytest

# Run specific test file
python -m pytest tests/test_models.py
```

## Key Implementation Details

### Authentication Flow
- First registered user automatically gets admin privileges
- Subsequent users require admin approval
- All routes except login/register require authentication

### CSV Upload Process
1. Validate file format and required columns
2. Parse each row with data type validation
3. Check for existing records using (environment_id, bssid, ssid)
4. Insert only new records to prevent duplicates
5. Log upload metadata (user, timestamp)

### Security Considerations
- All passwords hashed with bcrypt
- CSRF protection on all POST routes
- File upload size limits (1MB max)
- Input sanitization for remarks and form data
- SQLAlchemy ORM prevents SQL injection

### Environment Variables Required
- `SECRET_KEY`: Flask secret key for sessions
- `DATABASE_URI`: SQLite database path
- `UPLOAD_FOLDER`: Path for temporary file uploads

## Route Structure

### Authentication Routes
- `GET /register` - Registration form
- `POST /register` - Create new user
- `GET /login` - Login form  
- `POST /login` - Authenticate user

### Admin Routes
- `GET /admin/dashboard` - User approval interface
- `POST /admin/approve/user/<id>` - Approve user

### Environment Management
- `GET /environments` - List environments
- `POST /environment/new` - Create environment (admin only)
- `GET /environment/<id>` - View environment and scans
- `POST /environment/<id>/upload` - Upload CSV data

### Scan Management
- `POST /scan/<id>/remarks` - Update scan remarks
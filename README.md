# WiFi Scanner Management Application

A Flask-based web application designed for home use to manage wireless network scan data with secure user authentication, CSV upload capabilities, and automatic data deduplication.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.3+-green.svg)
![SQLite](https://img.shields.io/badge/sqlite-3-orange.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

## Features

- **User Authentication**: Secure registration and login system with admin approval
- **Environment Management**: Create and manage different scanning environments
- **CSV Upload**: Upload wireless scan data in CSV format with automatic deduplication
- **Data Management**: View scan data, add remarks, and track upload history
- **Admin Dashboard**: User management and system statistics for administrators
- **Responsive Design**: Bootstrap-based UI that works on desktop and mobile devices

## Quick Start

### Using Docker (Recommended)

1. **Clone and setup**:
   ```bash
   git clone <your-repo-url>
   cd wifi
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

3. **Access the application**: Open http://localhost:5000

### Local Development

1. **Setup environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Initialize database**:
   ```bash
   python run.py init-db
   ```

4. **Run the application**:
   ```bash
   python run.py
   ```

## CSV File Format

Your CSV files must contain these columns:

- `bssid` - MAC address (e.g., AA:BB:CC:DD:EE:FF)
- `ssid` - Network name
- `quality` - Signal quality percentage (0-100)
- `signal` - Signal strength in dBm (e.g., -45)
- `channel` - WiFi channel number
- `encryption` - Security type (WPA2, WEP, Open, etc.)
- `timestamp` - Scan time (YYYY-MM-DD HH:MM:SS)

### Sample CSV:
```csv
bssid,ssid,quality,signal,channel,encryption,timestamp
AA:BB:CC:DD:EE:FF,MyNetwork,85,-42,6,WPA2,2023-12-01 10:30:00
11:22:33:44:55:66,GuestWiFi,62,-58,11,WPA3,2023-12-01 10:30:05
```

## User Roles

- **First User**: Automatically becomes admin with full privileges
- **Admin Users**: Can create environments, manage users, and access admin dashboard
- **Regular Users**: Can upload CSV data to existing environments (requires approval)

## Production Deployment

1. **Set strong environment variables**:
   ```bash
   SECRET_KEY=your-very-secure-secret-key
   DATABASE_URI=sqlite:///data/wifi_scanner.db
   ```

2. **Deploy with Docker**:
   ```bash
   docker-compose up -d
   ```

3. **Optional**: Setup reverse proxy (nginx) for HTTPS

## Security Features

- Password hashing with bcrypt
- CSRF protection on all forms
- File upload size limits (1MB default)
- SQLAlchemy ORM prevents SQL injection
- Input validation and sanitization
- Session-based authentication

## Database Schema

- **Users**: Authentication and user management
- **Environments**: Logical groupings for scan data
- **WirelessScans**: Network scan data with deduplication constraints

## Architecture

### Tech Stack
- **Backend**: Flask with SQLAlchemy ORM
- **Database**: SQLite (single file, suitable for home use)
- **Authentication**: Flask-Login with bcrypt password hashing
- **Frontend**: Jinja2 templates with Bootstrap 5 styling
- **Security**: Flask-WTF for CSRF protection and form validation
- **Containerization**: Docker with Python 3.9+ base

### Project Structure
```
/
├── app/
│   ├── src/
│   │   ├── __init__.py          # Flask app initialization
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── routes.py            # Main application routes
│   │   ├── auth.py              # Authentication helpers
│   │   ├── forms.py             # WTForms validation
│   │   └── utils.py             # CSV parsing utilities
│   ├── templates/               # Jinja2 HTML templates
│   └── static/                  # CSS, JS, images
├── uploads/                     # Temporary CSV storage
├── instance/                    # SQLite database location
├── Dockerfile                   # Container configuration
├── docker-compose.yml           # Multi-container setup
├── requirements.txt             # Python dependencies
├── run.py                       # Application entry point
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## API Endpoints

### Authentication
- `GET /register` - User registration form
- `POST /register` - Create new user account
- `GET /login` - User login form
- `POST /login` - Authenticate user
- `POST /logout` - End user session

### Environment Management
- `GET /environments` - List all environments
- `POST /environment/new` - Create new environment (admin only)
- `GET /environment/<id>` - View environment and scan data
- `POST /environment/<id>/upload` - Upload CSV scan data

### Administration
- `GET /admin/dashboard` - Admin user management interface
- `POST /admin/approve/user/<id>` - Approve pending users

### Scan Data
- `POST /scan/<id>/remarks` - Add/update remarks on scan entry

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

### Common Issues

**Database locked errors**:
```bash
# Stop all containers and restart
docker-compose down
docker-compose up --build
```

**Permission denied on uploads**:
```bash
# Fix upload directory permissions
chmod 755 uploads/
```

**Container won't start**:
```bash
# Check logs
docker-compose logs -f
```

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
python -m pytest

# Run with coverage
python -m pytest --cov=app/src
```

### Database Management
```bash
# Initialize database
python run.py init-db

# Reset database (development only)
rm instance/wifi_scanner.db
python run.py init-db
```

## License

This project is for educational and home use purposes. See the code comments and documentation for specific implementation details.# wifi-tracker

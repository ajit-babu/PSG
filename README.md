# PSG - Professional Safety Guardian
## Desktop Application for MEP Construction Safety Management

### Overview
A professional, offline-first desktop application designed for construction sites in the UAE where internet connectivity is intermittent. Built with Python 3.12+ and PyQt6 for a robust, responsive user experience.

### Key Features
- **Offline-First Architecture**: Full functionality without internet connectivity
- **Intelligent Sync Engine**: Automatic background synchronization when connectivity is restored
- **Conflict Resolution**: Last-Write-Wins strategy with timestamp-based conflict detection
- **Professional GUI**: Clean, intuitive interface built with PyQt6
- **Data Integrity**: SQLite local database with comprehensive sync metadata

### Technology Stack
- **Python 3.12+**: Modern Python with type hints and async capabilities
- **PyQt6**: Professional desktop GUI framework
- **SQLite**: Lightweight, serverless local database
- **Requests**: HTTP client for API communication

### Project Structure
```
PSG/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── config.py               # Configuration management
│   ├── constants.py            # Application constants
│   │
│   ├── database/               # Data Access Layer
│   │   ├── __init__.py
│   │   ├── models.py           # SQLAlchemy/SQLite models
│   │   ├── repository.py       # Data repository pattern
│   │   ├── connection.py       # Database connection management
│   │   └── migrations/         # Database migration scripts
│   │
│   ├── ui/                     # Presentation Layer
│   │   ├── __init__.py
│   │   ├── main_window.py      # Main application window
│   │   ├── dialogs/            # Modal dialogs
│   │   ├── widgets/            # Custom widgets
│   │   ├── views/              # View components
│   │   └── resources/          # Icons, stylesheets, images
│   │
│   ├── services/               # Business Logic Layer
│   │   ├── __init__.py
│   │   ├── sync_service.py     # Offline-to-online sync engine
│   │   ├── connectivity.py     # Network connectivity detection
│   │   ├── notification.py     # User notifications
│   │   └── workers/            # Background workers (QThread)
│   │
│   └── utils/                  # Utility modules
│       ├── __init__.py
│       ├── logger.py           # Logging configuration
│       ├── validators.py       # Input validation
│       └── helpers.py          # Helper functions
│
├── requirements.txt            # Python dependencies
├── pyproject.toml             # Project metadata
├── setup.py                   # Installation script
└── run.py                     # Development entry point
```

### Installation

#### Prerequisites
- Python 3.12 or higher
- pip package manager

#### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd PSG

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python run.py
```

### Configuration

The application uses a configuration file located at:
- **Windows**: `%APPDATA%/PSG/config.json`
- **Linux**: `~/.config/PSG/config.json`
- **macOS**: `~/Library/Application Support/PSG/config.json`

#### Configuration Options
```json
{
    "api": {
        "base_url": "https://api.psg-safety.com/v1",
        "timeout": 30,
        "retry_attempts": 3,
        "backoff_factor": 2
    },
    "database": {
        "path": "data/psg.db",
        "backup_enabled": true,
        "backup_interval_hours": 24
    },
    "sync": {
        "interval_minutes": 5,
        "batch_size": 50,
        "auto_sync": true
    },
    "ui": {
        "theme": "light",
        "language": "en",
        "font_size": 12
    }
}
```

### Database Schema

The application uses SQLite with the following core tables:

#### Incidents Table
- Stores safety incidents and near-miss reports
- Includes photo attachments and location data
- Tracks reporter information and severity levels

#### Training/Compliance Logs
- Employee training records
- Course completion tracking
- Expiry date monitoring and alerts

#### Audit/Inspection Reports
- Compliance check items
- Pass/fail status tracking
- Detailed comments and recommendations

#### Sync Metadata
Every table includes sync tracking fields:
- `id` (UUID): Unique identifier
- `created_at`: Record creation timestamp
- `updated_at`: Last modification timestamp
- `is_synced`: Boolean sync status
- `sync_status_code`: Detailed sync state

### Sync Engine

The SyncService provides robust offline-to-online synchronization:

1. **Connectivity Detection**: Monitors network status before sync attempts
2. **Batch Processing**: Efficiently uploads records in configurable batches
3. **Error Resilience**: Exponential backoff retry mechanism
4. **Conflict Resolution**: Last-Write-Wins strategy based on timestamps

### Building for Distribution

#### Windows Executable
```bash
pyinstaller --onefile --windowed --icon=app/ui/resources/icon.ico run.py
```

#### Linux AppImage
```bash
pyinstaller --onefile --windowed --icon=app/ui/resources/icon.png run.py
```

### License
Proprietary - All rights reserved

### Support
For technical support, contact: support@psg-safety.com
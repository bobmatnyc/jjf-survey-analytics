# 🔍 Hybrid Surveyor

**Advanced Google Sheets Data Extraction and Normalization Tool**

Hybrid Surveyor combines the best features from multiple architectural approaches to provide a production-ready, async-first data extraction tool for Google Spreadsheets.

## ✨ Features

### 🚀 **Performance & Scalability**
- **Async/await architecture** for high-performance concurrent operations
- **Intelligent rate limiting** to respect Google API limits
- **Batch processing** with configurable batch sizes
- **Connection pooling** for optimal database performance
- **Circuit breaker pattern** for resilient external service calls

### 🏗️ **Architecture Excellence**
- **Mature dependency injection** using `dependency-injector`
- **Service-oriented architecture** with clear separation of concerns
- **Repository pattern** for clean data access
- **Comprehensive error handling** with typed exceptions
- **Retry strategies** with exponential backoff and jitter

### 📊 **Data Pipeline**
- **Flexible raw + processed approach** for data reprocessing capabilities
- **Type-safe data models** using Pydantic
- **Automatic schema detection** and data type conversion
- **Data validation** with detailed error reporting
- **Deduplication** using content hashing

### 🖥️ **Developer Experience**
- **Rich CLI interface** with progress bars and colored output
- **Comprehensive health checking** for all system components
- **Structured logging** with JSON output support
- **Complete test suite** with async test support
- **Type hints throughout** for better IDE support

### 🔧 **Production Ready**
- **Environment-based configuration** with validation
- **Database migrations** support
- **Monitoring and metrics** collection
- **Graceful error recovery** and job resumption
- **Docker support** for containerized deployment

## 🏆 **Hybrid Approach Benefits**

This project combines the strengths of multiple approaches:

| Feature | Source | Benefit |
|---------|--------|---------|
| **Async Architecture** | sheets_processor | High performance, concurrent processing |
| **Dependency Injection** | sheets_processor | Mature DI framework with auto-wiring |
| **Project Structure** | Surveyor | Complete development setup and tooling |
| **CLI Design** | Surveyor | Excellent user experience with rich output |
| **Type Safety** | Surveyor | Comprehensive type hints and validation |
| **Data Pipeline** | Both | Flexible raw+processed with type safety |

## 📋 **Prerequisites**

- **Python 3.11+** (async/await features)
- **Google Cloud Console project** with Sheets API enabled
- **Google API credentials** (service account or OAuth)

## 🚀 **Quick Start**

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd hybrid_surveyor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Required configuration:**
```bash
# Google Sheets API
GOOGLE_CREDENTIALS_FILE=path/to/credentials.json

# Database (optional, defaults to SQLite)
DATABASE_URL=sqlite+aiosqlite:///hybrid_surveyor.db

# Processing (optional)
PROCESSING_BATCH_SIZE=1000
PROCESSING_MAX_CONCURRENT_JOBS=5
```

### 3. Google Sheets API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Google Sheets API** and **Google Drive API**
4. Create **Service Account** credentials
5. Download `credentials.json` file
6. Update `.env` with the file path

### 4. Initialize Database

```bash
hybrid-surveyor init-db
```

### 5. Extract Data

```bash
# Use default configured spreadsheets
hybrid-surveyor extract --use-default-urls

# Extract specific spreadsheets
hybrid-surveyor extract --urls "https://docs.google.com/spreadsheets/d/your-id/edit"

# Extract with custom job name
hybrid-surveyor extract --use-default-urls --job-name "Monthly Import"

# Extract only (skip processing)
hybrid-surveyor extract --use-default-urls --extract-only
```

## 📖 **Usage Examples**

### Basic Operations

```bash
# Check system health
hybrid-surveyor health

# View configuration
hybrid-surveyor config

# Check job status
hybrid-surveyor status --limit 20

# Process unprocessed data
hybrid-surveyor process --batch-size 2000
```

### Advanced Usage

```bash
# Verbose logging with structured output
hybrid-surveyor --verbose --structured-logs extract --use-default-urls

# Custom batch size for large datasets
hybrid-surveyor extract --use-default-urls --batch-size 5000

# Extract multiple specific sheets
hybrid-surveyor extract \
  --urls "https://docs.google.com/spreadsheets/d/sheet1/edit" \
  --urls "https://docs.google.com/spreadsheets/d/sheet2/edit" \
  --job-name "Custom Import"
```

## 🏗️ **Architecture Overview**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI Layer     │    │  Service Layer  │    │  Data Layer     │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Rich CLI      │───▶│ • Sheets Service│───▶│ • Database      │
│ • Progress Bars │    │ • Transform Svc │    │ • Raw Storage   │
│ • Error Display │    │ • Extraction Svc│    │ • Processed     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Config & DI     │    │ Core Interfaces │    │ Domain Models   │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Settings      │    │ • Abstractions  │    │ • Pydantic      │
│ • DI Container  │    │ • Error Types   │    │ • SQLAlchemy    │
│ • Environment   │    │ • Retry Logic   │    │ • Type Safety   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📊 **Data Flow**

```
Google Sheets ──┐
                ├─▶ Extract ──▶ Raw Storage ──▶ Transform ──▶ Normalized Storage
Google Sheets ──┘       │            │              │              │
                         ▼            ▼              ▼              ▼
                    Job Tracking  Deduplication  Validation    Final Tables
```

## 🧪 **Testing**

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/hybrid_surveyor --cov-report=html

# Run specific test types
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Skip slow tests

# Run async tests
pytest --asyncio-mode=auto
```

## 📈 **Monitoring & Health**

### Health Checks

```bash
# Comprehensive health check
hybrid-surveyor health
```

**Monitors:**
- Database connectivity
- Google Sheets API availability
- System resources (CPU, memory, disk)
- Configuration validation

### Logging

```bash
# Structured JSON logging
hybrid-surveyor --structured-logs extract --use-default-urls

# Debug logging
hybrid-surveyor --verbose extract --use-default-urls
```

## 🔧 **Configuration Reference**

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///hybrid_surveyor.db` | Database connection URL |
| `GOOGLE_CREDENTIALS_FILE` | None | Path to Google service account JSON |
| `PROCESSING_BATCH_SIZE` | 1000 | Batch size for data processing |
| `PROCESSING_MAX_CONCURRENT_JOBS` | 5 | Max concurrent processing jobs |
| `LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_ENABLE_STRUCTURED` | true | Enable JSON structured logging |

### Default Spreadsheets

The application processes these Google Sheets by default:

1. `1fAAXXGOiDWc8lMVaRwqvuM2CDNAyNY_Px3usyisGhaw` - Main dataset
2. `1qEHKDVIO4YTR3TjMt336HdKLIBMV2cebAcvdbGOUdCU` - Secondary data
3. `1-aw7gjjvRMQj89lstVBtKDZ67Cs-dO1SHNsp4scJ4II` - Reference data
4. `1f3NKqhNR-CJr_e6_eLSTLbSFuYY8Gm0dxpSL0mlybMA` - Lookup tables
5. `1mQxcZ9U1UsVmHstgWdbHuT7bqfVXV4ZNCr9pn0TlVWM` - Historical data
6. `1h9AooI-E70v36EOxuErh4uYBg2TLbsF7X5kXdkrUkoQ` - Metadata

## 🐳 **Docker Support**

```dockerfile
# Dockerfile included for containerized deployment
docker build -t hybrid-surveyor .
docker run -e GOOGLE_CREDENTIALS_FILE=/app/creds.json hybrid-surveyor
```

## 🤝 **Contributing**

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install

# Run linting
black src/ tests/
isort src/ tests/
flake8 src/ tests/
mypy src/

# Run tests
pytest
```

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **sheets_processor** - Async architecture and DI patterns
- **Surveyor** - Project structure and CLI design
- **Google Sheets API** - Data source integration
- **SQLAlchemy** - Database ORM
- **Rich** - Beautiful CLI output
- **Pydantic** - Data validation and settings

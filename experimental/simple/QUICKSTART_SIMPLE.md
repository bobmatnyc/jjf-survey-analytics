# Simple App - Quick Start Guide

## 🚀 5-Minute Setup

### Prerequisites
- Python 3.8+ installed
- Internet connection (to fetch Google Sheets)
- Virtual environment activated

### Step 1: Activate Virtual Environment
```bash
source venv/bin/activate
```

### Step 2: Run the App
```bash
python simple_app.py
```

That's it! The app will:
1. Load data from Google Sheets (~3 seconds)
2. Start Flask server on port 8080
3. Display: "✓ Data loaded successfully. Ready to serve requests."

### Step 3: Open Browser
```
http://localhost:8080
```

---

## 📊 What You'll See

### Home Dashboard
- **Participation Overview:** Total orgs, completion rates
- **Organization Status:** Per-org completion tracking
- **Latest Activity:** Recent survey submissions
- **Participation Funnel:** Intake → CEO → Tech → Staff flow

### Data Pages
- **Data Navigation:** `/data` - Links to all 7 tabs
- **Tab Viewer:** `/data/Intake` - View any tab's data

---

## 🔄 Refresh Data

### Via Web UI
Click "Extract Data from Google Sheets" button on home page

### Via API
```bash
curl -X POST http://localhost:8080/api/refresh
```

### Via Code
```python
from sheets_reader import SheetsReader
data = SheetsReader.fetch_all_tabs(verbose=True)
```

---

## 🧪 Test It Works

### Test 1: Check API
```bash
curl http://localhost:8080/api/stats
```

Expected: JSON with 7 tabs and ~123 total rows

### Test 2: View Dashboard
```bash
open http://localhost:8080
```

Expected: Dashboard with participation metrics

### Test 3: Verify No Database
```bash
rm simple_data.db 2>/dev/null
curl http://localhost:8080/api/stats
```

Expected: Still works! (No database needed)

---

## 🛠️ Troubleshooting

### Port 8080 in Use
```bash
lsof -ti:8080 | xargs kill -9
python simple_app.py
```

### Data Not Loading
```bash
curl -X POST http://localhost:8080/api/refresh
```

### Import Error
```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📁 Key Files

- **`simple_app.py`** - Main Flask app (in-memory storage)
- **`sheets_reader.py`** - Google Sheets reader
- **`templates/simple_*.html`** - UI templates

### Legacy Files (Not Used)
- ~~`simple_extractor.py`~~ - OLD database extractor
- ~~`simple_data.db`~~ - OLD database file

---

## ⚡ Key Features

✅ **No Database Required** - Data stored in memory
✅ **Auto-Load on Startup** - Data fetched when app starts
✅ **Fast Dashboard** - ~50ms load time
✅ **Simple Refresh** - One click or API call
✅ **Pure Python** - No SQL queries needed

---

## 📖 Full Documentation

See **[SIMPLE_APP_README.md](SIMPLE_APP_README.md)** for complete details:
- Architecture details
- Implementation guide
- Production deployment
- Advanced usage

---

## 🎯 Quick Commands

```bash
# Start app
source venv/bin/activate && python simple_app.py

# Test reader
python3 sheets_reader.py

# Refresh data
curl -X POST http://localhost:8080/api/refresh

# Check stats
curl http://localhost:8080/api/stats

# Kill port 8080
lsof -ti:8080 | xargs kill -9
```

---

**Need help?** Check [SIMPLE_APP_README.md](SIMPLE_APP_README.md) or review the code comments.

# 📊 Surveyor Data Viewer

A modern web interface for viewing and managing Google Sheets survey data with a beautiful Tailwind CSS interface.

## 🚀 Quick Start

### 1. Extract Data from Google Sheets
```bash
python improved_extractor.py
```

### 2. Start the Web Interface
```bash
python app.py
```

### 3. Open in Browser
Navigate to: **http://localhost:5001**

## 📁 Project Structure

```
surveyor/
├── app.py                      # Flask web application
├── improved_extractor.py       # Google Sheets data extractor
├── surveyor_data_improved.db   # SQLite database (created after extraction)
├── templates/                  # HTML templates
│   ├── base.html              # Base template with navigation
│   ├── dashboard.html         # Dashboard overview
│   ├── spreadsheets.html      # Spreadsheets listing
│   ├── spreadsheet_detail.html # Individual spreadsheet view
│   ├── jobs.html              # Extraction jobs history
│   └── error.html             # Error page
└── README.md                  # This file
```

## 🎯 Features

### 📊 **Dashboard**
- **Overview statistics** of all spreadsheets and data
- **Sheet type distribution** (Survey, Assessment, Inventory)
- **Latest extraction job status** and progress
- **Recent spreadsheets** with quick access

### 📋 **Spreadsheets Management**
- **Grid view** of all imported spreadsheets
- **Search and filter** by title and type
- **Type categorization** with color-coded badges
- **Row count** and last sync information
- **Direct links** to Google Sheets

### 🔍 **Data Viewing**
- **Paginated table view** of spreadsheet data
- **Column sorting** and data export
- **Full-text search** within data
- **Responsive design** for mobile and desktop
- **CSV export** functionality

### ⚙️ **Job Monitoring**
- **Extraction job history** with detailed progress
- **Success/failure rates** and error reporting
- **Real-time status updates** for running jobs
- **Job duration** and performance metrics

## 🎨 **User Interface**

### **Design System**
- **Tailwind CSS** for modern, responsive design
- **Font Awesome icons** for visual clarity
- **Color-coded categories**:
  - 🔵 **Survey** - Blue theme
  - 🟢 **Assessment** - Green theme  
  - 🟣 **Inventory** - Purple theme
- **Mobile-first** responsive design

### **Interactive Features**
- **Hover effects** and smooth transitions
- **Copy-to-clipboard** functionality
- **Modal dialogs** for detailed views
- **Auto-refresh** for live data updates

## 🗄️ **Database Schema**

### **Tables**
1. **`spreadsheets`** - Metadata about each Google Sheet
2. **`raw_data`** - Actual spreadsheet data stored as JSON
3. **`extraction_jobs`** - Job tracking and history

### **Key Features**
- **JSON storage** for flexible data structure
- **SHA256 hashing** for deduplication
- **Foreign key constraints** for data integrity
- **Optimized indexes** for fast queries

## 📈 **Supported Google Sheets**

The system currently supports **6 JJF Technology Assessment spreadsheets**:

| **Type** | **Count** | **Description** |
|----------|-----------|-----------------|
| **Survey** | 2 | Survey questions and response collection |
| **Assessment** | 3 | Technology maturity assessments (CEO, Staff, Tech Lead) |
| **Inventory** | 1 | Software systems inventory |

## 🛠️ **Development**

### **Requirements**
- **Python 3.8+**
- **Flask** - Web framework
- **SQLite3** - Database (built into Python)
- **Internet connection** - For Google Sheets access

### **Installation**
```bash
# Install Flask
pip install flask

# No other dependencies required!
```

### **Running in Development**
```bash
# Extract data first
python improved_extractor.py

# Start web server
python app.py

# Access at http://localhost:5001
```

## 📊 **API Endpoints**

### **Web Routes**
- `GET /` - Dashboard
- `GET /spreadsheets` - Spreadsheets listing
- `GET /spreadsheet/<id>` - Individual spreadsheet view
- `GET /jobs` - Extraction jobs history

### **API Routes**
- `GET /api/stats` - Dashboard statistics (JSON)
- `GET /api/spreadsheet/<id>/data` - Spreadsheet data (JSON)

## 🔍 **Troubleshooting**

### **Common Issues**

1. **Database not found**
   ```bash
   # Run the extractor first
   python improved_extractor.py
   ```

2. **Port already in use**
   ```bash
   # Change port in app.py or kill existing process
   lsof -ti:5001 | xargs kill -9
   ```

3. **Google Sheets access denied**
   - Check if sheets are publicly accessible
   - Verify URLs are correct
   - Check internet connection

### **Debug Mode**
The web application runs in debug mode by default:
- **Auto-reload** on code changes
- **Detailed error messages** in browser
- **Interactive debugger** for exceptions

## 📝 **Data Flow**

1. **Extract** → `improved_extractor.py` downloads Google Sheets data
2. **Store** → Data saved to SQLite database with metadata
3. **Serve** → Flask app provides web interface to view data
4. **Display** → Tailwind CSS renders beautiful, responsive UI

## 🎯 **Next Steps**

### **Potential Enhancements**
- **Real-time sync** with Google Sheets
- **Data visualization** charts and graphs
- **User authentication** and access control
- **Data export** to multiple formats (Excel, PDF)
- **Advanced filtering** and search capabilities
- **Email notifications** for extraction jobs

---

## 🏆 **Success!**

You now have a **complete web-based survey data management system** with:
- ✅ **6/6 Google Sheets** successfully imported
- ✅ **46 total data rows** extracted and stored
- ✅ **Modern web interface** with Tailwind CSS
- ✅ **Responsive design** for all devices
- ✅ **Real-time job monitoring** and progress tracking

**🌐 Access your data at: http://localhost:5001**

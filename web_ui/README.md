# AI Culinary Expert - Web UI

A clean, modern web interface for the AI Culinary Expert application, built with vanilla HTML/CSS/JavaScript and FastAPI.

## Features

- **User Authentication**: Mock login and registration system
- **Menu Processing**: Upload and process menu files (PDF, TXT, JPG, PNG, XLSX, CSV)
- **Wine Management**: Process wines from files or knowledge base
- **Wine Pairing**: Intelligent wine-dish pairing with scientific analysis
- **Report Generation**: Comprehensive reports with rankings, similar wines, and pairings
- **Report Management**: Save, view, and manage past reports
- **PDF Export**: Generate PDF reports with all data

## File Structure

```
web_ui/
├── index.html              # Welcome/login screen
├── home.html               # Home screen
├── create-report.html      # Report creation flow
├── report-preview.html     # Report preview before saving
├── report-view.html        # Full report display
├── past-reports.html       # Past reports list
├── css/
│   ├── styles.css          # Main stylesheet
│   ├── components.css      # Component-specific styles
│   └── errors.css          # Error states and messages
├── js/
│   ├── auth.js             # Authentication logic
│   ├── api.js              # API communication
│   ├── report.js           # Report creation logic
│   ├── validation.js       # File validation
│   ├── progress.js         # Progress tracking
│   └── utils.js            # Utility functions
├── assets/
│   └── logo.png            # App logo (replace with actual logo)
├── server.py               # FastAPI backend server
└── README.md               # This file
```

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Add Logo**:
   - Replace `assets/logo.png` with your actual logo image
   - Recommended size: 200x200px or similar

3. **Configure Environment**:
   - Ensure your `.env` file has `GOOGLE_AI_API_KEY` set
   - The app uses Gemini 3 Flash for processing

## Running the Application

1. **Start the Server**:
   ```bash
   cd web_ui
   python server.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn server:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Access the Application**:
   - Open your browser and navigate to: `http://localhost:8000`
   - The login screen will be displayed

## Usage

1. **Login/Register**:
   - Create an account or login with mock credentials
   - Authentication is stored in browser localStorage

2. **Create Report**:
   - Click "Create New Report" from the home screen
   - Upload menu files (PDF, TXT, images, etc.)
   - Select wine sources (detected wines, files, or knowledge base)
   - Wait for processing to complete
   - Preview the report
   - View full report and save if desired

3. **View Past Reports**:
   - Click "View Past Reports" from the home screen
   - Search, filter, and sort your saved reports
   - Edit report names
   - View or delete reports

4. **Export Reports**:
   - From the report view, click "Download PDF"
   - A comprehensive PDF will be generated with all report data

## API Endpoints

- `POST /api/login` - Mock authentication
- `POST /api/register` - Mock registration
- `POST /api/process-menu` - Process menu files
- `POST /api/process-wines` - Process wine files
- `POST /api/analyze-similarity` - Analyze wine similarity
- `POST /api/pair-wines` - Pair wines to dishes
- `POST /api/rank-wines` - Rank wines by matches
- `POST /api/generate-report` - Generate comprehensive report

## Design

- **Colors**: White background with dark green accents (#1a5f1a)
- **Style**: Clean, minimal, modern
- **Responsive**: Mobile-friendly design
- **Logo Visibility**: Logo shown on login screen and during loading animations

## Browser Compatibility

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Requires JavaScript enabled
- Uses localStorage for data persistence

## Notes

- All data is stored locally in the browser (localStorage)
- Reports are limited by browser storage capacity (~5MB)
- File uploads are limited to 10MB per file
- The application uses mock authentication (no real backend auth)

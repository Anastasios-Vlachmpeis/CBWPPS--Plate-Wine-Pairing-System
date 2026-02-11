# CBWPPS -- Plate - Wine Pairing System

A comprehensive molecular gastronomy-based wine pairing AI system that recommends wines based on shared flavor compounds between dishes and wines. The system combines scientific flavor analysis with intelligent pairing algorithms to provide restaurant-quality wine recommendations.

## Project Overview

A full-stack wine pairing application that processes restaurant menus, analyzes molecular flavor compounds, and generates intelligent wine recommendations. The system supports both individual dish pairing and complete menu analysis workflows, with a modern web interface and robust API.

## Architecture

The system is built with a modular architecture supporting multiple use cases:

### Core Components

1. **Data Processing Pipeline** (`processing.py`)
   - Processes raw CSV datasets (XWines, FlavorGraph)
   - Normalizes wine attributes (type, body, acidity, tannin) to standardized 1-5 scales
   - Maps ingredients to chemical flavor compounds via FlavorGraph database
   - Creates molecular "flavor bridge" connecting wines to compounds through grape varieties
   - Generates knowledge bases:
     - `processed_wines.json` - 1,007 wines with normalized attributes and flavor compounds
     - `ingredient_flavor_map.json` - 419 ingredients mapped to their chemical compounds

2. **Individual Dish Pairing** (`wine_sommelier.py`)
   - **Stage 1**: AI identifies key ingredients from dish description or image
   - **Stage 2**: Python-based molecular search finds candidate wines with shared compounds
   - **Stage 3**: AI selects top 3 wines and generates scientific/culinary reasoning
   - Supports both text and image inputs
   - Provides upselling tips for restaurant staff

3. **Menu Processing System** (`core/menu_processor.py`)
   - Extracts dishes from multiple file formats (PDF, TXT, JPG, PNG, XLSX, CSV)
   - Processes complete restaurant menus
   - Extracts wine information from menu files
   - Creates comprehensive menu flavor profiles

4. **Wine Management** (`core/wine_manager.py`)
   - Loads wines from multiple sources (JSON, CSV, PDF, XLSX)
   - Enriches wines with flavor compounds using AI
   - Normalizes wine data formats
   - Manages wine knowledge base

5. **Pairing Engine** (`core/pairing_engine.py`)
   - Pairs wines to individual dishes based on molecular flavor matching
   - Uses shared compound analysis
   - Supports batch pairing for entire menus
   - Configurable pairing parameters

6. **Wine Similarity Analysis** (`core/wine_similarity.py`)
   - Identifies similar wines based on flavor compounds and attributes
   - Helps with wine selection and substitution recommendations
   - Configurable similarity thresholds

7. **Wine Ranking System** (`core/wine_ranker.py`)
   - Ranks wines by match count and quality
   - Considers pairing frequency across menu
   - Provides prioritized wine recommendations for inventory management

8. **Report Generation** (`core/report_generator.py`)
   - Generates comprehensive reports in multiple formats (dict, JSON, text)
   - Includes wine rankings, pairings, similarity analysis
   - Exportable reports for restaurant management

9. **Batch Menu Profiler** (`batch_profiler.py`)
   - Processes multiple restaurant recipes in batch
   - Creates molecular flavor profiles for entire menus
   - Efficient batch processing with progress tracking

## Current Functionality

### Individual Dish Pairing
- **Input**: Dish description (text) or dish image
- **Output**: 
  - Top 3 wine recommendations with IDs
  - Scientific reasoning (molecular compound analysis)
  - Culinary reasoning (human-friendly explanation)
  - Upsell tips for restaurant staff

### Full Menu Analysis
- **Input**: Menu files (PDF, TXT, JPG, PNG, XLSX, CSV) or existing menu profile
- **Output**:
  - Complete menu flavor profile
  - Wine-dish pairings for all dishes
  - Wine rankings by match quality
  - Similar wine analysis
  - Comprehensive reports

### Web Interface
- Modern, responsive web UI built with vanilla HTML/CSS/JavaScript
- User authentication system
- Menu file upload and processing
- Wine management interface
- Interactive report generation and viewing
- PDF export functionality
- Past reports management

### API
- FastAPI-based REST API
- Serverless deployment support (Vercel)
- File upload endpoints
- Menu processing endpoints
- Wine pairing endpoints
- Report generation endpoints

## Key Features

- **Molecular Science**: Uses FlavorGraph chemical compound data for scientific pairing
- **Efficient**: Two-stage approach minimizes API token usage (~95% reduction)
- **Robust**: JSON repair logic handles malformed AI responses
- **Flexible**: Supports both text and image inputs
- **Multi-format Support**: Processes menus from PDF, TXT, images, Excel, CSV
- **Scalable**: Batch processing capabilities for large menus
- **Production-Ready**: Web UI and API for real-world deployment
- **Comprehensive Analysis**: Wine similarity, ranking, and detailed reporting

## Project Structure

```
.
├── api/                    # Serverless API entrypoint
├── core/                   # Core business logic modules
│   ├── menu_processor.py   # Menu extraction and processing
│   ├── wine_manager.py     # Wine loading and enrichment
│   ├── pairing_engine.py   # Wine-dish pairing logic
│   ├── wine_similarity.py  # Similarity analysis
│   ├── wine_ranker.py      # Wine ranking system
│   ├── report_generator.py # Report generation
│   └── wine_sommelier_wrapper.py  # Individual dish pairing wrapper
├── web_ui/                 # Web interface
│   ├── *.html              # UI pages
│   ├── css/                # Stylesheets
│   ├── js/                 # Frontend JavaScript
│   └── server.py           # FastAPI backend
├── utils/                  # Utility modules
│   ├── config.py           # Configuration
│   └── file_parsers.py     # File parsing utilities
├── Datasets/               # Raw data files
├── processed_data/         # Processed knowledge bases
├── app.py                  # Main application orchestrator
├── processing.py           # Data processing pipeline
├── wine_sommelier.py       # Individual dish pairing
├── batch_profiler.py       # Batch menu profiling
└── requirements.txt        # Python dependencies
```

## Quick Start

### Prerequisites
- Python 3.8+
- Google AI API key (for Gemini models)

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set API key:**
   ```bash
   export GOOGLE_AI_API_KEY='your-api-key'
   # Or create .env file with: GOOGLE_AI_API_KEY=your-api-key
   ```

3. **Process datasets (if not already done):**
   ```bash
   python processing.py
   ```

### Usage Examples

**Individual Dish Pairing:**
```bash
python wine_sommelier.py
# Or use the example_usage.py script
python example_usage.py
```

**Full Menu Analysis:**
```bash
python app.py
# Follow the CLI prompts to process menus and generate reports
```

**Web Interface:**
```bash
cd web_ui
python server.py
# Navigate to http://localhost:8000
```

**Batch Menu Profiling:**
```bash
python batch_profiler.py
```

## Progress Summary

### Completed Features
- Data processing pipeline for wine and ingredient databases
- Individual dish wine pairing with scientific reasoning
- Multi-format menu file processing (PDF, images, Excel, CSV, TXT)
- Complete menu analysis workflow
- Wine similarity analysis
- Wine ranking system
- Comprehensive report generation
- Web user interface with authentication
- REST API with FastAPI
- Batch processing capabilities
- Wine extraction from menu files
- Serverless deployment configuration

### Technical Achievements
- Processed 1,007 wines with normalized attributes
- Mapped 419 ingredients to flavor compounds
- Implemented efficient two-stage pairing to reduce API costs by ~95%
- Built robust error handling and JSON repair logic
- Created modular, extensible architecture
- Developed production-ready web interface
- Implemented comprehensive reporting system

## Sample Results

The system has been tested with various dishes demonstrating different pairing scenarios:
- **Seafood dishes** (e.g., salmon with lemon & herbs) → High acidity wines, white wines
- **Rich meat dishes** (e.g., Veal Saltimbocca) → Full-bodied red wines, buttery whites
- Each recommendation includes detailed scientific analysis of shared flavor compounds, culinary explanations, and upselling tips

## Configuration

Key configuration options are available in `utils/config.py`:
- Maximum wines per dish pairing
- Similarity thresholds
- Default menu profile paths
- API model selection

## Dependencies

- `google-genai` - Google AI API client
- `pandas` - Data processing
- `fastapi` - Web API framework
- `uvicorn` - ASGI server
- `Pillow` - Image processing
- `pdfplumber` - PDF parsing
- `openpyxl` - Excel file support
- `python-dotenv` - Environment variable management


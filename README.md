# AI Culinary Expert - Wine Pairing System

A molecular gastronomy-based wine pairing AI that uses Gemini 3 Flash to recommend wines based on shared flavor compounds between dishes and wines.

## Architecture

The system operates in two main stages:

### 1. Data Processing (`processing.py`)
- **Input**: Raw CSV datasets (XWines, FlavorGraph)
- **Process**: 
  - Normalizes wine attributes (type, body, acidity) to 1-5 scales
  - Maps ingredients to chemical flavor compounds via FlavorGraph
  - Creates molecular "flavor bridge" connecting wines to compounds through grape varieties
- **Output**: Two JSON knowledge bases:
  - `processed_wines.json` - 1,007 wines with normalized attributes and flavor compounds
  - `ingredient_flavor_map.json` - 419 ingredients mapped to their chemical compounds

### 2. Wine Recommendation (`wine_sommelier.py`)
- **Stage 1**: Gemini identifies key ingredients from dish description/image
- **Stage 2**: Python-based molecular search finds candidate wines with shared compounds
- **Stage 3**: Gemini selects top 3 wines and generates scientific/culinary reasoning

## Current Functionality

- **Input**: Dish description (text) or dish image
- **Output**: 
  - Top 3 wine recommendations with IDs
  - Scientific reasoning (molecular compound analysis)
  - Culinary reasoning (human-friendly explanation)
  - Upsell tips for restaurant staff

## Sample Runs
2 runs with different sample dishes (Salomon dish, with lemon & herbs -> High acidity / seafood) (Veal Saltimbocca -> salty, buttery, red meat) provide different wine selections
with detailed scientific, culinary and upselling explanations.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set API key:
   ```bash
   export GOOGLE_AI_API_KEY='your-api-key'
   # Or create .env file with: GOOGLE_AI_API_KEY=your-api-key
   ```

3. Process datasets (if not already done):
   ```bash
   python processing.py
   ```

4. Run example:
   ```bash
   python example_usage.py
   ```

## Key Features

- **Molecular Science**: Uses FlavorGraph chemical compound data for scientific pairing
- **Efficient**: Two-stage approach minimizes API token usage (~95% reduction)
- **Robust**: JSON repair logic handles malformed Gemini responses
- **Flexible**: Supports both text and image inputs

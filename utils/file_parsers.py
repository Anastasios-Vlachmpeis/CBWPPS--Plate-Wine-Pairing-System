"""
File parsing utilities for wine lists and other data files
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional


def detect_file_type(file_path: str) -> str:
    """
    Detect file type from extension
    
    Args:
        file_path: Path to file
        
    Returns:
        File type: 'csv', 'json', 'xlsx', 'pdf', or 'unknown'
    """
    path = Path(file_path)
    ext = path.suffix.lower()
    
    if ext == '.csv':
        return 'csv'
    elif ext == '.json':
        return 'json'
    elif ext in ['.xlsx', '.xls']:
        return 'xlsx'
    elif ext == '.pdf':
        return 'pdf'
    else:
        return 'unknown'


def parse_json_wine_list(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse JSON wine list file
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        List of wine dictionaries
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Wine list file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle different JSON structures
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        # Check if wines are in a 'wines' key
        if 'wines' in data:
            return data['wines']
        # Check if it's a dict mapping wine_id to wine data
        elif all(isinstance(k, (int, str)) and isinstance(v, dict) for k, v in data.items()):
            return list(data.values())
        else:
            raise ValueError("Unrecognized JSON structure for wine list")
    else:
        raise ValueError(f"Invalid JSON structure: expected list or dict, got {type(data)}")


def parse_csv_wine_list(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse CSV wine list file
    
    Expected columns (flexible):
    - wine_id, wine_name, type_name, body_name, acidity_name, grapes, country, region, winery, etc.
    
    Args:
        file_path: Path to CSV file
        
    Returns:
        List of wine dictionaries
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Wine list file not found: {file_path}")
    
    wines = []
    
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Normalize keys to lowercase and strip whitespace
            wine = {k.lower().strip(): v.strip() if v else None for k, v in row.items()}
            
            # Try to parse grapes if it's a string representation of a list
            if 'grapes' in wine and wine['grapes']:
                try:
                    import ast
                    grapes = ast.literal_eval(wine['grapes'])
                    if isinstance(grapes, list):
                        wine['grapes'] = grapes
                    elif isinstance(grapes, str):
                        wine['grapes'] = [g.strip() for g in grapes.split(',') if g.strip()]
                except (ValueError, SyntaxError):
                    # If parsing fails, treat as comma-separated string
                    wine['grapes'] = [g.strip() for g in wine['grapes'].split(',') if g.strip()]
            
            # Try to parse wine_id as integer
            if 'wine_id' in wine and wine['wine_id']:
                try:
                    wine['wine_id'] = int(wine['wine_id'])
                except ValueError:
                    pass
            
            wines.append(wine)
    
    return wines


def parse_xlsx_wine_list(file_path: str, sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Parse XLSX/XLS wine list file
    
    Args:
        file_path: Path to Excel file
        sheet_name: Name of sheet to read (None = first sheet)
        
    Returns:
        List of wine dictionaries
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "pandas is required for XLSX parsing. Install it with: pip install pandas openpyxl"
        )
    
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Wine list file not found: {file_path}")
    
    try:
        # Read Excel file
        # Use openpyxl engine for .xlsx files, xlrd for .xls (if available)
        if sheet_name:
            df = pd.read_excel(path, sheet_name=sheet_name, engine='openpyxl')
        else:
            # Read first sheet by default
            df = pd.read_excel(path, sheet_name=0, engine='openpyxl')
        
        # Handle empty DataFrame
        if df.empty:
            return []
        
        # Convert NaN values to None
        df = df.where(pd.notna(df), None)
        
        # Convert to list of dictionaries
        wines = df.to_dict('records')
        
        # Normalize column names and values
        normalized_wines = []
        for wine in wines:
            # Normalize keys to lowercase and strip whitespace
            normalized_wine = {}
            for key, value in wine.items():
                if pd.isna(value):
                    value = None
                elif isinstance(value, (int, float)) and pd.isna(value):
                    value = None
                elif isinstance(value, str):
                    value = value.strip() if value else None
                
                normalized_key = str(key).lower().strip() if key else None
                if normalized_key:
                    normalized_wine[normalized_key] = value
            
            # Try to parse grapes if it's a string representation of a list
            if 'grapes' in normalized_wine and normalized_wine['grapes']:
                try:
                    import ast
                    grapes = ast.literal_eval(str(normalized_wine['grapes']))
                    if isinstance(grapes, list):
                        normalized_wine['grapes'] = grapes
                    elif isinstance(grapes, str):
                        normalized_wine['grapes'] = [g.strip() for g in grapes.split(',') if g.strip()]
                except (ValueError, SyntaxError):
                    # If parsing fails, treat as comma-separated string
                    grapes_str = str(normalized_wine['grapes'])
                    normalized_wine['grapes'] = [g.strip() for g in grapes_str.split(',') if g.strip()]
            
            # Try to parse wine_id as integer
            if 'wine_id' in normalized_wine and normalized_wine['wine_id']:
                try:
                    normalized_wine['wine_id'] = int(float(normalized_wine['wine_id']))
                except (ValueError, TypeError):
                    pass
            
            normalized_wines.append(normalized_wine)
        
        return normalized_wines
    
    except ImportError as e:
        raise ImportError(
            f"openpyxl is required for XLSX parsing. Install it with: pip install openpyxl"
        ) from e
    except Exception as e:
        raise ValueError(f"Failed to parse XLSX file {file_path}: {e}") from e


def parse_pdf_wine_list(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse PDF wine list file
    
    Attempts to extract tables from PDF first (most supplier lists are in table format).
    Falls back to text extraction if no tables are found.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        List of wine dictionaries
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError(
            "pdfplumber is required for PDF parsing. Install it with: pip install pdfplumber"
        )
    
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Wine list file not found: {file_path}")
    
    wines = []
    
    # #region agent log
    import json as json_module
    log_path = Path(".cursor/debug.log")
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json_module.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"file_parsers.py:235","message":"Starting PDF wine parsing","data":{"file_path":file_path},"timestamp":int(__import__('time').time()*1000)}) + "\n")
    except: pass
    # #endregion
    
    try:
        with pdfplumber.open(path) as pdf:
            all_tables = []
            
            # Extract tables from all pages
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    all_tables.extend(tables)
            
            # #region agent log
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json_module.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"file_parsers.py:245","message":"Tables extracted from PDF","data":{"table_count":len(all_tables),"table_sizes":[len(t) for t in all_tables]},"timestamp":int(__import__('time').time()*1000)}) + "\n")
            except: pass
            # #endregion
            
            if all_tables:
                # Find the largest table (likely the wine list)
                largest_table = max(all_tables, key=len)
                
                if len(largest_table) < 2:
                    # Table has no data rows, try text extraction
                    return _parse_pdf_text(pdf)
                
                # Use first row as headers
                headers = [str(cell).lower().strip() if cell else "" for cell in largest_table[0]]
                
                # Parse data rows
                for row in largest_table[1:]:
                    if not row or all(not cell or str(cell).strip() == "" for cell in row):
                        continue  # Skip empty rows
                    
                    wine = {}
                    for i, header in enumerate(headers):
                        if i < len(row):
                            value = row[i]
                            if value is not None:
                                value = str(value).strip()
                                if value:
                                    wine[header] = value
                    
                    if wine:  # Only add non-empty wines
                        wines.append(wine)
            
            # #region agent log
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json_module.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"file_parsers.py:273","message":"Wines from table extraction","data":{"wine_count":len(wines)},"timestamp":int(__import__('time').time()*1000)}) + "\n")
            except: pass
            # #endregion
            
            else:
                # No tables found, try text extraction
                # #region agent log
                try:
                    with open(log_path, 'a', encoding='utf-8') as f:
                        f.write(json_module.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"file_parsers.py:277","message":"No tables found, trying text extraction","data":{},"timestamp":int(__import__('time').time()*1000)}) + "\n")
                except: pass
                # #endregion
                wines = _parse_pdf_text(pdf)
                # #region agent log
                try:
                    with open(log_path, 'a', encoding='utf-8') as f:
                        f.write(json_module.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"file_parsers.py:280","message":"Wines from text extraction","data":{"wine_count":len(wines)},"timestamp":int(__import__('time').time()*1000)}) + "\n")
                except: pass
                # #endregion
    
    except ImportError as e:
        raise ImportError(
            f"pdfplumber is required for PDF parsing. Install it with: pip install pdfplumber"
        ) from e
    except Exception as e:
        raise ValueError(f"Failed to parse PDF file {file_path}: {e}") from e
    
    return wines


def _parse_pdf_text(pdf) -> List[Dict[str, Any]]:
    """
    Fallback method to parse PDF text when no tables are found
    
    Args:
        pdf: pdfplumber PDF object
        
    Returns:
        List of wine dictionaries
    """
    wines = []
    import re
    
    # Extract text from all pages
    full_text = ""
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"
    
    if not full_text.strip():
        return wines
    
    # Simple line-by-line parsing
    # Look for lines that might contain wine information
    lines = full_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 5:
            continue
        
        # More conservative wine detection - look for patterns that indicate wines
        # Skip if line is too short, is a number, or looks like formatting
        line_clean = line.strip()
        
        # Skip obvious non-wines
        if len(line_clean) < 3:
            return
        if line_clean.lower() in ["menu", "wine", "list", "page", "price", "total", "header", "footer"]:
            return
        if line_clean.replace(" ", "").replace("-", "").isdigit():
            return
        
        # Look for wine-like patterns (contains wine-related keywords or structure)
        wine_keywords = ["wine", "château", "domaine", "vineyard", "estate", "reserve", "cuvée", 
                        "pinot", "chardonnay", "cabernet", "merlot", "sauvignon", "riesling",
                        "bordeaux", "burgundy", "champagne", "prosecco", "rioja", "barolo"]
        
        line_lower = line_clean.lower()
        has_wine_keyword = any(keyword in line_lower for keyword in wine_keywords)
        
        # Also check for price patterns (wines often have prices)
        has_price = bool(re.search(r'[\$€£]\s*\d+|\d+\s*[\$€£]', line_clean))
        
        # Only create wine entry if it looks like a wine
        if has_wine_keyword or (len(line_clean.split()) >= 2 and has_price):
            parts = [p.strip() for p in re.split(r'[\s\t]+', line_clean) if p.strip()]
            
            if len(parts) >= 2:
                wine = {
                    "wine_name": parts[0] if parts else "Unknown",
                    "raw_text": line_clean
                }
                
                # Try to extract type from context
                if len(parts) > 1:
                    wine["type_name"] = parts[1] if len(parts) > 1 else "Unknown"
                
                wines.append(wine)
    
    return wines


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract all text from PDF file
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Extracted text content
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError(
            "pdfplumber is required for PDF text extraction. Install it with: pip install pdfplumber"
        )
    
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    full_text = ""
    
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF {pdf_path}: {e}") from e
    
    return full_text


def extract_images_from_pdf(pdf_path: str) -> List[bytes]:
    """
    Extract images from PDF file (for OCR if needed)
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        List of image bytes
    """
    try:
        import pdfplumber
        from PIL import Image
        import io
    except ImportError:
        raise ImportError(
            "pdfplumber and Pillow are required for PDF image extraction. "
            "Install with: pip install pdfplumber Pillow"
        )
    
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    images = []
    
    try:
        with pdfplumber.open(path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract images from page
                page_images = page.images
                for img in page_images:
                    # Try to extract image data
                    # Note: pdfplumber's image extraction is limited
                    # This is a basic implementation
                    pass  # Image extraction from PDF is complex, may need different library
    except Exception as e:
        # If image extraction fails, return empty list
        # Text extraction is more reliable
        pass
    
    return images


def read_excel_content(excel_path: str) -> str:
    """
    Convert Excel file content to text representation for Gemini
    
    Args:
        excel_path: Path to Excel file
        
    Returns:
        Text representation of Excel content
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "pandas is required for Excel reading. Install it with: pip install pandas openpyxl"
        )
    
    path = Path(excel_path)
    if not path.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_path}")
    
    try:
        # Read all sheets
        excel_file = pd.ExcelFile(path, engine='openpyxl')
        text_parts = []
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name, engine='openpyxl')
            
            # Convert DataFrame to text representation
            text_parts.append(f"Sheet: {sheet_name}\n")
            text_parts.append(df.to_string(index=False))
            text_parts.append("\n\n")
        
        return "\n".join(text_parts)
    
    except Exception as e:
        raise ValueError(f"Failed to read Excel file {excel_path}: {e}") from e


def read_csv_content(csv_path: str) -> str:
    """
    Convert CSV file content to text representation for Gemini
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        Text representation of CSV content
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    try:
        import pandas as pd
        
        # Read CSV
        df = pd.read_csv(path)
        
        # Convert to text representation
        return df.to_string(index=False)
    
    except Exception as e:
        # Fallback: read as plain text
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e2:
            raise ValueError(f"Failed to read CSV file {csv_path}: {e}") from e2

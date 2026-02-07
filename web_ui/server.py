"""
FastAPI server for AI Culinary Expert Web UI
Provides API endpoints for menu processing, wine pairing, and report generation
"""

import os
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import sys
import os

# Add parent directory to path to import app modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Change working directory to project root so relative paths work
os.chdir(project_root)

from app import CulinaryExpertApp

# Initialize FastAPI app
app = FastAPI(title="AI Culinary Expert API")

# CORS configuration for localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (HTML, CSS, JS)
static_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Serve CSS, JS, and assets from root paths (for HTML compatibility)
@app.get("/css/{file_path:path}")
async def serve_css(file_path: str):
    """Serve CSS files"""
    css_file = static_dir / "css" / file_path
    if css_file.exists() and css_file.suffix == '.css':
        return FileResponse(css_file, media_type="text/css")
    raise HTTPException(status_code=404, detail="CSS file not found")

@app.get("/js/{file_path:path}")
async def serve_js(file_path: str):
    """Serve JavaScript files"""
    js_file = static_dir / "js" / file_path
    if js_file.exists() and js_file.suffix == '.js':
        return FileResponse(js_file, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="JavaScript file not found")

@app.get("/assets/{file_path:path}")
async def serve_assets(file_path: str):
    """Serve asset files (images, etc.)"""
    asset_file = static_dir / "assets" / file_path
    if asset_file.exists():
        # Determine media type based on extension
        media_type = "image/png" if asset_file.suffix == '.png' else "image/jpeg" if asset_file.suffix in ['.jpg', '.jpeg'] else "application/octet-stream"
        return FileResponse(asset_file, media_type=media_type)
    raise HTTPException(status_code=404, detail="Asset file not found")

# Global app instance (could be improved with dependency injection)
culinary_app = None

def get_app():
    """Get or create CulinaryExpertApp instance"""
    global culinary_app
    if culinary_app is None:
        culinary_app = CulinaryExpertApp()
    return culinary_app

# File validation constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.jpg', '.jpeg', '.png', '.xlsx', '.csv', '.json'}

def validate_file(file: UploadFile) -> Dict[str, Any]:
    """
    Validate uploaded file
    
    Returns:
        Dict with 'valid' (bool) and 'error' (str if invalid)
    """
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return {
            'valid': False,
            'error': f'File type {file_ext} not supported. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
        }
    
    # Note: File size check would need to read the file
    # We'll do a basic check here, but full validation happens after upload
    return {'valid': True, 'error': None}

@app.get("/")
async def root():
    """Serve index.html"""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "AI Culinary Expert API"}

@app.post("/api/login")
async def login(username: str = Form(...), password: str = Form(...)):
    """Mock authentication endpoint"""
    # Simple mock authentication (always succeeds)
    return {
        "success": True,
        "user": {
            "username": username,
            "token": "mock_token_" + username
        }
    }

@app.post("/api/register")
async def register(username: str = Form(...), password: str = Form(...), confirm_password: str = Form(...)):
    """Mock registration endpoint"""
    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    return {
        "success": True,
        "user": {
            "username": username,
            "token": "mock_token_" + username
        }
    }

@app.post("/api/process-menu")
async def process_menu(files: List[UploadFile] = File(...)):
    """
    Process menu files and extract dishes and wines
    
    Returns:
        Dict with menu_profile, extracted_wines, has_wines, and progress info
    """
    try:
        app_instance = get_app()
        
        # Validate files
        validated_files = []
        for file in files:
            validation = validate_file(file)
            if not validation['valid']:
                raise HTTPException(status_code=400, detail=validation['error'])
            validated_files.append(file)
        
        if not validated_files:
            raise HTTPException(status_code=400, detail="No valid files provided")
        
        # Save uploaded files temporarily
        temp_files = []
        try:
            for file in validated_files:
                # Check file size
                content = await file.read()
                if len(content) > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File {file.filename} exceeds maximum size of 10MB"
                    )
                
                # Save to temp file
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=Path(file.filename).suffix
                )
                temp_file.write(content)
                temp_file.close()
                temp_files.append(temp_file.name)
            
            # Process menu files
            menu_result = app_instance.process_menu(
                menu_files=temp_files,
                extract_wines=True
            )
            
            return {
                "success": True,
                "menu_profile": menu_result.get("menu_profile", {}),
                "extracted_wines": menu_result.get("extracted_wines", []),
                "has_wines": menu_result.get("has_wines", False),
                "dish_count": len(menu_result.get("menu_profile", {})),
                "wine_count": len(menu_result.get("extracted_wines", []))
            }
        
        finally:
            # Clean up temp files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing menu files: {str(e)}"
        )

@app.post("/api/process-wines")
async def process_wines(
    wine_files: Optional[List[UploadFile]] = File(None),
    use_detected_wines: bool = Form(False),
    use_knowledge_base: bool = Form(False),
    detected_wines: Optional[str] = Form(None)  # JSON string of detected wines
):
    """
    Process wine files and enrich with flavors
    
    Args:
        wine_files: Optional list of wine file uploads
        use_detected_wines: Whether to use wines detected in menu
        use_knowledge_base: Whether to use internal knowledge base
        detected_wines: JSON string of wines detected in menu files
    """
    try:
        app_instance = get_app()
        
        wine_sources = []
        
        # Add detected wines if requested
        if use_detected_wines and detected_wines:
            try:
                detected = json.loads(detected_wines)
                if isinstance(detected, list):
                    wine_sources.extend(detected)
            except json.JSONDecodeError:
                pass
        
        # Add uploaded wine files
        if wine_files:
            temp_files = []
            try:
                for file in wine_files:
                    validation = validate_file(file)
                    if not validation['valid']:
                        raise HTTPException(status_code=400, detail=validation['error'])
                    
                    content = await file.read()
                    if len(content) > MAX_FILE_SIZE:
                        raise HTTPException(
                            status_code=400,
                            detail=f"File {file.filename} exceeds maximum size of 10MB"
                        )
                    
                    temp_file = tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=Path(file.filename).suffix
                    )
                    temp_file.write(content)
                    temp_file.close()
                    temp_files.append(temp_file.name)
                
                # Load wines from files
                wines_from_files = app_instance.wine_manager.load_wines(temp_files)
                wine_sources.extend(wines_from_files)
            
            finally:
                for temp_file in temp_files:
                    try:
                        os.unlink(temp_file)
                    except:
                        pass
        
        # Add knowledge base wines if requested
        if use_knowledge_base:
            try:
                # Load from internal processed_wines.json
                from utils.config import DEFAULT_WINES_PATH
                wines_path = Path(DEFAULT_WINES_PATH)
                if wines_path.exists():
                    with open(wines_path, 'r', encoding='utf-8') as f:
                        kb_wines = json.load(f)
                    # Normalize wines
                    kb_wines = [app_instance.wine_manager.normalize_wine_format(w) for w in kb_wines]
                    wine_sources.extend(kb_wines)
            except Exception as e:
                # Knowledge base might not be available, continue without it
                pass
        
        if not wine_sources:
            raise HTTPException(
                status_code=400,
                detail="No wine sources selected. Please select at least one wine source."
            )
        
        # Enrich wines with flavors
        enriched_wines = app_instance.wine_manager.enrich_wines_with_flavors(wine_sources)
        
        # Store in app instance
        app_instance.wines = enriched_wines
        
        return {
            "success": True,
            "wines": enriched_wines,
            "wine_count": len(enriched_wines)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing wines: {str(e)}"
        )

@app.post("/api/analyze-similarity")
async def analyze_similarity(threshold: Optional[float] = Form(None)):
    """Analyze wine similarity"""
    try:
        app_instance = get_app()
        
        if not app_instance.wines:
            raise HTTPException(status_code=400, detail="No wines loaded. Please process wines first.")
        
        similar_pairs = app_instance.analyze_wine_similarity(threshold=threshold)
        
        return {
            "success": True,
            "similar_pairs": [
                {
                    "wine_id1": pair[0],
                    "wine_id2": pair[1],
                    "similarity": pair[2]
                }
                for pair in similar_pairs
            ],
            "pair_count": len(similar_pairs)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing similarity: {str(e)}"
        )

@app.post("/api/pair-wines")
async def pair_wines():
    """Pair wines to dishes"""
    try:
        app_instance = get_app()
        
        if not app_instance.menu_profile:
            raise HTTPException(status_code=400, detail="No menu profile loaded. Please process menu first.")
        
        if not app_instance.wines:
            raise HTTPException(status_code=400, detail="No wines loaded. Please process wines first.")
        
        pairings = app_instance.pair_wines_to_dishes()
        
        return {
            "success": True,
            "pairings": pairings,
            "paired_dishes": sum(1 for wine_ids in pairings.values() if wine_ids),
            "total_dishes": len(pairings)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error pairing wines: {str(e)}"
        )

@app.post("/api/rank-wines")
async def rank_wines():
    """Rank wines by match count and quality"""
    try:
        app_instance = get_app()
        
        if not app_instance.pairings:
            raise HTTPException(status_code=400, detail="No pairings found. Please pair wines first.")
        
        rankings = app_instance.rank_wines()
        
        return {
            "success": True,
            "rankings": [
                {
                    "wine_id": rank[0],
                    "score": rank[1],
                    "wine": rank[2]
                }
                for rank in rankings
            ],
            "rank_count": len(rankings)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error ranking wines: {str(e)}"
        )

@app.post("/api/generate-report")
async def generate_report(format: str = Form("dict")):
    """Generate comprehensive report"""
    try:
        app_instance = get_app()
        
        if not app_instance.pairings:
            raise HTTPException(status_code=400, detail="No pairings found. Please complete pairing first.")
        
        report = app_instance.generate_reports(format=format)
        
        return {
            "success": True,
            "report": report
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating report: {str(e)}"
        )

# Serve HTML files directly (must be last route to catch all unmatched paths)
@app.get("/{path:path}")
async def serve_static(path: str):
    """Serve static HTML files"""
    file_path = static_dir / path
    if file_path.exists() and file_path.suffix == '.html':
        return FileResponse(file_path)
    elif path == "" or path == "/":
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print("AI Culinary Expert - Web Server")
    print("=" * 60)
    print(f"Server starting on http://localhost:8000")
    print(f"Access the application at: http://localhost:8000")
    print("=" * 60 + "\n")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

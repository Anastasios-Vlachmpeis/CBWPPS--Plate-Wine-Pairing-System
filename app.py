"""
AI Culinary Expert - Main Application Orchestrator
Implements the complete workflow from menu processing to report generation
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from core.menu_processor import MenuProcessor
from core.wine_manager import WineManager
from core.wine_similarity import WineSimilarityAnalyzer
from core.pairing_engine import PairingEngine
from core.wine_ranker import WineRanker
from core.report_generator import ReportGenerator
from utils.config import DEFAULT_MENU_PROFILE_PATH


class CulinaryExpertApp:
    """
    Main application orchestrator that implements the simplified workflow
    """
    
    def __init__(self):
        """Initialize all core modules"""
        print("Initializing AI Culinary Expert...")
        self.menu_processor = MenuProcessor()
        self.wine_manager = WineManager()
        self.similarity_analyzer = WineSimilarityAnalyzer()
        self.pairing_engine = PairingEngine()
        self.wine_ranker = WineRanker()
        self.report_generator = ReportGenerator()
        
        # State tracking
        self.menu_profile = None
        self.wines = []
        self.similar_pairs = []
        self.pairings = {}
        self.wine_rankings = []
        self.reports = {}
    
    def process_menu(
        self, 
        menu_files: Optional[List[str]] = None,
        menu_profile_path: Optional[str] = None,
        extract_wines: bool = True
    ) -> Dict[str, Any]:
        """
        Process menu files (any format) or load existing menu profile
        
        Args:
            menu_files: List of paths to menu files (txt, pdf, jpg, png, xlsx, csv)
            menu_profile_path: Path to existing menu profile JSON
            extract_wines: Whether to extract wines from files (default: True)
            
        Returns:
            Dictionary with:
            - 'menu_profile': Menu profile dictionary
            - 'has_wines': Boolean indicating if wines were found
            - 'extracted_wines': List of extracted wines (if any)
        """
        print("\n" + "=" * 70)
        print("STEP 1: MENU PROCESSING")
        print("=" * 70)
        
        extracted_wines = []
        has_wines = False
        
        if menu_profile_path:
            print(f"Loading menu profile from: {menu_profile_path}")
            self.menu_profile = self.menu_processor.load_menu_profile(
                Path(menu_profile_path)
            )
        elif menu_files:
            print(f"Processing {len(menu_files)} menu files...")
            result = self.menu_processor.process_files(menu_files, extract_wines=extract_wines)
            self.menu_profile = result.get("menu_profile", {})
            extracted_wines = result.get("wines", [])
            has_wines = result.get("has_wines", False)
            
            print(f"✓ Processed {len(self.menu_profile)} dishes")
            if has_wines:
                print(f"✓ Found {len(extracted_wines)} wines in menu files")
        else:
            # Try to load default menu profile
            print("No menu provided, loading default menu profile...")
            try:
                self.menu_profile = self.menu_processor.load_menu_profile()
            except FileNotFoundError:
                raise ValueError(
                    "No menu files or profile path provided, and default menu profile not found."
                )
        
        print(f"✓ Menu profile loaded: {len(self.menu_profile)} dishes")
        
        # Store extracted wines for later use
        self.extracted_wines = extracted_wines
        
        return {
            "menu_profile": self.menu_profile,
            "has_wines": has_wines,
            "extracted_wines": extracted_wines
        }
    
    def load_wines(
        self,
        wine_files: Optional[List[str]] = None,
        extracted_wines: Optional[List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Load wines from files or use extracted wines
        
        Args:
            wine_files: List of paths to wine files (JSON, CSV, PDF, XLSX)
            extracted_wines: List of wines extracted from menu files
            
        Returns:
            List of wine dictionaries enriched with flavor compounds
        """
        print("\n" + "=" * 70)
        print("STEP 2: WINE LOADING & ENRICHMENT")
        print("=" * 70)
        
        if extracted_wines:
            print(f"Using {len(extracted_wines)} wines extracted from menu files")
            self.wines = [self.wine_manager.normalize_wine_format(w) for w in extracted_wines]
        elif wine_files:
            print(f"Loading wines from {len(wine_files)} file(s)...")
            self.wines = self.wine_manager.load_wines(wine_files)
        else:
            raise ValueError("Either wine_files or extracted_wines must be provided")
        
        print(f"✓ Loaded {len(self.wines)} wines")
        
        # Enrich wines with flavor compounds via Gemini
        print("Enriching wines with flavor compounds...")
        self.wines = self.wine_manager.enrich_wines_with_flavors(self.wines)
        print(f"✓ Enriched {len(self.wines)} wines with flavor compounds")
        
        return self.wines
    
    def analyze_wine_similarity(
        self,
        wines: Optional[List[Dict[str, Any]]] = None,
        threshold: Optional[float] = None
    ) -> List[tuple]:
        """
        Analyze wines for similarity
        
        Args:
            wines: List of wine dictionaries (uses self.wines if None)
            threshold: Similarity threshold (uses default if None)
            
        Returns:
            List of (wine_id1, wine_id2, similarity_score) tuples
        """
        if wines is None:
            wines = self.wines
        
        if not wines:
            return []
        
        print("\n" + "=" * 70)
        print("STEP 3: WINE SIMILARITY ANALYSIS")
        print("=" * 70)
        
        self.similar_pairs = self.similarity_analyzer.find_similar_pairs(wines, threshold)
        
        print(f"✓ Found {len(self.similar_pairs)} similar wine pairs")
        if self.similar_pairs:
            print(f"  Top similarity: {self.similar_pairs[0][2]:.2f}")
        
        return self.similar_pairs
    
    def pair_wines_to_dishes(
        self,
        wines: Optional[List[Dict[str, Any]]] = None,
        menu_profile: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, List[int]]:
        """
        Pair wines to individual dishes
        
        Args:
            wines: List of wine dictionaries (uses self.wines if None)
            menu_profile: Menu profile dictionary (uses self.menu_profile if None)
            
        Returns:
            Dictionary mapping dish_id -> list of wine_ids
        """
        print("\n" + "=" * 70)
        print("STEP 4: WINE-DISH PAIRING")
        print("=" * 70)
        
        if wines is None:
            wines = self.wines
        if menu_profile is None:
            menu_profile = self.menu_profile
        
        if not wines or not menu_profile:
            raise ValueError("Wines and menu_profile are required")
        
        # Pair wines to dishes
        self.pairings = self.pairing_engine.pair_wines_to_dishes(
            dishes=menu_profile,
            wines=wines,
            menu_profile=menu_profile
        )
        
        # Count pairings
        paired_count = sum(1 for wine_ids in self.pairings.values() if wine_ids)
        total_dishes = len(self.pairings)
        pairing_rate = paired_count / total_dishes if total_dishes > 0 else 0.0
        
        print(f"✓ Paired wines to {paired_count} / {total_dishes} dishes")
        print(f"✓ Pairing rate: {pairing_rate:.1%}")
        
        return self.pairings
    
    def rank_wines(
        self,
        pairings: Optional[Dict[str, List[int]]] = None,
        wines: Optional[List[Dict[str, Any]]] = None,
        menu_profile: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> List[tuple]:
        """
        Rank wines by match count and quality
        
        Args:
            pairings: Dictionary mapping dish_id -> list of wine_ids
            wines: List of wine dictionaries
            menu_profile: Menu profile dictionary
            
        Returns:
            List of (wine_id, score, wine_dict) tuples, sorted by score
        """
        print("\n" + "=" * 70)
        print("STEP 5: WINE RANKING")
        print("=" * 70)
        
        if pairings is None:
            pairings = self.pairings
        if wines is None:
            wines = self.wines
        if menu_profile is None:
            menu_profile = self.menu_profile
        
        # Rank wines
        self.wine_rankings = self.wine_ranker.rank_wines(
            wines=wines,
            pairings=pairings,
            menu_profile=menu_profile,
            pairing_engine=self.pairing_engine
        )
        
        print(f"✓ Ranked {len(self.wine_rankings)} wines")
        
        return self.wine_rankings
    
    def generate_reports(
        self,
        pairings: Optional[Dict[str, List[int]]] = None,
        wines: Optional[List[Dict[str, Any]]] = None,
        similar_pairs: Optional[List[tuple]] = None,
        wine_rankings: Optional[List[tuple]] = None,
        menu_profile: Optional[Dict[str, Dict[str, Any]]] = None,
        format: str = "dict"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive reports
        
        Args:
            pairings: Dictionary mapping dish_id -> list of wine_ids
            wines: List of wine dictionaries
            similar_pairs: List of similar wine pairs
            wine_rankings: List of (wine_id, score, wine_dict) tuples
            menu_profile: Menu profile dictionary
            format: Output format ('dict', 'json', 'text')
            
        Returns:
            Comprehensive report
        """
        print("\n" + "=" * 70)
        print("STEP 6: REPORT GENERATION")
        print("=" * 70)
        
        if pairings is None:
            pairings = self.pairings
        if wines is None:
            wines = self.wines
        if similar_pairs is None:
            similar_pairs = self.similar_pairs
        if wine_rankings is None:
            wine_rankings = self.wine_rankings
        if menu_profile is None:
            menu_profile = self.menu_profile
        
        # Generate comprehensive report
        self.reports = self.report_generator.generate_comprehensive_report(
            pairings=pairings,
            wines=wines,
            similar_pairs=similar_pairs,
            menu_profile=menu_profile,
            wine_rankings=wine_rankings,
            pairing_engine=self.pairing_engine,
            format=format
        )
        
        print("✓ Generated comprehensive report")
        
        return self.reports
    
    def run_full_workflow(
        self,
        menu_files: Optional[List[str]] = None,
        menu_profile_path: Optional[str] = None,
        wine_files: Optional[List[str]] = None,
        analyze_similarity: bool = True,
        output_format: str = "dict"
    ) -> Dict[str, Any]:
        """
        Execute simplified workflow
        
        Args:
            menu_files: List of menu file paths (any format)
            menu_profile_path: Path to existing menu profile
            wine_files: List of wine file paths (JSON, CSV, PDF, XLSX)
            analyze_similarity: Whether to analyze wine similarity
            output_format: Report format ('dict', 'json', 'text')
            
        Returns:
            Complete workflow results dictionary
        """
        print("\n" + "=" * 70)
        print("AI CULINARY EXPERT - WORKFLOW")
        print("=" * 70)
        
        try:
            # Step 1: Process menu files
            menu_result = self.process_menu(menu_files, menu_profile_path, extract_wines=True)
            extracted_wines = menu_result.get("extracted_wines", [])
            
            # Step 2: Load wines (from files or extracted from menu)
            if extracted_wines:
                self.load_wines(extracted_wines=extracted_wines)
            elif wine_files:
                self.load_wines(wine_files=wine_files)
            else:
                raise ValueError("Either wine_files must be provided or wines must be found in menu files")
            
            # Step 3: Analyze wine similarity
            if analyze_similarity:
                self.analyze_wine_similarity()
            
            # Step 4: Pair wines to dishes
            self.pair_wines_to_dishes()
            
            # Step 5: Rank wines
            self.rank_wines()
            
            # Step 6: Generate reports
            self.generate_reports(format=output_format)
            
            print("\n" + "=" * 70)
            print("✓ WORKFLOW COMPLETE")
            print("=" * 70)
            
            return {
                "success": True,
                "menu_profile": self.menu_profile,
                "wines": self.wines,
                "similar_pairs": self.similar_pairs,
                "pairings": self.pairings,
                "wine_rankings": self.wine_rankings,
                "reports": self.reports
            }
        
        except Exception as e:
            print(f"\n✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "state": {
                    "menu_profile": self.menu_profile,
                    "wines": self.wines,
                    "pairings": self.pairings
                }
            }


def main():
    """CLI interface for the application"""
    import sys
    
    app = CulinaryExpertApp()
    
    print("\n" + "=" * 70)
    print("AI CULINARY EXPERT - CLI INTERFACE")
    print("=" * 70)
    
    # Menu selection
    print("\nMenu Options:")
    print("1. Load existing menu profile")
    print("2. Process menu files (txt, pdf, jpg, png, xlsx, csv)")
    menu_choice = input("Select option (1): ").strip() or "1"
    
    menu_files = None
    menu_profile_path = None
    
    if menu_choice == "1":
        menu_profile_path = input("Enter menu profile path (press Enter for default): ").strip()
        if not menu_profile_path:
            menu_profile_path = str(DEFAULT_MENU_PROFILE_PATH)
    elif menu_choice == "2":
        file_input = input("Enter menu file path(s), comma-separated: ").strip()
        if file_input:
            menu_files = [f.strip() for f in file_input.split(",") if f.strip()]
    
    # Wine file selection
    print("\nWine Files:")
    print("(If wines were found in menu files, they will be used automatically)")
    wine_input = input("Enter wine file path(s), comma-separated (or press Enter to skip): ").strip()
    wine_files = None
    if wine_input:
        wine_files = [f.strip() for f in wine_input.split(",") if f.strip()]
    
    # Analyze similarity?
    analyze_sim = input("\nAnalyze wine similarity? (y/n, default: y): ").strip().lower()
    analyze_similarity = analyze_sim != "n"
    
    # Run workflow
    results = app.run_full_workflow(
        menu_files=menu_files,
        menu_profile_path=menu_profile_path,
        wine_files=wine_files,
        analyze_similarity=analyze_similarity,
        output_format="text"
    )
    
    if results["success"]:
        # Display report
        if isinstance(results["reports"], str):
            print("\n" + results["reports"])
        else:
            print("\n" + str(results["reports"]))
        
        # Save report option
        save = input("\nSave report to file? (y/n): ").strip().lower()
        if save == "y":
            output_path = input("Enter output path (default: report.txt): ").strip() or "report.txt"
            with open(output_path, 'w', encoding='utf-8') as f:
                if isinstance(results["reports"], str):
                    f.write(results["reports"])
                else:
                    f.write(str(results["reports"]))
            print(f"✓ Report saved to {output_path}")
    else:
        print(f"\n✗ Workflow failed: {results.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()

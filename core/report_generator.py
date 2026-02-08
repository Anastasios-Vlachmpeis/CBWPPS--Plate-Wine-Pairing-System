"""
Report generation module
Generates comprehensive reports on dish-wine pairings with scientific analysis
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
from datetime import datetime
import google.genai as genai


class ReportGenerator:
    """
    Generates comprehensive reports on wine pairings and recommendations
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Report Generator
        
        Args:
            api_key: Google AI API key (if None, reads from GOOGLE_AI_API_KEY env var)
        """
        # Get API key for Gemini explanations
        if api_key is None:
            api_key = os.getenv("GOOGLE_AI_API_KEY")
            if api_key is None:
                try:
                    from dotenv import load_dotenv
                    load_dotenv()
                    api_key = os.getenv("GOOGLE_AI_API_KEY")
                except ImportError:
                    pass
        
        self.api_key = api_key
        if api_key:
            self.client = genai.Client(api_key=api_key)
            self.model_name = "gemini-3-flash-preview"
        else:
            self.client = None
    
    def _generate_scientific_analysis(
        self,
        dish: Dict[str, Any],
        wine: Dict[str, Any],
        pairing_score: float
    ) -> Dict[str, Any]:
        """
        Generate scientific analysis of dish-wine pairing
        
        Args:
            dish: Dish dictionary with compounds
            wine: Wine dictionary with flavor_compounds
            pairing_score: Jaccard similarity score
            
        Returns:
            Dictionary with scientific analysis
        """
        dish_compounds = set(dish.get("compounds", []))
        wine_compounds = set(wine.get("flavor_compounds", []))
        shared_compounds = dish_compounds & wine_compounds
        
        return {
            "pairing_score": pairing_score,
            "dish_compounds_count": len(dish_compounds),
            "wine_compounds_count": len(wine_compounds),
            "shared_compounds_count": len(shared_compounds),
            "shared_compounds": sorted(list(shared_compounds)),
            "matching_method": "Jaccard similarity based on flavor compounds"
        }
    
    def _generate_sommelier_explanation(
        self,
        dish: Dict[str, Any],
        wine: Dict[str, Any],
        scientific_analysis: Dict[str, Any]
    ) -> str:
        """
        Generate simple sommelier-style explanation using Gemini
        
        Args:
            dish: Dish dictionary
            wine: Wine dictionary
            scientific_analysis: Scientific analysis dictionary
            
        Returns:
            Simple, human-readable explanation
        """
        if not self.client:
            # Fallback explanation without Gemini
            shared_count = scientific_analysis.get("shared_compounds_count", 0)
            if shared_count > 0:
                return f"This {wine.get('type_name', 'wine')} shares {shared_count} flavor compounds with the dish, creating a harmonious pairing."
            return f"This {wine.get('type_name', 'wine')} complements the dish's flavor profile."
        
        dish_name = dish.get("name") or dish.get("dish_name", "dish")  # Use "name" from normalized format
        wine_name = wine.get("wine_name", "wine")
        wine_type = wine.get("type_name", "wine")
        shared_compounds = scientific_analysis.get("shared_compounds", [])
        
        prompt = f"""You are a sommelier explaining a wine pairing in simple, friendly language.

Dish: {dish_name}
Wine: {wine_name} ({wine_type})
Shared flavor compounds: {', '.join(shared_compounds[:5]) if shared_compounds else 'None'}

Provide a brief, simple explanation (2-3 sentences) of why this wine pairs well with this dish.
Use everyday language, not technical jargon. Be warm and inviting.

Explanation:"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "temperature": 0.7,
                    "max_output_tokens": 200
                }
            )
            
            if hasattr(response, 'text'):
                explanation = response.text.strip()
            elif hasattr(response, 'candidates') and response.candidates:
                explanation = response.candidates[0].content.parts[0].text.strip()
            else:
                explanation = str(response).strip()
            
            return explanation
        except Exception as e:
            # Fallback
            shared_count = scientific_analysis.get("shared_compounds_count", 0)
            return f"This {wine_type} pairs beautifully with {dish_name}, sharing {shared_count} flavor compounds that create a harmonious match."
    
    def generate_similarity_report(
        self,
        similar_pairs: List[Tuple[int, int, float]],
        wines: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate report on similar wines
        
        Args:
            similar_pairs: List of (wine_id1, wine_id2, similarity_score) tuples
            wines: List of wine dictionaries
            
        Returns:
            Dictionary with similarity statistics and details
        """
        # Create wine lookup
        wine_dict = {w.get("wine_id"): w for w in wines if w.get("wine_id") is not None}
        
        # Build pair details
        pair_details = []
        for wine_id1, wine_id2, similarity in similar_pairs:
            wine1 = wine_dict.get(wine_id1)
            wine2 = wine_dict.get(wine_id2)
            
            if wine1 and wine2:
                pair_details.append({
                    "wine1": {
                        "wine_id": wine_id1,
                        "wine_name": wine1.get("wine_name", "Unknown"),
                        "type_name": wine1.get("type_name", "Unknown")
                    },
                    "wine2": {
                        "wine_id": wine_id2,
                        "wine_name": wine2.get("wine_name", "Unknown"),
                        "type_name": wine2.get("type_name", "Unknown")
                    },
                    "similarity_score": similarity
                })
        
        # Group by similarity ranges
        high_similarity = [p for p in similar_pairs if p[2] >= 0.8]
        medium_similarity = [p for p in similar_pairs if 0.6 <= p[2] < 0.8]
        low_similarity = [p for p in similar_pairs if p[2] < 0.6]
        
        report = {
            "total_similar_pairs": len(similar_pairs),
            "high_similarity_pairs": len(high_similarity),
            "medium_similarity_pairs": len(medium_similarity),
            "low_similarity_pairs": len(low_similarity),
            "similar_pairs": pair_details
        }
        
        return report
    
    def generate_recommendation_report(
        self,
        recommendations: List[Dict[str, Any]],
        existing_wines: List[Dict[str, Any]] = None,
        addition_limits: Dict[str, int] = None
    ) -> Dict[str, Any]:
        """
        Generate report on wine recommendations (additions/removals)
        
        Args:
            recommendations: List of recommendation dictionaries
            existing_wines: List of existing wine dictionaries
            addition_limits: Dictionary mapping type_name -> max wines to add
            
        Returns:
            Dictionary with recommendation details
        """
        wines_to_add = []
        wines_to_remove = []
        
        for rec in recommendations:
            action = rec.get("action", "add")  # 'add' or 'remove'
            wine = rec.get("wine", {})
            
            if action == "add":
                wines_to_add.append({
                    "wine_id": wine.get("wine_id"),
                    "wine_name": wine.get("wine_name", "Unknown"),
                    "type_name": wine.get("type_name", "Unknown"),
                    "reason": rec.get("reason", "Recommended for pairing")
                })
            elif action == "remove":
                wines_to_remove.append({
                    "wine_id": wine.get("wine_id"),
                    "wine_name": wine.get("wine_name", "Unknown"),
                    "type_name": wine.get("type_name", "Unknown"),
                    "reason": rec.get("reason", "Similar to existing wines")
                })
        
        # Group additions by type
        additions_by_type = defaultdict(list)
        for wine in wines_to_add:
            type_name = wine.get("type_name", "Unknown")
            additions_by_type[type_name].append(wine)
        
        # Apply addition limits if provided
        if addition_limits:
            limited_additions = []
            for type_name, wines in additions_by_type.items():
                limit = addition_limits.get(type_name, 0)
                limited_additions.extend(wines[:limit])
            wines_to_add = limited_additions
        
        report = {
            "wines_to_add": wines_to_add,
            "wines_to_remove": wines_to_remove,
            "additions_count": len(wines_to_add),
            "removals_count": len(wines_to_remove),
            "additions_by_type": dict(additions_by_type)
        }
        
        return report
    
    def generate_comprehensive_report(
        self,
        pairings: Dict[str, List[int]],
        wines: List[Dict[str, Any]],
        similar_pairs: List[Tuple[int, int, float]] = None,
        menu_profile: Dict[str, Dict[str, Any]] = None,
        wine_rankings: List[Tuple[int, float, Dict[str, Any]]] = None,
        pairing_engine = None,
        format: str = "dict"
    ) -> Any:
        """
        Generate comprehensive report with dish-level pairings
        
        Args:
            pairings: Dictionary mapping dish_id -> list of wine_ids
            wines: List of wine dictionaries
            similar_pairs: List of similar wine pairs (wine_id1, wine_id2, similarity)
            menu_profile: Menu profile dictionary
            wine_rankings: List of (wine_id, score, wine_dict) tuples from ranker
            pairing_engine: PairingEngine instance for calculating scores
            format: Output format ('dict', 'json', 'text')
            
        Returns:
            Comprehensive report in requested format
        """
        if menu_profile is None:
            menu_profile = {}
        
        # Create lookups
        wine_dict = {w.get("wine_id"): w for w in wines if w.get("wine_id") is not None}
        
        # #region agent log
        log_path = Path(".cursor/debug.log")
        try:
            import json as json_module
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json_module.dumps({"id":"log_report_gen_1","timestamp":int(__import__('time').time()*1000),"location":"report_generator.py:283","message":"Generating report","data":{"wine_count":len(wines),"wine_dict_size":len(wine_dict),"pairings_count":len(pairings),"menu_profile_size":len(menu_profile)},"runId":"run1","hypothesisId":"D"}) + "\n")
        except: pass
        # #endregion
        
        # Generate wine rankings
        if wine_rankings is None:
            # Simple ranking by pairing count
            pairing_counts = defaultdict(int)
            for dish_id, wine_ids in pairings.items():
                for wine_id in wine_ids:
                    pairing_counts[wine_id] += 1
            
            wine_rankings = []
            for wine_id, count in sorted(pairing_counts.items(), key=lambda x: x[1], reverse=True):
                wine = wine_dict.get(wine_id)
                if wine:
                    wine_rankings.append((wine_id, float(count), wine))
        
        # Generate wines to remove (from similar pairs)
        wines_to_remove = []
        if similar_pairs:
            removed_ids = set()
            for wine_id1, wine_id2, similarity in similar_pairs:
                if wine_id1 not in removed_ids:
                    wine = wine_dict.get(wine_id1)
                    if wine:
                        wines_to_remove.append({
                            "wine_id": wine_id1,
                            "wine_name": wine.get("wine_name", "Unknown"),
                            "type_name": wine.get("type_name", "Unknown"),
                            "reason": f"Similar to {wine_dict.get(wine_id2, {}).get('wine_name', 'another wine')} (similarity: {similarity:.2f})"
                        })
                        removed_ids.add(wine_id1)
        
        # Generate dish pairings with best wine, scientific analysis, and explanation
        dish_pairings = {}
        
        # Import pairing engine if needed
        if pairing_engine is None:
            from .pairing_engine import PairingEngine
            pairing_engine = PairingEngine()
        
        # Process all dishes in menu_profile, including those with no pairings
        for dish_id, dish in menu_profile.items():
            wine_ids = pairings.get(dish_id, [])
            
            # Check if dish has no flavor profile
            flavor_profile_note = dish.get("flavor_profile_note")
            if flavor_profile_note:
                dish_pairings[dish_id] = {
                    "dish_name": dish.get("name") or dish.get("dish_name", "Unknown"),  # Use "name" from normalized format
                    "flavor_profile_note": flavor_profile_note,
                    "wines": [],
                    "message": "No good wine pairings can be made with this plate, based on your current winelist"
                }
                continue
            
            # Check if no pairings found
            if not wine_ids:
                dish_pairings[dish_id] = {
                    "dish_name": dish.get("name") or dish.get("dish_name", "Unknown"),  # Use "name" from normalized format
                    "wines": [],
                    "message": "No good wine pairings can be made with this plate, based on your current winelist"
                }
                continue
            
            # Limit to up to 3 wines per dish
            wine_ids = wine_ids[:3]
            
            # Generate pairings for each wine (up to 3)
            wine_pairings = []
            for wine_id in wine_ids:
                wine = wine_dict.get(wine_id)
                if not wine:
                    continue
                
                # Calculate pairing score
                pairing_score = pairing_engine.calculate_pairing_score(
                    dish_id=dish_id,
                    wine=wine,
                    menu_profile=menu_profile
                )
                
                # Generate scientific analysis
                scientific_analysis = self._generate_scientific_analysis(
                    dish=dish,
                    wine=wine,
                    pairing_score=pairing_score
                )
                
                # Generate sommelier explanation (max 2 sentences)
                sommelier_explanation = self._generate_sommelier_explanation(
                    dish=dish,
                    wine=wine,
                    scientific_analysis=scientific_analysis
                )
                
                wine_pairings.append({
                    "wine_id": wine_id,
                    "wine_name": wine.get("wine_name", "Unknown"),
                    "type_name": wine.get("type_name", "Unknown"),
                    "scientific_analysis": scientific_analysis,
                    "sommelier_explanation": sommelier_explanation
                })
            
            dish_pairings[dish_id] = {
                "dish_name": dish.get("name") or dish.get("dish_name", "Unknown"),  # Use "name" field from normalized format
                "wines": wine_pairings
            }
        
        # Build comprehensive report
        comprehensive = {
            "timestamp": datetime.now().isoformat(),
            "wine_rankings": [
                {
                    "rank": i + 1,
                    "wine_id": wine_id,
                    "wine_name": wine.get("wine_name", "Unknown"),
                    "type_name": wine.get("type_name", "Unknown"),
                    "score": score,
                    "dishes_matched": sum(1 for wine_ids in pairings.values() if wine_id in wine_ids)
                }
                for i, (wine_id, score, wine) in enumerate(wine_rankings)
            ],
            "wines_to_remove": wines_to_remove,
            "dish_pairings": dish_pairings
        }
        
        # Format output
        if format == "json":
            return json.dumps(comprehensive, indent=2, ensure_ascii=False)
        elif format == "text":
            return self._format_text_report(comprehensive)
        else:
            return comprehensive
    
    def _format_text_report(self, report: Dict[str, Any]) -> str:
        """
        Format report as human-readable text
        
        Args:
            report: Comprehensive report dictionary
            
        Returns:
            Formatted text string
        """
        lines = []
        lines.append("=" * 70)
        lines.append("COMPREHENSIVE WINE PAIRING REPORT")
        lines.append("=" * 70)
        lines.append(f"Generated: {report['timestamp']}")
        lines.append("")
        
        # Wine Rankings
        lines.append("WINE RANKINGS")
        lines.append("-" * 70)
        lines.append("Ranked by number of dishes matched and match quality")
        lines.append("")
        for ranking in report["wine_rankings"][:20]:
            lines.append(
                f"  {ranking['rank']}. {ranking['wine_name']} ({ranking['type_name']}) - "
                f"Score: {ranking['score']:.3f}, Matched {ranking['dishes_matched']} dishes"
            )
        lines.append("")
        
        # Wines to Remove
        if report["wines_to_remove"]:
            lines.append("WINES TO REMOVE")
            lines.append("-" * 70)
            lines.append("These wines are too similar to others in the list")
            lines.append("")
            for wine in report["wines_to_remove"]:
                lines.append(f"  - {wine['wine_name']} ({wine['type_name']})")
                lines.append(f"    Reason: {wine['reason']}")
            lines.append("")
        
        # Dish Pairings
        lines.append("DISH-WINE PAIRINGS")
        lines.append("-" * 70)
        lines.append("Up to 3 best wine matches for each dish with scientific analysis")
        lines.append("")
        
        for dish_id, pairing_info in report["dish_pairings"].items():
            dish_name = pairing_info.get("dish_name") or pairing_info.get("name", "Unknown")
            
            # Check for flavor profile note
            if "flavor_profile_note" in pairing_info:
                lines.append(f"Dish: {dish_name}")
                lines.append(f"  {pairing_info['flavor_profile_note']}")
                lines.append(f"  {pairing_info.get('message', 'No pairings available')}")
                lines.append("")
                continue
            
            # Check for no pairings message
            if "message" in pairing_info:
                lines.append(f"Dish: {dish_name}")
                lines.append(f"  {pairing_info['message']}")
                lines.append("")
                continue
            
            # Show up to 3 wine pairings
            wines = pairing_info.get("wines", [])
            lines.append(f"Dish: {dish_name}")
            
            if not wines:
                lines.append("  No good wine pairings found")
            else:
                for i, wine_pairing in enumerate(wines, 1):
                    wine_name = wine_pairing["wine_name"]
                    wine_type = wine_pairing["type_name"]
                    scientific = wine_pairing["scientific_analysis"]
                    explanation = wine_pairing["sommelier_explanation"]
                    
                    lines.append(f"  Wine {i}: {wine_name} ({wine_type})")
                    lines.append(f"    Pairing Score: {scientific['pairing_score']:.3f}")
                    lines.append(f"    Shared Compounds: {scientific['shared_compounds_count']} "
                                f"({', '.join(scientific['shared_compounds'][:5]) if scientific['shared_compounds'] else 'None'})")
                    lines.append(f"    Explanation: {explanation}")
                    lines.append("")
            
            lines.append("")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)

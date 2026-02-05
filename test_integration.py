"""
Integration tests for AI Culinary Expert application
Tests all modules working together
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from app import CulinaryExpertApp
from core import (
    MenuProcessor,
    PlateCombinationGenerator,
    WineManager,
    WineSimilarityAnalyzer,
    PairingEngine,
    WineRanker,
    ReportGenerator
)
from utils.config import DEFAULT_MENU_PROFILE_PATH, DEFAULT_WINES_PATH


def test_menu_processing():
    """Test menu processing"""
    print("\n" + "=" * 70)
    print("TEST 1: MENU PROCESSING")
    print("=" * 70)
    
    try:
        processor = MenuProcessor()
        
        # Test loading existing menu profile
        menu_profile = processor.load_menu_profile()
        
        assert isinstance(menu_profile, dict), "Menu profile should be a dictionary"
        assert len(menu_profile) > 0, "Menu profile should not be empty"
        
        # Verify structure
        for dish_id, dish in menu_profile.items():
            assert "name" in dish, f"Dish {dish_id} missing 'name'"
            assert "compounds" in dish, f"Dish {dish_id} missing 'compounds'"
            assert isinstance(dish["compounds"], list), "Compounds should be a list"
        
        print(f"✓ Menu profile loaded: {len(menu_profile)} dishes")
        print(f"✓ Sample dish: {list(menu_profile.keys())[0]}")
        return True
    
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_combination_generation():
    """Test combination generation"""
    print("\n" + "=" * 70)
    print("TEST 2: COMBINATION GENERATION")
    print("=" * 70)
    
    try:
        processor = MenuProcessor()
        menu_profile = processor.load_menu_profile()
        
        generator = PlateCombinationGenerator()
        
        # Test logical combinations
        logical = generator.generate_logical_combinations(menu_profile)
        assert isinstance(logical, list), "Logical combinations should be a list"
        print(f"✓ Logical combinations: {len(logical)}")
        
        # Test flavor-similar combinations
        flavor_similar = generator.generate_flavor_similar_combinations(menu_profile)
        assert isinstance(flavor_similar, list), "Flavor-similar combinations should be a list"
        print(f"✓ Flavor-similar combinations: {len(flavor_similar)}")
        
        # Test random combinations
        random_combos = generator.generate_random_combinations(menu_profile, num_combos=10)
        assert isinstance(random_combos, list), "Random combinations should be a list"
        assert len(random_combos) == 10, "Should generate 10 random combinations"
        print(f"✓ Random combinations: {len(random_combos)}")
        
        # Test all combinations
        all_combos = generator.generate_all_combinations(menu_profile)
        assert isinstance(all_combos, dict), "All combinations should be a dictionary"
        assert "logical" in all_combos, "Should include logical combinations"
        assert "flavor_similar" in all_combos, "Should include flavor-similar combinations"
        assert "random" in all_combos, "Should include random combinations"
        print(f"✓ All combination types generated")
        
        return True
    
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_wine_loading():
    """Test wine loading"""
    print("\n" + "=" * 70)
    print("TEST 3: WINE LOADING")
    print("=" * 70)
    
    try:
        manager = WineManager()
        
        # Test loading from internal database
        wines = manager.load_internal_wines()
        assert isinstance(wines, list), "Wines should be a list"
        assert len(wines) > 0, "Should load wines"
        
        # Verify wine structure
        for wine in wines[:5]:  # Check first 5
            assert "wine_id" in wine, "Wine missing 'wine_id'"
            assert "wine_name" in wine, "Wine missing 'wine_name'"
            assert "type_name" in wine, "Wine missing 'type_name'"
            assert "flavor_compounds" in wine, "Wine missing 'flavor_compounds'"
            assert isinstance(wine["flavor_compounds"], list), "Flavor compounds should be a list"
        
        print(f"✓ Loaded {len(wines)} wines from internal database")
        print(f"✓ Sample wine: {wines[0].get('wine_name')}")
        
        return True
    
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_similarity_analysis():
    """Test similarity analysis"""
    print("\n" + "=" * 70)
    print("TEST 4: SIMILARITY ANALYSIS")
    print("=" * 70)
    
    try:
        manager = WineManager()
        wines = manager.load_internal_wines()
        
        # Use subset for faster testing
        test_wines = wines[:50]
        
        analyzer = WineSimilarityAnalyzer()
        
        # Test similarity calculation
        if len(test_wines) >= 2:
            similarity = analyzer.calculate_similarity(test_wines[0], test_wines[1])
            assert 0 <= similarity <= 1, "Similarity should be between 0 and 1"
            print(f"✓ Similarity calculation: {similarity:.3f}")
        
        # Test finding similar pairs
        similar_pairs = analyzer.find_similar_pairs(test_wines, threshold=0.5)
        assert isinstance(similar_pairs, list), "Similar pairs should be a list"
        print(f"✓ Found {len(similar_pairs)} similar pairs (threshold=0.5)")
        
        # Test grouping
        groups = analyzer.group_similar_wines(test_wines, threshold=0.7)
        assert isinstance(groups, list), "Groups should be a list"
        print(f"✓ Grouped into {len(groups)} similarity clusters")
        
        return True
    
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pairing_engine():
    """Test pairing engine"""
    print("\n" + "=" * 70)
    print("TEST 5: PAIRING ENGINE")
    print("=" * 70)
    
    try:
        processor = MenuProcessor()
        menu_profile = processor.load_menu_profile()
        
        manager = WineManager()
        wines = manager.load_internal_wines()
        
        # Generate test combinations
        generator = PlateCombinationGenerator()
        combo_results = generator.generate_all_combinations(menu_profile)
        
        # Combine combinations
        all_combos = []
        for combos in combo_results.values():
            all_combos.extend(combos[:5])  # Use first 5 of each type
        
        if not all_combos:
            print("⚠ No combinations generated, skipping pairing test")
            return True
        
        # Create combination dictionary
        combinations = {f"test_{i}": combo for i, combo in enumerate(all_combos)}
        
        # Test pairing
        pairing_engine = PairingEngine()
        pairings = pairing_engine.pair_all_combinations(
            combinations=list(combinations.values()),
            wines=wines[:100],  # Use subset for speed
            menu_profile=menu_profile,
            combination_ids=list(combinations.keys())
        )
        
        assert isinstance(pairings, dict), "Pairings should be a dictionary"
        assert len(pairings) == len(combinations), "Should have pairings for all combinations"
        
        paired_count = sum(1 for wine_ids in pairings.values() if wine_ids)
        print(f"✓ Paired {paired_count} / {len(pairings)} combinations")
        
        # Test unpaired detection
        unpaired = pairing_engine.find_unpaired_combinations(pairings)
        print(f"✓ Found {len(unpaired)} unpaired combinations")
        
        return True
    
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_wine_ranking():
    """Test wine ranking"""
    print("\n" + "=" * 70)
    print("TEST 6: WINE RANKING")
    print("=" * 70)
    
    try:
        manager = WineManager()
        wines = manager.load_internal_wines()
        
        processor = MenuProcessor()
        menu_profile = processor.load_menu_profile()
        
        # Create test pairings
        generator = PlateCombinationGenerator()
        combo_results = generator.generate_all_combinations(menu_profile)
        
        all_combos = []
        for combos in combo_results.values():
            all_combos.extend(combos[:3])
        
        if not all_combos:
            print("⚠ No combinations, skipping ranking test")
            return True
        
        combinations = {f"test_{i}": combo for i, combo in enumerate(all_combos)}
        
        pairing_engine = PairingEngine()
        pairings = pairing_engine.pair_all_combinations(
            combinations=list(combinations.values()),
            wines=wines[:50],
            menu_profile=menu_profile,
            combination_ids=list(combinations.keys())
        )
        
        # Test ranking
        ranker = WineRanker()
        
        # Test frequency ranking
        frequency_rankings = ranker.rank_by_pairing_frequency(pairings)
        assert isinstance(frequency_rankings, dict), "Frequency rankings should be a dictionary"
        print(f"✓ Ranked {len(frequency_rankings)} wines by frequency")
        
        # Test coverage ranking
        coverage_rankings = ranker.rank_by_flavor_coverage(wines[:50], menu_profile)
        assert isinstance(coverage_rankings, dict), "Coverage rankings should be a dictionary"
        print(f"✓ Ranked wines by flavor coverage")
        
        # Test combined ranking
        combined_rankings = ranker.rank_wines(
            wines=wines[:50],
            pairings=pairings,
            menu_profile=menu_profile
        )
        assert isinstance(combined_rankings, dict), "Combined rankings should be a dictionary"
        print(f"✓ Generated combined rankings")
        
        # Test final wine list generation
        final_list = ranker.generate_wine_list(
            wines=wines[:100],
            rankings=combined_rankings
        )
        assert isinstance(final_list, list), "Final list should be a list"
        print(f"✓ Generated final wine list: {len(final_list)} wines")
        
        return True
    
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_report_generation():
    """Test report generation"""
    print("\n" + "=" * 70)
    print("TEST 7: REPORT GENERATION")
    print("=" * 70)
    
    try:
        manager = WineManager()
        wines = manager.load_internal_wines()[:50]
        
        processor = MenuProcessor()
        menu_profile = processor.load_menu_profile()
        
        # Create test data
        generator = PlateCombinationGenerator()
        combo_results = generator.generate_all_combinations(menu_profile)
        
        all_combos = []
        for combos in combo_results.values():
            all_combos.extend(combos[:3])
        
        combinations = {f"test_{i}": combo for i, combo in enumerate(all_combos)}
        
        pairing_engine = PairingEngine()
        pairings = pairing_engine.pair_all_combinations(
            combinations=list(combinations.values()),
            wines=wines,
            menu_profile=menu_profile,
            combination_ids=list(combinations.keys())
        )
        
        analyzer = WineSimilarityAnalyzer()
        similar_pairs = analyzer.find_similar_pairs(wines, threshold=0.7)
        
        # Test report generation
        report_gen = ReportGenerator()
        
        # Test pairing report
        pairing_report = report_gen.generate_pairing_report(pairings, wines, combinations)
        assert isinstance(pairing_report, dict), "Pairing report should be a dictionary"
        assert "total_combinations" in pairing_report, "Report missing 'total_combinations'"
        print(f"✓ Generated pairing report")
        
        # Test similarity report
        similarity_report = report_gen.generate_similarity_report(similar_pairs, wines)
        assert isinstance(similarity_report, dict), "Similarity report should be a dictionary"
        print(f"✓ Generated similarity report")
        
        # Test comprehensive report
        comprehensive = report_gen.generate_comprehensive_report(
            pairings=pairings,
            wines=wines,
            similar_pairs=similar_pairs,
            combinations=combinations,
            format="dict"
        )
        assert isinstance(comprehensive, dict), "Comprehensive report should be a dictionary"
        assert "summary" in comprehensive, "Report missing 'summary'"
        print(f"✓ Generated comprehensive report")
        
        # Test text format
        text_report = report_gen.generate_comprehensive_report(
            pairings=pairings,
            wines=wines,
            similar_pairs=similar_pairs,
            combinations=combinations,
            format="text"
        )
        assert isinstance(text_report, str), "Text report should be a string"
        assert len(text_report) > 0, "Text report should not be empty"
        print(f"✓ Generated text report ({len(text_report)} chars)")
        
        return True
    
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_workflow():
    """Test full workflow"""
    print("\n" + "=" * 70)
    print("TEST 8: FULL WORKFLOW")
    print("=" * 70)
    
    try:
        app = CulinaryExpertApp()
        
        # Run workflow with internal wines
        results = app.run_full_workflow(
            menu_profile_path=str(DEFAULT_MENU_PROFILE_PATH),
            wine_source_type="internal",
            analyze_similarity=False,
            output_format="dict"
        )
        
        assert results["success"], "Workflow should succeed"
        assert "menu_profile" in results, "Results should include menu_profile"
        assert "combinations" in results, "Results should include combinations"
        assert "wines" in results, "Results should include wines"
        assert "pairings" in results, "Results should include pairings"
        assert "reports" in results, "Results should include reports"
        
        print(f"✓ Workflow completed successfully")
        print(f"  - Menu dishes: {len(results['menu_profile'])}")
        print(f"  - Combinations: {len(results['combinations'])}")
        print(f"  - Wines: {len(results['wines'])}")
        print(f"  - Pairings: {len(results['pairings'])}")
        
        return True
    
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "=" * 70)
    print("AI CULINARY EXPERT - INTEGRATION TESTS")
    print("=" * 70)
    
    tests = [
        ("Menu Processing", test_menu_processing),
        ("Combination Generation", test_combination_generation),
        ("Wine Loading", test_wine_loading),
        ("Similarity Analysis", test_similarity_analysis),
        ("Pairing Engine", test_pairing_engine),
        ("Wine Ranking", test_wine_ranking),
        ("Report Generation", test_report_generation),
        ("Full Workflow", test_full_workflow),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print(f"✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(run_all_tests())

"""
Example usage of WineSommelier
"""

from wine_sommelier import WineSommelier

def main():
    # Initialize the sommelier
    # Make sure GOOGLE_AI_API_KEY is set in your .env file or environment
    sommelier = WineSommelier()
    
    # Example 1: Text-based recommendation
    print("=" * 70)
    print("EXAMPLE 1: Text-based recommendation")
    print("=" * 70)
    
    result = sommelier.recommend(
        dish_description="Grilled sea bass with lemon butter sauce, capers, and fresh dill"
    )
    
    print(f"\nTop 3 Wine IDs: {result['top_matches']}")
    print(f"\nScientific Reasoning:\n{result['scientific_reasoning']}")
    print(f"\nCulinary Reasoning:\n{result['culinary_reasoning']}")
    print(f"\nUpsell Tip:\n{result['upsell_tip']}")
    
    print("\n" + "-" * 70)
    print("Wine Details:")
    for i, wine in enumerate(result['wine_details'], 1):
        print(f"\n{i}. {wine['wine_name']}")
        print(f"   Type: {wine['type_name']} | Body: {wine['body_name']} | Acidity: {wine['acidity_name']}")
        print(f"   Grapes: {', '.join(wine['grapes'])}")
        print(f"   Region: {wine['region']}, {wine['country']}")
        print(f"   Winery: {wine['winery']}")
        if wine.get('harmonize'):
            print(f"   Harmonizes with: {', '.join(wine['harmonize'])}")
    
    # Example 2: Image-based recommendation (uncomment to use)
    # print("\n" + "=" * 70)
    # print("EXAMPLE 2: Image-based recommendation")
    # print("=" * 70)
    # 
    # result = sommelier.recommend(
    #     dish_image="path/to/dish_image.jpg"  # or bytes
    # )
    # 
    # print(f"\nTop 3 Wine IDs: {result['top_matches']}")
    # print(f"\nScientific Reasoning:\n{result['scientific_reasoning']}")
    
    # Example 3: Search wines by compounds
    # print("\n" + "=" * 70)
    # print("EXAMPLE 3: Search wines by specific compounds")
    # print("=" * 70)
    
    # matches = sommelier.search_wines_by_compounds(["Citral", "Geraniol", "Linalool"])
    # print(f"\nFound {len(matches)} wines with matching compounds")
    # print("\nTop 5 matches:")
    # for i, match in enumerate(matches[:5], 1):
    #     wine = match['wine']
    #     print(f"\n{i}. {wine['wine_name']} (ID: {wine['wine_id']})")
    #     print(f"   Shared compounds: {', '.join(match['shared_compounds'][:5])}")
    #     print(f"   Total matches: {match['match_count']}")


if __name__ == "__main__":
    main()

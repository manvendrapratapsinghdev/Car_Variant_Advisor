"""
Simplified recommendation engine without LangChain agent complexity.
Direct function-based approach for faster, more reliable results.
"""
import sys
sys.path.append('/Users/d111879/Documents/Project/DEMO/Hackthon/HT_Jan_26')
from src.database.queries import init_queries, get_variant_details, find_upgrade_options
from typing import Dict, List, Optional
import json

# Initialize database
init_queries("/Users/d111879/Documents/Project/DEMO/Hackthon/HT_Jan_26/data/car_variants_db")


class SimpleRecommendationEngine:
    """
    Simple, direct recommendation engine without agent complexity.
    """
    
    @staticmethod
    def calculate_feature_difference(variant1: Dict, variant2: Dict) -> Dict:
        """
        Calculate what's new in variant2 compared to variant1.
        """
        price_diff = variant2['price'] - variant1['price']
        
        additional_features = {}
        total_new_features = 0
        
        for category in ['safety', 'comfort', 'technology', 'exterior', 'convenience']:
            features1 = set(variant1['features'][category])
            features2 = set(variant2['features'][category])
            new_features = list(features2 - features1)
            
            if new_features:
                additional_features[category] = new_features
                total_new_features += len(new_features)
        
        return {
            "price_difference": price_diff,
            "additional_features": additional_features,
            "total_new_features": total_new_features,
            "cost_per_feature": price_diff / max(1, total_new_features)
        }
    
    @staticmethod
    def get_recommendations(make: str, model: str, variant_name: str, num_recommendations: int = 3) -> Dict:
        """
        Get upgrade recommendations for a selected variant.
        
        Args:
            make: Car manufacturer
            model: Car model
            variant_name: Selected variant name
            num_recommendations: Number of upgrade options to show (2-3, default 3)
        
        Returns:
            Dictionary with selected variant, upgrade options, and reasoning trace
        """
        trace_steps = []
        
        # Step 1: Get selected variant details
        trace_steps.append(f"Step 1: Retrieving details for {make} {model} {variant_name}")
        selected_variant = get_variant_details(make, model, variant_name)
        
        if not selected_variant:
            return {
                "status": "error",
                "error": f"Variant not found: {make} {model} {variant_name}",
                "trace": trace_steps
            }
        
        trace_steps.append(f"✓ Found {variant_name} - ₹{selected_variant['price']:,.0f} ({selected_variant['tier_name']} tier)")
        
        # Step 2: Check if top variant
        if selected_variant['tier_order'] >= 4:
            trace_steps.append("Step 2: Checking for upgrades")
            trace_steps.append("✓ This is the top variant! No upgrades available.")
            
            return {
                "status": "success",
                "is_top_variant": True,
                "selected_variant": selected_variant,
                "upgrade_options": [],
                "message": f"🎉 You've selected the {variant_name}, which is the top variant with all available features!",
                "trace": trace_steps
            }
        
        # Step 3: Find upgrade options
        trace_steps.append(f"Step 2: Finding up to {num_recommendations} upgrade options (tier > {selected_variant['tier_order']})")
        upgrades = find_upgrade_options(make, model, selected_variant['tier_order'], limit=num_recommendations)
        
        if not upgrades:
            trace_steps.append("✓ No higher variants available")
            return {
                "status": "success",
                "is_top_variant": True,
                "selected_variant": selected_variant,
                "upgrade_options": [],
                "message": "You've selected the highest available variant!",
                "trace": trace_steps
            }
        
        trace_steps.append(f"✓ Found {len(upgrades)} upgrade option(s)")
        
        # Step 3: Calculate differences for each upgrade
        trace_steps.append(f"Step 3: Calculating feature differences for {len(upgrades)} upgrade(s)")
        
        upgrade_recommendations = []
        for i, upgrade in enumerate(upgrades, 1):  # Use all available upgrades (up to limit)
            diff = SimpleRecommendationEngine.calculate_feature_difference(selected_variant, upgrade)
            
            # Create recommendation text
            if diff['total_new_features'] > 0:
                value_assessment = "Good value" if diff['cost_per_feature'] < 50000 else "Premium choice"
            else:
                value_assessment = "Similar features"
            
            trace_steps.append(f"  Upgrade {i}: {upgrade['variant_name']} - +₹{diff['price_difference']:,.0f} for {diff['total_new_features']} new features")
            
            upgrade_recommendations.append({
                "variant": upgrade,
                "price_difference": diff['price_difference'],
                "additional_features": diff['additional_features'],
                "total_new_features": diff['total_new_features'],
                "cost_per_feature": diff['cost_per_feature'],
                "value_assessment": value_assessment
            })
        
        trace_steps.append("✓ Analysis complete")
        
        return {
            "status": "success",
            "is_top_variant": False,
            "selected_variant": selected_variant,
            "upgrade_options": upgrade_recommendations,
            "trace": trace_steps
        }


if __name__ == "__main__":
    # Test recommendation engine
    print("=== Testing Simple Recommendation Engine ===\n")
    
    engine = SimpleRecommendationEngine()
    
    # Test 1: Mid-tier variant
    print("Test 1: Mid-tier variant (Swift Vdi)")
    result = engine.get_recommendations("Maruti Suzuki", "Swift", "Vdi")
    
    print(f"\nStatus: {result['status']}")
    print(f"Selected: {result['selected_variant']['variant_name']} - ₹{result['selected_variant']['price']:,.0f}")
    
    if result['upgrade_options']:
        print(f"\nUpgrade Options: {len(result['upgrade_options'])}")
        for i, opt in enumerate(result['upgrade_options'], 1):
            print(f"\n  Option {i}: {opt['variant']['variant_name']}")
            print(f"    Price: ₹{opt['variant']['price']:,.0f} (+₹{opt['price_difference']:,.0f})")
            print(f"    New Features: {opt['total_new_features']}")
            print(f"    Value: ₹{opt['cost_per_feature']:,.0f} per feature ({opt['value_assessment']})")
    
    print("\n\nReasoning Trace:")
    for step in result['trace']:
        print(f"  {step}")
    
    print("\n✅ Recommendation engine test complete!")

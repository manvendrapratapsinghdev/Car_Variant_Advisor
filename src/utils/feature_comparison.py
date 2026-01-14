"""
Feature Comparison Matrix Utility
Creates differential feature comparison tables for variant upgrades
"""
import pandas as pd
from typing import Dict, List, Tuple


def build_feature_comparison_matrix(selected_variant: Dict, upgrade_options: List[Dict]) -> pd.DataFrame:
    """
    Build a differential feature comparison matrix showing NEW features in upgrade variants.
    
    Args:
        selected_variant: Dictionary containing the currently selected variant details
        upgrade_options: List of dictionaries containing upgrade variant details
    
    Returns:
        pandas DataFrame with features as rows and variants as columns
        Shows ✅ for available features, ❌ for unavailable features
    """
    # Collect all variants (selected + upgrades)
    all_variants = [selected_variant] + [opt['variant'] if 'variant' in opt else opt for opt in upgrade_options]
    
    # Store price differences for upgrades
    price_diffs = {}
    selected_price = selected_variant['price']
    for opt in upgrade_options:
        variant = opt['variant'] if 'variant' in opt else opt
        price_diff = variant['price'] - selected_price
        price_diffs[variant['variant_name']] = price_diff
    
    # Extract all unique NEW features across all upgrades
    # We only show differential features (what's new in higher variants)
    all_differential_features = {}
    categories = ['safety', 'comfort', 'technology', 'exterior', 'convenience']
    
    selected_features_sets = {
        cat: set(selected_variant['features'].get(cat, [])) 
        for cat in categories
    }
    
    # For each upgrade, find NEW features
    for variant in all_variants[1:]:  # Skip selected variant
        for category in categories:
            variant_features = set(variant['features'].get(category, []))
            new_features = variant_features - selected_features_sets[category]
            
            if category not in all_differential_features:
                all_differential_features[category] = set()
            all_differential_features[category].update(new_features)
    
    # Build the comparison matrix
    matrix_data = []
    
    for category in categories:
        differential_features = sorted(list(all_differential_features.get(category, [])))
        
        if not differential_features:
            continue  # Skip categories with no new features
        
        # Add category header row
        category_row = {
            'Feature': f'━━━ {category.upper()} ━━━',
            'Category': category
        }
        for i, variant in enumerate(all_variants):
            if i == 0:  # Current variant
                variant_col_name = f"{variant['variant_name']} (CURRENT)"
            else:  # Upgrade variants
                price_diff = price_diffs.get(variant['variant_name'], 0)
                variant_col_name = f"{variant['variant_name']} (+₹{price_diff:,.0f})"
            category_row[variant_col_name] = ''
        matrix_data.append(category_row)
        
        # Add feature rows
        for feature in differential_features:
            feature_row = {
                'Feature': feature,
                'Category': category
            }
            
            for i, variant in enumerate(all_variants):
                if i == 0:  # Current variant
                    variant_col_name = f"{variant['variant_name']} (CURRENT)"
                else:  # Upgrade variants
                    price_diff = price_diffs.get(variant['variant_name'], 0)
                    variant_col_name = f"{variant['variant_name']} (+₹{price_diff:,.0f})"
                
                variant_features = set(variant['features'].get(category, []))
                
                # Check if this feature exists in this variant
                if feature in variant_features:
                    feature_row[variant_col_name] = '✅'
                else:
                    feature_row[variant_col_name] = '❌'
            
            matrix_data.append(feature_row)
    
    # Convert to DataFrame
    if not matrix_data:
        # No differential features found
        columns = {'Feature': ['No new features found']}
        for i, v in enumerate(all_variants):
            if i == 0:
                col_name = f"{v['variant_name']} (CURRENT)"
            else:
                price_diff = price_diffs.get(v['variant_name'], 0)
                col_name = f"{v['variant_name']} (+₹{price_diff:,.0f})"
            columns[col_name] = ['-']
        return pd.DataFrame(columns)
    
    df = pd.DataFrame(matrix_data)
    
    # Drop the Category column (used for organization only)
    df = df.drop('Category', axis=1)
    
    return df


def style_comparison_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply styling to the comparison matrix for better visualization.
    
    Args:
        df: Feature comparison DataFrame
    
    Returns:
        Styled DataFrame
    """
    def highlight_cells(val):
        """Apply color coding to cells"""
        if val == '✅':
            return 'background-color: #d4edda; color: #155724; font-weight: bold;'
        elif val == '❌':
            return 'background-color: #f8d7da; color: #721c24;'
        elif '━━━' in str(val):
            return 'background-color: #e9ecef; font-weight: bold; font-size: 14px;'
        return ''
    
    return df.style.applymap(highlight_cells)


if __name__ == "__main__":
    # Test the feature comparison matrix
    print("=== Testing Feature Comparison Matrix ===\n")
    
    # Mock data for testing
    selected = {
        'variant_name': 'Swift LXi',
        'tier_name': 'base',
        'price': 550000,
        'features': {
            'safety': ['ABS', 'Airbags (2)'],
            'comfort': ['AC', 'Power Windows'],
            'technology': ['USB Port'],
            'exterior': ['Steel Wheels'],
            'convenience': ['Remote Key']
        }
    }
    
    upgrades = [
        {
            'variant': {
                'variant_name': 'Swift VXi',
                'tier_name': 'mid',
                'price': 650000,
                'features': {
                    'safety': ['ABS', 'Airbags (2)', 'ESP'],
                    'comfort': ['AC', 'Power Windows', 'Steering Mounted Controls'],
                    'technology': ['USB Port', 'Bluetooth'],
                    'exterior': ['Steel Wheels', 'Fog Lamps'],
                    'convenience': ['Remote Key', 'Keyless Entry']
                }
            }
        },
        {
            'variant': {
                'variant_name': 'Swift ZXi',
                'tier_name': 'high',
                'price': 750000,
                'features': {
                    'safety': ['ABS', 'Airbags (2)', 'ESP', 'Hill Hold'],
                    'comfort': ['AC', 'Power Windows', 'Steering Mounted Controls', 'Climate Control'],
                    'technology': ['USB Port', 'Bluetooth', 'Touchscreen', 'Apple CarPlay'],
                    'exterior': ['Steel Wheels', 'Fog Lamps', 'Alloy Wheels', 'LED DRLs'],
                    'convenience': ['Remote Key', 'Keyless Entry', 'Push Button Start']
                }
            }
        }
    ]
    
    # Build matrix
    matrix = build_feature_comparison_matrix(selected, upgrades)
    
    print("Feature Comparison Matrix:")
    print("=" * 100)
    print(matrix.to_string(index=False))
    print("\n✅ Feature comparison matrix test complete!")

"""
Tier inference logic for car variants.
Assigns tier_order (1=base, 2=mid, 3=high, 4=top) based on variant name patterns.
"""
import pandas as pd
import re
from typing import Optional, Tuple


class TierInference:
    """
    Infer variant tiers using pattern matching on variant names.
    """
    
    # Common tier patterns across different brands
    TIER_PATTERNS = {
        # Maruti patterns (LXi, VXi, ZXi, ZXi+)
        'maruti_lx': (r'\bL[XTM][iI]?\b', 1),
        'maruti_vx': (r'\bV[XTM][iI]?\+?\b', 2),
        'maruti_zx': (r'\bZ[XTM][iI]?\b(?!\+)', 3),
        'maruti_zx_plus': (r'\bZ[XTM][iI]?\+\b', 4),
        
        # Hyundai patterns (E, S, SX, SX(O))
        'hyundai_e': (r'\b[EX]E\b', 1),
        'hyundai_s': (r'\bS\b(?!X)', 2),
        'hyundai_sx': (r'\bSX\b(?!\()', 3),
        'hyundai_sx_o': (r'\bSX\([OoP]\)\b', 4),
        
        # Tata patterns (XE, XM, XT, XZ)
        'tata_xe': (r'\bXE\b', 1),
        'tata_xm': (r'\bXM[A]?\b', 2),
        'tata_xt': (r'\bXT\b(?!\+)', 3),
        'tata_xz_plus': (r'\bXZ\+?\b', 4),
        
        # Mahindra patterns (W4, W6, W8, W10)
        'mahindra_w4': (r'\bW[34]\b', 1),
        'mahindra_w6': (r'\bW[56]\b', 2),
        'mahindra_w8': (r'\bW[78]\b', 3),
        'mahindra_w10': (r'\bW[91][01]\b', 4),
        
        # Generic patterns (Base, Standard, Comfort, Luxury, etc.)
        'generic_base': (r'\b(Base|Standard|Essential|Xe)\b', 1),
        'generic_mid': (r'\b(Mid|Comfort|Active|S)\b', 2),
        'generic_high': (r'\b(High|Style|Ambiente|SV)\b', 3),
        'generic_top': (r'\b(Top|Luxury|Premium|Highline|SVP)\b', 4),
        
        # Kia/Seltos patterns (HTE, HTK, HTX)
        'kia_hte': (r'\bHTE\b', 1),
        'kia_htk': (r'\bHTK\b', 2),
        'kia_htx': (r'\bHTX\b(?!\+)', 3),
        'kia_htx_plus': (r'\bHTX\+\b', 4),
        
        # Honda patterns (S, V, VX, ZX)
        'honda_s': (r'\b[SV]\b(?!X)', 1),
        'honda_v': (r'\bV\b(?!X)', 2),
        'honda_vx': (r'\bVX\b', 3),
        'honda_zx': (r'\bZX\b', 4),
        
        # Plus/Lux modifiers
        'plus_modifier': (r'\b(Plus|Lux|Luxury|Pro)\b', 4),
    }
    
    @staticmethod
    def infer_tier(variant_name: str, make: str = None) -> Tuple[Optional[int], str]:
        """
        Infer tier order from variant name.
        
        Args:
            variant_name: Variant name string
            make: Car manufacturer (optional, helps with brand-specific patterns)
        
        Returns:
            Tuple of (tier_order, confidence_level)
            tier_order: 1-4 or None if cannot infer
            confidence_level: 'high', 'medium', 'low'
        """
        if pd.isna(variant_name):
            return None, 'none'
        
        variant_upper = str(variant_name).upper()
        make_lower = str(make).lower() if make else ''
        
        # Try brand-specific patterns first (higher confidence)
        if make:
            for pattern_name, (pattern, tier) in TierInference.TIER_PATTERNS.items():
                if make_lower in pattern_name:
                    if re.search(pattern, variant_upper):
                        return tier, 'high'
        
        # Try generic patterns
        for pattern_name, (pattern, tier) in TierInference.TIER_PATTERNS.items():
            if 'generic' in pattern_name or pattern_name.startswith('honda'):
                if re.search(pattern, variant_upper):
                    return tier, 'medium'
        
        # Fallback: use price-based grouping (lower confidence)
        return None, 'low'
    
    @staticmethod
    def assign_tiers_by_price(df: pd.DataFrame, make_model_group: pd.DataFrame) -> pd.Series:
        """
        Fallback method: Assign tiers based on price quartiles within a model.
        
        Args:
            df: Full dataframe
            make_model_group: Filtered df for one make+model combination
        
        Returns:
            Series with tier assignments
        """
        if len(make_model_group) == 1:
            return pd.Series([2], index=make_model_group.index)  # Single variant = mid tier
        
        # Sort by price
        sorted_group = make_model_group.sort_values('price_numeric')
        n_variants = len(sorted_group)
        
        # Assign tiers based on quartiles
        tiers = []
        for idx, (i, row) in enumerate(sorted_group.iterrows()):
            if idx < n_variants * 0.25:
                tiers.append(1)  # Bottom 25% = base
            elif idx < n_variants * 0.5:
                tiers.append(2)  # 25-50% = mid
            elif idx < n_variants * 0.75:
                tiers.append(3)  # 50-75% = high
            else:
                tiers.append(4)  # Top 25% = top
        
        return pd.Series(tiers, index=sorted_group.index)
    
    @classmethod
    def process_dataframe(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add tier_order and confidence columns to dataframe.
        
        Args:
            df: Dataframe with Make, Model, Variant, price_numeric columns
        
        Returns:
            Dataframe with added tier_order, tier_confidence columns
        """
        print("\n=== Tier Inference Process ===")
        
        # Apply pattern-based inference
        tier_results = df.apply(
            lambda row: cls.infer_tier(row['Variant'], row['Make']),
            axis=1
        )
        
        df['tier_order'] = tier_results.apply(lambda x: x[0])
        df['tier_confidence'] = tier_results.apply(lambda x: x[1])
        
        # Count pattern-based successes
        pattern_based = df['tier_order'].notna().sum()
        print(f"Pattern-based inference: {pattern_based}/{len(df)} variants ({pattern_based/len(df)*100:.1f}%)")
        
        # For variants without tier, use price-based fallback
        no_tier_mask = df['tier_order'].isna()
        
        if no_tier_mask.sum() > 0:
            print(f"Using price-based fallback for {no_tier_mask.sum()} variants...")
            
            for (make, model), group in df[no_tier_mask].groupby(['Make', 'Model']):
                if len(group) > 0:
                    price_tiers = cls.assign_tiers_by_price(df, 
                                                             df[(df['Make']==make) & (df['Model']==model)])
                    df.loc[price_tiers.index, 'tier_order'] = price_tiers
                    df.loc[price_tiers.index, 'tier_confidence'] = 'low'
        
        # Assign tier names
        tier_names = {1: 'base', 2: 'mid', 3: 'high', 4: 'top'}
        df['tier_name'] = df['tier_order'].map(tier_names)
        
        # Summary statistics
        print("\n=== Tier Distribution ===")
        print(df['tier_order'].value_counts().sort_index())
        print(f"\nConfidence levels:")
        print(df['tier_confidence'].value_counts())
        
        # Models with all tier levels
        models_with_tiers = df.groupby(['Make', 'Model'])['tier_order'].agg(['nunique', 'count'])
        complete_models = models_with_tiers[models_with_tiers['nunique'] >= 3]
        print(f"\nModels with 3+ tier levels: {len(complete_models)}")
        print(complete_models.head(10))
        
        return df


if __name__ == "__main__":
    # Load cleaned data - use relative paths
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_path = os.path.join(project_root, "data/processed/cars_cleaned.csv")
    
    print("Loading cleaned data...")
    df = pd.read_csv(csv_path)
    
    # Apply tier inference
    df_with_tiers = TierInference.process_dataframe(df)
    
    # Save
    output_path = os.path.join(project_root, "data/processed/cars_with_tiers.csv")
    df_with_tiers.to_csv(output_path, index=False)
    print(f"\nSaved data with tiers to {output_path}")
    
    # Show examples
    print("\n=== Sample Variants with Tiers ===")
    sample_cols = ['Make', 'Model', 'Variant', 'price_numeric', 'tier_order', 'tier_name', 'tier_confidence']
    print(df_with_tiers[sample_cols].head(10).to_string())

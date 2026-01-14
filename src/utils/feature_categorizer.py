"""
Feature categorization utilities.
Maps 140 CSV columns into 5 feature categories for car variants.
"""
import pandas as pd
import re
from typing import Dict, List, Set


class FeatureCategorizer:
    """
    Categorize car features into 5 main categories:
    - Safety: Airbags, ABS, EBD, ESP, seat belts, etc.
    - Comfort: AC, seats, adjustments, interior amenities
    - Technology: Infotainment, connectivity, displays
    - Exterior: Wheels, lights, sunroof, body features
    - Convenience: Keyless entry, sensors, automated features
    """
    
    # Feature category mapping (column name patterns → category)
    CATEGORY_MAPPING = {
        'safety': [
            'Airbags', 'ABS', 'EBD', 'ESP', 'ASR', 'Traction_Control',
            'Seat-Belt', 'Seat_Belt', 'Child_Safety', 'ISOFIX',
            'Brake', 'Hill_Assist', 'EBA', 'Engine_Immobilizer',
            'High_Speed_Alert', 'Parking_Assistance', 'Camera',
            'Sensor', 'Tyre_Pressure'
        ],
        'comfort': [
            'AC', 'Climate', 'Seat', 'Cushion', 'Armrest',
            'Cup_Holders', 'Cooled_Glove', 'Ventilation',
            'Sun_Visor', 'Height_Adjustment', 'Adjustable',
            'Heated_Seats', 'Cruise_Control'
        ],
        'technology': [
            'Touchscreen', 'Infotainment', 'Screen', 'Display',
            'CarPlay', 'Android_Auto', 'Bluetooth', 'USB',
            'Navigation', 'Audiosystem', 'FM_Radio', 'CD', 'MP3',
            'Aux', 'iPod', 'Voice_Recognition', 'Multifunction_Display',
            'Heads-Up_Display', 'Instrument_Console'
        ],
        'exterior': [
            'Sunroof', 'Alloy', 'Wheel', 'Tyre', 'LED', 'DRL',
            'Headlamp', 'Fog', 'Light', 'Mirror', 'Wiper',
            'Body_Type', 'Ground_Clearance', 'Boot_Space'
        ],
        'convenience': [
            'Keyless', 'Push_Button', 'Start_/_Stop', 'Power_Steering',
            'Power_Windows', 'Central_Locking', 'Remote',
            'Boot-lid_Opener', 'Fuel-lid_Opener', 'Auto-Dimming',
            'Rain_Sensing', 'Paddle_Shifters', 'Automatic_Headlamps',
            'Welcome_Lights', 'Ambient', 'Walk_Away', '12v_Power_Outlet',
            'Cigarette_Lighter'
        ]
    }
    
    @staticmethod
    def match_column_to_category(column_name: str) -> str:
        """
        Match a column name to its most appropriate category.
        
        Args:
            column_name: Column name from CSV
        
        Returns:
            Category name ('safety', 'comfort', 'tech', 'exterior', 'convenience', or 'specs')
        """
        column_lower = column_name.lower()
        
        # Check each category's keywords
        for category, keywords in FeatureCategorizer.CATEGORY_MAPPING.items():
            for keyword in keywords:
                if keyword.lower() in column_lower:
                    return category
        
        # Default to 'specs' for technical specifications
        return 'specs'
    
    @staticmethod
    def extract_feature_value(value) -> str:
        """
        Convert raw CSV value to human-readable feature string.
        
        Args:
            value: Raw value from CSV
        
        Returns:
            Cleaned string or 'Not Available'
        """
        if pd.isna(value) or value == '':
            return None
        
        # Handle boolean-like values
        value_str = str(value).strip()
        
        if value_str.lower() in ['yes', 'available', 'standard', 'true', '1']:
            return 'Available'
        elif value_str.lower() in ['no', 'not available', 'false', '0', 'na', 'n/a']:
            return None
        
        # Return the value as-is (e.g., "4 Airbags", "Auto AC")
        return value_str
    
    @classmethod
    def categorize_features(cls, row: pd.Series, df_columns: List[str]) -> Dict[str, List[str]]:
        """
        Extract and categorize features from a dataframe row.
        
        Args:
            row: Single row from dataframe
            df_columns: List of all column names
        
        Returns:
            Dictionary with 5 categories, each containing list of features
        """
        categorized = {
            'safety': [],
            'comfort': [],
            'technology': [],
            'exterior': [],
            'convenience': []
        }
        
        # Columns to skip (not features)
        skip_columns = {
            'Make', 'Model', 'Variant', 'Ex-Showroom_Price', 'price_numeric',
            'variant_id', 'tier_order', 'tier_name', 'tier_confidence',
            'Displacement', 'Cylinders', 'Power', 'Torque', 'Wheelbase',
            'Compression_Ratio', 'Gross_Vehicle_Weight', 'Kerb_Weight',
            'Fuel_Type', 'Gears', 'Type', 'Seating_Capacity', 'Doors',
            'Engine_Type', 'Turbocharger', 'Battery', 'Electric_Range',
            'Emission_Norm', 'Drivetrain', 'Cylinder_Configuration',
            'Engine_Location', 'Fuel_System'
        }
        
        for col in df_columns:
            if col in skip_columns:
                continue
            
            # Get feature value
            value = cls.extract_feature_value(row[col]) if col in row.index else None
            
            if value and value != 'Not Available':
                # Determine category
                category = cls.match_column_to_category(col)
                
                if category in categorized:
                    # Format feature name (remove underscores, capitalize)
                    feature_name = col.replace('_', ' ').replace('/', ' / ')
                    
                    # Create feature string
                    if value == 'Available':
                        feature_str = feature_name
                    else:
                        feature_str = f"{feature_name}: {value}"
                    
                    categorized[category].append(feature_str)
        
        return categorized
    
    @classmethod
    def create_feature_summary(cls, categorized_features: Dict[str, List[str]]) -> str:
        """
        Create a text summary of all features for embedding generation.
        
        Args:
            categorized_features: Output from categorize_features()
        
        Returns:
            Single string summarizing all features
        """
        parts = []
        
        for category, features in categorized_features.items():
            if features:
                parts.append(f"{category.title()}: {', '.join(features[:5])}")  # Limit to 5 per category
        
        return "; ".join(parts)
    
    @classmethod
    def process_dataframe(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add categorized features to dataframe.
        
        Args:
            df: Dataframe with car variant data
        
        Returns:
            Dataframe with added 'features' column (dict) and 'feature_summary' column (str)
        """
        print("\n=== Feature Categorization Process ===")
        print(f"Processing {len(df)} variants...")
        
        df_columns = df.columns.tolist()
        
        # Apply categorization to each row
        df['features'] = df.apply(
            lambda row: cls.categorize_features(row, df_columns),
            axis=1
        )
        
        # Create feature summaries
        df['feature_summary'] = df['features'].apply(cls.create_feature_summary)
        
        # Statistics
        print("\n=== Feature Statistics ===")
        
        # Count features per category
        category_counts = {cat: 0 for cat in ['safety', 'comfort', 'technology', 'exterior', 'convenience']}
        
        for features_dict in df['features']:
            for category, feature_list in features_dict.items():
                category_counts[category] += len(feature_list)
        
        print("Average features per category:")
        for category, total in category_counts.items():
            avg = total / len(df)
            print(f"  {category.title()}: {avg:.1f}")
        
        # Sample features
        print("\n=== Sample Feature Categorization ===")
        sample_row = df.iloc[0]
        print(f"Variant: {sample_row['Make']} {sample_row['Model']} {sample_row['Variant']}")
        for category, features in sample_row['features'].items():
            if features:
                print(f"\n{category.upper()}:")
                for feat in features[:5]:  # Show first 5
                    print(f"  - {feat}")
        
        return df


if __name__ == "__main__":
    # Load data with tiers - use relative paths
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_path = os.path.join(project_root, "data/processed/cars_with_tiers.csv")
    
    print("Loading data with tiers...")
    df = pd.read_csv(csv_path)
    
    # Apply feature categorization
    df_with_features = FeatureCategorizer.process_dataframe(df)
    
    # Save
    output_path = os.path.join(project_root, "data/processed/cars_final_processed.csv")
    
    # Note: features column is dict, need to save differently
    # For CSV, save as JSON string
    df_save = df_with_features.copy()
    df_save['features'] = df_save['features'].apply(str)
    
    df_save.to_csv(output_path, index=False)
    print(f"\nSaved processed data to {output_path}")
    
    # Also save as pickle to preserve dict structure
    pickle_path = os.path.join(project_root, "data/processed/cars_final_processed.pkl")
    df_with_features.to_pickle(pickle_path)
    print(f"Saved pickle format to {pickle_path}")
    
    print("\n✅ Feature categorization complete!")

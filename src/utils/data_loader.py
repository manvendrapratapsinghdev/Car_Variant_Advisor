"""
Data loading and cleaning utilities for car variants dataset.
"""
import pandas as pd
import re
import os
from typing import Dict, Optional


def parse_price(price_str: str) -> Optional[float]:
    """
    Parse price string and convert to numeric value.
    
    Args:
        price_str: Price string like "Rs. 2,92,667" or "₹2,92,667"
    
    Returns:
        Float price or None if parsing fails
    
    Examples:
        >>> parse_price("Rs. 2,92,667")
        292667.0
        >>> parse_price("₹10,50,000")
        1050000.0
    """
    if pd.isna(price_str) or not isinstance(price_str, str):
        return None
    
    # Remove currency symbols, commas, spaces
    cleaned = re.sub(r'[Rs.₹,\s]', '', price_str)
    
    try:
        return float(cleaned)
    except ValueError:
        return None


def create_variant_id(make: str, model: str, variant: str, year: int = 2024) -> str:
    """
    Create unique variant ID from make, model, variant name.
    
    Args:
        make: Car manufacturer
        model: Car model name
        variant: Variant name
        year: Model year (default 2024)
    
    Returns:
        Unique ID string in format: make_model_variant_year
    
    Examples:
        >>> create_variant_id("Maruti", "Swift", "VXi", 2024)
        'maruti_swift_vxi_2024'
    """
    # Handle NaN values
    make = str(make) if pd.notna(make) else "unknown"
    model = str(model) if pd.notna(model) else "unknown"
    variant = str(variant) if pd.notna(variant) else "unknown"
    
    # Convert to lowercase and replace spaces/special chars with underscore
    make_clean = re.sub(r'[^a-z0-9]+', '_', make.lower().strip())
    model_clean = re.sub(r'[^a-z0-9]+', '_', model.lower().strip())
    variant_clean = re.sub(r'[^a-z0-9]+', '_', variant.lower().strip())
    
    return f"{make_clean}_{model_clean}_{variant_clean}_{year}"


def load_and_clean_data(csv_path: str) -> pd.DataFrame:
    """
    Load cars_ds_final.csv and perform initial cleaning.
    
    Args:
        csv_path: Path to the CSV file
    
    Returns:
        Cleaned DataFrame with parsed prices and variant IDs
    """
    print(f"Loading data from {csv_path}...")
    
    # Load CSV
    df = pd.read_csv(csv_path, index_col=0)
    
    print(f"Loaded {len(df)} variants with {len(df.columns)} columns")
    
    # Parse price column
    print("Parsing prices...")
    df['price_numeric'] = df['Ex-Showroom_Price'].apply(parse_price)
    
    # Drop rows with missing critical fields
    before_drop = len(df)
    df = df[
        df['price_numeric'].notna() & 
        df['Make'].notna() & 
        df['Model'].notna() & 
        df['Variant'].notna()
    ].copy()
    after_drop = len(df)
    print(f"Dropped {before_drop - after_drop} variants with missing critical fields")
    
    # Create unique IDs
    print("Creating variant IDs...")
    df['variant_id'] = df.apply(
        lambda row: create_variant_id(row['Make'], row['Model'], row['Variant']),
        axis=1
    )
    
    # Check for duplicate IDs
    duplicates = df['variant_id'].duplicated().sum()
    if duplicates > 0:
        print(f"Warning: Found {duplicates} duplicate variant IDs")
        # Add counter suffix to duplicates
        df['variant_id'] = df.groupby('variant_id').cumcount().astype(str).replace('0', '')
        df['variant_id'] = df['variant_id'].apply(lambda x: x if x == '' else '_' + x)
    
    # Basic data quality checks
    print("\n=== Data Quality Summary ===")
    print(f"Total variants: {len(df)}")
    print(f"Unique makes: {df['Make'].nunique()}")
    print(f"Unique models: {df['Model'].nunique()}")
    print(f"Price range: ₹{df['price_numeric'].min():,.0f} - ₹{df['price_numeric'].max():,.0f}")
    print(f"Missing values per column:")
    missing = df.isnull().sum()
    print(missing[missing > 0].head(10))
    
    return df


def save_cleaned_data(df: pd.DataFrame, output_path: str):
    """Save cleaned dataframe to CSV."""
    df.to_csv(output_path, index=False)
    print(f"\nSaved cleaned data to {output_path}")


if __name__ == "__main__":
    # Paths
    input_csv = "/Users/d111879/Documents/Project/DEMO/Hackthon/HT_Jan_26/cars_ds_final.csv"
    output_csv = "/Users/d111879/Documents/Project/DEMO/Hackthon/HT_Jan_26/data/processed/cars_cleaned.csv"
    
    # Load and clean
    df_cleaned = load_and_clean_data(input_csv)
    
    # Save
    save_cleaned_data(df_cleaned, output_csv)
    
    # Display sample
    print("\n=== Sample Data (First 3 Rows) ===")
    print(df_cleaned[['Make', 'Model', 'Variant', 'price_numeric', 'variant_id']].head(3))

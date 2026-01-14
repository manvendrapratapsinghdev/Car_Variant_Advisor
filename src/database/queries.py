"""
Query utilities for car variant database.
Provides functions for UI dropdowns and variant retrieval.
"""
from typing import List, Dict, Optional, Tuple
from src.database.chroma_client import CarVariantDB
import ast


class VariantQueries:
    """Query functions for car variant database."""
    
    def __init__(self, db_path: str = "./data/car_variants_db"):
        """Initialize with database connection."""
        import os
        # Ensure absolute path for cloud deployment
        if not os.path.isabs(db_path):
            # If relative path, make it absolute relative to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(project_root, db_path)
        
        self.db = CarVariantDB(persist_directory=db_path)
        self.collection = self.db.get_collection()
        
        if not self.collection:
            raise Exception(f"Database collection not found at {db_path}. Run chroma_client.py first to ingest data.")
    
    def get_all_makes(self) -> List[str]:
        """
        Get list of all car manufacturers.
        
        Returns:
            Sorted list of unique make names
        """
        # Get all documents and extract unique makes
        result = self.collection.get()
        
        if not result['metadatas']:
            return []
        
        makes = set(meta['make'] for meta in result['metadatas'] if 'make' in meta)
        return sorted(list(makes))
    
    def get_models_by_make(self, make: str) -> List[str]:
        """
        Get all models for a specific make.
        
        Args:
            make: Car manufacturer name
        
        Returns:
            Sorted list of model names
        """
        result = self.collection.get(
            where={"make": make}
        )
        
        if not result['metadatas']:
            return []
        
        models = set(meta['model'] for meta in result['metadatas'] if 'model' in meta)
        return sorted(list(models))
    
    def get_variants_by_model(self, make: str, model: str) -> List[Dict[str, any]]:
        """
        Get all variants for a specific make+model combination.
        
        Args:
            make: Car manufacturer name
            model: Car model name
        
        Returns:
            List of dicts with variant_name, tier_order, tier_name, price
        """
        result = self.collection.get(
            where={"$and": [{"make": make}, {"model": model}]}
        )
        
        if not result['metadatas']:
            return []
        
        variants = []
        for meta in result['metadatas']:
            variants.append({
                'variant_name': meta['variant_name'],
                'tier_order': meta['tier_order'],
                'tier_name': meta['tier_name'],
                'price': meta['price']
            })
        
        # Sort by tier_order
        variants.sort(key=lambda x: x['tier_order'])
        return variants
    
    def get_variant_details(self, make: str, model: str, variant_name: str) -> Optional[Dict]:
        """
        Get complete details for a specific variant.
        
        Args:
            make: Car manufacturer name
            model: Car model name
            variant_name: Variant name
        
        Returns:
            Dict with all variant information or None if not found
        """
        result = self.collection.get(
            where={"$and": [
                {"make": make},
                {"model": model},
                {"variant_name": variant_name}
            ]},
            limit=1
        )
        
        if not result['metadatas']:
            return None
        
        meta = result['metadatas'][0]
        
        # Parse feature strings back to lists
        features = {
            'safety': self._parse_feature_string(meta.get('features_safety', '[]')),
            'comfort': self._parse_feature_string(meta.get('features_comfort', '[]')),
            'technology': self._parse_feature_string(meta.get('features_technology', '[]')),
            'exterior': self._parse_feature_string(meta.get('features_exterior', '[]')),
            'convenience': self._parse_feature_string(meta.get('features_convenience', '[]')),
        }
        
        return {
            'make': meta['make'],
            'model': meta['model'],
            'variant_name': meta['variant_name'],
            'price': meta['price'],
            'tier_order': meta['tier_order'],
            'tier_name': meta['tier_name'],
            'tier_confidence': meta['tier_confidence'],
            'features': features,
            'fuel_type': meta.get('fuel_type', ''),
            'body_type': meta.get('body_type', ''),
            'seating_capacity': meta.get('seating_capacity', ''),
        }
    
    def find_upgrade_options(self, make: str, model: str, current_tier: int, limit: int = 3) -> List[Dict]:
        """
        Find upgrade options (higher tier variants) for a given variant.
        
        Args:
            make: Car manufacturer name
            model: Car model name
            current_tier: Current variant's tier_order (1-4)
            limit: Maximum number of upgrades to return (default 3, configurable 2-3)
        
        Returns:
            List of variant details for upgrade options
        """
        # Get all variants for this make+model with higher tier
        result = self.collection.get(
            where={"$and": [
                {"make": make},
                {"model": model},
                {"tier_order": {"$gt": current_tier}}
            ]}
        )
        
        if not result['metadatas']:
            return []
        
        # Sort by tier_order and take first 'limit' items
        upgrades = sorted(result['metadatas'], key=lambda x: x['tier_order'])[:limit]
        
        # Get full details for each upgrade
        upgrade_details = []
        for meta in upgrades:
            details = self.get_variant_details(make, model, meta['variant_name'])
            if details:
                upgrade_details.append(details)
        
        return upgrade_details
    
    @staticmethod
    def _parse_feature_string(feature_str: str) -> List[str]:
        """Parse feature string back to list."""
        try:
            # Handle truncated strings (ending with ...)
            if feature_str.endswith('...') or not feature_str.endswith(']'):
                feature_str = feature_str.rstrip('...') + ']'
            
            # Use ast.literal_eval to safely parse string representation of list
            features = ast.literal_eval(feature_str)
            return features if isinstance(features, list) else []
        except:
            return []


# Module-level convenience functions
_queries = None

def init_queries(db_path: str = "./data/car_variants_db"):
    """Initialize query module."""
    global _queries
    _queries = VariantQueries(db_path)

def get_all_makes() -> List[str]:
    """Get all car makes."""
    if not _queries:
        init_queries()
    return _queries.get_all_makes()

def get_models_by_make(make: str) -> List[str]:
    """Get models for a make."""
    if not _queries:
        init_queries()
    return _queries.get_models_by_make(make)

def get_variants_by_model(make: str, model: str) -> List[Dict]:
    """Get variants for a model."""
    if not _queries:
        init_queries()
    return _queries.get_variants_by_model(make, model)

def get_variant_details(make: str, model: str, variant_name: str) -> Optional[Dict]:
    """Get full variant details."""
    if not _queries:
        init_queries()
    return _queries.get_variant_details(make, model, variant_name)

def find_upgrade_options(make: str, model: str, current_tier: int, limit: int = 3) -> List[Dict]:
    """Find upgrade options with configurable limit (2-3)."""
    if not _queries:
        init_queries()
    return _queries.find_upgrade_options(make, model, current_tier, limit)


if __name__ == "__main__":
    # Test queries
    print("=== Testing Query Utilities ===\n")
    
    init_queries("/Users/d111879/Documents/Project/DEMO/Hackthon/HT_Jan_26/data/car_variants_db")
    
    # Test 1: Get all makes
    makes = get_all_makes()
    print(f"1. Total makes: {len(makes)}")
    print(f"   Sample: {makes[:5]}\n")
    
    # Test 2: Get models for Maruti
    models = get_models_by_make("Maruti")
    print(f"2. Maruti models: {len(models)}")
    print(f"   Models: {models}\n")
    
    # Test 3: Get variants for Swift
    variants = get_variants_by_model("Maruti", "Swift")
    print(f"3. Swift variants: {len(variants)}")
    for v in variants:
        print(f"   - {v['variant_name']} ({v['tier_name']}) - ₹{v['price']:,.0f}")
    
    # Test 4: Get details for specific variant
    details = get_variant_details("Maruti", "Swift", "Vdi")
    if details:
        print(f"\n4. Swift Vdi details:")
        print(f"   Price: ₹{details['price']:,.0f}")
        print(f"   Tier: {details['tier_name']} (order: {details['tier_order']})")
        print(f"   Safety features: {len(details['features']['safety'])}")
        print(f"   Sample: {details['features']['safety'][:3]}")
    
    # Test 5: Find upgrades
    if details:
        upgrades = find_upgrade_options("Maruti", "Swift", details['tier_order'])
        print(f"\n5. Upgrade options for Swift Vdi:")
        for up in upgrades:
            print(f"   - {up['variant_name']} ({up['tier_name']}) - ₹{up['price']:,.0f}")
            print(f"     Features: {len(up['features']['safety'])} safety, {len(up['features']['technology'])} tech")
    
    print("\n✅ Query utilities working!")

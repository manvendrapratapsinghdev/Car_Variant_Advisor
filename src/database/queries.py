"""Query utilities for car variant database.

Provides functions for UI dropdowns and variant retrieval.
"""

from typing import List, Dict, Optional, Tuple, Iterable, Any
from src.database.chroma_client import CarVariantDB
import ast


class VariantQueries:
    """Query functions for car variant database."""
    
    def __init__(self, db_path: str = "./data/car_variants_db"):
        """Initialize with database connection."""
        self.db = CarVariantDB(persist_directory=db_path)
        self.collection = self.db.get_collection()
        
        if not self.collection:
            raise RuntimeError("Database collection not found. Run chroma_client.py first to ingest data.")
    
    def get_all_makes(self) -> List[str]:
        """
        Get list of all car manufacturers.
        
        Returns:
            Sorted list of unique make names
        """
        # Get all documents and extract unique makes
        result = self.collection.get(include=["metadatas"])
        
        if not result['metadatas']:
            return []
        
        makes = {meta['make'] for meta in result['metadatas'] if 'make' in meta}
        return sorted(makes)
    
    def get_models_by_make(self, make: str) -> List[str]:
        """
        Get all models for a specific make.
        
        Args:
            make: Car manufacturer name
        
        Returns:
            Sorted list of model names
        """
        result = self.collection.get(where={"make": make}, include=["metadatas"])
        
        if not result['metadatas']:
            return []
        
        models = {meta['model'] for meta in result['metadatas'] if 'model' in meta}
        return sorted(models)
    
    def get_variants_by_model(self, make: str, model: str) -> List[Dict[str, any]]:
        """
        Get all variants for a specific make+model combination.
        
        Args:
            make: Car manufacturer name
            model: Car model name
        
        Returns:
            List of dicts with variant_name, tier_order, tier_name, price
        """
        result = self.collection.get(where={"$and": [{"make": make}, {"model": model}]}, include=["metadatas"])
        
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

    def get_price_range(self, make: Optional[str] = None, model: Optional[str] = None) -> Tuple[Optional[float], Optional[float]]:
        """Get min/max price from metadata (in rupees).

        Args:
            make: Optional make constraint
            model: Optional model constraint (only meaningful with make)

        Returns:
            (min_price, max_price) or (None, None) if no records
        """
        where = self._build_where_clause(make=make, model=model)
        result = self.collection.get(where=where, include=["metadatas"]) if where else self.collection.get(include=["metadatas"])
        metadatas = result.get('metadatas') or []
        prices = [meta.get('price') for meta in metadatas if isinstance(meta, dict) and isinstance(meta.get('price'), (int, float))]
        if not prices:
            return None, None
        return float(min(prices)), float(max(prices))

    def find_variants_by_budget(
        self,
        budget_rupees: float,
        pct: float,
        make: Optional[str] = None,
        model: Optional[str] = None,
        k_min: int = 2,
        k_max: int = 5,
        expand_step_pct: float = 5.0,
        max_pct: float = 50.0,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Find 2–5 candidate variants near a budget.

        Behavior:
        - Filters by price range computed from budget +/- pct
        - Optional make/model constraints
        - Sorts by nearest price to budget (stable ordering on ties)
        - Dedupes while filling using (make, model, variant_name)
        - Auto-expands margin if fewer than k_min candidates
        - If still empty, falls back to nearest-lower and nearest-higher priced variants

        Returns:
            (candidates, meta)
            meta includes flags: expanded (bool), used_fallback (bool), effective_pct (float)
        """
        if budget_rupees is None or not isinstance(budget_rupees, (int, float)):
            return [], {"expanded": False, "used_fallback": False, "effective_pct": pct}

        budget_rupees = float(budget_rupees)
        pct = float(pct)
        k_min = max(0, int(k_min))
        k_max = max(k_min, int(k_max))

        expanded = False
        used_fallback = False
        effective_pct = pct

        candidates: List[Dict[str, Any]] = []
        while True:
            min_price, max_price = self._budget_bounds(budget_rupees, effective_pct)
            metadatas = self._get_metadatas_in_price_range(min_price, max_price, make=make, model=model)
            candidates = self._select_candidates_from_metadatas(metadatas, budget_rupees, k_max=k_max)

            if len(candidates) >= k_min:
                break

            next_pct = effective_pct + float(expand_step_pct)
            if next_pct > float(max_pct):
                break

            expanded = True
            effective_pct = next_pct

        if not candidates:
            used_fallback = True
            candidates = self._fallback_nearest_neighbors(budget_rupees, make=make, model=model, k_max=k_max)

        return candidates, {"expanded": expanded, "used_fallback": used_fallback, "effective_pct": effective_pct}
    
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
            limit=1,
            include=["metadatas"],
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
            ]},
            include=["metadatas"],
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
        except Exception:
            return []

    @staticmethod
    def _budget_bounds(budget_rupees: float, pct: float) -> Tuple[float, float]:
        pct = max(0.0, float(pct))
        delta = (pct / 100.0) * float(budget_rupees)
        return float(budget_rupees - delta), float(budget_rupees + delta)

    @staticmethod
    def _dedupe_key(meta: Dict[str, Any]) -> Tuple[str, str, str]:
        return (
            str(meta.get('make', '')).strip(),
            str(meta.get('model', '')).strip(),
            str(meta.get('variant_name', '')).strip(),
        )

    @staticmethod
    def _select_candidates_from_metadatas(
        metadatas: Iterable[Dict[str, Any]],
        budget_rupees: float,
        k_max: int,
    ) -> List[Dict[str, Any]]:
        """Pure selection logic: sort by nearest price, stable on ties, and dedupe while filling."""
        metas = [m for m in metadatas if isinstance(m, dict) and isinstance(m.get('price'), (int, float))]
        indexed = list(enumerate(metas))
        indexed.sort(key=lambda pair: (abs(float(pair[1]['price']) - float(budget_rupees)), pair[0]))

        selected: List[Dict[str, Any]] = []
        seen = set()
        for _, meta in indexed:
            key = VariantQueries._dedupe_key(meta)
            if key in seen:
                continue
            seen.add(key)
            selected.append(meta)
            if len(selected) >= int(k_max):
                break
        return selected

    def _build_where_clause(self, make: Optional[str] = None, model: Optional[str] = None, price_filter: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        clauses: List[Dict[str, Any]] = []
        if make:
            clauses.append({"make": make})
        if model:
            clauses.append({"model": model})
        if price_filter:
            clauses.append({"price": price_filter})
        if not clauses:
            return None
        if len(clauses) == 1:
            return clauses[0]
        return {"$and": clauses}

    def _get_metadatas_in_price_range(
        self,
        min_price: float,
        max_price: float,
        make: Optional[str] = None,
        model: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        # Chroma's where syntax expects operator expressions to contain exactly one operator.
        # So a range must be expressed as an $and of two separate comparisons.
        clauses: List[Dict[str, Any]] = []
        if make:
            clauses.append({"make": make})
        if model:
            clauses.append({"model": model})
        clauses.append({"price": {"$gte": float(min_price)}})
        clauses.append({"price": {"$lte": float(max_price)}})

        if not clauses:
            where = None
        elif len(clauses) == 1:
            where = clauses[0]
        else:
            where = {"$and": clauses}

        result = self.collection.get(where=where, include=["metadatas"]) if where else self.collection.get(include=["metadatas"])
        return result.get('metadatas') or []

    def _fallback_nearest_neighbors(
        self,
        budget_rupees: float,
        make: Optional[str] = None,
        model: Optional[str] = None,
        k_max: int = 5,
    ) -> List[Dict[str, Any]]:
        """Fallback when range query is empty: return nearest lower + nearest higher (then fill outward if needed)."""
        where = self._build_where_clause(make=make, model=model)
        result = self.collection.get(where=where, include=["metadatas"]) if where else self.collection.get(include=["metadatas"])
        metadatas = [
            m
            for m in (result.get('metadatas') or [])
            if isinstance(m, dict) and isinstance(m.get('price'), (int, float))
        ]
        if not metadatas:
            return []

        budget = float(budget_rupees)
        all_sorted = self._sorted_by_distance(metadatas, budget)

        picked: List[Dict[str, Any]] = []
        seen = set()
        self._append_first_match(picked, seen, all_sorted, predicate=lambda m: float(m['price']) <= budget)
        self._append_first_match(picked, seen, all_sorted, predicate=lambda m: float(m['price']) >= budget)

        if len(picked) >= int(k_max):
            return picked[: int(k_max)]

        for meta in all_sorted:
            key = self._dedupe_key(meta)
            if key in seen:
                continue
            seen.add(key)
            picked.append(meta)
            if len(picked) >= int(k_max):
                break

        return picked

    @staticmethod
    def _sorted_by_distance(metadatas: List[Dict[str, Any]], budget_rupees: float) -> List[Dict[str, Any]]:
        indexed = list(enumerate(metadatas))
        indexed.sort(key=lambda pair: (abs(float(pair[1]['price']) - float(budget_rupees)), pair[0]))
        return [meta for _, meta in indexed]

    def _append_first_match(
        self,
        picked: List[Dict[str, Any]],
        seen: set,
        sorted_metas: List[Dict[str, Any]],
        predicate,
    ) -> None:
        for meta in sorted_metas:
            if not predicate(meta):
                continue
            key = self._dedupe_key(meta)
            if key in seen:
                continue
            seen.add(key)
            picked.append(meta)
            return


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


def get_price_range(make: Optional[str] = None, model: Optional[str] = None) -> Tuple[Optional[float], Optional[float]]:
    """Get min/max price in rupees for optional constraints."""
    if not _queries:
        init_queries()
    return _queries.get_price_range(make=make, model=model)


def find_variants_by_budget(
    budget_rupees: float,
    pct: float,
    make: Optional[str] = None,
    model: Optional[str] = None,
    k_min: int = 2,
    k_max: int = 5,
    expand_step_pct: float = 5.0,
    max_pct: float = 50.0,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Module-level wrapper for budget-based candidate search."""
    if not _queries:
        init_queries()
    return _queries.find_variants_by_budget(
        budget_rupees=budget_rupees,
        pct=pct,
        make=make,
        model=model,
        k_min=k_min,
        k_max=k_max,
        expand_step_pct=expand_step_pct,
        max_pct=max_pct,
    )


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
        print("\n4. Swift Vdi details:")
        print(f"   Price: ₹{details['price']:,.0f}")
        print(f"   Tier: {details['tier_name']} (order: {details['tier_order']})")
        print(f"   Safety features: {len(details['features']['safety'])}")
        print(f"   Sample: {details['features']['safety'][:3]}")
    
    # Test 5: Find upgrades
    if details:
        upgrades = find_upgrade_options("Maruti", "Swift", details['tier_order'])
        print("\n5. Upgrade options for Swift Vdi:")
        for up in upgrades:
            print(f"   - {up['variant_name']} ({up['tier_name']}) - ₹{up['price']:,.0f}")
            print(f"     Features: {len(up['features']['safety'])} safety, {len(up['features']['technology'])} tech")
    
    print("\n✅ Query utilities working!")

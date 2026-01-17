import unittest

from src.database.queries import VariantQueries


class _FakeVariantQueries(VariantQueries):
    """A test double that avoids connecting to Chroma.

    It provides in-memory metadata lists and reuses the selection logic from VariantQueries.
    """

    def __init__(self, metadatas):
        # Skip DB initialization
        self._metadatas = list(metadatas)

    def _get_metadatas_in_price_range(self, min_price, max_price, make=None, model=None):
        out = []
        for meta in self._metadatas:
            if make and meta.get("make") != make:
                continue
            if model and meta.get("model") != model:
                continue
            price = meta.get("price")
            if not isinstance(price, (int, float)):
                continue
            if float(min_price) <= float(price) <= float(max_price):
                out.append(meta)
        return out

    def _fallback_nearest_neighbors(self, budget_rupees, make=None, model=None, k_max=5):
        filtered = []
        for meta in self._metadatas:
            if make and meta.get("make") != make:
                continue
            if model and meta.get("model") != model:
                continue
            if isinstance(meta.get("price"), (int, float)):
                filtered.append(meta)

        if not filtered:
            return []

        all_sorted = self._sorted_by_distance(filtered, float(budget_rupees))

        picked = []
        seen = set()
        self._append_first_match(picked, seen, all_sorted, predicate=lambda m: float(m["price"]) <= float(budget_rupees))
        self._append_first_match(picked, seen, all_sorted, predicate=lambda m: float(m["price"]) >= float(budget_rupees))

        for meta in all_sorted:
            key = self._dedupe_key(meta)
            if key in seen:
                continue
            seen.add(key)
            picked.append(meta)
            if len(picked) >= int(k_max):
                break

        return picked


class BudgetSearchTests(unittest.TestCase):
    def test_budget_bounds(self):
        min_p, max_p = VariantQueries._budget_bounds(600_000, 10)
        self.assertEqual(min_p, 540_000.0)
        self.assertEqual(max_p, 660_000.0)

    def test_select_candidates_stable_ties_and_dedupe(self):
        # Two entries equally close to budget; order should be stable based on input order.
        # Also include a duplicate variant that should be deduped.
        metas = [
            {"make": "A", "model": "M", "variant_name": "V1", "price": 100},
            {"make": "A", "model": "M", "variant_name": "V2", "price": 110},
            {"make": "A", "model": "M", "variant_name": "V2", "price": 110},
        ]
        selected = VariantQueries._select_candidates_from_metadatas(metas, budget_rupees=105, k_max=5)
        self.assertEqual([m["variant_name"] for m in selected], ["V1", "V2"])

    def test_find_variants_by_budget_auto_expands(self):
        # Budget=100, initial pct=5 gives 95-105 (none).
        # Expands until pct=30 gives 70-130 (includes 120 and 130 => 2 candidates).
        metas = [
            {"make": "X", "model": "A", "variant_name": "L", "price": 120},
            {"make": "X", "model": "A", "variant_name": "U", "price": 130},
        ]
        q = _FakeVariantQueries(metas)
        candidates, meta = q.find_variants_by_budget(
            budget_rupees=100,
            pct=5,
            make=None,
            model=None,
            k_min=2,
            k_max=5,
            expand_step_pct=5,
            max_pct=50,
        )
        self.assertTrue(meta["expanded"])
        self.assertFalse(meta["used_fallback"])
        self.assertEqual(meta["effective_pct"], 30.0)
        self.assertEqual([c["variant_name"] for c in candidates], ["L", "U"])

    def test_find_variants_by_budget_fallback_nearest(self):
        metas = [
            {"make": "X", "model": "A", "variant_name": "LOW", "price": 50},
            {"make": "X", "model": "A", "variant_name": "HIGH", "price": 200},
            {"make": "X", "model": "A", "variant_name": "HIGHER", "price": 250},
        ]
        q = _FakeVariantQueries(metas)
        candidates, meta = q.find_variants_by_budget(
            budget_rupees=100,
            pct=0,
            make=None,
            model=None,
            k_min=2,
            k_max=5,
            expand_step_pct=5,
            max_pct=0,
        )
        self.assertTrue(meta["used_fallback"])
        # Fallback should include the nearest lower and nearest higher.
        names = [c["variant_name"] for c in candidates]
        self.assertIn("LOW", names)
        self.assertIn("HIGH", names)


if __name__ == "__main__":
    unittest.main()

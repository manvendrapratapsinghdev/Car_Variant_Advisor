#!/usr/bin/env python3
"""Automated test for budget search functionality."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.queries import (
    search_variants_by_budget,
    get_price_range,
    init_queries,
)


def test_budget_search():
    """Test budget search with various parameters."""
    init_queries('./data/car_variants_db')
    
    # Get price range
    min_p, max_p = get_price_range()
    print(f"Database price range: ₹{min_p:,.0f} - ₹{max_p:,.0f}")
    print(f"In lakhs: {min_p/100000:.2f}L - {max_p/100000:.2f}L")
    print()
    
    test_cases = [
        # (budget, margin, count, brand, model, expected_min_results, description)
        (960000, 10, 3, None, None, 1, "9.60L, no filters"),
        (600000, 10, 3, None, None, 1, "6.00L, no filters"),
        (800000, 10, 3, None, None, 1, "8.00L, no filters"),
        (1000000, 10, 3, None, None, 1, "10.00L, no filters"),
        (500000, 10, 3, None, None, 1, "5.00L, no filters"),
        (1500000, 10, 3, None, None, 1, "15.00L, no filters"),
        (960000, 10, 3, "Maruti Suzuki", None, 0, "9.60L, Maruti only (may be 0)"),
        (800000, 10, 3, "Maruti Suzuki", None, 1, "8.00L, Maruti only"),
        # Edge cases - should NOT pass brand/model as strings like "All brands"
        (960000, 10, 3, "All brands", None, 0, "WRONG: 'All brands' as string - should be None"),
    ]
    
    passed = 0
    failed = 0
    
    for budget, margin, count, brand, model, min_expected, desc in test_cases:
        results, meta = search_variants_by_budget(
            budget_rupees=budget,
            margin_pct=margin,
            count=count,
            brand=brand,
            model=model,
        )
        
        status = "✅ PASS" if len(results) >= min_expected else "❌ FAIL"
        if "WRONG" in desc:
            # This is expected to fail to show the bug
            status = "⚠️ EXPECTED" if len(results) == 0 else "❌ BUG FIXED"
        
        print(f"{status}: {desc}")
        print(f"       Budget: ₹{budget/100000:.2f}L, Margin: {margin}%, Count: {count}")
        print(f"       Brand: {brand!r}, Model: {model!r}")
        print(f"       Results: {len(results)}, Meta: {meta}")
        if results:
            for r in results[:3]:
                print(f"         - {r['make']} {r['model']} {r['variant_name']} @ ₹{r['price']:,.0f}")
        print()
        
        if "WRONG" not in desc:
            if len(results) >= min_expected:
                passed += 1
            else:
                failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("\n❌ SOME TESTS FAILED!")
        sys.exit(1)
    else:
        print("\n✅ ALL TESTS PASSED!")
        sys.exit(0)


if __name__ == "__main__":
    test_budget_search()

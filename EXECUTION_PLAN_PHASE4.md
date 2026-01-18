# Execution Plan - Phase 4: Text-Based Natural Language Search

## Overview

Enable intelligent natural language search where Gemini parses free-form user queries into structured parameters. Users can describe their requirements in plain English (e.g., "I want a Maruti or Mahindra car, 5-6 lacs budget, with 6 airbags") and the system extracts and applies search filters automatically.

## Search Priority Hierarchy

| Priority | Parameter | Behavior | If Absent |
|----------|-----------|----------|-----------|
| 1 | **Price** | Strict filter within range | No price filter (all prices) |
| 2 | **Brand(s)** | OR condition for multiple brands | All brands in price range |
| 3 | **Model** | Filter specific model | All models (requires brand) |
| 4 | **Features** | Ranking score, not exclusion | Show all matches |

## Budget Parsing Rules

| User Input | Parsed Output | Applied Range |
|------------|---------------|---------------|
| "5 lakh" | `budget_min=500000, budget_max=null` | 450,000 - 550,000 (10% margin) |
| "5-6 lakh" | `budget_min=500000, budget_max=600000` | 500,000 - 600,000 (exact) |
| No mention | `budget_min=null, budget_max=null` | All prices |

## Stories

---

### Story 4.1: NLP Query Parser in Gemini Agent

**Description:** Add `parse_search_query(text: str) -> dict` method to `DirectGeminiAgent` that uses Gemini's JSON output mode to extract structured search parameters from natural language.

**File:** `src/agent/direct_gemini_agent.py`

**Output Schema:**
```json
{
  "budget_min": 500000,
  "budget_max": 600000,
  "brands": ["Maruti", "Mahindra"],
  "model": null,
  "fuel_type": null,
  "body_type": null,
  "seating_capacity": null,
  "transmission": null,
  "required_features": ["6 airbags", "sunroof", "Android Auto"]
}
```

**Acceptance Criteria:**
- [x] Method returns valid JSON with all fields (null for unspecified)
- [x] Multiple brands parsed as list
- [x] Budget range correctly identified (single value vs range)
- [x] Features extracted as list of strings
- [x] Error handling returns None on parse failure

**Status:** ✅ Completed

---

### Story 4.2: Extended Search Function with Requirements

**Description:** Create `search_variants_by_requirements()` function that applies priority-based filtering: Price → Brand(s) → Model → Features.

**File:** `src/database/queries.py`

**Parameters:**
- `budget_min: Optional[float]`
- `budget_max: Optional[float]`
- `margin_pct: float = 10.0` (applied only when budget_max is null)
- `brands: Optional[List[str]]`
- `model: Optional[str]`
- `fuel_type: Optional[str]`
- `body_type: Optional[str]`
- `seating_capacity: Optional[int]`
- `transmission: Optional[str]`
- `required_features: Optional[List[str]]`
- `count: int = 3`

**Acceptance Criteria:**
- [x] Price filter applied first (strict match)
- [x] Multiple brands filtered with OR condition
- [x] Model filter requires brand to be set
- [x] Features used for ranking, not exclusion
- [x] Returns same format as existing `search_variants_by_budget()`

**Status:** ✅ Completed

---

### Story 4.3: Feature Ranking Scorer

**Description:** Implement feature matching logic that scores variants by counting how many `required_features` they contain.

**File:** `src/database/queries.py`

**Logic:**
1. For each variant, check `features_safety`, `features_comfort`, `features_technology`, `features_exterior`, `features_convenience`
2. Count matches (case-insensitive, partial match allowed)
3. Add `feature_score` to metadata
4. Sort results by feature_score descending

**Acceptance Criteria:**
- [x] Partial text match works (e.g., "airbag" matches "6 Airbags")
- [x] Score added to each result's metadata
- [x] Results sorted by score within filtered set
- [x] No results excluded due to missing features

**Status:** ✅ Completed

---

### Story 4.4: Empty Results Handling (Phase 3 Rule)

**Description:** When no exact matches found, relax constraints progressively and show nearby alternatives.

**File:** `src/database/queries.py`

**Relaxation Order:**
1. Remove feature ranking requirement
2. Expand price range by additional 10%
3. Remove model filter
4. Remove brand filter (keep price only)

**Acceptance Criteria:**
- [x] Returns `meta.relaxed = true` when constraints relaxed
- [x] Shows message indicating relaxation
- [x] Maintains minimum result count (3 by default)

**Status:** ✅ Completed

---

### Story 4.5: Wire Text Search to UI

**Description:** Connect the existing `search_query` text area to the NLP parser and new search function.

**File:** `app/streamlit_app.py`

**Logic:**
1. If `search_query` has text when "🔎 Search Cars" clicked:
   - Call `parse_search_query(search_query)`
   - If parse succeeds → call `search_variants_by_requirements()`
   - If parse fails → show error message
2. If `search_query` empty:
   - Use existing dropdown/slider values
   - Call existing `search_variants_by_budget()`

**Acceptance Criteria:**
- [x] Text search takes priority over dropdown selections
- [x] Parse errors show user-friendly message
- [x] Results displayed using existing variant card UI
- [x] Loading state shown during Gemini parsing

**Status:** ✅ Completed

---

### Story 4.6: Error Handling for Gemini Parsing

**Description:** Graceful error handling when Gemini fails to parse or returns invalid JSON.

**Files:** `src/agent/direct_gemini_agent.py`, `app/streamlit_app.py`

**Error Cases:**
- Gemini API timeout/failure
- Invalid JSON response
- Missing required fields

**Acceptance Criteria:**
- [x] Error message: "Couldn't understand your query, please try rephrasing"
- [x] Text area highlighted on error
- [x] Fallback to manual search still works
- [x] No crash on malformed input

**Status:** ✅ Completed

---

## Implementation Order

1. Story 4.1 - NLP Parser (foundation)
2. Story 4.2 - Search Function (core logic)
3. Story 4.3 - Feature Ranking (enhancement)
4. Story 4.4 - Empty Results (UX)
5. Story 4.5 - UI Wiring (integration)
6. Story 4.6 - Error Handling (polish)

## Dependencies

- Gemini API (`google-generativeai` package) - already installed
- ChromaDB - already configured
- Existing `search_variants_by_budget()` function - reference implementation

## Testing Scenarios

| Query | Expected Extraction |
|-------|---------------------|
| "I want a Maruti car under 5 lakh" | `brands: ["Maruti"], budget_max: 500000` |
| "Mahindra or Tata SUV, 8-10 lacs, diesel" | `brands: ["Mahindra", "Tata"], budget_min: 800000, budget_max: 1000000, body_type: "SUV", fuel_type: "Diesel"` |
| "7 seater with sunroof and 6 airbags" | `seating_capacity: 7, required_features: ["sunroof", "6 airbags"]` |
| "automatic transmission car" | `transmission: "Automatic"` |

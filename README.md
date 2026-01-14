# 🚗 AI Car Variant Advisor

An intelligent recommendation system that helps car buyers find the perfect variant upgrade within their budget.

## Problem Statement

Car buyers get confused choosing between variants of the same model (e.g., Swift LXi vs VXi vs ZXi+). They don't know if paying ₹50k-₹2L extra is worth the additional features.

## Solution

An AI-powered advisor that:
- Shows your selected variant with all features
- Suggests 2 better variants from the same model
- Explains exactly what extra features you get for the additional cost
- Calculates value per feature

## Features

### Phase 1 (Core Functionality)
✅ **LangChain + Gemini AI Integration** - Intelligent agent with natural language reasoning  
✅ **1,201 Car Variants** across 39 brands and 235 models  
✅ **Smart Tier Classification** (base/mid/high/top)  
✅ **5 Feature Categories** (Safety, Comfort, Technology, Exterior, Convenience)  
✅ **Tool-Based Agent** with get_variant_details, find_upgrades, calculate_difference  
✅ **Reasoning Transparency** - Shows agent's thinking process  
✅ **Dual Mode** - LangChain agent OR fast simple recommender (fallback)  
✅ **Clean, Intuitive UI** built with Streamlit  
✅ **Voice Assistant** - Text-to-speech recommendations with male/female voice options

### Phase 2 (Enhanced Analytics & UX) - NEW! 🎉
✅ **Configurable Recommendations** - User-adjustable slider for 2-3 variant suggestions  
✅ **AI Comparative Scoring** - Gemini provides 1-10 value scores with justifications  
✅ **Differential Feature Matrix** - Visual table showing ONLY NEW features in upgrades  
✅ **Interactive Plotly Charts** - Features vs Price correlation with hover tooltips  
✅ **Restructured UI** - Settings in sidebar, workflow collapsed by default, cleaner layout  
✅ **Improved TTS Experience** - Non-blocking audio generation, transcript shows first  
✅ **Tier-Based Color Coding** - Visual differentiation (blue/green/orange/red)  
✅ **Automatic Score Sorting** - Best value options ranked first  

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

1. **Clone and navigate to project**
```bash
cd /Users/d111879/Documents/Project/DEMO/Hackthon/HT_Jan_26
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure Gemini API (for LangChain agent)**

**Option A: Use setup script**
```bash
./setup.sh
```

**Option B: Manual setup**
```bash
cp .env.example .env
# Edit .env and add your Gemini API key from https://makersuite.google.com/app/apikey
```

**Option C: Skip API (uses simple recommender)**
- App works perfectly without API key, just uses deterministic logic instead of LLM

4. **Run the app**
```bash
PYTHONPATH=$(pwd):$PYTHONPATH streamlit run app/streamlit_app.py
```

5. **Open browser**
```
http://localhost:8501
```

## Using Phase 2 Features

### 🎯 Customizing Recommendations
1. Open the **left sidebar**
2. Use the **"Number of upgrades"** slider to select 2 or 3 recommendations
3. Choose your preferred **AI voice** (Female/Male) for audio playback

### 📊 Understanding AI Scores
- Each upgrade option displays an **AI Score (1-10)** indicating value for money
- Scores are automatically calculated by Gemini AI
- Higher scores = better value proposition
- Options are ranked with best value first

### 🔍 Exploring Feature Comparisons
- Scroll to the **Feature Comparison Matrix** below upgrade options
- ✅ Green checkmarks = Feature available in this variant
- ❌ Red crosses = Feature not available
- Only **NEW features** (differential) are shown for clarity

### 📈 Visualizing Value
- Check the **Features vs Price Chart** for visual insights
- Hover over data points to see:
  - Variant name and tier
  - Exact price and feature count
  - Top 5 key features
- Trend line shows overall value correlation

### 🎙️ Audio Recommendations
- Transcript appears **immediately** (no waiting)
- Audio generates in the background (you can scroll while waiting)
- Audio player appears at the **bottom** when ready
- Status messages keep you informed

## Project Structure

```
HT_Jan_26/
├── app/
│   └── streamlit_app.py          # Streamlit UI
├── src/
│   ├── database/
│   │   ├── chroma_client.py      # ChromaDB setup
│   │   └── queries.py            # Query utilities
│   ├── agent/
│   │   ├── simple_recommender.py # Recommendation engine
│   │   ├── direct_gemini_agent.py # Gemini AI integration
│   │   ├── nlg_engine.py         # Natural language generation
│   │   └── voice_assistant.py    # Text-to-speech
│   └── utils/
│       ├── data_loader.py        # CSV loading/cleaning
│       ├── tier_inference.py     # Variant tier classification
│       ├── feature_categorizer.py # Feature organization
│       ├── feature_comparison.py  # Comparison matrix builder (Phase 2)
│       └── feature_price_chart.py # Plotly visualization (Phase 2)
├── data/
│   ├── cars_ds_final.csv         # Raw data (1,277 variants)
│   ├── processed/                # Cleaned data
│   └── car_variants_db/          # ChromaDB storage
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
└── README.md                     # This file
```

## How It Works

### 1. Data Processing Pipeline

```
Raw CSV (1,277 variants)
    ↓
Price Parsing & ID Generation
    ↓
Tier Inference (pattern matching + price-based)
    ↓
Feature Categorization (140 columns → 5 categories)
    ↓
ChromaDB Ingestion (1,201 clean variants)
```

### 2. Recommendation Logic

```
User selects variant
    ↓
Fetch variant details from ChromaDB
    ↓
Find higher tier variants (same make/model)
    ↓
Calculate feature differences (set operations)
    ↓
Compute cost per feature
    ↓
Present top 2 upgrade options
```

### 3. UI Flow

```
Brand dropdown → Model dropdown → Variant dropdown
    ↓
Show selected variant with features
    ↓
Display 2 upgrade options with:
  - Price difference
  - New features list
  - Value assessment (₹ per feature)
    ↓
Collapsible AI reasoning trace
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | Python 3.11 | Core logic |
| **Database** | ChromaDB | Vector store for variants |
| **UI** | Streamlit | Interactive web app |
| **Data Processing** | Pandas, NumPy | Data manipulation |
| **Recommendation** | Custom algorithm | Feature comparison |

## Data Statistics

- **Total Variants**: 1,201 (filtered from 1,277)
- **Brands**: 39 manufacturers
- **Models**: 235 car models
- **Price Range**: ₹2.36L - ₹21.2Cr
- **Tier Distribution**:
  - Base: 342 variants (28%)
  - Mid: 311 variants (26%)
  - High: 331 variants (28%)
  - Top: 217 variants (18%)

## Key Algorithms

### Tier Inference

Uses pattern matching on variant names:
- **Maruti**: LXi (base) → VXi (mid) → ZXi (high) → ZXi+ (top)
- **Hyundai**: E (base) → S (mid) → SX (high) → SX(O) (top)
- **Tata**: XE (base) → XM (mid) → XT (high) → XZ+ (top)
- **Fallback**: Price-based quartile assignment

### Feature Comparison

```python
additional_features = set(variant2_features) - set(variant1_features)
price_difference = variant2_price - variant1_price
cost_per_feature = price_difference / len(additional_features)
```

### Value Assessment

- **Good Value**: < ₹50,000 per feature
- **Premium Choice**: ≥ ₹50,000 per feature

## Example Usage

1. **Select**: Maruti Suzuki → Swift → Vdi
2. **See**: ₹6,98,000 with mid-tier features
3. **Get Recommendations**:
   - **Option 1**: Zdi (₹7,57,000, +₹59,000)
     - 13 new features
     - ₹4,538 per feature (Good value)
   - **Option 2**: Zdi Plus (₹8,12,000, +₹1,14,000)
     - 18 new features
     - ₹6,333 per feature (Good value)

## Testing

The project includes comprehensive testing:

```bash
# Test data loading
python src/utils/data_loader.py

# Test tier inference
python src/utils/tier_inference.py

# Test feature categorization
python src/utils/feature_categorizer.py

# Test database queries
python src/database/queries.py

# Test recommendation engine
python src/agent/simple_recommender.py
```

## Future Enhancements

### Phase 2: Contextual Recommendations
- User input: "I have 2 kids, drive in city"
- AI weighs features based on needs (safety > luxury for families)
- Personalized recommendations

### Phase 3: Comparison Mode
- Compare any 2 variants side-by-side
- Highlight differences in table format
- Show real-world owner reviews

### Phase 4: Financial Tools
- EMI calculator integration
- Insurance cost estimates
- Total cost of ownership (5-year projection)
- Resale value prediction (ML model)

### Phase 5: Production Features
- Real-time price updates (API integration)
- User accounts + saved comparisons
- Test drive booking integration
- WhatsApp/Email sharing

## Troubleshooting

### Import Errors
```bash
# Always set PYTHONPATH
export PYTHONPATH=/Users/d111879/Documents/Project/DEMO/Hackthon/HT_Jan_26:$PYTHONPATH
```

### Database Not Found
```bash
# Re-run data ingestion
python src/database/chroma_client.py
```

### No Variants Found
- Check exact spelling of make/model (e.g., "Maruti Suzuki" not "Maruti")
- Verify data in ChromaDB: `data/car_variants_db/`

## Performance

- **Database Query**: < 200ms
- **Recommendation Generation**: < 2s
- **Page Load**: < 3s
- **Total Variants**: 1,201 (manageable for local DB)

## Credits

- **Data Source**: Kaggle Indian Cars Dataset (modified)
- **Built for**: Hackathon January 2026
- **Timeline**: 2-day sprint

## License

MIT License - Feel free to use for learning and demo purposes

---

**Status**: ✅ MVP Complete  
**Demo Ready**: Yes  
**Video Recording**: Pending  
**Deployment**: Local only (Streamlit Cloud deployment ready)

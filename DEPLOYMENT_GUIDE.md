# Deployment Guide - Car Variant Advisor

## Common Deployment Issues & Solutions

### ✅ Fixed Issues in This Update:

#### 1. **Missing `.env` File Error**
- **Problem**: Code runs locally with `.env`, but deployment fails because `.env` doesn't exist on server
- **Solution**: Added error handling to gracefully skip missing `.env` files
- **Location**: `app/streamlit_app.py` line 20

#### 2. **Hardcoded Relative Paths**
- **Problem**: `./data/car_variants_db` works locally but fails on cloud servers with different file structures
- **Solution**: Convert all paths to absolute paths based on script location
- **Files Updated**:
  - `src/database/chroma_client.py` 
  - `src/database/queries.py`

#### 3. **Database Initialization Failures**
- **Problem**: Database paths not found during deployment
- **Solution**: Added database existence checks before initialization
- **Location**: `app/streamlit_app.py` line 295-301

---

## Deployment Instructions

### For Streamlit Cloud:

1. **Push to GitHub** (already done)
   ```bash
   git push origin main
   ```

2. **Go to Streamlit Cloud** (https://share.streamlit.io)
   - Click "New app"
   - Connect your GitHub repository
   - Select: `Car_Variant_Advisor/app/streamlit_app.py`

3. **Set Environment Secrets** (CRITICAL)
   - In the app dashboard, click "Settings" → "Secrets"
   - Add your Gemini API key:
     ```
     GEMINI_API_KEY = "your_api_key_here"
     ```
   - Get key from: https://makersuite.google.com/app/apikey

4. **Ensure Database is Included**
   - The `data/car_variants_db/` directory must be committed to GitHub
   - Run locally first: `python src/database/chroma_client.py` to create database
   - Then commit: `git add data/car_variants_db/ && git commit -m "Add database"`

### For Heroku / Docker:

1. **Create `Procfile`**:
   ```
   web: streamlit run app/streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
   ```

2. **Set Environment Variables**:
   ```bash
   heroku config:set GEMINI_API_KEY="your_key_here"
   ```

3. **Deploy**:
   ```bash
   git push heroku main
   ```

### For Self-Hosted (Linux Server):

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```

3. **Run App**:
   ```bash
   streamlit run app/streamlit_app.py
   ```

---

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'src'` | Missing project root in path | Fixed: uses absolute paths now |
| `Database collection not found` | Database not deployed | Commit `data/` directory to GitHub |
| `No such file or directory: ./data/car_variants_db` | Relative path issues | Fixed: uses absolute paths now |
| `GEMINI_API_KEY not found` | Missing environment variable | Add in Streamlit Secrets or `.env` |
| `FileNotFoundError: .env` | Missing `.env` file | Fixed: gracefully handles missing `.env` |

---

## Testing Before Deployment

```bash
# Run locally to verify everything works
streamlit run app/streamlit_app.py

# Test imports
python -c "from src.database.queries import init_queries; print('✅ Imports work')"

# Check database exists
ls -la data/car_variants_db/
```

---

## Key Changes Made for Deployment:

✅ Error handling for missing `.env` files
✅ Absolute path resolution for database
✅ Database existence validation
✅ Better error messages showing actual paths
✅ Cross-platform path handling (works on Windows/Linux/Mac)

"""
Streamlit UI for AI Car Variant Advisor
Powered by Gemini AI + Voice AI
"""
import streamlit as st
import sys
import os
import base64

try:
    if sys.version_info >= (3, 13):
        from pydantic import typing as pydantic_typing

        def _patched_evaluate_forwardref(type_, globalns, localns):
            return type_._evaluate(globalns, localns, recursive_guard=set())

        pydantic_typing.evaluate_forwardref = _patched_evaluate_forwardref
except ImportError:
    pass

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from src.database.queries import (
    init_queries,
    get_all_makes,
    get_models_by_make,
    get_variant_details,
    find_upgrade_options,
    get_price_range,
    find_variants_by_budget,
    search_variants_by_budget,
    search_variants_by_requirements,
)
from src.agent.simple_recommender import SimpleRecommendationEngine
from src.agent.nlg_engine import NLGEngine
from src.agent.voice_assistant import VoiceAssistant
from src.agent.direct_gemini_agent import DirectGeminiAgent
from src.utils.feature_comparison import build_feature_comparison_matrix
from src.utils.feature_price_chart import generate_feature_price_chart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
# Page config
st.set_page_config(
    page_title="AI Car Variant Advisor",
    page_icon="🚗",
    layout="wide"
)
# Custom CSS - Professional Theme (Pink & Purple with Sky Blue)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&family=Inter:wght@400;500;600&family=Roboto+Mono:wght@400;500&display=swap');
    
    /* CSS Variables */
    :root {
        --primary: #E91E63;
        --secondary: #9C27B0;
        --background: #FFFFFF;
        --sidebar-bg: #F5F5F5;
        --surface: #FFFFFF;
        --text-primary: #212121;
        --text-secondary: #757575;
        --border: #E0E0E0;
        --success: #4CAF50;
        --warning: #FF9800;
    }
    
    /* Global Styles */
    .main {
        background-color: var(--background) !important;
    }
    
    .stApp {
        background-color: var(--background) !important;
    }
    
    [data-testid="stAppViewContainer"] {
        background-color: var(--background) !important;
    }
    
    .block-container {
        background-color: var(--background) !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Poppins', sans-serif !important;
        color: var(--text-primary) !important;
    }
    
    /* Header Gradient */
    .main h1 {
        background: linear-gradient(135deg, #E91E63, #9C27B0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700 !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: var(--sidebar-bg) !important;
    }
    
    section[data-testid="stSidebar"] > div {
        background-color: var(--sidebar-bg) !important;
    }
    
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div {
        color: var(--text-primary) !important;
    }
    
    /* Sidebar internal content spacing */
    section[data-testid="stSidebar"] h3 {
        margin-top: 0.65rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    section[data-testid="stSidebar"] h3:first-of-type {
        margin-top: 0.25rem !important;
    }
    
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] ol,
    section[data-testid="stSidebar"] ul {
        margin-left: 0.2rem !important;
        margin-right: 0.25rem !important;
        margin-bottom: 0.95rem !important;
    }
    
    section[data-testid="stSidebar"] li {
        margin-bottom: 0.4rem !important;
    }
    
    section[data-testid="stSidebar"] hr {
        margin: 1rem 0.25rem !important;
    }

    section[data-testid="stSidebar"] > div > div > div {
        display: flex !important;
        flex-direction: column !important;
        gap: 0.9rem;
    }

    section[data-testid="stSidebar"] .stMarkdown > div {
        margin: 0.25rem 0.35rem 1rem !important;
    }

    section[data-testid="stSidebar"] .stMarkdown div h3 {
        margin: 0.6rem 0.4rem 0.3rem !important;
    }

    section[data-testid="stSidebar"] .stMarkdown div ol {
        margin-left: 0.4rem !important;
        margin-right: 0.4rem !important;
    }

    section[data-testid="stSidebar"] .stMarkdown div p {
        margin: 0 0.4rem 0.9rem !important;
    }
    section[data-testid="stSidebar"] .stSlider {
        padding-left: 1.0rem !important;
        padding-right: 2.0rem !important;
    }
      section[data-testid="stSidebar"] .metric {
        padding-left: 1.0rem !important;
        padding-right: 2.0rem !important;
    }
            
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #E91E63, #9C27B0) !important;
        color: white !important;
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important;
        padding: 12px 32px !important;
        border: none !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(233, 30, 99, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(233, 30, 99, 0.4) !important;
    }
    
    /* Metrics */
    div[data-testid="stMetric"] {
        background-color: var(--surface) !important;
        padding: 16px !important;
        border-radius: 8px !important;
        border: 1px solid var(--border) !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        margin-bottom: 1rem !important;
    }
    
    div[data-testid="stMetricValue"] {
        font-family: 'Roboto Mono', monospace !important;
        color: var(--primary) !important;
        font-weight: 700 !important;
    }
    
    /* DataFrames */
    .dataframe {
        border-radius: 8px !important;
        overflow: hidden !important;
        margin: 1rem 0 !important;
    }
    
    .dataframe thead tr {
        background: linear-gradient(135deg, #E91E63, #9C27B0) !important;
    }
    
    .dataframe thead th {
        color: white !important;
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important;
        padding: 12px 16px !important;
    }
    
    .dataframe tbody tr:nth-child(even) {
        background-color: #F5F5F5 !important;
    }
    
    .dataframe tbody tr:hover {
        background-color: var(--background) !important;
        transition: background-color 0.2s ease !important;
    }
    
    .dataframe td {
        padding: 12px 16px !important;
    }
    
    /* Alerts */
    div[data-testid="stSuccess"] {
        background-color: rgba(76, 175, 80, 0.1) !important;
        border-left: 4px solid var(--success) !important;
        border-radius: 8px !important;
    }
    
    div[data-testid="stInfo"] {
        background-color: rgba(156, 39, 176, 0.1) !important;
        border-left: 4px solid var(--secondary) !important;
        border-radius: 8px !important;
    }
    
    div[data-testid="stWarning"] {
        background-color: rgba(255, 152, 0, 0.1) !important;
        border-left: 4px solid var(--warning) !important;
        border-radius: 8px !important;
    }
    
    /* Radio buttons */
    .stRadio > div {
        background-color: var(--surface) !important;
        padding: 8px !important;
        border-radius: 8px !important;
    }
    
    /* Slider */
    div[data-baseweb="slider"] [role="slider"] {
        background: var(--primary) !important;
    }
    
    /* Dividers */
    hr {
        border-color: var(--border) !important;
        margin: 24px 0 !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Spacing utilities */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* Card Components */
    .selection-card {
        background: linear-gradient(135deg, #FFF0F5, #F3E5F5) !important;
        border: 2px solid var(--primary) !important;
        border-radius: 12px !important;
        padding: 24px !important;
        box-shadow: 0 4px 12px rgba(233, 30, 99, 0.2) !important;
        margin-bottom: 24px !important;
    }
    
    .upgrade-card {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 20px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
        margin-bottom: 20px !important;
        transition: all 0.3s ease !important;
    }
    
    .upgrade-card:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 8px 20px rgba(156, 39, 176, 0.15) !important;
        border-color: var(--secondary) !important;
    }
    
    /* Container styling for cards */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        gap: 16px;
    }
    
    /* Section headers */
    .main h2, .main h3 {
        margin-top: 32px !important;
        margin-bottom: 16px !important;
        padding-bottom: 8px !important;
        border-bottom: 2px solid var(--border) !important;
    }
    
    /* Metric cards with colored accents */
    div[data-testid="column"]:nth-child(1) div[data-testid="stMetric"] {
        border-left: 4px solid var(--primary) !important;
    }
    
    div[data-testid="column"]:nth-child(2) div[data-testid="stMetric"] {
        border-left: 4px solid var(--secondary) !important;
    }
    
    div[data-testid="column"]:nth-child(3) div[data-testid="stMetric"] {
        border-left: 4px solid var(--success) !important;
    }
    
    /* Feature badges */
    .feature-item {
        background-color: rgba(156, 39, 176, 0.05) !important;
        padding: 8px 12px !important;
        border-radius: 6px !important;
        margin: 4px 0 !important;
        border-left: 3px solid var(--secondary) !important;
    }
    
    /* Improve spacing between sections */
    .main > div > div > div > div {
        margin-bottom: 16px;
    }
    
    /* Expander styling */
    
    /* Caption text styling */
    .main .stCaption {
        color: var(--text-secondary) !important;
        font-size: 0.85rem !important;
    }
    
    /* Spinner styling */
    div[data-testid="stSpinner"] > div {
        border-top-color: var(--primary) !important;
    }

</style>
""", unsafe_allow_html=True)

# Initialize database and engine
@st.cache_resource(show_spinner=False)
def initialize_system():
    db_path = os.path.join(project_root, "data/car_variants_db")
    init_queries(db_path)
    from src.agent.direct_gemini_agent import DirectGeminiAgent
    return DirectGeminiAgent(), NLGEngine(), VoiceAssistant()

# Initialize with custom spinner
with st.spinner("🚗 Loading AI Car Advisor..."):
    engine, nlg_engine, voice_assistant = initialize_system()

# Compact Top Header Bar
st.markdown("""
<div style="background: linear-gradient(135deg, #F8F7FF, #F5F3FF, #F0EDFF); 
            padding: 0.8rem 1.5rem; 
            border-bottom: 2px solid #E0E0E0;
            border-radius: 16px; 
            margin: -1rem -1rem 1.5rem -1rem;">
    <div style="display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 0.8rem;">
            <span style="font-size: 2rem; margin-top: 1.5rem;">🚗</span>
            <span style="color: #9C27B0; 
                         font-size: 2.25rem; 
                         font-weight: 600;
                         letter-spacing: 0.5px;
                         margin-left: 0.5rem;
            margin-top: 2.0rem;">
                 AI Car Variant Advisor</span>
            </span>
            <span style="color: #A0A0A0; 
                         font-size: 0.75rem; 
                         font-weight: 600;
                         letter-spacing: 0.5px;
                         margin-left: 0.5rem; margin-top: 1.5rem;">
                POWERED BY <span style="color: #6366F1; font-weight: 700;">Gemini AI</span>
            </span>
        </div>
    </div>
    <p style="color: #8B7BA8; 
              font-size: 0.95rem; 
              margin: 0.3rem 0 0 3rem;
              font-family: 'Inter', sans-serif;">
        Find the perfect car variant within your budget with AI-powered insights
    </p>
</div>
""", unsafe_allow_html=True)

# Initialize variables for sidebar access
voice_gender = "Female"  # Default to Female
num_recommendations = 3  # Default value

# Sidebar with settings (define early for variable scope)
with st.sidebar:
    # Branding header
    
    st.markdown("### 💡 About")
    st.markdown("<p style='font-size: 0.95rem;'>AI-powered car advisor that understands natural language. Just describe what you want - budget, features, brands - and let AI find the perfect match.</p>", unsafe_allow_html=True)
    
    st.markdown("### 🎯 How it works")
    st.markdown("""
    <ol style='font-size: 0.9rem; padding-left: 0.6rem;'>
    <li><b>Text Search:</b> Just type what you want in plain English - AI understands your requirements</li>
    <li><b>Or Use Filters:</b> Pick budget range, brand, model from dropdowns</li>
    <li><b>AI Magic:</b> Gemini AI extracts budget, brands, features & ranks best matches</li>
    <li><b>Compare:</b> View feature-by-feature comparison across variants</li>
    </ol>
    """, unsafe_allow_html=True)
    st.divider()
    st.markdown("### ⚙️ Search Settings")
    count_options = [2, 3, 4, 5]
    selected_count = st.selectbox(
        "🔢 Number of suggestions",
        count_options,
        index=1,  # Default 3
        format_func=lambda x: f"{x} results",
        key="result_count",
        help="Number of car variants to show in results"
    )

    st.divider()
    st.markdown("### 📊 Statistics")
    makes_count = len(get_all_makes())
    st.metric("Total Makes", makes_count)

    # st.divider()
    # st.divider()
    # # Voice and Recommendation Settings
    # st.markdown("### 🎙️ AI Voice Settings")
    # voice_gender = st.radio("Voice", ["Female", "Male"], horizontal=True, help="Choose your preferred AI voice assistant")
    
    
    
   

# Selection Panel with gradient card
# st.markdown("""
# <div style="background: linear-gradient(135deg, #7B68EE, #9370DB, #BA55D3); 
#             padding: 1rem; 
#             border-radius: 16px; 
#             margin-bottom: 1rem;
#             box-shadow: 0 4px 16px rgba(123, 104, 238, 0.3);">
#     <h3 style="color: white; 
#                margin: 0 0 0 0; 
#                font-family: 'Poppins', sans-serif;
#                font-size: 1.8rem;
#                font-weight: 600;">
#         🎯 Search by Budget
#     </h3>
#     <p style="color: rgba(255, 255, 255, 0.9); 
#               font-size: 1rem; 
#               margin: 0 0 1rem 0;
#               font-family: 'Inter', sans-serif;">
#         Pick a budget and optionally narrow by brand/model
#     </p>
# </div>
# """, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _build_budget_options(step_rupees: int = 10_000):
    min_p, max_p = get_price_range()
    if min_p is None or max_p is None:
        return []
    start = int(min_p // step_rupees) * step_rupees
    end = int((max_p + step_rupees - 1) // step_rupees) * step_rupees
    return list(range(start, end + 1, step_rupees))


def _format_budget_lakhs(rupees: int) -> str:
    lakhs = float(rupees) / 100_000.0
    return f"₹{lakhs:.2f} L"


def _closest_index(values, target: int) -> int:
    if not values:
        return 0
    return min(range(len(values)), key=lambda i: abs(int(values[i]) - int(target)))


ALL_BRANDS = "All brands"
ALL_MODELS = "All models"


budget_options = _build_budget_options()

# Text search option
st.markdown("#### 🔍 Text based search")

st.markdown("<p style='font-size: 0.85rem; color: #666; margin-bottom: 0.5rem;'>Describe your budget, preferred features, and brands - AI will find the best matches</p>", unsafe_allow_html=True)
search_query = st.text_area(
    "Search",
    placeholder="e.g., I have a budget of 5-6 lacs, looking for a car with sunroof, 6 airbags, and automatic transmission. Preferred brands are Hyundai or Kia",
    key="feature_search",
    label_visibility="collapsed",
    height=80,
)



st.markdown("<div style='display: flex; justify-content: center; margin: 1.25rem 0 0.5rem;'>", unsafe_allow_html=True)
col_left, col_center, col_right = st.columns([1, 2, 1])
with col_center:
    text_search_button = st.button(
        "🔎 Search Cars",
        type="secondary",
        disabled=not bool(budget_options),
        use_container_width=True,
        key="text_search_btn",
    )
st.markdown("</div>", unsafe_allow_html=True)

# Handle text-based search with NLP parsing
if text_search_button and search_query and search_query.strip():
    with st.spinner("🤖 AI is parsing your search query..."):
        try:
            # Initialize Gemini agent for NLP parsing
            nlp_agent = DirectGeminiAgent()
            parsed_params = nlp_agent.parse_search_query(search_query.strip())
            
            if parsed_params is None:
                st.error("❌ Couldn't understand your query. Please try rephrasing it.")
                st.session_state["text_search_error"] = True
            else:
                st.session_state["text_search_error"] = False
                st.session_state["parsed_search_params"] = parsed_params
                
                # Show what was parsed
                parsed_info = []
                if parsed_params.get("budget_min") or parsed_params.get("budget_max"):
                    if parsed_params.get("budget_min") and parsed_params.get("budget_max"):
                        parsed_info.append(f"💰 Budget: ₹{parsed_params['budget_min']/100000:.1f}L - ₹{parsed_params['budget_max']/100000:.1f}L")
                    elif parsed_params.get("budget_min"):
                        parsed_info.append(f"💰 Budget: ~₹{parsed_params['budget_min']/100000:.1f}L (±10% margin)")
                    else:
                        parsed_info.append(f"💰 Budget: Under ₹{parsed_params['budget_max']/100000:.1f}L")
                if parsed_params.get("brands"):
                    parsed_info.append(f"🏢 Brands: {', '.join(parsed_params['brands'])}")
                if parsed_params.get("model"):
                    parsed_info.append(f"🚗 Model: {parsed_params['model']}")
                if parsed_params.get("fuel_type"):
                    parsed_info.append(f"⛽ Fuel: {parsed_params['fuel_type']}")
                if parsed_params.get("body_type"):
                    parsed_info.append(f"🚙 Body: {parsed_params['body_type']}")
                if parsed_params.get("seating_capacity"):
                    parsed_info.append(f"👥 Seats: {parsed_params['seating_capacity']}")
                if parsed_params.get("transmission"):
                    parsed_info.append(f"⚙️ Transmission: {parsed_params['transmission']}")
                if parsed_params.get("required_features"):
                    parsed_info.append(f"✨ Features: {', '.join(parsed_params['required_features'][:5])}")
                
                if parsed_info:
                    st.success("✅ Understood! Searching with: " + " | ".join(parsed_info))
                
                # Execute the search with parsed parameters
                with st.spinner("🔍 Searching variants matching your requirements..."):
                    candidates, search_meta = search_variants_by_requirements(
                        budget_min=parsed_params.get("budget_min"),
                        budget_max=parsed_params.get("budget_max"),
                        margin_pct=10.0,  # Default margin
                        brands=parsed_params.get("brands"),
                        model=parsed_params.get("model"),
                        fuel_type=parsed_params.get("fuel_type"),
                        body_type=parsed_params.get("body_type"),
                        seating_capacity=parsed_params.get("seating_capacity"),
                        transmission=parsed_params.get("transmission"),
                        required_features=parsed_params.get("required_features"),
                        count=3,  # Default count
                    )
                    
                    st.session_state["budget_candidates"] = candidates
                    st.session_state["budget_search_meta"] = search_meta
                    st.session_state["budget_search_params"] = {
                        "budget_rupees": parsed_params.get("budget_min") or parsed_params.get("budget_max") or 0,
                        "margin_pct": 10.0,
                        "count": 3,
                        "brand": parsed_params.get("brands")[0] if parsed_params.get("brands") else None,
                        "model": parsed_params.get("model"),
                        "text_search": True,
                        "parsed_params": parsed_params,
                    }
                    
                    # Show filter relaxation info if applicable
                    if search_meta.get("relaxed"):
                        st.info("ℹ️ No exact matches found. Showing similar options with relaxed filters.")
                    if search_meta.get("feature_ranking_applied"):
                        st.info("✨ Results ranked by feature match score.")
                        
        except Exception as e:
            st.error(f"❌ Error parsing query: {str(e)}")
            st.session_state["text_search_error"] = True

elif text_search_button and (not search_query or not search_query.strip()):
    st.warning("⚠️ Please enter a search query or use the selection-based search below.")

st.markdown("<p style='text-align: center; color: #9C27B0; font-weight: 600; font-size: 1.2rem; margin: 1rem 0;'>— OR —</p>", unsafe_allow_html=True)


# Row 1: Budget and Margin
st.markdown("#### Selection based search ")
row1_col1, row1_col2 = st.columns([3, 1])

with row1_col1:
    st.markdown("**💰 Budget**")
    if budget_options:
        # Add placeholder option at the beginning
        budget_display_options = ["Select budget..."] + budget_options
        selected_budget_idx = st.selectbox(
            "Budget",
            range(len(budget_display_options)),
            index=0,  # Default to placeholder
            format_func=lambda i: budget_display_options[i] if i == 0 else _format_budget_lakhs(budget_display_options[i]),
            key="budget_rupees",
            label_visibility="collapsed",
        )
        # Get actual budget value (None if placeholder selected)
        selected_budget = None if selected_budget_idx == 0 else budget_display_options[selected_budget_idx]
    else:
        selected_budget = st.selectbox("Budget", ["No price data"], disabled=True, label_visibility="collapsed")
        selected_budget = None

with row1_col2:
    st.markdown("**Margin budget**")
    margin_options = [5, 10, 15, 20, 25, 30, 40, 50]
    selected_margin = st.selectbox(
        "Margin",
        margin_options,
        index=1,  # Default 10%
        format_func=lambda x: f"{x}%",
        key="budget_margin_pct",
        label_visibility="collapsed",
    )

# Row 2: Additional Filters
st.markdown("<p style='font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;'>🎯 Additional Filters</p>", unsafe_allow_html=True)
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.markdown("**🏢 Brand**")
    makes = get_all_makes()
    selected_make = st.selectbox(
        "Brand",
        [ALL_BRANDS] + makes,
        key="make",
        label_visibility="collapsed",
    )
    if selected_make == ALL_BRANDS:
        selected_make = None

with row2_col2:
    st.markdown("**🚗 Model**")
    if selected_make:
        models = get_models_by_make(selected_make)
        selected_model = st.selectbox(
            "Model",
            [ALL_MODELS] + models,
            key="model",
            label_visibility="collapsed",
        )
        if selected_model == ALL_MODELS:
            selected_model = None
    else:
        st.selectbox("Model", [ALL_MODELS], disabled=True, label_visibility="collapsed", key="model_disabled")
        selected_model = None

st.markdown("<div style='display: flex; justify-content: center; margin: 1.25rem 0 0.5rem;'>", unsafe_allow_html=True)
col_left, col_center, col_right = st.columns([1, 2, 1])
with col_center:
    selection_search_button = st.button(
        "🔎 Search Cars",
        type="primary",
        disabled=not bool(budget_options),
        use_container_width=True,
        key="selection_search_btn",
    )
st.markdown("</div>", unsafe_allow_html=True)

if selection_search_button:
    if selected_budget is None:
        st.warning("⚠️ Please select a budget to search.")
    else:
        with st.spinner("Searching variants near your budget..."):
            candidates, search_meta = search_variants_by_budget(
                budget_rupees=float(selected_budget),
                margin_pct=float(selected_margin),
                count=int(selected_count),
                brand=selected_make,
                model=selected_model,
            )
            st.session_state["budget_candidates"] = candidates
            st.session_state["budget_search_meta"] = search_meta
            st.session_state["budget_search_params"] = {
                "budget_rupees": float(selected_budget),
                "margin_pct": float(selected_margin),
                "count": int(selected_count),
                "brand": selected_make,
            "model": selected_model,
        }

budget_candidates = st.session_state.get("budget_candidates") or []
budget_search_meta = st.session_state.get("budget_search_meta") or {}
budget_search_params = st.session_state.get("budget_search_params") or {}

# Show filter info
if selected_make or selected_model:
    if selected_make and selected_model:
        st.info(f"Showing results only for {selected_make} {selected_model} because you selected it.")
    elif selected_make:
        st.info(f"Showing results only for {selected_make} because you selected it.")

# Show search range info
if budget_search_meta.get("searched_lower") and not budget_search_meta.get("no_results"):
    st.info("Extended search to below-budget range to find more matches.")

if budget_search_meta.get("no_results"):
    st.warning("No cars found in your budget range. Try adjusting your budget or margin.")

st.divider()

# Helper function to parse feature strings from metadata
def parse_feature_string(feature_str: str) -> list:
    """Parse feature string back to list."""
    import ast
    try:
        if not feature_str or feature_str == '[]':
            return []
        if feature_str.endswith('...') or not feature_str.endswith(']'):
            feature_str = feature_str.rstrip('...') + ']'
        features = ast.literal_eval(feature_str)
        return features if isinstance(features, list) else []
    except Exception:
        return []

# Display Search Results with Full Feature Comparison
if budget_candidates:
    st.markdown(f"### 🚗 Search Results ({len(budget_candidates)} variants found)")
    
    # Build comparison table data
    import pandas as pd
    
    # Summary table first
    table_data = []
    for i, meta in enumerate(budget_candidates, 1):
        table_data.append({
            "#": i,
            "Brand": meta.get("make", ""),
            "Model": meta.get("model", ""),
            "Variant": meta.get("variant_name", ""),
            "Price (Lakhs)": f"₹{float(meta.get('price', 0))/100000:.2f} L",
            "Tier": str(meta.get("tier_name", "")).title(),
            "Fuel": meta.get("fuel_type", ""),
            "Body": meta.get("body_type", ""),
        })
    
    df = pd.DataFrame(table_data)
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "#": st.column_config.NumberColumn("#", width="small"),
            "Brand": st.column_config.TextColumn("Brand", width="small"),
            "Model": st.column_config.TextColumn("Model", width="small"),
            "Variant": st.column_config.TextColumn("Variant", width="medium"),
            "Price (Lakhs)": st.column_config.TextColumn("Price (Lakhs)", width="small"),
            "Tier": st.column_config.TextColumn("Tier", width="small"),
            "Fuel": st.column_config.TextColumn("Fuel", width="small"),
            "Body": st.column_config.TextColumn("Body", width="small"),
        }
    )
    
    st.divider()
    
    # Parse features for all candidates (needed for both sections)
    feature_categories = ['safety', 'comfort', 'technology', 'exterior', 'convenience']
    category_icons = {
        'safety': '🛡️',
        'comfort': '🛋️', 
        'technology': '💻',
        'exterior': '🚙',
        'convenience': '⚡'
    }
    
    # Collect all unique features per category across all variants
    all_features_by_category = {cat: set() for cat in feature_categories}
    variant_features = []
    
    for meta in budget_candidates:
        variant_feat = {}
        for cat in feature_categories:
            features = parse_feature_string(meta.get(f'features_{cat}', '[]'))
            variant_feat[cat] = set(features)
            all_features_by_category[cat].update(features)
        variant_features.append(variant_feat)
    
    # Individual Variant Details (expandable cards) - FIRST
    st.markdown("### 🔍 Individual Variant Details")
    
    for i, meta in enumerate(budget_candidates):
        variant_label = f"{meta.get('make', '')} {meta.get('model', '')} - {meta.get('variant_name', '')}"
        price_display = f"₹{float(meta.get('price', 0))/100000:.2f} L"
        tier_display = str(meta.get('tier_name', '')).title()
        
        with st.expander(f"**{i+1}. {variant_label}** | {price_display} | {tier_display} Tier", expanded=(i == 0)):
            # Basic info columns
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("💰 Price", price_display)
            with col2:
                st.metric("⛽ Fuel Type", meta.get("fuel_type", "N/A"))
            with col3:
                st.metric("🚙 Body Type", meta.get("body_type", "N/A"))
            with col4:
                st.metric("👥 Seats", int(float(meta.get("seating_capacity", 0))) if meta.get("seating_capacity") else "N/A")
            
            st.divider()
            
            # Features by category
            for category in feature_categories:
                features = parse_feature_string(meta.get(f'features_{category}', '[]'))
                if features:
                    icon = category_icons.get(category, '📌')
                    st.markdown(f"**{icon} {category.upper()}** ({len(features)} features)")
                    # Display features in a compact format
                    feature_html = " • ".join([f"<span style='background-color: #f0f2f6; padding: 2px 8px; border-radius: 12px; margin: 2px; display: inline-block; font-size: 0.85rem;'>{f}</span>" for f in features[:15]])
                    if len(features) > 15:
                        feature_html += f" <span style='color: #666; font-style: italic;'>+{len(features) - 15} more...</span>"
                    st.markdown(feature_html, unsafe_allow_html=True)
                    st.markdown("")  # Spacing
    
    st.divider()
    
    # Detailed Feature Comparison Section - SECOND
    st.markdown("### 📋 Detailed Feature Comparison")
    
    # Build feature comparison matrix per category
    for category in feature_categories:
        cat_features = sorted(list(all_features_by_category[category]))
        if not cat_features:
            continue
        
        icon = category_icons.get(category, '📌')
        with st.expander(f"{icon} {category.upper()} Features ({len(cat_features)} features)", expanded=False):
            # Build matrix for this category
            matrix_data = []
            for feature in cat_features:
                row = {"Feature": feature}
                for i, meta in enumerate(budget_candidates):
                    variant_name = f"{meta.get('make', '')} {meta.get('model', '')} - {meta.get('variant_name', '')}"
                    has_feature = feature in variant_features[i][category]
                    row[variant_name] = "✅" if has_feature else "❌"
                matrix_data.append(row)
            
            cat_df = pd.DataFrame(matrix_data)
            
            # Style the dataframe
            def highlight_features(val):
                if val == "✅":
                    return "background-color: #d4edda; color: #155724; font-weight: bold;"
                elif val == "❌":
                    return "background-color: #f8d7da; color: #721c24;"
                return ""
            
            styled_df = cat_df.style.applymap(highlight_features, subset=[c for c in cat_df.columns if c != "Feature"])
            st.dataframe(styled_df, use_container_width=True, hide_index=True, height=min(400, 50 + len(cat_features) * 35))
    
    st.divider()
    
    # AI Recommendation
    st.markdown("### 🤖 AI-Powered Recommendation")
    
    with st.spinner("🤖 AI is analyzing these variants for you..."):
        # Build context for AI
        variants_text = "\n".join([
            f"- {m.get('make')} {m.get('model')} {m.get('variant_name')} at ₹{float(m.get('price', 0)):,.0f} ({m.get('tier_name', '').title()} tier)"
            for m in budget_candidates
        ])
        budget_lakhs = float(budget_search_params.get('budget_rupees', 0)) / 100000
        
        prompt = f"""Given these car variants within budget ₹{budget_lakhs:.2f} Lakhs (±{budget_search_params.get('margin_pct', 10)}%):

{variants_text}

Please provide:
1. A brief comparison of these variants
2. Your recommendation for the best value option
3. Key factors to consider when choosing between them

Keep the response concise and helpful."""
        
        # Call AI engine for recommendation
        try:
            result = engine.get_budget_recommendation(budget_candidates, budget_search_params)
            if result and result.get('status') == 'success' and result.get('recommendation'):
                st.success("✅ AI Analysis Complete!")
                # Display recommendation in styled info box
                st.info(result['recommendation'])
                st.caption("*️⃣ Note: This is an AI recommendation based on value analysis. Final decision should be yours based on your specific needs and preferences.")
            else:
                # Show error message if available
                error_msg = result.get('message', 'Unknown error') if result else 'No response'
                st.warning(f"AI analysis returned: {error_msg}")
                # Fallback to simple recommendation
                if len(budget_candidates) > 0:
                    cheapest = min(budget_candidates, key=lambda x: float(x.get('price', float('inf'))))
                    st.info(f"💡 **Quick Tip:** The {cheapest.get('make')} {cheapest.get('model')} {cheapest.get('variant_name')} offers the lowest price at ₹{float(cheapest.get('price', 0)):,.0f}.")
                    st.caption("AI detailed analysis unavailable. Showing basic recommendation.")
        except Exception as e:
            st.warning(f"AI recommendation unavailable: {str(e)}")
            # Fallback to simple recommendation
            if len(budget_candidates) > 0:
                cheapest = min(budget_candidates, key=lambda x: float(x.get('price', float('inf'))))
                st.info(f"💡 **Quick Tip:** The {cheapest.get('make')} {cheapest.get('model')} {cheapest.get('variant_name')} offers the lowest price at ₹{float(cheapest.get('price', 0)):,.0f}.")

elif budget_search_meta.get("no_results"):
    st.markdown("### No Results")
    st.info("Try adjusting your budget, increasing the margin, or removing brand/model filters.")
elif not st.session_state.get("budget_candidates"):
    st.markdown("### 🎯 Getting Started")
    st.info("**Text Search:** Describe what you want in plain English above ☝️\n\n**Or use filters:** Select budget, brand & model from the dropdowns below and click **Search Cars**")

st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        <p style='margin-top: 15px; font-size: 0.9em;'>Developed with ❤️ by <a href='https://www.linkedin.com/in/manvendrapratapsinghdev/' target='_blank' style='color: #0077B5; text-decoration: none;'>Manvendra</a></p>
    </div>
    """,
    unsafe_allow_html=True
)

# Update sidebar statistics dynamically
with st.sidebar:
    if selected_make:
        st.metric(f"{selected_make} Models", len(get_models_by_make(selected_make)))
    
    st.divider()
    st.markdown('<p style="text-align: center; color: #9C27B0; font-size: 0.85rem; font-weight: 600; margin-top: 2rem;">✨ Built for HT Mini Hackathon 2026</p>', unsafe_allow_html=True)

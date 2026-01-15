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
from src.database.queries import init_queries, get_all_makes, get_models_by_make, get_variants_by_model, get_variant_details, find_upgrade_options
from src.agent.simple_recommender import SimpleRecommendationEngine
from src.agent.nlg_engine import NLGEngine
from src.agent.voice_assistant import VoiceAssistant
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
    
    p, div, span, label {
        font-family: 'Inter', sans-serif !important;
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
        Find the perfect variant upgrade for your budget with AI-powered insights
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
    st.markdown("<p style='font-size: 0.95rem;'>This AI advisor helps you find the best car variant upgrade based on your budget and needs.</p>", unsafe_allow_html=True)
    
    st.markdown("### 🎯 How it works")
    st.markdown("""
    <ol style='font-size: 0.95rem; padding-left: 0.6rem;'>
    <li>Select your desired brand, model, and variant</li>
    <li>The AI analyzes higher tier variants</li>
    <li>Get recommendations with price differences</li>
    </ol>
    """, unsafe_allow_html=True)
    st.divider()
    st.markdown("### 🎯 Recommendation Settings")
    num_recommendations = st.slider(
        "Number of upgrades",
        min_value=2,
        max_value=3,
        value=3,
        help="Choose how many upgrade options you'd like to see (based on availability)"
    )

    st.markdown("### 📊 Statistics")
    makes_count = len(get_all_makes())
    st.metric("Total Makes", makes_count)

    # st.divider()
    # st.divider()
    # # Voice and Recommendation Settings
    # st.markdown("### 🎙️ AI Voice Settings")
    # voice_gender = st.radio("Voice", ["Female", "Male"], horizontal=True, help="Choose your preferred AI voice assistant")
    
    
    
   

# Selection Panel with gradient card
st.markdown("""
<div style="background: linear-gradient(135deg, #7B68EE, #9370DB, #BA55D3); 
            padding: 1rem; 
            border-radius: 16px; 
            margin-bottom: 1rem;
            box-shadow: 0 4px 16px rgba(123, 104, 238, 0.3);">
    <h3 style="color: white; 
               margin: 0 0 0 0; 
               font-family: 'Poppins', sans-serif;
               font-size: 1.8rem;
               font-weight: 600;">
        🎯 Select Your Dream Car
    </h3>
    <p style="color: rgba(255, 255, 255, 0.9); 
              font-size: 1rem; 
              margin: 0 0 1rem 0;
              font-family: 'Inter', sans-serif;">
        Choose your preferred brand, model, and tier
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🏢 Brand")
    makes = get_all_makes()
    selected_make = st.selectbox("Brand", ["Select a brand..."] + makes, key="make", label_visibility="collapsed")
    if selected_make == "Select a brand...":
        selected_make = None

with col2:
    st.markdown("### 🚗 Model")
    if selected_make:
        models = get_models_by_make(selected_make)
        selected_model = st.selectbox("Model", ["Select a model..."] + models, key="model", label_visibility="collapsed")
        if selected_model == "Select a model...":
            selected_model = None
    else:
        selected_model = st.selectbox("Model", ["Select brand first"], disabled=True, label_visibility="collapsed")

with col3:
    st.markdown("### ⚙️ Variant")
    if selected_make and selected_model:
        variants = get_variants_by_model(selected_make, selected_model)
        variant_options = [f"{v['variant_name']} (₹{v['price']:,.0f})" for v in variants]
        selected_variant_display = st.selectbox("Variant", ["Select a variant..."] + variant_options, key="variant", label_visibility="collapsed")
        
        # Extract just the variant name
        if selected_variant_display and selected_variant_display != "Select a variant...":
            selected_variant = selected_variant_display.split(" (₹")[0]
        else:
            selected_variant = None
    else:
        selected_variant = st.selectbox("Variant", ["Select model first"], disabled=True, label_visibility="collapsed")

# Centered gradient button
st.markdown("<div style='display: flex; justify-content: center; margin: 2rem 0;'>", unsafe_allow_html=True)
col_left, col_center, col_right = st.columns([1, 2, 1])
with col_center:
    show_button = st.button(
        "🚀 Discover Upgrade Options", 
        type="primary", 
        disabled=not (selected_make and selected_model and selected_variant), 
        use_container_width=True
    )
st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# Display results
if show_button and selected_variant:
    # Get basic variant details immediately
    selected = get_variant_details(selected_make, selected_model, selected_variant)
    
    if not selected:
        st.error(f"Variant {selected_variant} not found")
    else:
        # Get upgrade options immediately
        upgrades = find_upgrade_options(selected_make, selected_model, selected['tier_order'], limit=num_recommendations)
        
        # Calculate basic feature differences
        basic_upgrade_options = []
        for upgrade in upgrades:
            diff = SimpleRecommendationEngine.calculate_feature_difference(selected, upgrade)
            basic_upgrade_options.append({
                'variant': upgrade,
                'price_difference': diff['price_difference'],
                'additional_features': diff['additional_features'],
                'total_new_features': diff['total_new_features'],
                'cost_per_feature': diff['cost_per_feature'],
                'value_assessment': diff['cost_per_feature'] < 5000 and "Excellent value!" or diff['cost_per_feature'] < 10000 and "Good value" or "Premium upgrade"
            })
        
        # Display selected variant instantly with card styling
        # st.markdown('<div class="selection-card">', unsafe_allow_html=True)
        st.markdown(f"## 🚗 Your Selection: {selected['variant_name']}")
        
        col_price, col_tier = st.columns([3, 1])
        
        with col_price:
            st.metric("Ex-showroom Price", f"₹{selected['price']:,.0f}")
        
        with col_tier:
            st.metric("Tier", selected['tier_name'].title())
        
        # Features in expanders (only show non-empty sections)
        if selected['features']['safety']:
            with st.expander("🛡️ Safety Features"):
                for feat in selected['features']['safety']:
                    st.markdown(f"✓ {feat}")
        
        if selected['features']['comfort']:
            with st.expander("🛋️ Comfort Features"):
                for feat in selected['features']['comfort']:
                    st.markdown(f"✓ {feat}")
        
        if selected['features']['technology']:
            with st.expander("📱 Technology Features"):
                for feat in selected['features']['technology']:
                    st.markdown(f"✓ {feat}")
        
        if selected['features']['exterior']:
            with st.expander("🎨 Exterior Features"):
                for feat in selected['features']['exterior']:
                    st.markdown(f"✓ {feat}")
        
        if selected['features']['convenience']:
            with st.expander("🔧 Convenience Features"):
                for feat in selected['features']['convenience']:
                    st.markdown(f"✓ {feat}")
        
        st.divider()
        
        # Show basic upgrade options instantly
        if upgrades:
            st.markdown("### 📊 Upgrade Options")
            
            for i, opt in enumerate(basic_upgrade_options, 1):
                upgrade = opt['variant']
                
                st.markdown(f"### Option {i}: {upgrade['variant_name']}")
                
                # Show price and tier without boxes
                col_price, col_tier = st.columns([3, 1])
                
                with col_price:
                    st.markdown(f"**Ex-showroom Price:** ₹{upgrade['price']:,.0f}")
                
                with col_tier:
                    st.markdown(f"**Tier:** {upgrade['tier_name'].title()}")
                
                # Show important metrics with boxes
                col_features, col_upgrade = st.columns([1, 1])
                
                with col_features:
                    st.metric("Extra Features", opt['total_new_features'])
                
                with col_upgrade:
                    st.metric("Upgrade with", f"+₹{opt['price_difference']:,.0f}")
                
                # Show cost per feature as normal text below the cards
                if opt['total_new_features'] > 0:
                    st.markdown(f"**Cost per Feature:** ₹{opt['cost_per_feature']:,.0f}")
                    st.caption(opt['value_assessment'])
                else:
                    st.caption("Similar features")
                
                # Show additional features in category-wise expanders
                if opt['total_new_features'] > 0:
                    st.markdown("**What You Get:**")
                    
                    # Safety Features
                    if opt['additional_features'].get('safety'):
                        with st.expander("🛡️ Safety Features"):
                            for feat in opt['additional_features']['safety']:
                                st.markdown(f"✓ {feat}")
                    
                    # Comfort Features
                    if opt['additional_features'].get('comfort'):
                        with st.expander("🛋️ Comfort Features"):
                            for feat in opt['additional_features']['comfort']:
                                st.markdown(f"✓ {feat}")
                    
                    # Technology Features
                    if opt['additional_features'].get('technology'):
                        with st.expander("📱 Technology Features"):
                            for feat in opt['additional_features']['technology']:
                                st.markdown(f"✓ {feat}")
                    
                    # Exterior Features
                    if opt['additional_features'].get('exterior'):
                        with st.expander("🎨 Exterior Features"):
                            for feat in opt['additional_features']['exterior']:
                                st.markdown(f"✓ {feat}")
                    
                    # Convenience Features
                    if opt['additional_features'].get('convenience'):
                        with st.expander("🔧 Convenience Features"):
                            for feat in opt['additional_features']['convenience']:
                                st.markdown(f"✓ {feat}")
                
                st.divider()
            
            # Feature Comparison Matrix
            st.markdown("### 🔍 Feature Comparison: What's New in Each Upgrade")
            st.caption("**CURRENT** = Your selected variant | **+₹Price** = Upgrade cost from current variant")
            
            comparison_matrix = build_feature_comparison_matrix(selected, basic_upgrade_options)
            
            # Display with custom styling and configuration
            st.dataframe(
                comparison_matrix,
                use_container_width=True,
                hide_index=True,
                height=min(len(comparison_matrix) * 35 + 38, 600),  # Dynamic height, max 600px
                column_config={
                    "Feature": st.column_config.TextColumn(
                        "Feature",
                        width="medium",
                    )
                }
            )
            
            st.divider()
        
        # Now show AI analysis with loading spinner
        st.markdown("### 🤖 AI-Powered Comparative Analysis")
        
        with st.spinner("🤖 AI is analyzing the upgrade options for you..."):
            # Call Gemini AI for detailed analysis
            result = engine.get_recommendations(selected_make, selected_model, selected_variant, num_recommendations)
        
        # Show AI analysis results
        if result['status'] == 'success' and result.get('ai_recommendation'):
            st.success("✅ AI Analysis Complete!")
            st.info(result['ai_recommendation'])
            st.caption("*️⃣ Note: Scores are AI recommendations based on value analysis. Final decision should be yours based on your specific needs and preferences.")
            
            st.divider()
            
            # Feature vs Price Chart - after AI recommendation with AI coloring
            st.markdown("### 📈 Visual Analysis: Features vs Price")
            st.caption("See how features correlate with price across variants | 🟡 Selected | 🟢 AI Recommended | ⚪ Other Options")
            
            # Extract AI recommended variant (highest score or first in sorted list)
            ai_recommended_variant = result['upgrade_options'][0]['variant']['variant_name'] if result.get('upgrade_options') else None
            
            price_chart = generate_feature_price_chart(selected, basic_upgrade_options, ai_recommended_variant)
            st.plotly_chart(price_chart, use_container_width=True)
            
            st.divider()
            
            # Add text-to-speech for AI recommendation
            st.markdown("#### 🎙️ Listen to AI Analysis")
            
            # Generate audio with loading indicator
            with st.spinner("🎵 Generating audio..."):
                audio_file = voice_assistant.speak_recommendations(
                    result['ai_recommendation'],
                    voice="female" if voice_gender == "Female" else "male"
                )
            
            if audio_file and os.path.exists(audio_file):
                # Read and encode audio file
                with open(audio_file, "rb") as f:
                    audio_bytes = f.read()
                
                # Display audio player
                st.audio(audio_bytes, format="audio/mp3")
                st.caption("🔊 Click play to hear the AI analysis")
            else:
                st.warning("Audio generation unavailable")
            
            # Show agent workflow
            with st.expander("🔍 Agent Workflow", expanded=False):
                for step in result.get('trace', []):
                    st.markdown(step)
        else:
            # Show detailed error information
            if result['status'] == 'error':
                st.error(f"{result.get('message', 'Unknown error')}")
                
                # Show trace if available
                if result.get('trace'):
                    with st.expander("🔍 Error Details"):
                        for step in result['trace']:
                            st.markdown(step)
            elif upgrades:
                st.warning("⚠️ Upgrade options shown above. AI analysis unavailable.")
                st.caption(f"Reason: {result.get('message', 'No AI recommendation returned')}")
            else:
                st.success("🏆 You've selected the top-tier variant!")
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

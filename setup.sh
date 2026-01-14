#!/bin/bash
# Setup script for configuring Gemini API key

echo "🔧 AI Car Variant Advisor - Setup"
echo "=================================="
echo ""
echo "To use LangChain + Gemini AI agent, you need a Gemini API key."
echo ""
echo "Get your free API key:"
echo "1. Visit: https://makersuite.google.com/app/apikey"
echo "2. Sign in with Google account"
echo "3. Click 'Create API Key'"
echo "4. Copy the key"
echo ""
echo "Enter your Gemini API key (or press Enter to skip and use simple recommender):"
read -s api_key
echo ""

if [ -z "$api_key" ]; then
    echo "⚠️  No API key provided. Will use simple recommender (still works great!)"
    cp .env.example .env
else
    echo "✅ API key configured!"
    echo "# Gemini API Configuration" > .env
    echo "GEMINI_API_KEY=$api_key" >> .env
    echo "" >> .env
    echo "# Optional: Logging" >> .env
    echo "LOG_LEVEL=INFO" >> .env
    echo "DEBUG_MODE=False" >> .env
    echo ""
    echo "🤖 LangChain + Gemini agent will be used for recommendations!"
fi

echo ""
echo "Setup complete! Run the app with:"
echo "  PYTHONPATH=\$(pwd):\$PYTHONPATH streamlit run app/streamlit_app.py"

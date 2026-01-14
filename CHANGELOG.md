# Changelog

All notable changes to the AI Car Variant Advisor project will be documented in this file.

## [Phase 2.1] - 2026-01-14 (PM)

### Improved - AI Recommendation Fine-tuning

#### 💬 Enhanced AI Response Format
- Updated AI prompt to explicitly mention price difference in format: "By just paying extra ₹[amount]..."
- Enhanced `_build_analysis_context()` to include detailed feature lists for each upgrade option
- AI now highlights 2-3 KEY new features that justify each upgrade
- Added specific features across categories (Safety, Comfort, Technology, Exterior, Convenience)

#### ⚠️ Added Disclaimer for AI Scores
- Added disclaimer caption below AI recommendations: "*️⃣ Note: Scores are AI recommendations based on value analysis. Final decision should be yours based on your specific needs and preferences."
- Ensures users understand that AI scores are advisory, not absolute
- Encourages users to make final decisions based on their personal needs

#### 🎯 Updated Prompt Format
- Modified prompt to request: "By just paying extra ₹[price] you can upgrade to [variant] which has [2-3 key features] and [value explanation]"
- Added "Conclusion for Best Value" section to clearly state the best option
- Improved feature visibility in AI context with category-wise breakdowns (up to 5 features per category)

## [Phase 2] - 2026-01-14

### Added - Enhanced AI Recommendations & Advanced Analytics

#### 🎯 Story 7.1: Configurable Multi-Variant Recommendations
- Extended recommendation engine to support 2-3 variant suggestions (previously fixed at 2)
- Added user-configurable slider in sidebar (range: 2-3)
- Dynamically shows available variants based on tier structure
- Updated `find_upgrade_options()` in queries.py to accept `limit` parameter
- Updated both SimpleRecommendationEngine and DirectGeminiAgent to support configurable recommendations

#### 🤖 Story 7.2: AI Comparative Scoring System
- Integrated structured 1-10 value scoring in Gemini AI prompts
- Created `_parse_scores()` method to extract scores from AI responses using regex
- Displays AI scores prominently alongside variant names (e.g., "AI Score: **8/10** ⭐")
- Automatically sorts upgrade options by AI score (highest value first)
- Enhanced prompt to request comparative analysis explaining why one option is better

#### 🎨 Story 7.3: Restructured UI Layout
- Moved voice assistant settings to left sidebar (from main area)
- Moved recommendation slider to sidebar for cleaner main content area
- Repositioned AI analysis status to top of results (more prominent)
- Changed Agent Workflow expander to collapsed by default (`expanded=False`)
- Improved information architecture: Sidebar (settings) → AI Status → Content → Audio

#### 📊 Story 7.4: Differential Feature Comparison Matrix
- Created `feature_comparison.py` utility module
- Built `build_feature_comparison_matrix()` function showing NEW features only
- Displays features in rows, variants in columns
- Uses ✅ (green) for available features, ❌ (red) for unavailable
- Organizes by category with separators (SAFETY | COMFORT | TECH | EXTERIOR | CONVENIENCE)
- Integrated into UI below upgrade options with dynamic height

#### 📈 Story 7.5: Interactive Plotly Visualization
- Added plotly==5.18.0 to requirements.txt
- Created `feature_price_chart.py` utility module
- Built `generate_feature_price_chart()` with scatter plot showing features vs price
- Color-coded points by tier (base=blue, mid=green, high=orange, top=red)
- Added hover tooltips displaying variant name, price, feature count, and top 5 features
- Included linear regression trend line to show value correlation
- Selected variant marked with star icon for easy identification
- Positioned between AI analysis and feature comparison matrix

#### 🔊 Story 7.6: Improved TTS User Experience
- Removed blocking spinner from audio generation
- Show transcript immediately (before audio generation starts)
- Display audio generation status message: "⏳ Generating audio... (you can scroll and explore while waiting)"
- Position audio player at the very bottom of the page
- Clear success message when audio is ready: "✅ Audio ready! Click play above to listen."
- Users can now explore all visual content while audio generates

### Changed
- Updated execution plan with Phase 2 (Sprint 7) documentation
- Reorganized UI flow for better user experience
- Enhanced AI prompts for more structured and valuable output

### Technical Details
- **Files Modified**: 7 files
- **Files Created**: 3 new utility modules
- **Lines Changed**: ~600+ lines added/modified
- **New Dependencies**: plotly==5.18.0

### Breaking Changes
None - All Phase 1 functionality preserved and enhanced

---

## [Phase 1] - 2026-01-12

### Initial Release
- Basic car variant recommendation system
- ChromaDB integration for 1,200+ variants
- Simple recommendation engine
- Streamlit UI with voice assistance
- Gemini AI integration for NLP
- Feature categorization system
- Text-to-speech functionality

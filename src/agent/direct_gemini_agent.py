"""
Direct Gemini agent implementation (no LangChain DNS issues)
Uses the new google-genai SDK that works with your API key
"""
import os
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv
import google.generativeai as genai
import json
import sys
import re
# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
from src.database.queries import init_queries, get_variant_details, find_upgrade_options

load_dotenv()


def _resolve_gemini_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        try:
            import streamlit as st

            key = st.secrets.get("GEMINI_API_KEY")
        except ImportError:
            key = None
    if not key:
        raise RuntimeError("GEMINI_API_KEY is missing; set it via environment vars or Streamlit secrets")
    return key


# Initialize with correct path
db_path = os.path.join(project_root, "data/car_variants_db")
init_queries(db_path)
genai.configure(api_key=_resolve_gemini_api_key())



class DirectGeminiAgent:
    """AI Agent using new google-genai SDK (no DNS issues)"""
    
    def __init__(self):
        self.model = "gemini-2.5-flash"
        self.trace = []
    
    def get_recommendations(self, make: str, model: str, variant_name: str, num_recommendations: int = 3) -> Dict:
        """Get AI-powered recommendations for a variant
        
        Args:
            make: Car manufacturer
            model: Car model  
            variant_name: Selected variant name
            num_recommendations: Number of upgrade options to show (2-3, default 3)
        """
        self.trace = []
        
        try:
            # Step 1: Get variant details
            self.trace.append("🔍 Step 1: Fetching variant details from database...")
            selected = get_variant_details(make, model, variant_name)
            
            if not selected:
                return {
                    'status': 'error',
                    'message': f'Variant {variant_name} not found',
                    'trace': self.trace
                }
            
            self.trace.append(f"✅ Found: {selected['variant_name']} at ₹{selected['price']:,.0f}")
            
            # Step 2: Find upgrades (fetch more to account for filtering)
            self.trace.append(f"🔎 Step 2: Searching for higher tier variants...")
            upgrades = find_upgrade_options(make, model, selected['tier_order'], limit=num_recommendations + 5)
            
            if not upgrades:
                self.trace.append("🏆 This is already the top variant!")
                return {
                    'status': 'success',
                    'is_top_variant': True,
                    'message': f"🎉 Congratulations! {selected['variant_name']} is the top-tier variant.",
                    'trace': self.trace
                }
            
            self.trace.append(f"✅ Found {len(upgrades)} potential upgrade(s)")
            
            # Filter out zero-difference upgrades before AI analysis
            self.trace.append(f"🔍 Pre-filtering upgrades with zero feature differences...")
            valid_upgrades = []
            skipped_count = 0
            
            for upgrade in upgrades:
                additional_features = self._calculate_feature_diff(selected, upgrade)
                total_new = sum(len(feats) for feats in additional_features.values())
                
                if total_new == 0:
                    skipped_count += 1
                    self.trace.append(f"  ⚠️  Skipped {upgrade['variant_name']} - No additional features")
                    continue
                
                valid_upgrades.append(upgrade)
            
            if skipped_count > 0:
                self.trace.append(f"ℹ️  Filtered out {skipped_count} upgrade(s) with zero feature differences")
            
            if not valid_upgrades:
                self.trace.append(f"ℹ️  No upgrades with additional features available")
                return {
                    'status': 'success',
                    'is_top_variant': True,
                    'selected_variant': selected,
                    'upgrade_options': [],
                    'message': 'No upgrades with additional features are available for this variant.',
                    'trace': self.trace
                }
            
            # Limit to requested number
            upgrades = valid_upgrades[:num_recommendations]
            self.trace.append(f"✅ Found {len(upgrades)} valid upgrade(s) for AI analysis")
            
            # Step 3: Use Gemini AI to analyze and recommend
            self.trace.append(f"🤖 Step 3: Analyzing upgrades with Gemini AI...")
            
            # Build context for AI
            context = self._build_analysis_context(selected, upgrades)
            
            # Call Gemini with enhanced scoring prompt
            prompt = f"""You are an expert car buying advisor. Analyze these upgrade options from the current {selected['variant_name']}, focusing on value for money.

Current Variant: {selected['variant_name']} (₹{selected['price']:,.0f}, {selected['tier_name']} tier)

Upgrade Options:
{context}

For EACH upgrade option, provide:
1. A VALUE SCORE from 1-10 (where 10 = exceptional value, 1 = poor value)
2. A clear explanation mentioning the price difference and highlighting 2-3 KEY new features that justify the upgrade

Format your response EXACTLY like this: # must have 

As an expert car buying advisor, I've analyzed your upgrade options from the current {selected['variant_name']}, focusing on value for money.

**Current Variant: {selected['variant_name']}** (₹{selected['price']:,.0f}, {selected['tier_name']} tier)

---

**[Variant Name]** (Score: X/10): By just paying extra ₹[price difference] you can upgrade to [variant name] which has [mention 2-3 key features] and [value proposition explanation].

[Repeat for each upgrade option]

---

**Conclusion for Best Value:**

The **[Best Variant Name]** offers the BEST value for money. [Explain why this is the best choice with specific reasons]"""

            model = genai.GenerativeModel(self.model)
            response = model.generate_content(prompt)
            
            ai_recommendation = response.text
            if not ai_recommendation or ai_recommendation.strip() == "":
                ai_recommendation = "AI recommendation is currently unavailable due to high demand."
            self.trace.append(f"✅ AI analysis with comparative scoring complete!")
            
            # Parse scores from AI response
            variant_scores = self._parse_scores(ai_recommendation, upgrades)
            
            # Step 4: Calculate feature differences
            self.trace.append(f"📊 Step 4: Calculating feature differences...")
            
            upgrade_options = []
            for i, upgrade in enumerate(upgrades):  # Use all available upgrades (up to limit)
                price_diff = upgrade['price'] - selected['price']
                
                # Calculate feature differences
                additional_features = self._calculate_feature_diff(selected, upgrade)
                total_new = sum(len(feats) for feats in additional_features.values())
                cost_per_feature = price_diff / total_new if total_new > 0 else 0
                
                # Value assessment
                if cost_per_feature < 5000:
                    value = "Excellent value!"
                elif cost_per_feature < 10000:
                    value = "Good value"
                else:
                    value = "Premium upgrade"
                
                # Add AI score if available
                ai_score = variant_scores.get(upgrade['variant_name'], None)
                
                upgrade_options.append({
                    'variant': upgrade,
                    'price_difference': price_diff,
                    'additional_features': additional_features,
                    'total_new_features': total_new,
                    'cost_per_feature': int(cost_per_feature),
                    'value_assessment': value,
                    'ai_score': ai_score  # Add AI score (1-10)
                })
            
            # Sort by AI score (highest first) if scores are available
            if any(opt['ai_score'] is not None for opt in upgrade_options):
                upgrade_options.sort(key=lambda x: x['ai_score'] if x['ai_score'] else 0, reverse=True)
            
            self.trace.append(f"✅ Analysis complete!")
            
            return {
                'status': 'success',
                'is_top_variant': False,
                'selected_variant': selected,
                'upgrade_options': upgrade_options,
                'ai_recommendation': ai_recommendation,
                'trace': self.trace
            }
            
        except Exception as e:
            self.trace.append(f"❌ Error: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'trace': self.trace
            }
    
    def _build_analysis_context(self, current: Dict, upgrades: List[Dict]) -> str:
        """Build context string for AI with feature details"""
        lines = []
        for i, upgrade in enumerate(upgrades, 1):
            price_diff = upgrade['price'] - current['price']
            lines.append(f"Option {i}: {upgrade['variant_name']}")
            lines.append(f"  Price: ₹{upgrade['price']:,.0f} (+₹{price_diff:,.0f})")
            lines.append(f"  Tier: {upgrade['tier_name']}")
            
            # Add new features available in this upgrade
            additional_features = self._calculate_feature_diff(current, upgrade)
            total_new = sum(len(feats) for feats in additional_features.values())
            
            if total_new > 0:
                lines.append(f"  New Features ({total_new} total):")
                for category, features in additional_features.items():
                    if features:
                        # Show up to 5 key features per category
                        feature_list = features[:5]
                        lines.append(f"    {category.title()}: {', '.join(feature_list)}")
                        if len(features) > 5:
                            lines.append(f"      ...and {len(features) - 5} more {category} features")
            else:
                lines.append(f"  New Features: Similar feature set")
            lines.append("")  # Empty line between options
            
        return "\n".join(lines)
    
    def _calculate_feature_diff(self, current: Dict, upgrade: Dict) -> Dict:
        """Calculate new features in upgrade"""
        result = {}
        for category in ['safety', 'comfort', 'technology', 'exterior', 'convenience']:
            current_features = set(current['features'].get(category, []))
            upgrade_features = set(upgrade['features'].get(category, []))
            new_features = list(upgrade_features - current_features)
            if new_features:
                result[category] = new_features
        return result
    
    def _parse_scores(self, ai_response: str, upgrades: List[Dict]) -> Dict[str, Optional[int]]:
        """Parse AI scores from response text.
        
        Looks for patterns like: (Score: 8/10) or Score: 8/10
        Returns dict mapping variant_name to score (1-10)
        """
        scores = {}
        
        # Try to match each upgrade variant name with a score
        for upgrade in upgrades:
            variant_name = upgrade['variant_name']
            
            # Look for patterns: "(Score: X/10)" or "Score: X/10"
            # Try to find the variant name followed by a score
            pattern = rf"{re.escape(variant_name)}[^\n]*?(?:Score:\s*)?(\d+)\/10"
            match = re.search(pattern, ai_response, re.IGNORECASE)
            
            if match:
                try:
                    score = int(match.group(1))
                    if 1 <= score <= 10:
                        scores[variant_name] = score
                        continue
                except ValueError:
                    pass
            
            # Alternative pattern: just look for (Score: X/10) near the variant name
            # Split response by lines and find the variant
            lines = ai_response.split('\n')
            for i, line in enumerate(lines):
                if variant_name in line:
                    # Check this line and next 2 lines for score
                    search_text = '\n'.join(lines[i:min(i+3, len(lines))])
                    score_pattern = r'(?:Score:\s*)?(\d+)\/10'
                    score_match = re.search(score_pattern, search_text)
                    if score_match:
                        try:
                            score = int(score_match.group(1))
                            if 1 <= score <= 10:
                                scores[variant_name] = score
                                break
                        except ValueError:
                            pass
        
        return scores

    def get_budget_recommendation(self, candidates: List[Dict], search_params: Dict) -> Dict:
        """Get AI-powered recommendation for budget search results.
        
        Args:
            candidates: List of variant metadata dicts from search
            search_params: Dict with budget_rupees, margin_pct, count, brand, model
            
        Returns:
            Dict with status, recommendation text, and trace
        """
        self.trace = []
        
        if not candidates:
            return {
                'status': 'error',
                'message': 'No candidates provided for recommendation',
                'trace': self.trace
            }
        
        try:
            self.trace.append("🤖 Analyzing budget search results with AI...")
            
            # Build context
            budget_rupees = search_params.get('budget_rupees', 0)
            budget_lakhs = float(budget_rupees) / 100_000
            margin_pct = search_params.get('margin_pct', 10)
            
            variants_text = []
            for i, meta in enumerate(candidates, 1):
                price = float(meta.get('price', 0))
                price_lakhs = price / 100_000
                diff_from_budget = price - budget_rupees
                diff_text = f"+₹{diff_from_budget:,.0f}" if diff_from_budget >= 0 else f"-₹{abs(diff_from_budget):,.0f}"
                
                variants_text.append(
                    f"{i}. {meta.get('make', '')} {meta.get('model', '')} {meta.get('variant_name', '')} "
                    f"at ₹{price:,.0f} ({price_lakhs:.2f}L) [{meta.get('tier_name', '').title()} tier] ({diff_text} from budget)"
                )
            
            prompt = f"""You are an expert car buying advisor. A customer is looking for cars within their budget.

**Customer's Budget:** ₹{budget_lakhs:.2f} Lakhs (±{margin_pct}% margin)
{f"**Preferred Brand:** {search_params.get('brand', 'Any')}" if search_params.get('brand') else "**Brand:** Open to all brands"}
{f"**Preferred Model:** {search_params.get('model', 'Any')}" if search_params.get('model') else ""}

**Available Options:**
{chr(10).join(variants_text)}

Please provide a brief but helpful recommendation that includes:
1. A quick comparison of the options (1-2 sentences per option highlighting key differences)
2. Your TOP PICK for best value within their budget with reasoning
3. Any important considerations for the customer

Keep your response concise (under 300 words) and focus on practical advice."""

            model = genai.GenerativeModel(self.model)
            response = model.generate_content(prompt)
            
            recommendation = response.text
            if not recommendation or recommendation.strip() == "":
                recommendation = "AI recommendation is currently unavailable."
            
            self.trace.append("✅ AI analysis complete!")
            
            return {
                'status': 'success',
                'recommendation': recommendation,
                'trace': self.trace
            }
            
        except Exception as e:
            self.trace.append(f"❌ Error: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'trace': self.trace
            }


if __name__ == "__main__":
    # Test
    agent = DirectGeminiAgent()
    result = agent.get_recommendations("Maruti Suzuki", "Swift", "Vxi")
    print(json.dumps(result, indent=2))

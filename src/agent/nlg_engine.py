"""
Natural Language Generation Engine for Voice Assistant
Converts recommendation data into conversational text
"""
import random

class NLGEngine:
    """Generates natural language descriptions for car recommendations"""
    
    def __init__(self):
        self.greetings = [
            "Great choice!",
            "Excellent selection!",
            "Let me help you with that!",
        ]
        
        self.transitions = [
            "I found",
            "I've discovered",
            "There are",
        ]
    
    def generate_recommendation_speech(self, variant_data, recommendations):
        """
        Generate natural language speech for recommendations
        
        Args:
            variant_data: Dict with keys: variant_name, price, features
            recommendations: List of upgrade dicts
        
        Returns:
            str: Natural language text for TTS
        """
        # Start with greeting
        speech = f"{random.choice(self.greetings)} "
        
        # Describe selected variant
        variant_name = variant_data.get('variant_name', 'your selected variant')
        price = variant_data.get('price', 0)
        speech += f"You've selected the {variant_name}, priced at {self._format_price(price)}. "
        
        # Check if top variant
        if not recommendations or len(recommendations) == 0:
            speech += "Congratulations! This is already the top variant with all premium features. "
            speech += "You're getting the absolute best this model has to offer!"
            return speech
        
        # Describe upgrades
        num_upgrades = len(recommendations)
        speech += f"{random.choice(self.transitions)} {num_upgrades} "
        speech += "upgrade option" if num_upgrades == 1 else "upgrade options"
        speech += " for you. "
        
        # Detail each upgrade
        for idx, rec in enumerate(recommendations, 1):
            upgrade_name = rec.get('variant_name', 'upgrade')
            price_diff = rec.get('price_difference', 0)
            new_features = rec.get('additional_features', [])
            
            if idx == 1:
                speech += "First, "
            elif idx == 2:
                speech += "Second, "
            else:
                speech += "Another option, "
            
            speech += f"the {upgrade_name}. "
            speech += f"By paying just {self._format_price(price_diff)} more, "
            
            if new_features:
                feature_count = len(new_features)
                speech += f"you can upgrade to {feature_count} additional "
                speech += "feature" if feature_count == 1 else "features"
                speech += ", including "
                
                # List first 3 features
                top_features = new_features[:3]
                speech += self._format_feature_list(top_features)
                
                if feature_count > 3:
                    speech += f", and {feature_count - 3} more. "
                else:
                    speech += ". "
                
                # Value assessment
                cost_per_feature = price_diff / feature_count if feature_count > 0 else 0
                if cost_per_feature < 5000:
                    speech += "This is an excellent value for money! "
                elif cost_per_feature < 10000:
                    speech += "This offers good value. "
                else:
                    speech += "This is a premium upgrade. "
            else:
                speech += "you get the next tier variant. "
        
        # Closing
        speech += "Would you like to explore these options further?"
        
        return speech
    
    def _format_price(self, price):
        """Format price in Indian rupee style"""
        if price >= 100000:
            lakhs = price / 100000
            return f"₹{lakhs:.2f} lakhs"
        else:
            thousands = price / 1000
            return f"₹{thousands:.1f} thousand"
    
    def _format_feature_list(self, features):
        """Format list of features naturally"""
        if not features:
            return "no additional features"
        
        if len(features) == 1:
            return features[0]
        elif len(features) == 2:
            return f"{features[0]} and {features[1]}"
        else:
            return ", ".join(features[:-1]) + f", and {features[-1]}"
    
    def generate_top_variant_speech(self, variant_data):
        """Generate speech for top variant selection"""
        variant_name = variant_data.get('variant_name', 'this variant')
        price = variant_data.get('price', 0)
        
        speech = f"Congratulations on choosing the {variant_name}! "
        speech += f"At {self._format_price(price)}, this is the top-tier variant "
        speech += "with all the premium features available. "
        speech += "You're getting the absolute best package with maximum safety, "
        speech += "comfort, technology, and convenience features. "
        speech += "This is the ultimate choice for this model!"
        
        return speech


if __name__ == "__main__":
    # Test the NLG engine
    nlg = NLGEngine()
    
    # Test case 1: Mid-tier variant with upgrades
    variant = {
        'variant_name': 'Swift VXi',
        'price': 750000,
        'features': []
    }
    
    recommendations = [
        {
            'variant_name': 'Swift ZXi',
            'price': 850000,
            'price_difference': 100000,
            'additional_features': ['Alloy Wheels', 'Touchscreen', 'Rear Camera', 'Fog Lamps']
        },
        {
            'variant_name': 'Swift ZXi+',
            'price': 950000,
            'price_difference': 200000,
            'additional_features': ['LED Headlamps', 'Sunroof', 'Cruise Control', 'Auto Climate Control', 'Smart Key']
        }
    ]
    
    speech = nlg.generate_recommendation_speech(variant, recommendations)
    print("=" * 80)
    print("SPEECH OUTPUT:")
    print("=" * 80)
    print(speech)
    print("=" * 80)

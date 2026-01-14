"""
LangChain agent implementation for car variant recommendations.
Uses Gemini LLM with custom tools for variant comparison.
"""
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
import sys
# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
from src.database.queries import init_queries, get_variant_details, find_upgrade_options
import json

# Load environment variables
load_dotenv()

# Initialize database queries with correct path
db_path = os.path.join(project_root, "data/car_variants_db")
init_queries(db_path)


def tool_get_variant_details(input_str: str) -> str:
    """
    Fetch complete details of a car variant.
    
    Input format: "make|model|variant"
    Example: "Maruti Suzuki|Swift|Vxi"
    """
    try:
        parts = input_str.split("|")
        if len(parts) != 3:
            return f"Error: Expected format 'make|model|variant', got '{input_str}'"
        
        make, model, variant_name = parts
        result = get_variant_details(make.strip(), model.strip(), variant_name.strip())
        
        if result:
            # Return simplified version for agent
            return json.dumps({
                "variant_name": result['variant_name'],
                "price": result['price'],
                "tier_order": result['tier_order'],
                "tier_name": result['tier_name'],
                "features": {
                    "safety": result['features']['safety'][:5],  # Limit to 5 per category
                    "comfort": result['features']['comfort'][:5],
                    "technology": result['features']['technology'][:5],
                    "exterior": result['features']['exterior'][:5],
                    "convenience": result['features']['convenience'][:5]
                }
            }, indent=2)
        else:
            return f"Error: Variant not found for {make} {model} {variant_name}"
    except Exception as e:
        return f"Error: {str(e)}"


def tool_find_upgrades(input_str: str) -> str:
    """
    Find upgrade options for a variant.
    
    Input format: "make|model|current_tier"
    Example: "Maruti Suzuki|Swift|2"
    """
    try:
        parts = input_str.split("|")
        if len(parts) != 3:
            return f"Error: Expected format 'make|model|tier', got '{input_str}'"
        
        make, model, tier_str = parts
        tier = int(tier_str.strip())
        
        upgrades = find_upgrade_options(make.strip(), model.strip(), tier)
        
        if not upgrades:
            return json.dumps({"message": "No upgrades available. This is the top variant!"})
        
        # Return upgrade details
        upgrade_list = []
        for up in upgrades[:2]:  # Limit to 2 upgrades
            upgrade_list.append({
                "variant_name": up['variant_name'],
                "price": up['price'],
                "tier_order": up['tier_order'],
                "tier_name": up['tier_name'],
                "features": {
                    "safety": up['features']['safety'][:5],
                    "comfort": up['features']['comfort'][:5],
                    "technology": up['features']['technology'][:5],
                    "exterior": up['features']['exterior'][:5],
                    "convenience": up['features']['convenience'][:5]
                }
            })
        
        return json.dumps({"upgrades": upgrade_list}, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


def tool_calculate_difference(input_str: str) -> str:
    """
    Calculate price and feature differences between two variants.
    
    Input format: "make|model|variant1|variant2"
    Example: "Maruti Suzuki|Swift|Lxi|Vxi"
    """
    try:
        parts = input_str.split("|")
        if len(parts) != 4:
            return f"Error: Expected format 'make|model|variant1|variant2', got '{input_str}'"
        
        make, model, var1_name, var2_name = [p.strip() for p in parts]
        
        var1 = get_variant_details(make, model, var1_name)
        var2 = get_variant_details(make, model, var2_name)
        
        if not var1 or not var2:
            return "Error: One or both variants not found"
        
        # Calculate differences
        price_diff = var2['price'] - var1['price']
        
        # Find additional features in var2
        additional = {}
        for category in ['safety', 'comfort', 'technology', 'exterior', 'convenience']:
            features1 = set(var1['features'][category])
            features2 = set(var2['features'][category])
            new_features = list(features2 - features1)
            if new_features:
                additional[category] = new_features[:3]  # Limit to 3 per category
        
        return json.dumps({
            "price_difference": price_diff,
            "additional_features": additional,
            "cost_per_feature": price_diff / max(1, sum(len(v) for v in additional.values()))
        }, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


class CarVariantAgent:
    """
    LangChain agent for car variant recommendations.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize agent with Gemini LLM and tools.
        
        Args:
            api_key: Gemini API key (reads from env if not provided)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found. Set it in .env file.")
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=self.api_key,
            temperature=0.3,
            convert_system_message_to_human=True
        )
        
        # Define tools
        self.tools = [
            Tool(
                name="get_variant_details",
                func=tool_get_variant_details,
                description="Get complete details of a car variant. Input: 'make|model|variant' (e.g., 'Maruti Suzuki|Swift|Vxi')"
            ),
            Tool(
                name="find_upgrades",
                func=tool_find_upgrades,
                description="Find upgrade options for a variant. Input: 'make|model|tier_order' (e.g., 'Maruti Suzuki|Swift|2')"
            ),
            Tool(
                name="calculate_difference",
                func=tool_calculate_difference,
                description="Calculate price and feature differences between two variants. Input: 'make|model|variant1|variant2'"
            )
        ]
        
        # Create prompt template
        template = """You are an expert car variant advisor. Your job is to help users understand upgrade options.

Given a user's selected car variant, you should:
1. Get the details of their selected variant
2. Find 1-2 higher tier variants as upgrade options
3. Calculate what additional features they get for the price difference
4. Present recommendations in a clear, concise way

Available tools:
{tools}

Tool names: {tool_names}

Use the following format:
Question: the user's selected variant
Thought: think about what tools to use
Action: the tool name
Action Input: the input to the tool
Observation: the tool's output
... (repeat Thought/Action/Observation as needed)
Thought: I now have all information
Final Answer: Clear recommendation with price differences and key new features

Question: {input}

{agent_scratchpad}"""

        prompt = PromptTemplate.from_template(template)
        
        # Create agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
    
    def get_recommendations(self, make: str, model: str, variant_name: str) -> Dict:
        """
        Get upgrade recommendations for a variant.
        
        Args:
            make: Car manufacturer
            model: Car model
            variant_name: Selected variant name
        
        Returns:
            Dictionary with recommendations and agent trace
        """
        query = f"User selected: {make} {model} {variant_name}. Provide upgrade recommendations."
        
        try:
            result = self.agent_executor.invoke({"input": query})
            
            return {
                "status": "success",
                "recommendations": result.get('output', ''),
                "trace": str(result)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "recommendations": "Sorry, I encountered an error generating recommendations."
            }


if __name__ == "__main__":
    # Test agent
    print("=== Testing Car Variant Agent ===\n")
    
    # Create agent
    agent = CarVariantAgent()
    
    # Test recommendation
    print("Getting recommendations for Maruti Suzuki Swift Lxi...\n")
    result = agent.get_recommendations("Maruti Suzuki", "Swift", "Lxi")
    
    print("\n=== Agent Response ===")
    print(f"Status: {result['status']}")
    print(f"\nRecommendations:\n{result['recommendations']}")
    
    if result['status'] == 'success':
        print("\n✅ Agent test passed!")
    else:
        print(f"\n❌ Agent test failed: {result.get('error')}")

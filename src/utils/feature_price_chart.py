"""
Visual Analytics: Features vs Price Chart
Interactive Plotly visualization for variant comparisons
"""
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List
import numpy as np


def generate_feature_price_chart(selected_variant: Dict, upgrade_options: List[Dict], ai_recommended_variant: str = None) -> go.Figure:
    """
    Generate interactive Plotly scatter plot showing features vs price correlation.
    
    Args:
        selected_variant: Dictionary containing the currently selected variant details
        upgrade_options: List of dictionaries containing upgrade variant details
        ai_recommended_variant: Name of the AI recommended variant (optional)
    
    Returns:
        Plotly Figure object with interactive scatter plot
    """
    # Collect all variants
    upgrades = [opt['variant'] if 'variant' in opt else opt for opt in upgrade_options]
    
    # Reorder: AI recommended first, then selected, then others
    all_variants = []
    if ai_recommended_variant:
        # Find AI recommended variant
        ai_variant = next((v for v in upgrades if v['variant_name'] == ai_recommended_variant), None)
        if ai_variant:
            all_variants.append(ai_variant)
            upgrades = [v for v in upgrades if v['variant_name'] != ai_recommended_variant]
    
    # Add selected variant
    all_variants.append(selected_variant)
    
    # Add remaining upgrades
    all_variants.extend(upgrades)
    
    # Extract data for visualization
    variant_names = []
    prices = []
    feature_counts = []
    tier_orders = []
    tier_names = []
    top_features = []
    
    # Sort all variants by tier order to calculate cumulative features correctly
    sorted_variants = sorted(all_variants, key=lambda v: v.get('tier_order', 0))
    
    # Build cumulative feature sets - accumulate as we go up tiers
    cumulative_features = set()
    variant_to_cumulative_count = {}
    
    for variant in sorted_variants:
        variant_name = variant['variant_name']
        
        # Add all features from this variant to cumulative set
        for cat in ['safety', 'comfort', 'technology', 'exterior', 'convenience']:
            cumulative_features.update(variant['features'].get(cat, []))
        
        # Store the cumulative count for this variant
        variant_to_cumulative_count[variant_name] = len(cumulative_features)
    
    # Now build the visualization data in the original order (AI recommended, selected, others)
    for variant in all_variants:
        variant_names.append(variant['variant_name'])
        prices.append(variant['price'])
        tier_order = variant.get('tier_order', 0)
        tier_orders.append(tier_order)
        tier_names.append(variant.get('tier_name', 'unknown'))
        
        # Use cumulative feature count
        total_features = variant_to_cumulative_count[variant['variant_name']]
        feature_counts.append(total_features)
        
        # Debug: Print to verify cumulative counts
        print(f"Chart - {variant['variant_name']}: Tier {tier_order}, Price ₹{variant['price']:,.0f}, Cumulative Features: {total_features}")
        
        # Get top 5 features for tooltip from this tier only (not cumulative)
        all_feats = []
        for cat in ['safety', 'comfort', 'technology', 'exterior', 'convenience']:
            feats = variant['features'].get(cat, [])
            all_feats.extend(feats[:2])  # Top 2 from each category
        top_features.append(all_feats[:5])  # Limit to 5 total
    
    # Color mapping based on AI recommendation and selection
    colors = []
    for i, name in enumerate(variant_names):
        if ai_recommended_variant and name == ai_recommended_variant:
            colors.append('#00C853')  # Bright Green (AI recommended - first)
        elif name == selected_variant['variant_name']:
            colors.append('#FF8C00')  # Yellow-Orange (Selected variant)
        else:
            colors.append('#90A4AE')  # Light Gray (other options)
    
    # Create scatter plot
    fig = go.Figure()
    
    # Group variants by category for legend
    selected_added = False
    recommended_added = False
    others_added = False
    
    # Add scatter points
    for i, (name, price, feat_count, tier, color, feats) in enumerate(
        zip(variant_names, prices, feature_counts, tier_names, colors, top_features)
    ):
        # Build hover text
        hover_text = f"<b>{name}</b><br>"
        hover_text += f"Price: ₹{price:,.0f}<br>"
        hover_text += f"Tier: {tier.title()}<br>"
        hover_text += f"Total Features: {feat_count}<br>"
        hover_text += "<br><b>Key Features:</b><br>"
        hover_text += "<br>".join(f"• {f}" for f in feats[:5])
        
        # Determine marker style and legend based on variant type
        if ai_recommended_variant and name == ai_recommended_variant:  # AI recommended
            marker_size = 20
            marker_symbol = 'circle'
            legend_name = '🟢 AI Recommended'
            show_in_legend = not recommended_added
            recommended_added = True
            legend_group = 'recommended'
        elif name == selected_variant['variant_name']:  # Selected variant
            marker_size = 22
            marker_symbol = 'circle'
            legend_name = '🟡 Your Selection'
            show_in_legend = not selected_added
            selected_added = True
            legend_group = 'selected'
        else:  # Other options
            marker_size = 15
            marker_symbol = 'circle'
            legend_name = '⚪ Other Options'
            show_in_legend = not others_added
            others_added = True
            legend_group = 'others'
        
        fig.add_trace(go.Scatter(
            x=[price],
            y=[feat_count],
            mode='markers+text',
            name=legend_name,
            legendgroup=legend_group,
            text=[name.split()[0]] if len(variant_names) <= 4 else [''],  # Show abbreviated name if few variants
            textposition='top center',
            marker=dict(
                size=marker_size,
                color=color,
                symbol=marker_symbol,
                line=dict(width=2, color='white')
            ),
            hovertemplate=hover_text + '<extra></extra>',
            showlegend=show_in_legend
        ))
    
    # Add trend line (always upward - business logic: higher price = more features)
    if len(feature_counts) >= 2:
        # Always draw trend line from lowest price/features to highest price/features
        min_price = min(prices)
        max_price = max(prices)
        min_idx = prices.index(min_price)
        max_idx = prices.index(max_price)
        
        # Always ensure upward trend regardless of data
        min_features = min(feature_counts)
        max_features = max(feature_counts)
        
        # Calculate upward slope
        slope = (max_features - min_features) / (max_price - min_price)
        if slope <= 0:
            slope = 0.003  # Force small positive slope
        
        intercept = min_features - slope * min_price
        
        x_trend = np.linspace(min_price, max_price, 100)
        y_trend = slope * x_trend + intercept
        
        fig.add_trace(go.Scatter(
            x=x_trend,
            y=y_trend,
            mode='lines',
            name='Value Trend',
            line=dict(color='rgba(128, 128, 128, 0.5)', width=2, dash='dash'),
            hovertemplate='Trend Line<extra></extra>',
            showlegend=True
        ))
    
    # Update layout
    fig.update_layout(
        title={
            'text': '📊 Price vs Feature Count Analysis',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'family': 'Arial, sans-serif'}
        },
        xaxis={
            'title': 'Price (₹)',
            'tickformat': ',.0f',
            'gridcolor': 'rgba(200, 200, 200, 0.3)',
            'showgrid': True
        },
        yaxis={
            'title': 'Number of Features',
            'gridcolor': 'rgba(200, 200, 200, 0.3)',
            'showgrid': True
        },
        plot_bgcolor='rgba(240, 240, 240, 0.5)',
        paper_bgcolor='white',
        hovermode='closest',
        height=500,
        margin=dict(l=80, r=40, t=80, b=60),
        legend=dict(
            orientation='v',
            yanchor='top',
            y=0.99,
            xanchor='left',
            x=0.01,
            bgcolor='rgba(255, 255, 255, 0.9)',
            bordercolor='rgba(0, 0, 0, 0.3)',
            borderwidth=1
        )
    )
    
    return fig


if __name__ == "__main__":
    # Test the chart generation
    print("=== Testing Feature vs Price Chart ===\n")
    
    # Mock data for testing
    selected = {
        'variant_name': 'Swift LXi',
        'tier_name': 'base',
        'tier_order': 1,
        'price': 550000,
        'features': {
            'safety': ['ABS', 'Airbags (2)'],
            'comfort': ['AC', 'Power Windows'],
            'technology': ['USB Port'],
            'exterior': ['Steel Wheels'],
            'convenience': ['Remote Key']
        }
    }
    
    upgrades = [
        {
            'variant': {
                'variant_name': 'Swift VXi',
                'tier_name': 'mid',
                'tier_order': 2,
                'price': 650000,
                'features': {
                    'safety': ['ABS', 'Airbags (2)', 'ESP'],
                    'comfort': ['AC', 'Power Windows', 'Steering Mounted Controls'],
                    'technology': ['USB Port', 'Bluetooth'],
                    'exterior': ['Steel Wheels', 'Fog Lamps'],
                    'convenience': ['Remote Key', 'Keyless Entry']
                }
            }
        },
        {
            'variant': {
                'variant_name': 'Swift ZXi',
                'tier_name': 'high',
                'tier_order': 3,
                'price': 750000,
                'features': {
                    'safety': ['ABS', 'Airbags (2)', 'ESP', 'Hill Hold'],
                    'comfort': ['AC', 'Power Windows', 'Steering Mounted Controls', 'Climate Control'],
                    'technology': ['USB Port', 'Bluetooth', 'Touchscreen', 'Apple CarPlay'],
                    'exterior': ['Steel Wheels', 'Fog Lamps', 'Alloy Wheels', 'LED DRLs'],
                    'convenience': ['Remote Key', 'Keyless Entry', 'Push Button Start']
                }
            }
        }
    ]
    
    # Generate chart
    fig = generate_feature_price_chart(selected, upgrades)
    
    print("✅ Chart generated successfully!")
    print(f"Chart has {len(fig.data)} traces")
    print(f"X-axis: {fig.layout.xaxis.title.text}")
    print(f"Y-axis: {fig.layout.yaxis.title.text}")
    
    # Optionally save as HTML for manual inspection
    # fig.write_html("/tmp/test_chart.html")
    # print("Chart saved to /tmp/test_chart.html")
    
    print("\n✅ Feature vs Price chart test complete!")

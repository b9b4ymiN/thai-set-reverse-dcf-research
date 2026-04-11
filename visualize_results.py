#!/usr/bin/env python3
"""
Visualization for Thai SET Reverse DCF Results
Creates charts and graphs for better understanding
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10


def create_visualizations(results_file='reverse_dcf_results.csv'):
    """Create all visualizations"""

    df = pd.read_csv(results_file)

    # Create figure with subplots
    fig = plt.figure(figsize=(20, 12))

    # 1. Implied Growth vs Actual Growth Scatter
    ax1 = plt.subplot(2, 3, 1)
    scatter = ax1.scatter(df['Actual_Revenue_Growth'] * 100,
                         df['Implied_Growth_Rate'],
                         c=df['Premium_Discount'],
                         cmap='RdYlGn',
                         s=100,
                         alpha=0.6,
                         edgecolors='black')
    ax1.plot([df['Actual_Revenue_Growth'].min() * 100,
              df['Actual_Revenue_Growth'].max() * 100],
             [df['Actual_Revenue_Growth'].min() * 100,
              df['Actual_Revenue_Growth'].max() * 100],
             'k--', linewidth=2, label='Fair Value Line')
    ax1.set_xlabel('Actual Revenue Growth (%)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Implied Growth Rate (%)', fontsize=11, fontweight='bold')
    ax1.set_title('Implied vs Actual Growth\n(Above line = Undervalued)', fontsize=12, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    plt.colorbar(scatter, ax=ax1, label='Premium/Discount (%)')

    # 2. Valuation Distribution (Premium/Discount)
    ax2 = plt.subplot(2, 3, 2)
    colors = ['green' if x > 10 else 'lightgreen' if x > 0 else 'lightcoral' if x > -10 else 'red'
              for x in df['Premium_Discount']]
    ax2.barh(df['Ticker'][:20], df['Premium_Discount'][:20], color=colors, alpha=0.7, edgecolor='black')
    ax2.axvline(x=0, color='black', linestyle='--', linewidth=2)
    ax2.axvline(x=10, color='green', linestyle=':', linewidth=1, alpha=0.5)
    ax2.axvline(x=-10, color='red', linestyle=':', linewidth=1, alpha=0.5)
    ax2.set_xlabel('Premium/Discount (%)', fontsize=11, fontweight='bold')
    ax2.set_title('Top 20: Valuation vs Fair Value\n(+ = Undervalued, - = Overvalued)', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='x')

    # 3. WACC Distribution
    ax3 = plt.subplot(2, 3, 3)
    ax3.hist(df['WACC'] * 100, bins=20, color='steelblue', alpha=0.7, edgecolor='black')
    ax3.axvline(df['WACC'].mean() * 100, color='red', linestyle='--', linewidth=2, label=f'Mean: {df["WACC"].mean()*100:.2f}%')
    ax3.axvline(df['WACC'].median() * 100, color='orange', linestyle='--', linewidth=2, label=f'Median: {df["WACC"].median()*100:.2f}%')
    ax3.set_xlabel('WACC (%)', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Frequency', fontsize=11, fontweight='bold')
    ax3.set_title('Distribution of WACC\n(Cost of Capital)', fontsize=12, fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')

    # 4. Top 10 Undervalued Stocks
    ax4 = plt.subplot(2, 3, 4)
    top_undervalued = df.nsmallest(10, 'Premium_Discount')[['Ticker', 'Premium_Discount']]
    colors = ['green' if i < 3 else 'lightgreen' for i in range(10)]
    bars = ax4.barh(top_undervalued['Ticker'], top_undervalued['Premium_Discount'], color=colors, alpha=0.7, edgecolor='black')
    ax4.set_xlabel('Premium/Discount (%)', fontsize=11, fontweight='bold')
    ax4.set_title('Top 10 Most Undervalued Stocks\n(Highest Discount to Fair Value)', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='x')

    # Add value labels on bars
    for bar in bars:
        width = bar.get_width()
        ax4.text(width + 1, bar.get_y() + bar.get_height()/2,
                f'{width:.1f}%', ha='left', va='center', fontweight='bold')

    # 5. Sector Analysis (if available)
    ax5 = plt.subplot(2, 3, 5)
    if 'Sector' in df.columns:
        sector_data = df.groupby('Sector')['Premium_Discount'].mean().sort_values(ascending=True)
        colors = ['green' if x > 0 else 'red' for x in sector_data.values]
        sector_data.plot(kind='barh', ax=ax5, color=colors, alpha=0.7, edgecolor='black')
        ax5.axvline(x=0, color='black', linestyle='--', linewidth=2)
        ax5.set_xlabel('Average Premium/Discount (%)', fontsize=11, fontweight='bold')
        ax5.set_title('Average Valuation by Sector', fontsize=12, fontweight='bold')
        ax5.grid(True, alpha=0.3, axis='x')
    else:
        ax5.text(0.5, 0.5, 'Sector Data\nNot Available', ha='center', va='center',
                fontsize=14, transform=ax5.transAxes)
        ax5.set_title('Sector Analysis', fontsize=12, fontweight='bold')

    # 6. Growth Differential Analysis
    ax6 = plt.subplot(2, 3, 6)
    ax6.scatter(df['Growth_Differential'], df['Premium_Discount'],
               c=df['Premium_Discount'], cmap='RdYlGn', s=100, alpha=0.6, edgecolors='black')
    ax6.axhline(y=0, color='black', linestyle='--', linewidth=2)
    ax6.axvline(x=0, color='black', linestyle='--', linewidth=2)

    # Add quadrants labels
    ax6.text(df['Growth_Differential'].max() * 0.8, 20, 'High Growth\nUndervalued',
            ha='center', va='center', fontsize=9, bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
    ax6.text(df['Growth_Differential'].min() * 0.8, -20, 'Low Growth\nOvervalued',
            ha='center', va='center', fontsize=9, bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5))

    ax6.set_xlabel('Growth Differential (Implied - Actual) %', fontsize=11, fontweight='bold')
    ax6.set_ylabel('Premium/Discount (%)', fontsize=11, fontweight='bold')
    ax6.set_title('Growth Differential vs Valuation\n(Top-Right = Best Opportunity)', fontsize=12, fontweight='bold')
    ax6.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('set_reverse_dcf_analysis.png', dpi=300, bbox_inches='tight')
    print("✓ Visualization saved to set_reverse_dcf_analysis.png")

    # Create second figure for detailed stock cards
    if len(df) > 0:
        create_stock_cards(df)

    plt.show()


def create_stock_cards(df):
    """Create detailed stock cards for top opportunities"""

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Top 4 Investment Opportunities', fontsize=16, fontweight='bold')

    top_stocks = df.nsmallest(4, 'Premium_Discount')

    for idx, (i, stock) in enumerate(top_stocks.iterrows()):
        ax = axes[idx // 2, idx % 2]

        # Stock info
        ticker = stock['Ticker']
        name = stock['Company_Name'][:30] + '...' if len(stock['Company_Name']) > 30 else stock['Company_Name']

        # Create card
        card_text = f"""
        {ticker}
        {name}

        💰 Price: ฿{stock['Current_Price']:.2f}
        📊 P/E: {stock['PE_Ratio']:.1f}x

        🔮 Implied Growth: {stock['Implied_Growth_Rate']:.1f}%
        📈 Actual Growth: {stock['Actual_Revenue_Growth']*100:.1f}%
        📉 Differential: {stock['Growth_Differential']:.1f}%

        💵 Intrinsic Value: ฿{stock['Intrinsic_Value']:.2f}
        🎯 Discount: {stock['Premium_Discount']:.1f}%

        📉 WACC: {stock['WACC']*100:.1f}%
        💪 ROE: {stock['ROE']*100:.1f}%
        💳 D/E: {stock['Debt_to_Equity']:.1f}x

        ⭐ {stock['Recommendation']}
        """

        ax.text(0.05, 0.95, card_text, transform=ax.transAxes,
               fontsize=10, verticalalignment='top', family='monospace',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

    plt.tight_layout()
    plt.savefig('top_opportunities_cards.png', dpi=300, bbox_inches='tight')
    print("✓ Stock cards saved to top_opportunities_cards.png")


def main():
    """Main execution"""
    try:
        create_visualizations()
        print("\n✓ All visualizations created successfully!")
        print("\nGenerated files:")
        print("  - set_reverse_dcf_analysis.png (Overview dashboard)")
        print("  - top_opportunities_cards.png (Top 4 stock cards)")
    except Exception as e:
        print(f"Error creating visualizations: {str(e)}")
        print("Note: Make sure you have run the analysis first")


if __name__ == "__main__":
    main()

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def visualize_price_data(csv_report_path):
    df = pd.read_csv(csv_report_path)
    
    # 1. Coverage Years Distribution
    df['Years Coverage'] = df['Days Coverage'] / 365.25
    
    plt.figure(figsize=(10, 6))
    sns.histplot(df['Years Coverage'], bins=10, kde=True, color='skyblue')
    plt.axvline(10, color='red', linestyle='--', label='10 Year Goal')
    plt.title('Distribution of Price Data History (Years)', fontsize=14)
    plt.xlabel('Years of Data History', fontsize=12)
    plt.ylabel('Number of Stocks', fontsize=12)
    plt.legend()
    plt.grid(alpha=0.3)
    plt.savefig('price_coverage_histogram.png')
    
    # 2. Completion Percentage (though it's 100% now, good for future)
    plt.figure(figsize=(10, 6))
    sns.boxplot(y=df['Completion %'], color='lightgreen')
    plt.title('Data Completion Percentage across Tickers', fontsize=14)
    plt.ylabel('Completion %', fontsize=12)
    plt.grid(alpha=0.3)
    plt.savefig('price_completion_boxplot.png')

    print("Visualizations saved: price_coverage_histogram.png, price_completion_boxplot.png")

if __name__ == "__main__":
    visualize_price_data('price_verification_report.csv')

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

from . import config

plt.style.use('ggplot')


def plot_risk_score_distribution(active_wallets: pd.DataFrame, save_path: Path = None):
    plt.figure(figsize=(10, 5))
    plt.hist(active_wallets['FINAL_RISK_SCORE'], bins=20)
    plt.title("Distribution of Final Risk Scores")
    plt.xlabel("Final Risk Score")
    plt.ylabel("Number of Wallets")
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
    else:
        plt.show()
    plt.close()

def plot_correlation_heatmap(active_wallets: pd.DataFrame, save_path: Path = None):
    features = ['FINAL_RISK_SCORE', 'structuring_score', 'passthrough_score', 
                'bot_score', 'snd_tx_count', 'snd_Amount_sum']
    
    plt.figure(figsize=(10, 7))
    sns.heatmap(active_wallets[features].corr(), annot=True, cmap="coolwarm", center=0)
    plt.title("Correlation Heatmap of Risk Features")
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
    else:
        plt.show()
    plt.close()


def plot_top_wallets_table(active_wallets: pd.DataFrame, n: int = None, save_path: Path = None):
    if n is None:
        n = config.TOP_N_WALLETS
    
    top_n = active_wallets.sort_values(by="FINAL_RISK_SCORE", ascending=False).head(n)
    
    table_data = []
    for idx, (wallet, row) in enumerate(top_n.iterrows(), 1):
        table_data.append([
            idx,
            wallet[:12] + "...",
            f"{row['FINAL_RISK_SCORE']:.1f}",
            row['Risk_Level'],
            int(row['snd_tx_count']),
            f"{row['snd_Amount_sum']:.2f}",
            f"{row['structuring_score']:.2f}",
            f"{row['passthrough_score']:.2f}",
            f"{row['bot_score']:.2f}"
        ])
    
    fig, ax = plt.subplots(figsize=(16, n * 0.4 + 1))
    ax.axis('tight')
    ax.axis('off')
    
    columns = ['#', 'Wallet Address', 'Risk Score', 'Level', 'Tx Count', 
               'Total Amount', 'Structuring', 'Passthrough', 'Bot Score']
    
    table = ax.table(cellText=table_data, colLabels=columns, cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    
    for i in range(len(columns)):
        table[(0, i)].set_facecolor('#40466e')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    for i in range(1, len(table_data) + 1):
        risk_level = table_data[i-1][3]
        if risk_level == 'CRITICAL':
            color = '#ffcccc'
        elif risk_level == 'HIGH':
            color = '#ffe6cc'
        elif risk_level == 'MEDIUM':
            color = '#ffffcc'
        else:
            color = '#e6ffe6'
        
        for j in range(len(columns)):
            table[(i, j)].set_facecolor(color)
    
    plt.title(f"Top {n} Highest Risk Wallets - Detailed Analysis", fontsize=14, weight='bold', pad=20)
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
    else:
        plt.show()
    plt.close()


def generate_all_plots(active_wallets: pd.DataFrame, save_to_file: bool = True):
    if save_to_file:
        config.RISK_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        plot_risk_score_distribution(active_wallets, config.RISK_FIGURES_DIR / "risk_distribution.png")
        plot_correlation_heatmap(active_wallets, config.RISK_FIGURES_DIR / "correlation_heatmap.png")
        plot_top_wallets_table(active_wallets, save_path=config.RISK_FIGURES_DIR / "top_wallets_table.png")
        print(f"[INFO] Visualizations saved to {config.RISK_FIGURES_DIR}")
    else:
        plot_risk_score_distribution(active_wallets)
        plot_correlation_heatmap(active_wallets)
        plot_top_wallets_table(active_wallets)

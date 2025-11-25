import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

from . import config

plt.style.use(config.PLOT_STYLE)


def plot_risk_score_distribution(active_wallets: pd.DataFrame, save_path: Path = None):
    plt.figure(figsize=(10, 5))
    plt.hist(active_wallets['FINAL_RISK_SCORE'], bins=20)
    plt.title("Distribution of Final Risk Scores")
    plt.xlabel("Final Risk Score")
    plt.ylabel("Number of Wallets")
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        print(f"   - Saved: {save_path}")
    else:
        plt.show()
    plt.close()


def plot_risk_level_pie(active_wallets: pd.DataFrame, save_path: Path = None):
    plt.figure(figsize=(6, 6))
    active_wallets['Risk_Level'].value_counts().plot(kind='pie', autopct='%1.1f%%')
    plt.title("Risk Level Distribution")
    plt.ylabel("")
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        print(f"   - Saved: {save_path}")
    else:
        plt.show()
    plt.close()


def plot_top_risky_wallets(active_wallets: pd.DataFrame, n: int = None, save_path: Path = None):
    if n is None:
        n = config.TOP_N_CHART
    
    top_n = active_wallets.sort_values(by="FINAL_RISK_SCORE", ascending=False).head(n)
    
    plt.figure(figsize=(12, 6))
    plt.bar(range(len(top_n)), top_n['FINAL_RISK_SCORE'])
    plt.xticks(range(len(top_n)), [f"Wallet {i+1}" for i in range(len(top_n))], rotation=45)
    plt.title(f"Top {n} Wallets – Final Risk Score")
    plt.ylabel("Risk Score")
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        print(f"   - Saved: {save_path}")
    else:
        plt.show()
    plt.close()


def plot_transactions_vs_risk(active_wallets: pd.DataFrame, save_path: Path = None):
    plt.figure(figsize=(10, 6))
    plt.scatter(active_wallets['snd_tx_count'], active_wallets['FINAL_RISK_SCORE'], alpha=0.5)
    plt.title("Transactions vs Final Risk Score")
    plt.xlabel("Send Transaction Count")
    plt.ylabel("Risk Score")
    plt.grid(True)
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        print(f"   - Saved: {save_path}")
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
        print(f"   - Saved: {save_path}")
    else:
        plt.show()
    plt.close()


def generate_all_plots(active_wallets: pd.DataFrame, save_to_file: bool = True):
    print("\n[PLOTS] Generating visualizations...")
    
    if save_to_file:
        plot_risk_score_distribution(active_wallets, config.FIGURES_DIR / "risk_distribution.png")
        plot_risk_level_pie(active_wallets, config.FIGURES_DIR / "risk_level_pie.png")
        plot_top_risky_wallets(active_wallets, save_path=config.FIGURES_DIR / "top_risky_wallets.png")
        plot_transactions_vs_risk(active_wallets, config.FIGURES_DIR / "tx_vs_risk.png")
        plot_correlation_heatmap(active_wallets, config.FIGURES_DIR / "correlation_heatmap.png")
        print(f"   - All plots saved to: {config.FIGURES_DIR}")
    else:
        plot_risk_score_distribution(active_wallets)
        plot_risk_level_pie(active_wallets)
        plot_top_risky_wallets(active_wallets)
        plot_transactions_vs_risk(active_wallets)
        plot_correlation_heatmap(active_wallets)

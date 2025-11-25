import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Set, Tuple

from src import config


def build_transaction_graph(df_tx: pd.DataFrame) -> nx.DiGraph:
    G = nx.from_pandas_edgelist(
        df_tx,
        source='FromAddress',
        target='ToAddress',
        edge_attr=['Amount', 'PKID'],
        create_using=nx.DiGraph()
    )
    return G


def calculate_centrality_metrics(G: nx.DiGraph) -> Dict[str, int]:
    degree_dict = dict(G.degree())
    nx.set_node_attributes(G, degree_dict, 'degree')
    return degree_dict


def detect_communities(G: nx.DiGraph) -> Dict[str, int]:
    try:
        import community.community_louvain as community_louvain
        
        G_undirected = G.to_undirected()
        partition = community_louvain.best_partition(G_undirected)
        nx.set_node_attributes(G, partition, 'community')
        return partition
    except ImportError:
        print("   ⚠️ python-louvain not installed. Run: pip install python-louvain")
        return {}
    except Exception as e:
        print(f"   ⚠️ Community detection failed: {e}")
        return {}


def detect_wash_trading(G: nx.DiGraph) -> Set[Tuple[str, ...]]:
    wash_trade_suspects = []
    cycles = list(nx.simple_cycles(G))
    
    for cycle in cycles:
        if len(cycle) == 2:
            addr_a = cycle[0]
            addr_b = cycle[1]
            wash_trade_suspects.append(sorted((addr_a, addr_b)))
        elif len(cycle) == 3:
            wash_trade_suspects.append(sorted(cycle))
    
    unique_wash_trades = set(tuple(t) for t in wash_trade_suspects)
    return unique_wash_trades


def detect_mixer_usage(df_tx: pd.DataFrame, round_amounts: List[float]) -> pd.Series:
    mixer_txs = df_tx[df_tx['Amount'].isin(round_amounts)]
    mixer_users = mixer_txs['FromAddress'].unique()
    return mixer_users


def filter_important_nodes(
    G: nx.DiGraph,
    degree_dict: Dict[str, int],
    wash_trades: Set[Tuple[str, ...]],
    high_degree_threshold: int = 5
) -> Set[str]:
    important_nodes = set()
    
    important_nodes.update([n for n in G.nodes() if "BAD_ACTOR" in n])
    
    important_nodes.update([n for n, d in degree_dict.items() if d > high_degree_threshold])
    
    for group in wash_trades:
        important_nodes.update(group)
    
    for node in list(important_nodes):
        try:
            important_nodes.update(G.neighbors(node))
        except:
            pass
    
    return important_nodes


def prepare_visualization_attributes(
    H: nx.DiGraph,
    partition: Dict[str, int],
    degree_dict: Dict[str, int],
    wash_trades: Set[Tuple[str, ...]]
) -> Tuple[List[str], List[int], Dict[str, str]]:
    node_colors = []
    node_sizes = []
    labels = {}
    
    smurf_community = partition.get('0xBAD_ACTOR_SMURFING', -1) if partition else -1
    
    for node in H.nodes():
        if "BAD_ACTOR" in node:
            node_colors.append('red')
            node_sizes.append(300)
            labels[node] = node
        elif partition and partition.get(node) == smurf_community and smurf_community != -1:
            node_colors.append('orange')
            node_sizes.append(100)
        elif any(node in t for t in wash_trades):
            node_colors.append('purple')
            node_sizes.append(200)
        else:
            node_colors.append('#3498db')
            node_sizes.append(50)
        
        if degree_dict.get(node, 0) > 20 and "BAD_ACTOR" not in node:
            labels[node] = node[:6]
    
    return node_colors, node_sizes, labels


def visualize_investigation_graph(
    H: nx.DiGraph,
    node_colors: List[str],
    node_sizes: List[int],
    labels: Dict[str, str],
    output_path: Path
) -> None:
    pos = nx.spring_layout(H, k=0.5, seed=42)
    
    plt.figure(figsize=(14, 10))
    
    nx.draw_networkx_nodes(H, pos, node_color=node_colors, node_size=node_sizes, alpha=0.8)
    nx.draw_networkx_edges(H, pos, alpha=0.4, arrows=True, edge_color='gray')
    nx.draw_networkx_labels(H, pos, labels=labels, font_size=8, font_weight='bold')
    
    plt.title("Investigation Map: Smurfing (Orange), Wash Trading (Purple) & Bad Actors (Red)", fontsize=16)
    plt.axis('off')
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def add_graph_flags_to_wallets(
    df_wallets: pd.DataFrame,
    wash_trades: Set[Tuple[str, ...]],
    mixer_users: pd.Series
) -> pd.DataFrame:
    wash_trade_wallets = set()
    for group in wash_trades:
        wash_trade_wallets.update(group)
    
    df_wallets['wash_trading_flag'] = df_wallets.index.isin(wash_trade_wallets)
    df_wallets['mixer_suspect_flag'] = df_wallets.index.isin(mixer_users)
    
    return df_wallets


def run_graph_investigation(
    df_tx: pd.DataFrame,
    df_wallets: pd.DataFrame,
    filter_high_risk: bool = True,
    high_degree_threshold: int = 5
) -> Tuple[pd.DataFrame, Dict]:
    print("\n" + "="*70)
    print("GRAPH INVESTIGATION ENGINE")
    print("="*70)
    
    if filter_high_risk and 'Risk_Level' in df_wallets.columns:
        high_risk_wallets = df_wallets[
            df_wallets['Risk_Level'].isin(['HIGH', 'CRITICAL'])
        ].index
        df_tx_filtered = df_tx[
            df_tx['FromAddress'].isin(high_risk_wallets) |
            df_tx['ToAddress'].isin(high_risk_wallets)
        ]
        print(f"Filtered to {len(df_tx_filtered)} transactions involving HIGH/CRITICAL risk wallets")
    else:
        df_tx_filtered = df_tx
        print(f"Analyzing all {len(df_tx_filtered)} transactions")
    
    print("\n[1] Building Network Graph...")
    G = build_transaction_graph(df_tx_filtered)
    print(f"   Nodes (Wallets): {G.number_of_nodes()}")
    print(f"   Edges (Txs)    : {G.number_of_edges()}")
    
    print("\n[2] Analyzing Network Topology...")
    degree_dict = calculate_centrality_metrics(G)
    sorted_degree = sorted(degree_dict.items(), key=lambda x: x[1], reverse=True)
    print("   Top 5 Most Connected Wallets (Hubs):")
    for addr, deg in sorted_degree[:5]:
        role = "🚨 BAD ACTOR" if "BAD_ACTOR" in addr else "User"
        print(f"     - {addr[:25]}... : {deg} connections [{role}]")
    
    print("\n[3] Detecting Communities...")
    partition = detect_communities(G)
    if partition:
        num_communities = len(set(partition.values()))
        print(f"   Detected {num_communities} Communities (Gang Clusters)")
    
    print("\n[4] Running Pattern Recognition...")
    wash_trades = detect_wash_trading(G)
    print(f"   🎯 Wash Trading / Round Trips: {len(wash_trades)}")
    for group in list(wash_trades)[:5]:
        print(f"     - Cycle: {group}")
    
    mixer_users = detect_mixer_usage(df_tx_filtered, config.ROUND_AMOUNTS)
    print(f"   🎯 Mixer Usage Suspects: {len(mixer_users)}")
    
    print("\n[5] Generating Investigation Graph...")
    important_nodes = filter_important_nodes(G, degree_dict, wash_trades, high_degree_threshold)
    print(f"   Filtered to {len(important_nodes)} important nodes")
    
    H = G.subgraph(list(important_nodes))
    node_colors, node_sizes, labels = prepare_visualization_attributes(
        H, partition, degree_dict, wash_trades
    )
    
    output_path = config.FIGURES_DIR / 'investigation_graph_final.png'
    visualize_investigation_graph(H, node_colors, node_sizes, labels, output_path)
    print(f"   ✓ Graph saved to {output_path}")
    
    print("\n[6] Adding Graph Flags to Wallet Data...")
    df_wallets = add_graph_flags_to_wallets(df_wallets, wash_trades, mixer_users)
    
    results = {
        'graph': G,
        'communities': partition,
        'wash_trades': wash_trades,
        'mixer_users': mixer_users,
        'degree_dict': degree_dict
    }
    
    print("\n" + "="*70)
    print("GRAPH INVESTIGATION COMPLETE")
    print("="*70)
    print(f"1. Communities Detected: {len(set(partition.values())) if partition else 0}")
    print(f"2. Wash Trading Groups: {len(wash_trades)}")
    print(f"3. Mixer Suspects: {len(mixer_users)}")
    print(f"4. Visualization saved: {output_path}")
    
    return df_wallets, results

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
        print("   Warning: python-louvain not installed. Run: pip install python-louvain")
        return {}
    except Exception as e:
        print(f"   Warning: Community detection failed: {e}")
        return {}


def detect_wash_trading(G: nx.DiGraph, max_cycle_length: int = None) -> Set[Tuple[str, ...]]:
    if max_cycle_length is None:
        max_cycle_length = config.GRAPH_CYCLE_MAX_LENGTH
    
    wash_trade_suspects = []
    cycles = list(nx.simple_cycles(G))
    
    for cycle in cycles:
        if len(cycle) == 2:
            addr_a = cycle[0]
            addr_b = cycle[1]
            wash_trade_suspects.append(sorted((addr_a, addr_b)))
        elif len(cycle) <= max_cycle_length:
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
    validation_targets: List[str] = None,
    high_degree_threshold: int = None
) -> Set[str]:
    if high_degree_threshold is None:
        high_degree_threshold = config.GRAPH_HUB_DEGREE_THRESHOLD
    if validation_targets is None:
        validation_targets = config.VALIDATION_TARGETS
    
    important_nodes = set()
    
    if validation_targets:
        important_nodes.update([n for n in G.nodes() if n in validation_targets])
    
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
    wash_trades: Set[Tuple[str, ...]],
    validation_targets: List[str] = None
) -> Tuple[List[str], List[int], Dict[str, str]]:
    if validation_targets is None:
        validation_targets = config.VALIDATION_TARGETS
    
    node_colors = []
    node_sizes = []
    labels = {}
    
    smurf_community = partition.get(config.ACTOR_SMURF, -1) if partition and config.ACTOR_SMURF in config.VALIDATION_TARGETS else -1
    
    for node in H.nodes():
        if validation_targets and node in validation_targets:
            node_colors.append(config.GRAPH_COLOR_BAD_ACTOR)
            node_sizes.append(config.GRAPH_NODE_SIZE_BAD_ACTOR)
            labels[node] = node
        elif partition and partition.get(node) == smurf_community and smurf_community != -1:
            node_colors.append(config.GRAPH_COLOR_GANG)
            node_sizes.append(config.GRAPH_NODE_SIZE_GANG)
        elif any(node in t for t in wash_trades):
            node_colors.append(config.GRAPH_COLOR_WASH_TRADER)
            node_sizes.append(config.GRAPH_NODE_SIZE_WASH_TRADER)
        else:
            node_colors.append(config.GRAPH_COLOR_NORMAL)
            node_sizes.append(config.GRAPH_NODE_SIZE_NORMAL)
        
        is_validation = validation_targets and node in validation_targets
        if degree_dict.get(node, 0) > config.GRAPH_LABEL_DEGREE_THRESHOLD and not is_validation:
            labels[node] = node[:config.GRAPH_LABEL_PREFIX_LENGTH]
    
    return node_colors, node_sizes, labels


def visualize_investigation_graph(
    H: nx.DiGraph,
    node_colors: List[str],
    node_sizes: List[int],
    labels: Dict[str, str],
    output_path: Path
) -> None:
    pos = nx.spring_layout(H, k=config.GRAPH_LAYOUT_K, seed=config.GRAPH_LAYOUT_SEED)
    
    plt.figure(figsize=config.GRAPH_FIGURE_SIZE)
    
    nx.draw_networkx_nodes(H, pos, node_color=node_colors, node_size=node_sizes, alpha=config.GRAPH_NODE_ALPHA)
    nx.draw_networkx_edges(H, pos, alpha=config.GRAPH_EDGE_ALPHA, arrows=True, edge_color=config.GRAPH_COLOR_EDGE)
    nx.draw_networkx_labels(H, pos, labels=labels, font_size=config.GRAPH_FONT_SIZE, font_weight='bold')
    
    plt.title("Investigation Map: Smurfing (Orange), Wash Trading (Purple) & Bad Actors (Red)", fontsize=16)
    plt.axis('off')
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=config.GRAPH_DPI, bbox_inches='tight')
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
    print("[INFO] Running graph investigation...")
    
    if filter_high_risk and 'Risk_Level' in df_wallets.columns:
        high_risk_wallets = df_wallets[
            df_wallets['Risk_Level'].isin(['HIGH', 'CRITICAL'])
        ].index
        df_tx_filtered = df_tx[
            df_tx['FromAddress'].isin(high_risk_wallets) |
            df_tx['ToAddress'].isin(high_risk_wallets)
        ]
    else:
        df_tx_filtered = df_tx
    
    G = build_transaction_graph(df_tx_filtered)
    degree_dict = calculate_centrality_metrics(G)
    sorted_degree = sorted(degree_dict.items(), key=lambda x: x[1], reverse=True)
    
    partition = detect_communities(G)
    
    wash_trades = detect_wash_trading(G)
    mixer_users = detect_mixer_usage(df_tx_filtered, config.ROUND_AMOUNTS)
    
    important_nodes = filter_important_nodes(G, degree_dict, wash_trades, config.VALIDATION_TARGETS, high_degree_threshold)
    H = G.subgraph(list(important_nodes))
    node_colors, node_sizes, labels = prepare_visualization_attributes(
        H, partition, degree_dict, wash_trades, config.VALIDATION_TARGETS
    )
    
    config.GRAPH_INVESTIGATION_DIR.mkdir(parents=True, exist_ok=True)
    visualize_investigation_graph(H, node_colors, node_sizes, labels, config.GRAPH_OUTPUT_PNG_PATH)
    
    df_wallets = add_graph_flags_to_wallets(df_wallets, wash_trades, mixer_users)
    
    results = {
        'graph': G,
        'communities': partition,
        'wash_trades': wash_trades,
        'mixer_users': mixer_users,
        'degree_dict': degree_dict
    }
    
    print(f"[INFO] Graph investigation complete - saved to {config.GRAPH_OUTPUT_PNG_PATH}")
    
    return df_wallets, results

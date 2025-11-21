# ELISP CryptoTrace ML

Machine Learning & Analytics Module for Cryptocurrency Investigation Platform

## Overview

ELISP CryptoTrace ML adalah modul analisis dan machine learning yang dirancang untuk mendukung proses investigasi cryptocurrency. Sistem ini memproses data wallet, transaksi, smart contract, dan NFT dari berbagai blockchain untuk mendeteksi pola mencurigakan, melakukan risk scoring, membangun jaringan relasi, serta menghasilkan laporan investigasi otomatis.

## Features

### Supported Inputs
- Wallet Address  
- Transaction Hash  
- Smart Contract  
- NFT  

### Workflow
Input → Chain Detection → Data Gathering → ML Analysis → Visualization → Attribution → Report Generation

### Blockchain Support
**Current (Phase 2)**  
- Bitcoin  
- Ethereum  
- Binance Smart Chain  
- TRON  

**Planned (Year 3)**  
- 50+ chains (Polygon, Avalanche, Solana, Cardano, L2s, dan lainnya)

## Machine Learning Capabilities

### Risk Scoring
- Supervised learning  
- Label propagation  
- Confidence scoring berbasis evidence  

### Clustering & Pattern Detection
- Multi-input clustering  
- Change address detection  
- Peel-chain analysis  
- Temporal co-activity  

### Anomaly Detection
- Mixer/darknet detection  
- Outlier transaction patterns  
- Flash-loan & DeFi exploit identification  

### Attribution
- Exchange identification  
- Mixer & bridge detection  
- Darknet marketplace mapping  
- DeFi protocol tagging  

## Architecture

### Data Sources
| Chain | API/Service |
|-------|-------------|
| Bitcoin | Blockstream Esplora |
| Ethereum/BSC/Polygon | Etherscan API |
| TRON | TronGrid / TRON API |
| Solana | JSON-RPC / Helius |
| NFT | OpenSea API |

### Core Data Models
- Address  
- Transaction  
- TokenContract  
- Entity  
- Cluster  
- Alert  
- KnownList  
- Report  

## Non-Functional Requirements
- Latency: < 15 menit dari blockchain confirmation ke alert  
- Scale: 100k+ nodes, render 10k nodes  
- Availability: 99.5% ingest & API uptime  
- Auditability: Setiap label & score dapat ditelusuri  
- Security: Audit trail & encryption  

## Installation

```bash
git clone https://github.com/naufalkr/elisp-cryptotrace-ml.git
cd elisp-cryptotrace-ml
cp .env.example .env
pip install -e .

import pandas as pd
from pathlib import Path


def generate_html_report(csv_path: Path, output_path: Path = None):
    """
    Generate interactive HTML table from CSV with sorting, filtering, and search.
    Color-coded by risk level and flags.
    """
    df = pd.read_csv(csv_path)
    
    if output_path is None:
        output_path = csv_path.parent / (csv_path.stem + ".html")
    
    # Prepare styling based on risk level
    def get_row_color(row):
        if 'Risk_Level' in df.columns:
            level = row.get('Risk_Level', 'LOW')
            if level == 'CRITICAL':
                return '#ffebee'  
            elif level == 'HIGH':
                return '#fff3e0'  
            elif level == 'MEDIUM':
                return '#fff9c4'  # Light yellow
        return '#ffffff'  # White
    # Generate HTML with DataTables.js for interactivity
    html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>CryptoTrace - Graph Investigation Results</title>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
        }}
        .header p {{
            margin: 5px 0 0 0;
            opacity: 0.9;
        }}
        .stats {{
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            flex: 1;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }}
        .table-container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        table.dataTable {{
            width: 100% !important;
        }}
        .risk-CRITICAL {{
            background-color: #ffebee !important;
            font-weight: bold;
        }}
        .risk-HIGH {{
            background-color: #fff3e0 !important;
        }}
        .risk-MEDIUM {{
            background-color: #fff9c4 !important;
        }}
        .risk-LOW {{
            background-color: #ffffff !important;
        }}
        .flag-yes {{
            color: #d32f2f;
            font-weight: bold;
        }}
        .flag-no {{
            color: #666;
        }}
        .address-cell {{
            font-family: monospace;
            font-size: 11px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 CryptoTrace - Graph Investigation Results</h1>
        <p>Interactive wallet analysis with risk scores and pattern detection flags</p>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">{total_wallets}</div>
            <div class="stat-label">Total Wallets</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{high_risk}</div>
            <div class="stat-label">HIGH/CRITICAL Risk</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{wash_trading}</div>
            <div class="stat-label">Wash Trading Flags</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{mixer_suspects}</div>
            <div class="stat-label">Mixer Suspects</div>
        </div>
    </div>
    
    <div class="table-container">
        {table_html}
    </div>
    
    <script>
        $(document).ready(function() {{
            $('#data-table').DataTable({{
                pageLength: 50,
                order: [[1, 'desc']],  // Sort by risk score descending
                columnDefs: [
                    {{ targets: [0], className: 'address-cell' }},
                    {{ targets: [1, 3, 4, 5, 6, 7, 8, 9], className: 'dt-right' }}
                ],
                language: {{
                    search: "Search wallets:",
                    lengthMenu: "Show _MENU_ wallets per page",
                    info: "Showing _START_ to _END_ of _TOTAL_ wallets",
                    infoFiltered: "(filtered from _MAX_ total)"
                }}
            }});
            
            // Add row coloring based on risk level
            $('#data-table tbody tr').each(function() {{
                var riskLevel = $(this).find('td:eq(2)').text().trim();
                $(this).addClass('risk-' + riskLevel);
            }});
        }});
    </script>
</body>
</html>
"""
    
    # Calculate statistics
    total_wallets = len(df)
    high_risk = 0
    if 'Risk_Level' in df.columns:
        high_risk = len(df[df['Risk_Level'].isin(['HIGH', 'CRITICAL'])])
    
    wash_trading = 0
    mixer_suspects = 0
    if 'wash_trading_flag' in df.columns:
        wash_trading = df['wash_trading_flag'].sum()
    if 'mixer_suspect_flag' in df.columns:
        mixer_suspects = df['mixer_suspect_flag'].sum()
    
    # Select and reorder columns for display
    display_cols = []
    if df.index.name:
        df = df.reset_index()
        display_cols.append(df.columns[0])  # Address column
    
    # Priority columns
    priority = ['FINAL_RISK_SCORE', 'Risk_Level', 'snd_tx_count', 'snd_Amount_sum', 
                'structuring_score', 'passthrough_score', 'bot_score',
                'wash_trading_flag', 'mixer_suspect_flag']
    
    for col in priority:
        if col in df.columns:
            display_cols.append(col)
    
    # Add remaining columns
    for col in df.columns:
        if col not in display_cols:
            display_cols.append(col)
    
    df_display = df[display_cols].copy()
    
    # Format boolean flags
    for col in ['wash_trading_flag', 'mixer_suspect_flag']:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(
                lambda x: '<span class="flag-yes">YES</span>' if x else '<span class="flag-no">-</span>'
            )
    
    # Format numeric columns
    numeric_cols = df_display.select_dtypes(include=['float64', 'int64']).columns
    for col in numeric_cols:
        if 'score' in col.lower():
            df_display[col] = df_display[col].apply(lambda x: f'{x:.2f}' if pd.notna(x) else '-')
        elif 'amount' in col.lower():
            df_display[col] = df_display[col].apply(lambda x: f'{x:.4f}' if pd.notna(x) else '-')
        else:
            df_display[col] = df_display[col].apply(lambda x: f'{int(x)}' if pd.notna(x) else '-')
    
    # Generate table HTML
    table_html = df_display.to_html(
        classes='display',
        table_id='data-table',
        index=False,
        escape=False,
        border=0
    )
    
    # Fill template
    html_content = html_template.format(
        total_wallets=total_wallets,
        high_risk=high_risk,
        wash_trading=wash_trading,
        mixer_suspects=mixer_suspects,
        table_html=table_html
    )
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"[INFO] Interactive HTML report generated: {output_path}")
    return output_path

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import numpy as np

# --- CONFIGURATION ---
RESULTS_DIR = Path("/Users/grey/work/cloudmesh-ai-vm-results/gregor/smoke")
IMAGES_DIR = Path("/Users/grey/work/cloudmesh-ai-vm-results/images")
USE_LOG_SCALE = False  # Set to True to use logarithmic scale on Y axis for the main graph
MIN_POINTS_FOR_ERRORBAR = 3  # Only show error bars if we have at least this many points per group
# ---------------------

def load_data(results_dir):
    all_data = []
    json_files = list(results_dir.glob("*.json"))
    if not json_files:
        return pd.DataFrame()
    for json_file in json_files:
        with open(json_file, 'r') as f:
            try:
                data = json.load(f)
                benchmark = data['experiment']['benchmark']
                date_str = data['experiment']['date']
                for timer in data.get('timers', []):
                    all_data.append({
                        'benchmark': benchmark, 'date': date_str,
                        'operation': timer['name'], 'time': timer['time'], 'status': timer['status']
                    })
            except Exception as e:
                print(f"Error parsing {json_file}: {e}")
    df = pd.DataFrame(all_data)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df

def get_errorbar_setting(df, x, hue):
    counts = df.groupby([x, hue]).size()
    if (counts >= MIN_POINTS_FOR_ERRORBAR).all():
        return 'sd'
    return None

def plot_visualizations(df):
    if df.empty: return
    sns.set_theme(style="whitegrid")
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    # Graph 1: All Operations
    plt.figure(figsize=(12, 6))
    err = get_errorbar_setting(df, 'operation', 'benchmark')
    sns.barplot(data=df, x='operation', y='time', hue='benchmark', estimator='mean', errorbar=err)
    plt.title('Average Operation Time by Benchmark (CLI Only)')
    plt.xticks(rotation=45, ha='right')
    plt.ylabel('Time (seconds)')
    if USE_LOG_SCALE:
        plt.yscale('log')
        plt.ylabel('Time (seconds) - Log Scale')
    plt.tight_layout()
    plt.savefig(IMAGES_DIR / "all_operations.png")
    plt.close()
    
    # Graph 2: Start and Stop only (Linear scale)
    mask = (df['operation'].str.contains('start|run|stop', case=False, na=False)) & \
           (~df['operation'].str.contains('wait_running', case=False, na=False))
    start_stop_ops = df[mask].copy()
    
    if not start_stop_ops.empty:
        def categorize_op(op):
            op = op.lower()
            if 'stop' in op: return 'Stop'
            if 'start' in op or 'run' in op: return 'Start/Run'
            return 'Other'
        start_stop_ops['category'] = start_stop_ops['operation'].apply(categorize_op)
        
        plt.figure(figsize=(12, 6))
        err_ss = get_errorbar_setting(start_stop_ops, 'category', 'benchmark')
        ax = sns.barplot(data=start_stop_ops, x='category', y='time', hue='benchmark', estimator='mean', errorbar=err_ss)
        plt.title('Comparison of Start/Run and Stop Times by Benchmark (CLI Only)')
        plt.ylabel('Time (seconds)')
        plt.xlabel('Operation Category')
        
        hue_order = df['benchmark'].unique()
        cat_order = [c for c in ['Start/Run', 'Stop'] if c in start_stop_ops['category'].unique()]
        bar_idx = 0
        for hue in hue_order:
            for cat in cat_order:
                val = start_stop_ops[(start_stop_ops['benchmark'] == hue) & 
                                     (start_stop_ops['category'] == cat)]['time'].median()
                if not np.isnan(val):
                    if bar_idx < len(ax.patches):
                        rect = ax.patches[bar_idx]
                        ax.text(rect.get_x() + rect.get_width()/2, rect.get_height() + 0.5, 
                                f'{val:.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
                bar_idx += 1
        plt.tight_layout()
        plt.savefig(IMAGES_DIR / "start_stop_operations.png")
        plt.close()
    else:
        print("No start/stop operations found to plot.")

def plot_trends(df):
    if df.empty: return
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    benchmarks = df['benchmark'].unique()
    for b in benchmarks:
        b_df = df[df['benchmark'] == b]
        if len(b_df['date'].unique()) > 1:
            plt.figure(figsize=(10, 4))
            sns.lineplot(data=b_df, x='date', y='time', hue='operation', marker='o')
            plt.title(f'Performance Trend: {b}')
            plt.ylabel('Time (seconds)')
            if USE_LOG_SCALE:
                plt.yscale('log')
                plt.ylabel('Time (seconds) - Log Scale')
            plt.xticks(rotation=45)
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            filename = f"trend_{b.lower().replace(' ', '_').replace('/', '_')}.png"
            plt.savefig(IMAGES_DIR / filename)
            plt.close()

def main():
    df_raw = load_data(RESULTS_DIR)
    if df_raw.empty: return
    
    # Filter to only include benchmarks that contain "CLI" in their name
    df = df_raw[df_raw['benchmark'].str.contains('CLI', case=False, na=False)].copy()
    
    if df.empty:
        print("No benchmarks containing 'CLI' found.")
        return

    print(f"Loaded {len(df)} timer entries from CLI benchmarks.")
    print("\n--- Summary Statistics (CLI Only) ---")
    summary = df.groupby(['benchmark', 'operation'])['time'].agg(['mean', 'median', 'std', 'count']).reset_index()
    summary = summary.sort_values(by=['benchmark', 'mean'], ascending=[True, False])
    print(summary.to_string())
    plot_visualizations(df)
    plot_trends(df)
    print("\nAnalysis complete. Images are stored in:", IMAGES_DIR)

if __name__ == "__main__":
    main()

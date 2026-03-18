
"""
Final Benchmark Analysis Script

Reads benchmark results from all 3 databases (PostgreSQL, MongoDB, Neo4j)
Generates comparison tables, charts, and statistics for the report.

"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os


# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..', 'output'))
REPORT_DIR = os.path.normpath(os.path.join(OUTPUT_DIR, 'benchmark_report'))

os.makedirs(REPORT_DIR, exist_ok=True)

# Benchmark result files
BENCHMARK_FILES = {
    'PostgreSQL': os.path.join(OUTPUT_DIR, 'sql_queries_results', 'benchmark_psql_detailed.csv'),
    'MongoDB': os.path.join(OUTPUT_DIR, 'mongo_queries_results', 'benchmark_mongo_detailed.csv'),
    'Neo4j': os.path.join(OUTPUT_DIR, 'neo4j_queries_results', 'benchmark_neo4j_detailed.csv'),
}

# Query name mapping (for consistent display)
QUERY_NAMES = {
    'Task 3 - Campaign Analysis': 'Q1: Campaign Analysis',
    'Task 4 - Recommendations': 'Q2: Recommendations',
    'Task 5 - Full-Text Search': 'Q3: Full-Text Search',
}

# Colors for charts (matching reference paper style)
DB_COLORS = {
    'PostgreSQL': '#5B8AC9',  # Blue
    'MongoDB': '#E87B7B',  # Red/Pink
    'Neo4j': '#D4C685',  # Beige/Gold
}

# =============================================================================
# LOAD BENCHMARK DATA
# =============================================================================

def load_benchmark_data():
    #Load detailed benchmark results from all databases

    all_data = {}

    for db_name, file_path in BENCHMARK_FILES.items():
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)

            # Normalize query names
            df['Query'] = df['Query'].map(lambda x: QUERY_NAMES.get(x, x))

            all_data[db_name] = df
            print(f" Loaded {db_name}: {len(df)} records from {file_path}")
        else:
            print(f" File not found: {file_path}")
            all_data[db_name] = pd.DataFrame()

    return all_data


# =============================================================================
# CALCULATE STATISTICS
# =============================================================================

def calculate_statistics(all_data):
    #Calculate average and standard deviation for each query per database

    stats = []

    for db_name, df in all_data.items():
        if len(df) == 0:
            continue

        for query in df['Query'].unique():
            query_data = df[df['Query'] == query]['Time (s)']

            stats.append({
                'Database': db_name,
                'Query': query,
                'Avg (s)': query_data.mean(),
                'Std Dev (s)': query_data.std(),
                'Min (s)': query_data.min(),
                'Max (s)': query_data.max(),
                'Runs': len(query_data),
            })

    stats_df = pd.DataFrame(stats)
    return stats_df


# =============================================================================
# GENERATE CHARTS
# =============================================================================

def generate_charts(stats_df, all_data):
    #Generate comparison charts with similar style as reference paper

    charts = []

    # Chart 1: Bar Chart (Average execution time per query per database)
    fig1, ax1 = plt.subplots(figsize=(14, 8))

    queries = stats_df['Query'].unique()
    x = np.arange(len(queries))
    width = 0.25

    for i, db in enumerate(['PostgreSQL', 'MongoDB', 'Neo4j']):
        db_data = stats_df[stats_df['Database'] == db]
        averages = [db_data[db_data['Query'] == q]['Avg (s)'].values[0]
                    if len(db_data[db_data['Query'] == q]) > 0 else 0
                    for q in queries]

        ax1.bar(x + i * width, averages, width,
                label=db, color=DB_COLORS[db], edgecolor='black', linewidth=1)

        # Add value labels on bars
        for j, avg in enumerate(averages):
            ax1.text(x[j] + i * width, avg + 0.5, f'{avg:.1f}',
                     ha='center', va='bottom', fontsize=9, rotation=0)

    ax1.set_xlabel('Query', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Duration in seconds', fontsize=12, fontweight='bold')
    ax1.set_title('Query Execution Results - Average Time per Database', fontsize=14, fontweight='bold')
    ax1.set_xticks(x + width)
    ax1.set_xticklabels(queries, fontsize=10)
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    ax1.set_axisbelow(True)

    plt.tight_layout()
    chart1_path = os.path.join(REPORT_DIR, 'chart_average_comparison.png')
    plt.savefig(chart1_path, dpi=300, bbox_inches='tight')
    plt.close()
    charts.append(('Average Comparison Chart', chart1_path))

    # Chart 2: Standard Deviation Chart (stability)
    fig2, ax2 = plt.subplots(figsize=(14, 8))

    for i, db in enumerate(['PostgreSQL', 'MongoDB', 'Neo4j']):
        db_data = stats_df[stats_df['Database'] == db]
        std_devs = [db_data[db_data['Query'] == q]['Std Dev (s)'].values[0]
                    if len(db_data[db_data['Query'] == q]) > 0 else 0
                    for q in queries]

        ax2.bar(x + i * width, std_devs, width,
                label=db, color=DB_COLORS[db], edgecolor='black', linewidth=1)

        for j, std in enumerate(std_devs):
            ax2.text(x[j] + i * width, std + 0.05, f'{std:.2f}',
                     ha='center', va='bottom', fontsize=9, rotation=0)

    ax2.set_xlabel('Query', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Standard Deviation (seconds)', fontsize=12, fontweight='bold')
    ax2.set_title('Query Execution Stability - Standard Deviation per Database', fontsize=14, fontweight='bold')
    ax2.set_xticks(x + width)
    ax2.set_xticklabels(queries, fontsize=10)
    ax2.legend(loc='upper left', fontsize=10)
    ax2.grid(axis='y', alpha=0.3, linestyle='--')
    ax2.set_axisbelow(True)

    plt.tight_layout()
    chart2_path = os.path.join(REPORT_DIR, 'chart_stability_comparison.png')
    plt.savefig(chart2_path, dpi=300, bbox_inches='tight')
    plt.close()
    charts.append(('Stability Comparison Chart', chart2_path))

    # Chart 3: Line Chart (Run-by-run variation)
    fig3, axes3 = plt.subplots(1, 3, figsize=(18, 5))

    for idx, query in enumerate(queries):
        ax = axes3[idx]

        for db in ['PostgreSQL', 'MongoDB', 'Neo4j']:
            if db in all_data and len(all_data[db]) > 0:
                db_query_data = all_data[db][all_data[db]['Query'] == query]
                if len(db_query_data) == 5:
                    runs = list(range(1, 6))
                    times = db_query_data['Time (s)'].values
                    ax.plot(runs, times, marker='o', linewidth=2,
                            label=db, color=DB_COLORS[db], markersize=8)

        ax.set_xlabel('Run Number', fontsize=10)
        ax.set_ylabel('Time (seconds)', fontsize=10)
        ax.set_title(query, fontsize=11, fontweight='bold')
        ax.set_xticks([1, 2, 3, 4, 5])
        ax.grid(alpha=0.3, linestyle='--')
        ax.legend(fontsize=8)

    plt.suptitle('Query Execution Time Variation Across 5 Runs', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    chart3_path = os.path.join(REPORT_DIR, 'chart_run_variation.png')
    plt.savefig(chart3_path, dpi=300, bbox_inches='tight')
    plt.close()
    charts.append(('Run Variation Chart', chart3_path))

    # Chart 4: Combined Bar Chart (similar to reference paper Fig. 7)
    fig4, ax4 = plt.subplots(figsize=(16, 9))

    # Create grouped bars for each query
    bar_width = 0.25
    indices = np.arange(len(queries) * 3)  # 3 databases per query

    bar_positions = []
    bar_heights = []
    bar_colors = []
    bar_labels = []

    for q_idx, query in enumerate(queries):
        for db_idx, db in enumerate(['PostgreSQL', 'MongoDB', 'Neo4j']):
            db_data = stats_df[(stats_df['Query'] == query) & (stats_df['Database'] == db)]
            if len(db_data) > 0:
                avg = db_data['Avg (s)'].values[0]
                pos = q_idx * 3 + db_idx
                bar_positions.append(pos)
                bar_heights.append(avg)
                bar_colors.append(DB_COLORS[db])
                bar_labels.append(db)

    # Create bars with group labels
    for i, (pos, height, color) in enumerate(zip(bar_positions, bar_heights, bar_colors)):
        ax4.bar(pos, height, color=color, edgecolor='black', linewidth=1, width=0.8)
        ax4.text(pos, height + 0.5, f'{height:.1f}', ha='center', va='bottom', fontsize=9)

    # Add query group labels on x-axis
    ax4.set_xticks([i * 3 + 1 for i in range(len(queries))])
    ax4.set_xticklabels(queries, fontsize=11)
    ax4.set_xlabel('Query', fontsize=12, fontweight='bold')
    ax4.set_ylabel('Duration in seconds', fontsize=12, fontweight='bold')
    ax4.set_title('Query Execution Results on the Average', fontsize=14, fontweight='bold')
    ax4.grid(axis='y', alpha=0.3, linestyle='--')
    ax4.set_axisbelow(True)

    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=DB_COLORS['PostgreSQL'], edgecolor='black', label='PostgreSQL'),
        Patch(facecolor=DB_COLORS['MongoDB'], edgecolor='black', label='MongoDB'),
        Patch(facecolor=DB_COLORS['Neo4j'], edgecolor='black', label='Neo4j'),
    ]
    ax4.legend(handles=legend_elements, loc='upper left', fontsize=11)

    plt.tight_layout()
    chart4_path = os.path.join(REPORT_DIR, 'chart_final_comparison.png')
    plt.savefig(chart4_path, dpi=300, bbox_inches='tight')
    plt.close()
    charts.append(('Final Comparison Chart (Fig. 7 Style)', chart4_path))

    return charts


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print(" FINAL BENCHMARK ANALYSIS")
    print("=" * 80)

    # Step 1: Load benchmark data
    print("1/3 Loading benchmark data...")
    all_data = load_benchmark_data()
    print()

    # Step 2: Calculate statistics
    print("2/3 Calculating statistics...")
    stats_df = calculate_statistics(all_data)
    print(f"  Calculated statistics for {len(stats_df)} query-database combinations")
    print()

    # Step 3: Generate charts
    print("3/3 Generating charts...")
    charts = generate_charts(stats_df, all_data)
    print(f"  Generated {len(charts)} charts")
    for chart_name, chart_path in charts:
        print(f"    - {chart_name}: {chart_path}")
    print()


    # Save summary CSV
    summary_path = os.path.join(REPORT_DIR, 'benchmark_summary.csv')
    stats_df.to_csv(summary_path, index=False)
    print(f"  Summary CSV saved to: {summary_path}")
    print()

    # Print summary
    print("=" * 80)
    print(" BENCHMARK SUMMARY")
    print("=" * 80)
    print(stats_df.to_string(index=False))
    print()
    print("=" * 80)
    print(" FINAL BENCHMARK ANALYSIS COMPLETED!")
    print("=" * 80)
    print(f"\nReport location: {REPORT_DIR}")
    print(f"  - chart_*.png (Individual chart files)")
    print(f"  - benchmark_summary.csv (Summary statistics)")
    print()


if __name__ == "__main__":
    main()
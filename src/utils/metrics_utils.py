from typing import Dict, Any, List
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import seaborn as sns
from pathlib import Path

# Try to import plotly for interactive plots
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

class MetricsUtils:
    """Utility class for metrics analysis and visualization."""

    @staticmethod
    def analyze_query_performance(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze query performance metrics.

        Args:
            metrics: List of query execution metrics

        Returns:
            Dictionary containing analysis results
        """
        if not metrics:
            return {
                "summary_stats": {
                    "mean_duration": None,
                    "median_duration": None,
                    "std_duration": None,
                    "min_duration": None,
                    "max_duration": None,
                    "total_queries": 0,
                    "success_rate": 0
                },
                "percentiles": {
                    "p50": None,
                    "p90": None,
                    "p95": None,
                    "p99": None
                },
                "error_analysis": {
                    "error_count": 0,
                    "error_rate": 0
                }
            }

        df = pd.DataFrame(metrics)
        # Ensure required columns exist
        for col in ("duration", "success"):
            if col not in df.columns:
                df[col] = np.nan if col == "duration" else False

        analysis = {
            "summary_stats": {
                "mean_duration": df['duration'].mean(),
                "median_duration": df['duration'].median(),
                "std_duration": df['duration'].std(),
                "min_duration": df['duration'].min(),
                "max_duration": df['duration'].max(),
                "total_queries": len(df),
                "success_rate": (df['success'].sum() / len(df)) * 100 if len(df) > 0 else 0
            },
            "percentiles": {
                "p50": df['duration'].quantile(0.5),
                "p90": df['duration'].quantile(0.9),
                "p95": df['duration'].quantile(0.95),
                "p99": df['duration'].quantile(0.99)
            },
            "error_analysis": {
                "error_count": int((~df['success']).sum()),
                "error_rate": float((~df['success']).mean() * 100) if len(df) > 0 else 0
            }
        }
        return analysis

    @staticmethod
    def calculate_performance_scores(metrics: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate performance scores based on various metrics.

        Args:
            metrics: List of query execution metrics

        Returns:
            Dictionary containing performance scores
        """
        if not metrics:
            return {
                "reliability_score": 0.0,
                "performance_score": 0.0,
                "stability_score": 0.0,
                "overall_score": 0.0
            }

        df = pd.DataFrame(metrics)
        # Fill missing success as False
        if 'success' not in df.columns:
            df['success'] = False
        success_df = df[df['success'] & df['duration'].notna()]

        reliability = float(df['success'].mean() * 100) if len(df) > 0 else 0.0

        if len(success_df) > 0:
            mean_duration = success_df['duration'].mean()
            perf_score = (1 / (1 + np.log1p(mean_duration))) * 100 if mean_duration >= 0 else 0.0
            std_duration = success_df['duration'].std()
            stability_score = (1 / (1 + std_duration)) * 100 if std_duration and not np.isnan(std_duration) else 100.0
        else:
            perf_score = 0.0
            stability_score = 0.0

        scores = {
            "reliability_score": reliability,
            "performance_score": float(perf_score),
            "stability_score": float(stability_score)
        }

        weights = {
            "reliability_score": 0.4,
            "performance_score": 0.4,
            "stability_score": 0.2
        }
        scores["overall_score"] = sum(scores[k] * w for k, w in weights.items())
        return scores

    @staticmethod
    def generate_performance_plots(metrics: List[Dict[str, Any]], output_dir: str):
        """
        Generate and refine performance visualization plots.
        Creates both static (PNG) and interactive (HTML) versions when Plotly is available.
        Args:
            metrics: List of query execution metrics
            output_dir: Directory to save the plots
        """
        df = pd.DataFrame(metrics)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if df.empty or 'duration' not in df.columns:
            return

        # Prepare timestamp if available
        if 'start_time' in df.columns:
            try:
                df['timestamp'] = pd.to_datetime(df['start_time'], unit='s')
                df = df.sort_values('timestamp')
            except Exception:
                pass

        # === STATIC PLOTS (PNG) with proper legends ===
        
        # Duration distribution plot by complexity
        plt.figure(figsize=(12, 7))
        if 'complexity' in df.columns:
            complexities = sorted(df['complexity'].unique())
            colors = {'simple': '#4CAF50', 'medium': '#FFC107', 'complex': '#F44336'}
            for comp in complexities:
                comp_data = df[df['complexity'] == comp]['duration']
                color = colors.get(comp, 'royalblue')
                plt.hist(comp_data, bins=50, alpha=0.6, label=f'{comp.capitalize()} (n={len(comp_data)})', color=color)
            plt.legend(title='Query Complexity', loc='upper right', fontsize=11, framealpha=0.9)
        else:
            plt.hist(df['duration'], bins=50, color='royalblue', alpha=0.7, label=f'All Queries (n={len(df)})')
            plt.legend(loc='upper right')
        plt.title('Query Duration Distribution by Complexity', fontsize=14, fontweight='bold')
        plt.xlabel('Duration (seconds)', fontsize=12)
        plt.ylabel('Query Count', fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path / 'duration_by_complexity.png', dpi=150)
        plt.close()

        # Duration distribution plot by operation
        if 'operation' in df.columns:
            plt.figure(figsize=(12, 7))
            operations = sorted(df['operation'].unique())
            op_colors = sns.color_palette('Set2', len(operations))
            for idx, op in enumerate(operations):
                op_data = df[df['operation'] == op]['duration']
                plt.hist(op_data, bins=50, alpha=0.6, label=f'{op.upper()} (n={len(op_data)})', color=op_colors[idx])
            plt.legend(title='Operation Type', loc='upper right', fontsize=11, framealpha=0.9)
            plt.title('Query Duration Distribution by Operation', fontsize=14, fontweight='bold')
            plt.xlabel('Duration (seconds)', fontsize=12)
            plt.ylabel('Query Count', fontsize=12)
            plt.grid(True, linestyle='--', alpha=0.3)
            plt.tight_layout()
            plt.savefig(output_path / 'duration_distribution_by_operation.png', dpi=150)
            plt.close()

        # Success rate over time by complexity
        if 'timestamp' in df.columns and 'success' in df.columns:
            try:
                plt.figure(figsize=(14, 7))
                
                if 'complexity' in df.columns:
                    complexities = sorted(df['complexity'].unique())
                    colors = {'simple': '#4CAF50', 'medium': '#FFC107', 'complex': '#F44336'}
                    linestyles = {'simple': '-', 'medium': '--', 'complex': '-.'}
                    
                    for comp in complexities:
                        comp_df = df[df['complexity'] == comp].set_index('timestamp')
                        if len(comp_df) > 0:
                            success_rate = comp_df['success'].rolling('30s', min_periods=1).mean()
                            plt.plot(success_rate.index, success_rate.values, 
                                   label=f'{comp.capitalize()} (n={len(comp_df)})', 
                                   color=colors.get(comp, 'blue'),
                                   linestyle=linestyles.get(comp, '-'),
                                   linewidth=2.5, alpha=0.8, marker='o', markersize=3, markevery=20)
                    plt.legend(title='Query Complexity', loc='lower left', fontsize=11, framealpha=0.9)
                else:
                    success_rate = df.set_index('timestamp')['success'].rolling('30s', min_periods=1).mean()
                    plt.plot(success_rate.index, success_rate.values, 
                           color='seagreen', linewidth=2, label=f'All Queries (n={len(df)})')
                    plt.legend(loc='lower left')
                
                plt.title('Success Rate Over Time by Complexity (30-second rolling window)', fontsize=14, fontweight='bold')
                plt.xlabel('Time', fontsize=12)
                plt.ylabel('Success Rate', fontsize=12)
                plt.ylim(-0.05, 1.05)
                plt.grid(True, linestyle='--', alpha=0.3)
                plt.tight_layout()
                plt.savefig(output_path / 'success_rate_timeline.png', dpi=150)
                plt.close()
            except Exception as e:
                print(f"Error generating success rate timeline: {e}")

        # Duration by complexity boxplot
        if 'complexity' in df.columns:
            try:
                plt.figure(figsize=(12, 7))
                df_clean = df[df['duration'].notna()]
                complexities = sorted(df_clean['complexity'].unique())
                
                box_data = [df_clean[df_clean['complexity'] == c]['duration'].values 
                           for c in complexities]
                box_labels = [f'{c.capitalize()}\n(n={len(df_clean[df_clean["complexity"] == c])})' 
                             for c in complexities]
                
                bp = plt.boxplot(box_data, labels=box_labels, patch_artist=True,
                               showmeans=True, meanline=True,
                               boxprops=dict(linewidth=1.5),
                               whiskerprops=dict(linewidth=1.5),
                               capprops=dict(linewidth=1.5),
                               medianprops=dict(linewidth=2, color='darkred'),
                               meanprops=dict(linewidth=2, color='blue', linestyle='--'))
                
                # Color boxes with consistent scheme
                colors = {'simple': '#4CAF50', 'medium': '#FFC107', 'complex': '#F44336'}
                for patch, comp in zip(bp['boxes'], complexities):
                    patch.set_facecolor(colors.get(comp, 'lightblue'))
                    patch.set_alpha(0.7)
                
                plt.title('Query Duration Distribution by Complexity', fontsize=14, fontweight='bold')
                plt.xlabel('Query Complexity', fontsize=12)
                plt.ylabel('Duration (seconds)', fontsize=12)
                plt.grid(True, linestyle='--', alpha=0.3, axis='y')
                
                # Add legend for median/mean
                from matplotlib.lines import Line2D
                legend_elements = [
                    Line2D([0], [0], color='darkred', linewidth=2, label='Median'),
                    Line2D([0], [0], color='blue', linewidth=2, linestyle='--', label='Mean')
                ]
                plt.legend(handles=legend_elements, loc='upper right', fontsize=10)
                
                plt.tight_layout()
                plt.savefig(output_path / 'duration_by_complexity.png', dpi=150)
                plt.close()
            except Exception as e:
                print(f"Error generating complexity boxplot: {e}")

        # === INTERACTIVE PLOTS (HTML) using Plotly ===
        # Interactive plots disabled per user request
        # if PLOTLY_AVAILABLE:
        #     MetricsUtils._generate_interactive_plots(df, output_path)

    @staticmethod
    def _generate_interactive_plots(df: pd.DataFrame, output_path: Path):
        """Generate interactive HTML plots using Plotly."""
        try:
            # Interactive duration distribution by complexity (primary) or operation (fallback)
            if 'complexity' in df.columns:
                fig = px.histogram(df, x='duration', color='complexity',
                                 title='Query Duration Distribution by Complexity (Interactive)',
                                 labels={'duration': 'Duration (seconds)', 'complexity': 'Complexity'},
                                 nbins=50, opacity=0.7,
                                 color_discrete_map={'simple': '#4CAF50', 'medium': '#FFC107', 'complex': '#F44336'})
            elif 'operation' in df.columns:
                fig = px.histogram(df, x='duration', color='operation',
                                 title='Query Duration Distribution by Operation (Interactive)',
                                 labels={'duration': 'Duration (seconds)', 'operation': 'Operation'},
                                 nbins=50, opacity=0.7)
            else:
                fig = px.histogram(df, x='duration',
                                 title='Query Duration Distribution (Interactive)',
                                 labels={'duration': 'Duration (seconds)'},
                                 nbins=50, opacity=0.7)
            
            fig.update_layout(
                hovermode='x unified',
                legend=dict(title='Query Type', orientation='v', x=1.02, y=1),
                height=600,
                font=dict(size=12)
            )
            fig.write_html(output_path / 'duration_distribution_interactive.html')

            # Interactive timeline with success/failure
            if 'timestamp' in df.columns:
                # Success rate timeline
                fig = go.Figure()
                
                if 'complexity' in df.columns:
                    for comp in df['complexity'].unique():
                        comp_df = df[df['complexity'] == comp].sort_values('timestamp')
                        if len(comp_df) > 0:
                            # Calculate rolling success rate
                            comp_df = comp_df.set_index('timestamp')
                            success_rate = comp_df['success'].rolling('30s', min_periods=1).mean()
                            
                            fig.add_trace(go.Scatter(
                                x=success_rate.index,
                                y=success_rate.values,
                                mode='lines',
                                name=f'{comp.capitalize()} (n={len(comp_df)})',
                                line=dict(width=2),
                                hovertemplate='<b>Time:</b> %{x}<br><b>Success Rate:</b> %{y:.2%}<extra></extra>'
                            ))
                
                fig.update_layout(
                    title='Success Rate Over Time (Interactive, 30s rolling)',
                    xaxis_title='Time',
                    yaxis_title='Success Rate',
                    hovermode='x unified',
                    legend=dict(title='Query Complexity'),
                    height=600,
                    yaxis=dict(range=[-0.05, 1.05])
                )
                fig.write_html(output_path / 'success_rate_interactive.html')

                # Duration scatter plot over time
                fig = px.scatter(df, x='timestamp', y='duration', 
                               color='operation' if 'operation' in df.columns else None,
                               symbol='complexity' if 'complexity' in df.columns else None,
                               title='Query Duration Over Time (Interactive)',
                               labels={'timestamp': 'Time', 'duration': 'Duration (seconds)'},
                               hover_data=['query_gist', 'file_name', 'success'])
                fig.update_layout(
                    height=600,
                    legend=dict(title='Operation / Complexity')
                )
                fig.write_html(output_path / 'duration_timeline_interactive.html')

            # Interactive box plot by complexity
            if 'complexity' in df.columns:
                fig = px.box(df, x='complexity', y='duration', color='complexity',
                           title='Query Duration by Complexity (Interactive)',
                           labels={'complexity': 'Query Complexity', 'duration': 'Duration (seconds)'},
                           points='outliers')
                fig.update_layout(
                    showlegend=True,
                    legend=dict(title='Complexity Level'),
                    height=600
                )
                fig.write_html(output_path / 'duration_by_complexity_interactive.html')

        except Exception as e:
            print(f"Error generating interactive plots: {e}")

    @staticmethod
    def generate_metrics_report(metrics: List[Dict[str, Any]], output_file: str, db_config: Dict[str, Any] = None):
        """
        Generate a comprehensive metrics report in HTML format.

        Args:
            metrics: List of query execution metrics
            output_file: Path to save the HTML report
            db_config: Optional database configuration with host, username, etc.

        Returns:
            None
        """
        df = pd.DataFrame(metrics)
        # Do not modify query_id here; it is constructed correctly at source
        
        # Extract db info from config if provided
        db_host = db_config.get('host', 'N/A') if db_config else 'N/A'
        db_username = db_config.get('username', 'N/A') if db_config else 'N/A'
        db_database = db_config.get('database', 'N/A') if db_config else 'N/A'
        db_type = db_config.get('db_type', 'N/A') if db_config else 'N/A'
        # Ensure output directory exists
        out_path = Path(output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Format timestamps
        if 'start_time' in df.columns:
            df['start_time_iso'] = pd.to_datetime(df['start_time'], unit='s').dt.strftime('%Y-%m-%d %H:%M:%S')
        if 'end_time' in df.columns:
            df['end_time_iso'] = pd.to_datetime(df['end_time'], unit='s').dt.strftime('%Y-%m-%d %H:%M:%S')

        # Build clear summary statistics
        total_queries = len(df)
        success_count = int(df['success'].sum()) if 'success' in df.columns else 0
        avg_duration = df['duration'].mean() if 'duration' in df.columns else None
        percentiles = {}
        if 'duration' in df.columns and total_queries > 0:
            percentiles = {
                'p50': df['duration'].quantile(0.5),
                'p90': df['duration'].quantile(0.9),
                'p95': df['duration'].quantile(0.95),
                'p99': df['duration'].quantile(0.99),
            }
        total_rows = int(df['rows_processed'].sum()) if 'rows_processed' in df.columns else 0
        first_ts = df['start_time_iso'].iloc[0] if 'start_time_iso' in df.columns and len(df) > 0 else ''
        last_ts = df['end_time_iso'].iloc[-1] if 'end_time_iso' in df.columns and len(df) > 0 else ''

        # Set HTML title based on test_type (from thread_name prefix if present)
        html_title = 'Database Test Metrics Report'
        if 'thread_name' in df.columns and len(df['thread_name']) > 0:
            first_tn = df['thread_name'].iloc[0]
            if isinstance(first_tn, str) and first_tn.startswith('soaktest_'):
                html_title = 'Database Soak Test Metrics Report'
            elif isinstance(first_tn, str) and first_tn.startswith('loadtest_'):
                html_title = 'Database Load Test Metrics Report'
        html = ['<html>', '<head>', f'<title>{html_title}</title>', 
                '<style>',
                'body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }',
                'h1 { color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }',
                'h2 { color: #555; margin-top: 30px; }',
                'table { border-collapse: collapse; width: 100%; background-color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }',
                'th, td { border: 1px solid #ddd; padding: 10px; text-align: left; font-size: 13px; }',
                'th { background-color: #4CAF50; color: white; font-weight: bold; }',
                'tr:nth-child(even) { background-color: #f9f9f9; }',
                'tr:hover { background-color: #f1f1f1; }',
                '.section { margin-bottom: 40px; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }',
                '.interactive-link { display: inline-block; margin: 10px 10px 10px 0; padding: 10px 20px; background-color: #2196F3; color: white; text-decoration: none; border-radius: 4px; font-weight: bold; }',
                '.interactive-link:hover { background-color: #0b7dda; }',
                '.success-true { color: green; font-weight: bold; }',
                '.success-false { color: red; font-weight: bold; }',
                '</style>', '</head>', '<body>', f'<h1>🎯 {html_title}</h1>']

        # Add database connection info section at the top
        html.append('<div class="section"><h2>📊 Test Configuration</h2>')
        html.append('<table border="1">')
        html.append(f'<tr><th>Database Type</th><td>{db_type}</td></tr>')
        html.append(f'<tr><th>Database Host</th><td>{db_host}</td></tr>')
        html.append(f'<tr><th>Database User</th><td>{db_username}</td></tr>')
        html.append(f'<tr><th>Database Name</th><td>{db_database}</td></tr>')
        html.append(f'<tr><th>Report Generated</th><td>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</td></tr>')
        html.append('</table></div>')

        # Summary section - moved to top
        html.append('<div class="section"><h2>📈 Summary</h2>')
        # Overall summary
        html.append('<h3>Overall Statistics</h3><table border="1">')
        html.append(f'<tr><th>Total Queries</th><td>{total_queries}</td></tr>')
        html.append(f'<tr><th>Success Rate (%)</th><td>{(success_count/total_queries*100 if total_queries else 0):.2f}</td></tr>')
        if avg_duration is not None:
            html.append(f'<tr><th>Avg Duration (s)</th><td>{avg_duration:.6f}</td></tr>')
        else:
            html.append(f'<tr><th>Avg Duration (s)</th><td>N/A</td></tr>')
        for p, v in percentiles.items():
            html.append(f'<tr><th>Duration {p.upper()} (s)</th><td>{v:.6f}</td></tr>')
        html.append(f'<tr><th>Total Rows Processed</th><td>{total_rows}</td></tr>')
        html.append(f'<tr><th>First Query Start</th><td>{first_ts}</td></tr>')
        html.append(f'<tr><th>Last Query End</th><td>{last_ts}</td></tr>')
        html.append('</table>')
        
        # Breakdown by operation type (Read vs Write)
        if 'operation' in df.columns:
            html.append('<h3>Breakdown by Operation Type</h3>')
            
            # Classify operations
            read_ops = ['select', 'find']
            write_ops = ['insert', 'update', 'delete', 'insert_one', 'delete_many']
            
            read_df = df[df['operation'].str.lower().isin(read_ops)]
            write_df = df[df['operation'].str.lower().isin(write_ops)]
            
            html.append('<table border="1"><tr><th>Metric</th><th>Read Operations</th><th>Write Operations</th><th>All Operations</th></tr>')
            
            # Query counts
            html.append(f'<tr><td><b>Total Queries</b></td><td>{len(read_df)}</td><td>{len(write_df)}</td><td>{total_queries}</td></tr>')
            
            # Success rates
            read_success = (read_df['success'].sum() / len(read_df) * 100) if len(read_df) > 0 else 0
            write_success = (write_df['success'].sum() / len(write_df) * 100) if len(write_df) > 0 else 0
            html.append(f'<tr><td><b>Success Rate (%)</b></td><td>{read_success:.2f}</td><td>{write_success:.2f}</td><td>{(success_count/total_queries*100 if total_queries else 0):.2f}</td></tr>')
            
            # Average duration
            read_avg = read_df['duration'].mean() if len(read_df) > 0 else 0
            write_avg = write_df['duration'].mean() if len(write_df) > 0 else 0
            all_avg = avg_duration if avg_duration is not None else 0
            html.append(f'<tr><td><b>Avg Duration (s)</b></td><td>{read_avg:.6f}</td><td>{write_avg:.6f}</td><td>{all_avg:.6f}</td></tr>')
            
            # P95 duration
            read_p95 = read_df['duration'].quantile(0.95) if len(read_df) > 0 else 0
            write_p95 = write_df['duration'].quantile(0.95) if len(write_df) > 0 else 0
            all_p95 = percentiles.get('p95', 0)
            html.append(f'<tr><td><b>P95 Duration (s)</b></td><td>{read_p95:.6f}</td><td>{write_p95:.6f}</td><td>{all_p95:.6f}</td></tr>')
            
            # Rows processed
            read_rows = int(read_df['rows_processed'].sum()) if 'rows_processed' in read_df.columns else 0
            write_rows = int(write_df['rows_processed'].sum()) if 'rows_processed' in write_df.columns else 0
            html.append(f'<tr><td><b>Rows Processed</b></td><td>{read_rows}</td><td>{write_rows}</td><td>{total_rows}</td></tr>')
            
            html.append('</table>')
        
        # Breakdown by complexity
        if 'complexity' in df.columns:
            html.append('<h3>Breakdown by Query Complexity</h3>')
            html.append('<table border="1"><tr><th>Complexity</th><th>Query Count</th><th>Success Rate (%)</th><th>Avg Duration (s)</th><th>P95 Duration (s)</th></tr>')
            
            for comp in sorted(df['complexity'].unique()):
                comp_df = df[df['complexity'] == comp]
                comp_count = len(comp_df)
                comp_success = (comp_df['success'].sum() / comp_count * 100) if comp_count > 0 else 0
                comp_avg = comp_df['duration'].mean() if comp_count > 0 else 0
                comp_p95 = comp_df['duration'].quantile(0.95) if comp_count > 0 else 0
                
                html.append(f'<tr><td><b>{comp.capitalize()}</b></td><td>{comp_count}</td><td>{comp_success:.2f}</td><td>{comp_avg:.6f}</td><td>{comp_p95:.6f}</td></tr>')
            
            html.append('</table>')
        
        html.append('</div>')

        # Per-query table (random 50 rows) with robust value filling, only static formatting
        html.append('<div class="section"><h2>📋 Sample Query Metrics (random 50 queries)</h2>')
        html.append('<div style="overflow-x: auto;"><table border="1"><tr>')
        sample_cols = [
            'test_case_id', 'file_name', 'operation', 'complexity', 
            'duration', 'success', 'rows_affected', 
            'start_time_iso', 'end_time_iso',
            'thread_name', 'query_gist',
            'error', 'error_code', 'return_code',
            'memory_usage', 'cpu_time', 'job_id', 'db_host', 'db_username'
        ]
        # Add db_host and db_username to dataframe if not present
        if 'db_host' not in df.columns:
            df['db_host'] = db_host
        if 'db_username' not in df.columns:
            df['db_username'] = db_username
            
        cols = [col for col in sample_cols if col in df.columns]
        col_tooltips = {
            'test_case_id': 'Unique test case identifier',
            'file_name': 'SQL file name',
            'operation': 'Query operation type',
            'complexity': 'Query complexity level',
            'duration': 'Execution time (seconds)',
            'success': 'Query success status',
            'rows_affected': 'Number of rows affected/returned',
            'start_time_iso': 'Query start time',
            'end_time_iso': 'Query end time',
            'thread_name': 'Executing thread',
            'query_gist': 'First 200 chars of SQL',
            'error': 'Error message if failed',
            'memory_usage': 'Memory usage (MB)',
            'cpu_time': 'CPU time (seconds)',
            'db_host': 'Database host',
            'db_username': 'Database username'
        }
        for col in cols:
            tooltip = col_tooltips.get(col, col)
            html.append(f'<th title="{tooltip}">{col.replace("_", " ").title()}</th>')
        html.append('</tr>')
        # Show random 50 queries
        sample_df = df.sample(n=min(50, len(df)), random_state=42) if len(df) > 50 else df
        for _, row in sample_df.iterrows():
            html.append('<tr>')
            for col in cols:
                val = row.get(col)
                # Robust value filling
                if pd.isna(val) or val is None:
                    if col in ['error', 'error_code', 'return_code']:
                        val = ''
                    elif col in ['memory_usage', 'cpu_time']:
                        val = 0.0
                    elif col == 'rows_affected':
                        val = 0
                    else:
                        val = 'N/A'
                if col == 'success':
                    css_class = 'success-true' if val else 'success-false'
                    display_val = '✓ Yes' if val else '✗ No'
                    html.append(f'<td class="{css_class}">{display_val}</td>')
                elif col == 'duration':
                    try:
                        html.append(f'<td>{float(val):.6f}</td>')
                    except:
                        html.append(f'<td>0.000000</td>')
                elif col in ['memory_usage', 'cpu_time']:
                    try:
                        html.append(f'<td>{float(val):.2f}</td>')
                    except:
                        html.append(f'<td>0.00</td>')
                elif col == 'rows_affected':
                    try:
                        html.append(f'<td>{int(val)}</td>')
                    except:
                        html.append(f'<td>0</td>')
                elif col == 'query_gist':
                    gist = str(val) if val and val != 'N/A' else ''
                    gist = gist[:100] + ('...' if len(gist) > 100 else '')
                    gist = gist.replace('<', '&lt;').replace('>', '&gt;')
                    html.append(f'<td style="font-family: monospace; font-size: 11px;">{gist if gist else 'N/A'}</td>')
                elif col == 'error':
                    err = str(val) if val else ''
                    if err:
                        err = err.replace('<', '&lt;').replace('>', '&gt;')
                        html.append(f'<td style="color: red; font-size: 11px;">{err[:100]}</td>')
                    else:
                        html.append(f'<td></td>')
                elif col == 'return_code':
                    # Show numeric return codes including 0 without converting to N/A
                    html.append(f'<td>{"" if val is None else val}</td>')
                elif col in ['start_time_iso', 'end_time_iso']:
                    html.append(f'<td style="font-size: 11px; white-space: nowrap;">{val if val and val != 'N/A' else 'N/A'}</td>')
                elif col in ['db_host', 'db_username']:
                    # Display database connection info
                    db_val = row.get(col) if row.get(col) else 'N/A'
                    html.append(f'<td style="font-size: 11px;">{db_val}</td>')
                elif col in ['test_case_id', 'job_id']:
                    html.append(f'<td style="font-size: 10px;">{val if val and val != 'N/A' else 'N/A'}</td>')
                elif col in ['file_name', 'operation', 'complexity', 'thread_name']:
                    html.append(f'<td>{val if val and val != 'N/A' else 'N/A'}</td>')
                else:
                    html.append(f'<td>{val if val and val != 'N/A' else 'N/A'}</td>')
            html.append('</tr>')
        html.append('</table></div></div>')

        # Plots section - moved to end
        plot_dir = out_path.parent / 'plots'
        html.append('<div class="section"><h2>📊 Performance Visualizations</h2>')
        
        # Embed static plots if they exist
        plot_files = [
            ('duration_distribution_by_operation.png', 'Query Duration Distribution by Operation'),
            ('duration_by_complexity.png', 'Query Duration Distribution by Complexity'),
            ('success_rate_timeline.png', 'Success Rate Over Time by Complexity'),
            ('performance_heatmap.png', 'Query Duration Heatmap by Connection')
        ]
        for fname, caption in plot_files:
            plot_path = plot_dir / fname
            if plot_path.exists():
                html.append(f'<h3>{caption}</h3><img src="plots/{fname}" style="max-width:100%; border: 1px solid #ddd;"><br><br>')
        html.append('</div>')

        # Field legend
        html.append('<div class="section"><h2>📖 Field Definitions</h2><ul>')
        html.append('<li><b>query_gist</b>: First 200 chars of SQL query</li>')
        html.append('<li><b>file_name</b>: Source .sql file</li>')
        html.append('<li><b>operation</b>: Query type (select/insert/update/delete)</li>')
        html.append('<li><b>complexity</b>: Query complexity (simple/medium/complex)</li>')
        html.append('<li><b>duration</b>: Execution time in seconds</li>')
        html.append('<li><b>success</b>: True if query succeeded</li>')
        html.append('<li><b>error</b>: Error message if any</li>')
        html.append('<li><b>thread_name</b>: Thread assigned to query</li>')
        html.append('<li><b>start_time_iso</b>: Query start time (ISO8601)</li>')
        html.append('<li><b>db_host</b>: Database server host</li>')
        html.append('<li><b>db_username</b>: Database connection username</li>')
        html.append('</ul></div>')

        html.append('</body></html>')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html))
# Quick Start Guide - Viewing Enhanced Reports

## 🎯 How to View Your Test Results

### 1. Locate Your Report
After running a test, reports are saved in:
```
reports/<JOB_ID>/
├── soak_test_report_<user>.html    ← Main report (START HERE)
├── query_metrics_report_<user>.csv ← Full data export
├── metrics_<user>.json             ← Machine-readable metrics
└── plots/                          ← All visualizations
    ├── duration_distribution.png
    ├── success_rate_timeline.png
    ├── duration_by_complexity.png
    ├── duration_distribution_interactive.html
    ├── success_rate_interactive.html
    ├── duration_timeline_interactive.html
    └── duration_by_complexity_interactive.html
```

### 2. Open the Main HTML Report
**Double-click:** `soak_test_report_<user>.html`

The report opens in your default browser and contains:
- 📊 Interactive visualization links (top section)
- 📈 Static plots with legends (embedded)
- 📋 Sample query metrics (100 queries)
- 📊 Summary statistics

### 3. Use Interactive Plots

#### **Accessing Interactive Plots**
Click any blue button at the top of the report:
- 📈 Duration Distribution
- 📈 Success Rate  
- 📈 Duration Timeline
- 📈 Duration By Complexity

#### **Interactive Features**
| Action | How To |
|--------|--------|
| **Zoom In** | Click and drag to select area |
| **Zoom Out** | Double-click plot area |
| **Pan** | Click and drag while zoomed |
| **Filter Series** | Click legend items to show/hide |
| **See Details** | Hover over data points |
| **Reset View** | Click "Reset axes" button (top right) |
| **Download** | Click camera icon (top right) |

### 4. Understanding the Plots

#### **Duration Distribution** 
Shows how query execution times are distributed
- **Static PNG**: Histogram with color-coded operation types
- **Interactive HTML**: Zoom into specific duration ranges, filter by operation
- **Look for**: Most queries should be in low-duration range

#### **Success Rate Timeline**
Shows success percentage over time by complexity
- **Static PNG**: Line chart with complexity legends
- **Interactive HTML**: See exact success rates at any point
- **Look for**: Consistent 100% success rate (flat line at top)

#### **Duration by Complexity**
Shows how execution time varies by query complexity
- **Static PNG**: Color-coded boxplot (Blue=Simple, Green=Medium, Red=Complex)
- **Interactive HTML**: See individual data points and outliers
- **Look for**: Higher complexity = longer median duration

#### **Duration Timeline**
Shows all query durations over time (Interactive only)
- Scatter plot with each dot = one query
- Color by operation, shape by complexity
- **Look for**: Patterns or spikes in execution time

### 5. Reading the Metrics Table

The sample metrics table shows 100 queries with:

| Column | Meaning |
|--------|---------|
| **Test Case ID** | Unique identifier for each query execution |
| **File Name** | SQL file that was executed |
| **Operation** | select, insert, update, or delete |
| **Complexity** | simple, medium, or complex |
| **Duration** | Execution time in seconds (6 decimals) |
| **Success** | ✓ Yes (green) or ✗ No (red) |
| **Rows Affected** | Number of rows returned/modified |
| **Start/End Time** | ISO8601 timestamps |
| **Thread Name** | Which thread executed the query |
| **Query Gist** | First 100 characters of SQL |
| **Error** | Error message if failed (red text) |

### 6. Exporting Data

#### **CSV Export**
Open `query_metrics_report_<user>.csv` in Excel/Sheets for:
- Pivot tables
- Custom filtering
- Additional analysis

#### **JSON Export**
Use `metrics_<user>.json` for:
- Programmatic analysis
- Integration with other tools
- Machine learning pipelines

### 7. Comparing Tests

To compare multiple test runs:
1. Keep reports in different folders (each has unique JOB_ID)
2. Open CSVs side-by-side in Excel
3. Compare key metrics:
   - Average duration
   - Success rate
   - P95/P99 percentiles
   - Total queries executed

### 8. Tips & Tricks

#### **Performance Indicators**
- ✅ **Good**: Success rate = 100%, duration stable, no outliers
- ⚠️ **Warning**: Success rate 95-99%, some duration spikes
- ❌ **Problem**: Success rate < 95%, many errors, high variance

#### **Browser Compatibility**
- **Chrome/Edge**: Full support, best performance
- **Firefox**: Full support
- **Safari**: Full support  
- **IE11**: Not supported (use modern browser)

#### **Troubleshooting**
- **Interactive plots not loading?** 
  - Check if JavaScript is enabled
  - Try opening in Chrome/Firefox
  
- **Plots look wrong?**
  - Refresh the page (Ctrl+F5)
  - Check if all plot files exist in `/plots` folder

- **Want higher resolution?**
  - Static PNGs are 150 DPI (print quality)
  - Interactive plots can be downloaded at any resolution

### 9. Example Workflow

```
1. Run test: python main.py -c configs/read_heavy_load.json
2. Wait for completion
3. Open: reports/<JOB_ID>/soak_test_report_read_heavy.html
4. Review summary statistics
5. Click interactive plot links
6. Zoom into interesting time ranges
7. Check sample metrics for any errors
8. Export CSV if needed for detailed analysis
```

### 10. Configuration Tips

For better visualizations with clear patterns:
- **Short tests** (5-10s): Good for quick validation
- **Medium tests** (60s): Shows patterns and trends
- **Long tests** (300s+): Comprehensive load testing

Thread allocation affects complexity distribution:
```json
"read_complexity": {
    "simple": 0.6,   // 60% of read threads
    "medium": 0.3,   // 30% of read threads  
    "complex": 0.1   // 10% of read threads
}
```

## 🎉 You're Ready!

Your soak test framework now provides enterprise-grade reporting with:
- ✅ Clear legends on all plots
- ✅ Interactive HTML visualizations  
- ✅ Comprehensive sample metrics
- ✅ Complexity-based thread allocation

Happy testing! 🚀

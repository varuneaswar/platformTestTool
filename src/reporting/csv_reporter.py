from .reporter import Reporter
from typing import Dict, Any, List
import csv
import os
from datetime import datetime

class CsvReporter(Reporter):
    def __init__(self, path: str, fieldnames: List[str]):
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        self.path = path
        self.fieldnames = fieldnames
        self._rows = []

    def record(self, metric: Dict[str, Any]) -> None:
        """Normalize and record a metric row."""
        # Format timestamps
        def fmt_time(val):
            try:
                if val:
                    return datetime.fromtimestamp(float(val)).isoformat(sep=' ', timespec='seconds')
                return ''
            except Exception:
                return ''
        
        row = {}
        for k in self.fieldnames:
            if k == 'start_time':
                row[k] = fmt_time(metric.get('start_time'))
            elif k == 'end_time':
                row[k] = fmt_time(metric.get('end_time'))
            elif k == 'elapsed_time':
                row[k] = metric.get('duration', '')
            elif k == 'error_desc':
                row[k] = metric.get('error', '')
            else:
                row[k] = metric.get(k, '')
        
        self._rows.append(row)

    def finalize(self) -> None:
        """Write CSV file."""
        with open(self.path, "w", newline='', encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=self.fieldnames)
            writer.writeheader()
            for r in self._rows:
                writer.writerow(r)


import argparse
import pandas as pd
import os
from perfetto.trace_processor import TraceProcessor

def main(dummy, path):
    rows = []
    run_id = 0
    for trace_file in os.listdir(path):
        
        trace_path = os.path.join(path, trace_file)
        tp = TraceProcessor(trace=trace_path)
        
        cpu_sql = """
        SELECT
            (SUM(dur) * 100) / ((MAX(ts) - MIN(ts)) * COUNT(DISTINCT cpu)) AS cpu_percent
        FROM sched
        """
        cpu_result = tp.query(cpu_sql).as_pandas_dataframe()

        cpu_percent = (
            cpu_result["cpu_percent"].iloc[0] if not cpu_result.empty else 0.0
        )

      
        mem_sql = """
        SELECT 
            AVG(value) / 1024.0 / 1024.0 AS avg_memory_mb
        FROM counters
        WHERE name = 'mem.rss';
        """
        mem_result = tp.query(mem_sql).as_pandas_dataframe()

        avg_memory_mb = (
            mem_result["avg_memory_mb"].iloc[0] if not mem_result.empty else 0.0
        )

        df = pd.DataFrame(
            {"cpu_percent": [cpu_percent], "avg_memory_mb": [avg_memory_mb]}
        )
        rows.append({
            "run Id": run_id,
            "cpu_usage": cpu_percent,
            "execution_time": avg_memory_mb
        })
        run_id = run_id + 1
        parser = argparse.ArgumentParser(description="Aggregate Perfetto trace metrics.")
        parser.add_argument("--trace", required=True, help="Path to Perfetto trace file (.perfetto-trace)")
        parser.add_argument("--out", default="aggregate_metrics.csv", help="Output CSV file path")

        out_file = os.path.join(path, "aggregated_results.csv")
        pd.DataFrame(rows).to_csv(out_file, index=False)
        print(f"[aggregate_perfetto] Aggregated results saved to {out_file}")
        

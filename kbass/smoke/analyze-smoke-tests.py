#!/usr/bin/env python3
"""Analyze Cloudmesh VM smoke-test benchmark results."""

import json
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_benchmarks(root: Path = REPO_ROOT) -> pd.DataFrame:
    """Load benchmark timers from contributor JSON files."""
    records = []

    for path in sorted(
        set(root.glob("*/smoke/*.json"))
        | set(root.glob("results/**/*.json"))
    ):
        try:
            with path.open(encoding="utf-8") as file:
                data = json.load(file)

            experiment = data["experiment"]
            timers = data["timers"]
            platform = data.get("system", {}).get("platform", {})

            for timer in timers:
                records.append(
                    {
                        "file": str(path.relative_to(root)),
                        "benchmark": experiment["benchmark"],
                        "user": experiment["user"],
                        "date": experiment["date"],
                        "branch": experiment.get("branch", ""),
                        "commit": experiment.get("commit", ""),
                        "os": platform.get("system", ""),
                        "architecture": platform.get("machine", ""),
                        "operation": timer["name"],
                        "status": timer["status"],
                        "seconds": float(timer["time"]),
                    }
                )

        except (OSError, ValueError, KeyError, TypeError) as error:
            print(f"Skipping {path}: {error}")

    for path in sorted(
        set(root.glob("*/smoke/*.csv"))
        | set(root.glob("results/**/*.csv"))
    ):
        try:
            csv = pd.read_csv(path)

            required = {
                "benchmark", "user", "date",
                "operation", "status", "seconds"
            }

            missing = required - set(csv.columns)
            if missing:
                raise ValueError(
                    f"Missing required CSV columns: {sorted(missing)}"
                )

            for row in csv.to_dict(orient="records"):
                records.append({
                    "file": str(path.relative_to(root)),
                    "benchmark": row["benchmark"],
                    "user": row["user"],
                    "date": row["date"],
                    "branch": row.get("branch", ""),
                    "commit": row.get("commit", ""),
                    "os": row.get("os", ""),
                    "architecture": row.get("architecture", ""),
                    "operation": row["operation"],
                    "status": row["status"],
                    "seconds": float(row["seconds"]),
                })

        except (OSError, ValueError, TypeError) as error:
            print(f"Skipping {path}: {error}")

    return pd.DataFrame.from_records(records)



def plot_execution_times(df: pd.DataFrame) -> list[Path]:
    """Generate readable execution-time charts by benchmark category."""
    output = Path(__file__).resolve().parent / "images"
    output.mkdir(parents=True, exist_ok=True)

    generated = []

    successful = df[
        (df["status"] == "ok") &
        (df["seconds"] >= 0)
    ].copy()

    for benchmark, group in successful.groupby("benchmark"):
        summary = (
            group.groupby(["operation", "user"], as_index=False)
            .agg(
                median_seconds=("seconds", "median"),
                measurements=("seconds", "count"),
            )
        )

        summary = summary.sort_values("median_seconds")

        labels = [
            f"{row.operation} ({row.user}, n={row.measurements})"
            for row in summary.itertuples()
        ]

        fig, ax = plt.subplots(
            figsize=(12, max(5, len(summary) * 0.42))
        )

        ax.barh(labels, summary["median_seconds"])
        ax.set_xscale("symlog", linthresh=0.01)
        ax.set_xlabel(
            "Median successful execution time (seconds; "
            "symmetric logarithmic scale)"
        )
        ax.set_title(f"{benchmark}: Operation Execution Times")
        ax.grid(axis="x", alpha=0.25)
        ax.set_axisbelow(True)

        fig.tight_layout()

        filename = (
            benchmark.lower()
            .replace(" ", "-")
            .replace("_", "-")
            + "-execution-times.png"
        )

        destination = output / filename
        fig.savefig(destination, dpi=200, bbox_inches="tight")
        plt.close(fig)

        generated.append(destination)

    return generated




def generate_report(df: pd.DataFrame, charts: list[Path]) -> Path:
    """Generate a reproducible Markdown benchmark comparison report."""
    output = Path(__file__).resolve().parent / "comparison.md"

    total_runs = df["file"].nunique()
    total_operations = len(df)
    successful = int((df["status"] == "ok").sum())
    failed = total_operations - successful

    lines = [
        "# Cloudmesh VM Smoke Test Comparison",
        "",
        "## Overview",
        "",
        f"- Benchmark files: **{total_runs}**",
        f"- Operation measurements: **{total_operations}**",
        f"- Successful operations: **{successful}**",
        f"- Non-successful operations: **{failed}**",
        "",
        "## Benchmark Summary",
        "",
        "| Benchmark | Runs | Operations | Successful | Non-successful |",
        "|---|---:|---:|---:|---:|",
    ]

    for benchmark, group in df.groupby("benchmark", sort=True):
        runs = group["file"].nunique()
        operations = len(group)
        ok = int((group["status"] == "ok").sum())
        non_ok = operations - ok

        lines.append(
            f"| {benchmark} | {runs} | {operations} | {ok} | {non_ok} |"
        )

    lines.extend([
        "",
        "## Contributor Coverage",
        "",
        "| Benchmark | Contributor | Runs | Operations | Non-successful |",
        "|---|---|---:|---:|---:|",
    ])

    for (benchmark, user), group in df.groupby(
        ["benchmark", "user"], sort=True
    ):
        lines.append(
            f"| {benchmark} | {user} | {group['file'].nunique()} "
            f"| {len(group)} | {int((group['status'] != 'ok').sum())} |"
        )

    lines.extend([
        "",
        "## Execution-Time Visualizations",
        "",
        "Charts show median durations of successful operations, grouped "
        "by benchmark, operation, and contributor.",
        "",
    ])

    for chart in charts:
        title = chart.stem.replace("-", " ").title()
        lines.extend([
            f"### {title}",
            "",
            f"![{title}](images/{chart.name})",
            "",
        ])

    lines.extend([
        "## Non-Successful Operations",
        "",
    ])

    failures = df[df["status"] != "ok"]

    if failures.empty:
        lines.extend([
            "No non-successful operations were recorded.",
            "",
        ])
    else:
        lines.extend([
            "| Benchmark | Contributor | Operation | Status | Run Date |",
            "|---|---|---|---|---|",
        ])

        for row in failures.itertuples():
            lines.append(
                f"| {row.benchmark} | {row.user} | {row.operation} "
                f"| {row.status} | {row.date} |"
            )

        lines.append("")

    lines.extend([
        "## Interpretation and Limitations",
        "",
        "- Each benchmark JSON file represents one recorded execution run.",
        "- Operation measurements are not independent benchmark runs.",
        "- Timing charts exclude non-successful operations, but the "
        "report retains their statuses.",
        "- A median based on one measurement is that measurement itself; "
        "it does not establish typical performance.",
        "- Different contributors may use different hardware, software "
        "versions, configurations, and Git commits.",
        "- CLI benchmarks and provider smoke tests represent different "
        "workloads and should not be directly compared.",
        "- Timing differences alone do not establish performance "
        "regressions without comparable environments and repeated runs.",
        "",
        "## Reproduction",
        "",
        "From the repository root, run:",
        "",
        "```bash",
        "python kbass/smoke/analyze-smoke-tests.py",
        "```",
        "",
    ])

    output.write_text("\n".join(lines), encoding="utf-8")
    return output



def main() -> None:
    df = load_benchmarks()

    if df.empty:
        print("No valid benchmark results found.")
        return

    print(f"Loaded {df['file'].nunique()} benchmark files.")
    print(f"Loaded {len(df)} operation measurements.")
    print()
    print("Operations by status:")
    print(df.groupby(["benchmark", "status"]).size().to_string())
    charts = plot_execution_times(df)
    print()
    for chart in charts:
        print(f"Chart generated: {chart.relative_to(REPO_ROOT)}")

    report = generate_report(df, charts)
    print(f"Report generated: {report.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()

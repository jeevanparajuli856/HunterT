#!/usr/bin/env python3
"""
Generate table images from evaluation CSVs using matplotlib.

Usage:
    python plot_tables.py
    python plot_tables.py --results-csv ./results/eval_results.csv --output-dir ./results/figures
"""

import argparse
import os
from typing import List

import matplotlib.pyplot as plt
import pandas as pd


DEFAULT_SWEEP = [100, 250, 500, 750, 1000, 2000, 5000, 10000]


def _domain_label(raw_domain: str) -> str:
    """Map filename/domain strings to paper labels when possible."""
    s = str(raw_domain).lower()
    if 'uni' in s or 'univ' in s:
        return 'Universities'
    if 'hos' in s or 'hospital' in s:
        return 'Hospitals'
    if 'gov' in s:
        return 'Government'
    if 'com' in s or 'company' in s:
        return 'Companies'
    return str(raw_domain)


def _normalize_domain_type(value: str) -> str:
    """Normalize domain type strings to paper column names."""
    s = str(value).strip().lower()
    if s.startswith('uni'):
        return 'University'
    if s.startswith('hos'):
        return 'Hospitals'
    if s.startswith('com'):
        return 'Companies'
    if s.startswith('gov'):
        return 'Government'
    return s.title()


def _save_table_image(df: pd.DataFrame, title: str, output_path: str, font_size: int = 10) -> None:
    """Render a dataframe as a matplotlib table and save it as PNG."""
    if df.empty:
        raise ValueError(f"Cannot render empty table: {title}")

    # Scale figure size by table dimensions for readability.
    n_rows, n_cols = df.shape
    fig_w = max(10, n_cols * 2.2)
    fig_h = max(3.5, n_rows * 0.55 + 1.5)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.axis('off')
    ax.set_title(title, fontsize=14, pad=12)

    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        cellLoc='center',
        loc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(font_size)
    table.scale(1, 1.2)

    # Header styling
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold')
            cell.set_facecolor('#E6EEF8')

    fig.tight_layout()
    fig.savefig(output_path, dpi=220, bbox_inches='tight')
    plt.close(fig)


def build_summary_table(eval_df: pd.DataFrame) -> pd.DataFrame:
    """Create paper-style summary table: baseline vs best LM by domain + ALL."""
    baseline_df = eval_df[eval_df['approach'] == 'breadth_first'][['domain', 'successful_responses']].copy()
    baseline_df = baseline_df.rename(columns={'successful_responses': 'Breadth-First'})

    lm_df = eval_df[eval_df['model_file'] != 'baseline'].copy()
    if lm_df.empty:
        raise ValueError('No LM rows found in eval_results.csv. Run evaluation first.')

    best_lm = lm_df.sort_values('successful_responses', ascending=False).groupby('domain', as_index=False).first()
    best_lm = best_lm[['domain', 'successful_responses', 'prediction_limit', 'improvement_percent']]
    best_lm = best_lm.rename(columns={
        'successful_responses': 'Best LM',
        'prediction_limit': 'Best topPredicts',
        'improvement_percent': 'Improvement %'
    })

    merged = baseline_df.merge(best_lm, on='domain', how='inner')
    merged['Domain'] = merged['domain'].map(_domain_label)
    merged = merged[['Domain', 'Breadth-First', 'Best LM', 'Best topPredicts', 'Improvement %']]

    # Numeric formatting
    merged['Improvement %'] = merged['Improvement %'].map(lambda x: f"{x:.1f}%")

    # Add ALL row (mean across domains)
    all_row = {
        'Domain': 'ALL (mean)',
        'Breadth-First': round(pd.to_numeric(merged['Breadth-First']).mean(), 1),
        'Best LM': round(pd.to_numeric(merged['Best LM']).mean(), 1),
        'Best topPredicts': '-',
        'Improvement %': f"{((pd.to_numeric(merged['Best LM']).mean() - pd.to_numeric(merged['Breadth-First']).mean()) / max(pd.to_numeric(merged['Breadth-First']).mean(), 1) * 100):.1f}%"
    }

    merged = pd.concat([merged, pd.DataFrame([all_row])], ignore_index=True)
    return merged


def build_all_approaches_table(eval_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create per-domain table with all key approaches:
    breadth-first, depth-first, probabilistic, and best LM.
    """
    baseline_rows = eval_df[eval_df['model_file'] == 'baseline'].copy()
    baseline_rows = baseline_rows[baseline_rows['approach'].isin(['breadth_first', 'depth_first', 'probabilistic'])]

    baseline_pivot = baseline_rows.pivot_table(
        index='domain',
        columns='approach',
        values='successful_responses',
        aggfunc='max'
    ).reset_index()

    baseline_pivot = baseline_pivot.rename(columns={
        'breadth_first': 'Breadth-First',
        'depth_first': 'Depth-First',
        'probabilistic': 'Probabilistic'
    })

    lm_df = eval_df[eval_df['model_file'] != 'baseline'].copy()
    if lm_df.empty:
        raise ValueError('No LM rows found in eval_results.csv. Run evaluation first.')

    best_lm = lm_df.sort_values('successful_responses', ascending=False).groupby('domain', as_index=False).first()
    best_lm = best_lm[['domain', 'successful_responses', 'prediction_limit', 'improvement_percent']]
    best_lm = best_lm.rename(columns={
        'successful_responses': 'Best LM',
        'prediction_limit': 'Best topPredicts',
        'improvement_percent': 'LM vs BF %'
    })

    merged = baseline_pivot.merge(best_lm, on='domain', how='inner')
    merged['Domain'] = merged['domain'].map(_domain_label)
    merged = merged[[
        'Domain',
        'Breadth-First',
        'Depth-First',
        'Probabilistic',
        'Best LM',
        'Best topPredicts',
        'LM vs BF %'
    ]]

    # Ensure expected columns exist even if an approach is missing in some run.
    for col in ['Breadth-First', 'Depth-First', 'Probabilistic', 'Best LM']:
        if col not in merged.columns:
            merged[col] = 0

    merged['LM vs BF %'] = merged['LM vs BF %'].map(lambda x: f"{x:.1f}%")

    all_row = {
        'Domain': 'ALL (mean)',
        'Breadth-First': round(pd.to_numeric(merged['Breadth-First']).mean(), 1),
        'Depth-First': round(pd.to_numeric(merged['Depth-First']).mean(), 1),
        'Probabilistic': round(pd.to_numeric(merged['Probabilistic']).mean(), 1),
        'Best LM': round(pd.to_numeric(merged['Best LM']).mean(), 1),
        'Best topPredicts': '-',
        'LM vs BF %': f"{((pd.to_numeric(merged['Best LM']).mean() - pd.to_numeric(merged['Breadth-First']).mean()) / max(pd.to_numeric(merged['Breadth-First']).mean(), 1) * 100):.1f}%"
    }
    merged = pd.concat([merged, pd.DataFrame([all_row])], ignore_index=True)
    return merged


def build_paper_four_approaches_table(eval_df: pd.DataFrame) -> pd.DataFrame:
    """Build paper-style table for BF, DF, Probabilistic, and LM."""
    df = eval_df.copy()

    if 'domain_type' not in df.columns:
        # Backward-compatibility for old CSVs: infer a coarse type from domain filename.
        df['domain_type'] = df['domain'].map(_domain_label)

    df['domain_type'] = df['domain_type'].map(_normalize_domain_type)

    # Baseline approaches: one value per domain, then average per domain_type.
    baselines = df[(df['model_file'] == 'baseline') & (df['approach'].isin(['breadth_first', 'depth_first', 'probabilistic']))].copy()
    baseline_agg = baselines.groupby(['approach', 'domain_type'], as_index=False)['successful_responses'].mean()

    # LM: choose best run per domain across models/prediction_limit, then average per domain_type.
    lm = df[df['model_file'] != 'baseline'].copy()
    if lm.empty:
        raise ValueError('No LM rows found in eval_results.csv. Run evaluation first.')
    best_lm_per_domain = lm.sort_values('successful_responses', ascending=False).groupby('domain', as_index=False).first()
    lm_agg = best_lm_per_domain.groupby('domain_type', as_index=False)['successful_responses'].mean()
    lm_agg['approach'] = 'language_model'

    merged = pd.concat([
        baseline_agg[['approach', 'domain_type', 'successful_responses']],
        lm_agg[['approach', 'domain_type', 'successful_responses']]
    ], ignore_index=True)

    table = merged.pivot_table(
        index='approach',
        columns='domain_type',
        values='successful_responses',
        aggfunc='mean'
    )

    expected_cols = ['University', 'Hospitals', 'Companies', 'Government']
    for col in expected_cols:
        if col not in table.columns:
            table[col] = 0.0
    table = table[expected_cols]

    table['ALL Combined'] = table.mean(axis=1)

    row_order = ['breadth_first', 'depth_first', 'probabilistic', 'language_model']
    pretty_names = {
        'breadth_first': 'Breadth-First Baseline',
        'depth_first': 'Depth-First Baseline',
        'probabilistic': 'Probabilistic (Weighted Tree)',
        'language_model': 'Language Model'
    }
    table = table.reindex(row_order)
    table = table.reset_index().rename(columns={'approach': 'Approach'})
    table['Approach'] = table['Approach'].map(pretty_names)

    for col in expected_cols + ['ALL Combined']:
        table[col] = table[col].map(lambda x: f"{x:.1f}")

    return table


def build_sweep_table(eval_df: pd.DataFrame, sweep_values: List[int]) -> pd.DataFrame:
    """Create table showing mean LM discoveries by topPredicts across all domains/models."""
    lm_df = eval_df[eval_df['model_file'] != 'baseline'].copy()
    lm_df = lm_df[lm_df['prediction_limit'].isin(sweep_values)]

    if lm_df.empty:
        raise ValueError('No sweep rows found for selected prediction limits.')

    agg = lm_df.groupby('prediction_limit', as_index=False).agg(
        Mean_Discoveries=('successful_responses', 'mean'),
        Mean_Improvement_Percent=('improvement_percent', 'mean')
    )

    agg = agg.sort_values('prediction_limit')
    agg = agg.rename(columns={'prediction_limit': 'topPredicts'})
    agg['Mean_Discoveries'] = agg['Mean_Discoveries'].map(lambda x: f"{x:.1f}")
    agg['Mean_Improvement_Percent'] = agg['Mean_Improvement_Percent'].map(lambda x: f"{x:.1f}%")
    return agg


def main() -> None:
    parser = argparse.ArgumentParser(description='Generate table images from eval CSV outputs.')
    parser.add_argument('--results-csv', default='./results/eval_results.csv', help='Path to eval_results.csv')
    parser.add_argument('--output-dir', default='./results/figures', help='Directory to save PNG table images')
    parser.add_argument('--sweep', nargs='+', type=int, default=DEFAULT_SWEEP,
                        help='Prediction limits to include in sweep table')
    args = parser.parse_args()

    if not os.path.exists(args.results_csv):
        raise FileNotFoundError(
            f"Results CSV not found at {args.results_csv}. Run `python main.py evaluate` first."
        )

    os.makedirs(args.output_dir, exist_ok=True)
    eval_df = pd.read_csv(args.results_csv)

    # Summary table image (closest to paper-ready comparison)
    summary_df = build_summary_table(eval_df)
    summary_png = os.path.join(args.output_dir, 'table_summary_baseline_vs_lm.png')
    _save_table_image(summary_df, 'Baseline vs Best LSTM by Domain', summary_png)

    # Sweep-effect table image (topPredicts analysis)
    sweep_df = build_sweep_table(eval_df, args.sweep)
    sweep_png = os.path.join(args.output_dir, 'table_toppredicts_sweep.png')
    _save_table_image(sweep_df, 'topPredicts Sweep (Mean Across Runs)', sweep_png)

    # All-approaches table image (BF/DF/Prob/Best-LM)
    all_df = build_all_approaches_table(eval_df)
    all_png = os.path.join(args.output_dir, 'table_all_approaches_by_domain.png')
    _save_table_image(all_df, 'All Approaches by Domain', all_png)

    # Paper-style 4-approach summary table.
    paper_df = build_paper_four_approaches_table(eval_df)
    paper_png = os.path.join(args.output_dir, 'table_paper_four_approaches.png')
    _save_table_image(paper_df, 'Overall Performance (4 Approaches)', paper_png)

    # Save the rendered dataframes too for auditability
    summary_csv = os.path.join(args.output_dir, 'table_summary_baseline_vs_lm.csv')
    sweep_csv = os.path.join(args.output_dir, 'table_toppredicts_sweep.csv')
    all_csv = os.path.join(args.output_dir, 'table_all_approaches_by_domain.csv')
    paper_csv = os.path.join(args.output_dir, 'table_paper_four_approaches.csv')
    summary_df.to_csv(summary_csv, index=False)
    sweep_df.to_csv(sweep_csv, index=False)
    all_df.to_csv(all_csv, index=False)
    paper_df.to_csv(paper_csv, index=False)

    print('Saved table images and CSVs:')
    print(f'  - {summary_png}')
    print(f'  - {sweep_png}')
    print(f'  - {all_png}')
    print(f'  - {paper_png}')
    print(f'  - {summary_csv}')
    print(f'  - {sweep_csv}')
    print(f'  - {all_csv}')
    print(f'  - {paper_csv}')


if __name__ == '__main__':
    main()

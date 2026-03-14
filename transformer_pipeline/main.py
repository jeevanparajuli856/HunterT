#!/usr/bin/env python3
"""
DirHunterT Transformer Pipeline — entry point.

Commands:
    python main.py train       # Grid search: 64 transformer model combos
    python main.py evaluate    # Evaluate best models vs LSTM on test domains
    python main.py smoke-test  # 1 model, 1 epoch shape/interface check (~2 min)

Usage mirrors ltsm_pipeline/main.py so the two pipelines are directly comparable.
"""

import sys
import os
import argparse
import torch
import pandas as pd

# Allow imports from this package and from ltsm_pipeline
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, '..', 'ltsm_pipeline'))

from src.grid_search import TransformerGridSearch
from src.model import DirHunterT
from src.inference import generate
from src.utils import get_device, get_transformer_hyperparams_from_filename

# Reuse data + attack utilities from ltsm_pipeline without modification
from src.data import load_datasets, get_test_by_domain, create_vocabulary
from src.tree_builder import create_tree, create_tree_with_occurrences
from src.attacks import (
    breadth_first_attack, depth_first_attack,
    probabilistic_attack, lm_attack,
)


# ---------------------------------------------------------------------------
# train command
# ---------------------------------------------------------------------------

def train_command(args):
    print("\n" + "=" * 60)
    print("DirHunterT TRANSFORMER — TRAINING PHASE")
    print("=" * 60 + "\n")

    if not os.path.exists(args.data_folder):
        print(f"Error: Data folder not found: {args.data_folder}")
        sys.exit(1)

    trainer = TransformerGridSearch(
        data_folder=args.data_folder,
        saved_models_folder=args.saved_models_folder,
        device=get_device(),
        n_epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        clip=args.clip,
        early_stopping_patience=args.early_stopping_patience,
        weight_decay=args.weight_decay,
        warmup_epochs=args.warmup_epochs,
        resume=args.resume,
        progress_file=args.progress_file,
        checkpoint_dir=args.checkpoint_dir,
        sync_cmd=args.sync_cmd,
        sync_every_n=args.sync_every_n,
        smoke_test=args.smoke_test,
    )
    trainer.train_all()

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)


# ---------------------------------------------------------------------------
# evaluate command
# ---------------------------------------------------------------------------

def evaluate_command(args):
    print("\n" + "=" * 60)
    print("DirHunterT TRANSFORMER — EVALUATION PHASE")
    print("=" * 60 + "\n")

    device = get_device()

    _, _, test_df = load_datasets(args.data_folder)
    test_df_list = get_test_by_domain(test_df)
    print(f"Loaded {len(test_df_list)} test domains")

    if not os.path.exists(args.saved_models_folder):
        print(f"Error: Saved models folder not found: {args.saved_models_folder}")
        sys.exit(1)

    model_files = [f for f in os.listdir(args.saved_models_folder) if f.endswith('.pt')]
    if not model_files:
        print("Error: No trained models found. Run 'python main.py train' first.")
        sys.exit(1)
    print(f"Found {len(model_files)} transformer models")

    prediction_limits = args.prediction_sweep
    print(f"Prediction sweep: {prediction_limits}")

    results = []

    train_df, _, _ = load_datasets(args.data_folder)
    train_root = create_tree_with_occurrences(train_df)

    for test_domain_df in test_df_list:
        if len(test_domain_df) == 0:
            continue

        domain_name = test_domain_df['Filename'].iloc[0]
        domain_type = str(test_domain_df['Type'].iloc[0]).strip().lower()
        print(f"\n{'='*60}")
        print(f"Domain: {domain_name}  (type={domain_type}, n={len(test_domain_df)})")
        print(f"{'='*60}")

        test_root = create_tree(test_domain_df)

        # Baselines — identical to LSTM pipeline
        print("  BFS baseline...")
        bf_reqs, bf_success, _, _ = breadth_first_attack(
            args.wordlist_file, test_root, request_limit=args.request_limit
        )
        baseline_success = bf_success[-1] if bf_success else 0
        print(f"    BFS: {baseline_success} hits")
        results.append(_make_row(domain_name, domain_type, 'breadth_first', 'baseline', 0,
                                  baseline_success, bf_reqs[-1] if bf_reqs else 0, 0.0))

        print("  DFS baseline...")
        df_reqs, df_success, _, _ = depth_first_attack(
            args.wordlist_file, test_root, request_limit=args.request_limit
        )
        dfs_hits = df_success[-1] if df_success else 0
        results.append(_make_row(domain_name, domain_type, 'depth_first', 'baseline', 0,
                                  dfs_hits, df_reqs[-1] if df_reqs else 0,
                                  _pct(dfs_hits, baseline_success)))

        print("  Probabilistic baseline...")
        prob_reqs, prob_success, _, _ = probabilistic_attack(
            train_root, test_root, args.wordlist_file, request_limit=args.request_limit
        )
        prob_hits = prob_success[-1] if prob_success else 0
        results.append(_make_row(domain_name, domain_type, 'probabilistic', 'baseline', 0,
                                  prob_hits, prob_reqs[-1] if prob_reqs else 0,
                                  _pct(prob_hits, baseline_success)))

        # DirHunterT LM attack for each saved model × prediction_limit
        for model_file in sorted(model_files):
            params = get_transformer_hyperparams_from_filename(model_file)
            max_depth   = params['max_depth']
            min_freq    = params['min_freq']
            d_model     = params['d_model']
            n_heads     = params['n_heads']
            n_layers    = params['n_layers']
            dropout     = params['dropout_rate']

            vocab = create_vocabulary(train_df, min_freq, max_depth)
            vocab_size = len(vocab)

            model = DirHunterT(
                vocab_size=vocab_size,
                d_model=d_model,
                n_heads=n_heads,
                n_layers=n_layers,
                dropout=dropout,
                max_depth=max_depth,
                vocab=vocab,
            ).to(device)

            model_path = os.path.join(args.saved_models_folder, model_file)
            model.load_state_dict(torch.load(model_path, map_location=device))
            model.eval()
            print(f"  Model: {model_file}")

            for pred_limit in prediction_limits:
                lm_reqs, lm_success, _, _ = lm_attack(
                    model, vocab, max_depth, test_root, device,
                    request_limit=args.request_limit,
                    prediction_limit=pred_limit,
                    custom_tokenizer=None,
                )
                lm_hits = lm_success[-1] if lm_success else 0
                improvement = _pct(lm_hits, baseline_success)
                print(f"    topK={pred_limit:5d}: {lm_hits} hits  ({improvement:+.1f}%)")

                results.append(_make_row(
                    domain_name, domain_type,
                    f"transformer_{model_file}", model_file,
                    pred_limit, lm_hits,
                    lm_reqs[-1] if lm_reqs else 0,
                    improvement,
                ))

    # Save results
    os.makedirs(args.results_folder, exist_ok=True)
    results_df = pd.DataFrame(results)
    results_csv = os.path.join(args.results_folder, 'eval_results_transformer.csv')
    results_df.to_csv(results_csv, index=False)

    # Best LM result per domain/model across prediction limits
    lm_only = results_df[results_df['model_file'] != 'baseline'].copy()
    if not lm_only.empty:
        best_idx = lm_only.groupby(['domain', 'model_file'])['successful_responses'].idxmax()
        best_df  = lm_only.loc[best_idx].sort_values(
            ['domain', 'successful_responses'], ascending=[True, False]
        )
        best_csv = os.path.join(args.results_folder, 'eval_results_transformer_best.csv')
        best_df.to_csv(best_csv, index=False)
        print(f"\nBest-by-model summary -> {best_csv}")

    print(f"\n{'='*60}")
    print(f"Evaluation complete. Results -> {results_csv}")
    print(f"{'='*60}")
    print(results_df.groupby('domain_type')['successful_responses'].mean().round(1))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pct(hits, baseline):
    return ((hits - baseline) / max(baseline, 1)) * 100.0


def _make_row(domain, dtype, approach, model_file, pred_limit, hits, reqs, improvement):
    return {
        'domain': domain,
        'domain_type': dtype,
        'approach': approach,
        'model_file': model_file,
        'prediction_limit': pred_limit,
        'successful_responses': hits,
        'total_requests': reqs,
        'improvement_percent': improvement,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="DirHunterT Transformer Pipeline")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # ---- train ----
    train_p = subparsers.add_parser('train', help='Train transformer models with grid search')
    train_p.add_argument('--data-folder', default='../LTSM_Research/datasets/LM-training-datasets')
    train_p.add_argument('--saved-models-folder', default='./saved_models')
    train_p.add_argument('--epochs', type=int, default=200)
    train_p.add_argument('--batch-size', type=int, default=128)
    train_p.add_argument('--lr', type=float, default=1e-3)
    train_p.add_argument('--clip', type=float, default=0.25)
    train_p.add_argument('--early-stopping-patience', type=int, default=10)
    train_p.add_argument('--weight-decay', type=float, default=1e-4,
                         help='Adam L2 regularisation (default 1e-4)')
    train_p.add_argument('--warmup-epochs', type=int, default=5,
                         help='Linear LR warmup epochs (default 5)')
    train_p.add_argument('--resume', action='store_true', default=True)
    train_p.add_argument('--progress-file', default='./saved_models/train_progress.json')
    train_p.add_argument('--checkpoint-dir', default='./saved_models/checkpoints')
    train_p.add_argument('--sync-cmd', default=os.environ.get('TRANSFORMER_SYNC_CMD', ''))
    train_p.add_argument('--sync-every-n', type=int, default=1)
    train_p.add_argument('--smoke-test', action='store_true',
                         help='1 model, 1 epoch — quick shape/interface check')
    train_p.set_defaults(func=train_command)

    # ---- evaluate ----
    eval_p = subparsers.add_parser('evaluate', help='Evaluate trained transformer models')
    eval_p.add_argument('--data-folder', default='../LTSM_Research/datasets/LM-training-datasets')
    eval_p.add_argument('--saved-models-folder', default='./saved_models')
    eval_p.add_argument('--wordlist-file', default='../LTSM_Research/chosen_wordlists/big_wfuzz.txt')
    eval_p.add_argument('--request-limit', type=int, default=100_000)
    eval_p.add_argument('--prediction-sweep', nargs='+', type=int,
                        default=[100, 250, 500, 750, 1000, 2000, 5000, 10000])
    eval_p.add_argument('--results-folder', default='./results')
    eval_p.set_defaults(func=evaluate_command)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == '__main__':
    main()

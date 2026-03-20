#!/usr/bin/env python3
"""
Main entry point for LSTM directory enumeration pipeline.

Usage:
    python main.py train           # Train all models with grid search
    python main.py evaluate        # Evaluate trained models on test sets
"""

import sys
import os
import argparse
import torch
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.grid_search import GridSearchTrainer
from src.data import load_datasets, get_test_by_domain, create_vocabulary, custom_tokenizer
from src.model import LSTM
from src.tree_builder import create_tree, create_tree_with_occurrences
from src.attacks import breadth_first_attack, depth_first_attack, probabilistic_attack, lm_attack
from src.utils import get_device, get_model_hyperparams_from_filename


def train_command(args):
    """Execute training phase."""
    print("\n" + "="*60)
    print("LSTM DIRECTORY ENUMERATION - TRAINING PHASE")
    print("="*60 + "\n")
    
    # Check if datasets exist
    if not os.path.exists(args.data_folder):
        print(f"Error: Data folder not found: {args.data_folder}")
        sys.exit(1)
    
    # Create trainer
    trainer = GridSearchTrainer(
        data_folder=args.data_folder,
        saved_models_folder=args.saved_models_folder,
        device=get_device(),
        n_epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        clip=args.clip,
        early_stopping_patience=args.early_stopping_patience,
        resume=args.resume,
        progress_file=args.progress_file,
        checkpoint_dir=args.checkpoint_dir,
        sync_cmd=args.sync_cmd,
        sync_every_n=args.sync_every_n,
        smoke_test=args.smoke_test
    )
    
    # Train all models
    trainer.train_all()
    
    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)


def evaluate_command(args):
    """Execute evaluation phase."""
    print("\n" + "="*60)
    print("LSTM DIRECTORY ENUMERATION - EVALUATION PHASE")
    print("="*60 + "\n")
    
    device = get_device()
    
    # Load test data
    _, _, test_df = load_datasets(args.data_folder)
    test_df_list = get_test_by_domain(test_df)
    
    print(f"Loaded {len(test_df_list)} test domains")
    
    # Load trained models
    if not os.path.exists(args.saved_models_folder):
        print(f"Error: Saved models folder not found: {args.saved_models_folder}")
        sys.exit(1)
    
    model_files = [f for f in os.listdir(args.saved_models_folder) if f.endswith('.pt')]
    print(f"Found {len(model_files)} trained models")
    
    if not model_files:
        print("Error: No trained models found. Run 'python main.py train' first.")
        sys.exit(1)
    
    prediction_limits = args.prediction_sweep
    print(f"Using prediction limits: {prediction_limits}")

    # Results dataframe
    results = []

    # Build global training tree once for probabilistic baseline.
    train_df, _, _ = load_datasets(args.data_folder)
    train_root = create_tree_with_occurrences(train_df)
    
    # For each test domain
    for domain_idx, test_domain_df in enumerate(test_df_list):
        if len(test_domain_df) == 0:
            continue
        
        domain_name = test_domain_df['Filename'].iloc[0]
        domain_type = str(test_domain_df['Type'].iloc[0]).strip().lower()
        print(f"\n{'='*60}")
        print(f"Evaluating domain: {domain_name} (n={len(test_domain_df)})")
        print(f"{'='*60}")
        
        # Build test tree
        test_root = create_tree(test_domain_df)
        
        # Evaluate with breadth-first baseline
        print("  Running breadth-first baseline...")
        bf_reqs, bf_success, bf_failed, _ = breadth_first_attack(
            args.wordlist_file, test_root, request_limit=args.request_limit
        )
        
        baseline_success = bf_success[-1] if bf_success else 0
        print(f"    Breadth-first: {baseline_success} discoveries in {bf_reqs[-1] if bf_reqs else 0} requests")
        
        results.append({
            'domain': domain_name,
            'domain_type': domain_type,
            'approach': 'breadth_first',
            'model_file': 'baseline',
            'prediction_limit': 0,
            'successful_responses': baseline_success,
            'total_requests': bf_reqs[-1] if bf_reqs else 0,
            'improvement_percent': 0.0
        })

        # Evaluate with depth-first baseline
        print("  Running depth-first baseline...")
        df_reqs, df_success, df_failed, _ = depth_first_attack(
            args.wordlist_file, test_root, request_limit=args.request_limit
        )

        depth_success = df_success[-1] if df_success else 0
        depth_improvement = ((depth_success - baseline_success) / max(baseline_success, 1)) * 100
        print(f"    Depth-first: {depth_success} discoveries in {df_reqs[-1] if df_reqs else 0} requests "
              f"({depth_improvement:+.1f}% vs breadth-first)")

        results.append({
            'domain': domain_name,
            'domain_type': domain_type,
            'approach': 'depth_first',
            'model_file': 'baseline',
            'prediction_limit': 0,
            'successful_responses': depth_success,
            'total_requests': df_reqs[-1] if df_reqs else 0,
            'improvement_percent': depth_improvement
        })

        # Evaluate with probabilistic baseline
        print("  Running probabilistic baseline...")
        prob_reqs, prob_success, prob_failed, _ = probabilistic_attack(
            train_root, test_root, args.wordlist_file, request_limit=args.request_limit
        )

        prob_success_count = prob_success[-1] if prob_success else 0
        prob_improvement = ((prob_success_count - baseline_success) / max(baseline_success, 1)) * 100
        print(f"    Probabilistic: {prob_success_count} discoveries in {prob_reqs[-1] if prob_reqs else 0} requests "
              f"({prob_improvement:+.1f}% vs breadth-first)")

        results.append({
            'domain': domain_name,
            'domain_type': domain_type,
            'approach': 'probabilistic',
            'model_file': 'baseline',
            'prediction_limit': 0,
            'successful_responses': prob_success_count,
            'total_requests': prob_reqs[-1] if prob_reqs else 0,
            'improvement_percent': prob_improvement
        })
        
        # Load and evaluate each LSTM model
        for model_file in sorted(model_files):
            print(f"  Loading model: {model_file}")
            
            # Extract hyperparameters
            params = get_model_hyperparams_from_filename(model_file)
            max_depth = params['max_depth']
            min_freq = params['min_freq']
            embedding_size = params['embedding_size']
            num_layers = params['num_layers']
            dropout_rate = params['dropout_rate']
            
            # Build vocabulary for this model's global params
            vocab = create_vocabulary(train_df, min_freq, max_depth)
            vocab_size = len(vocab)
            
            # Create and load model
            model = LSTM(vocab_size, embedding_size, embedding_size, num_layers,
                        dropout_rate, tie_weights=True).to(device)
            
            model_path = os.path.join(args.saved_models_folder, model_file)
            model.load_state_dict(torch.load(model_path, map_location=device))
            model.eval()
            
            # Run LM attack for each prediction limit in sweep
            for prediction_limit in prediction_limits:
                print(f"    Running LM attack with prediction_limit={prediction_limit}...")
                lm_reqs, lm_success, lm_failed, _ = lm_attack(
                    model, vocab, max_depth, test_root, device,
                    request_limit=args.request_limit,
                    prediction_limit=prediction_limit
                )

                lm_success_count = lm_success[-1] if lm_success else 0
                improvement = ((lm_success_count - baseline_success) / max(baseline_success, 1)) * 100

                print(f"      LM: {lm_success_count} discoveries in {lm_reqs[-1] if lm_reqs else 0} requests "
                      f"(+{improvement:.1f}%)")

                results.append({
                    'domain': domain_name,
                    'domain_type': domain_type,
                    'approach': f"lm_{model_file}",
                    'model_file': model_file,
                    'prediction_limit': prediction_limit,
                    'successful_responses': lm_success_count,
                    'total_requests': lm_reqs[-1] if lm_reqs else 0,
                    'improvement_percent': improvement
                })
    
    # Save results
    results_df = pd.DataFrame(results)
    results_csv = os.path.join(args.results_folder, 'eval_results.csv')
    os.makedirs(args.results_folder, exist_ok=True)
    results_df.to_csv(results_csv, index=False)

    # Save best LM result per domain/model across prediction limits
    lm_only = results_df[results_df['model_file'] != 'baseline'].copy()
    if not lm_only.empty:
        best_idx = lm_only.groupby(['domain', 'model_file'])['successful_responses'].idxmax()
        best_df = lm_only.loc[best_idx].sort_values(['domain', 'successful_responses'], ascending=[True, False])
        best_csv = os.path.join(args.results_folder, 'eval_results_best_by_model.csv')
        best_df.to_csv(best_csv, index=False)
        print(f"Best-by-model summary saved to {best_csv}")
    
    print(f"\n{'='*60}")
    print(f"Evaluation complete! Results saved to {results_csv}")
    print(f"{'='*60}")
    print("\nSummary:")
    print(results_df)


def main():
    parser = argparse.ArgumentParser(
        description="LSTM Directory Enumeration Pipeline"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Train LSTM models with grid search')
    train_parser.add_argument('--data-folder', default='../LTSM_Research/datasets/LM-training-datasets',
                             help='Path to training data folder')
    train_parser.add_argument('--saved-models-folder', default='./saved_models',
                             help='Path to save trained models')
    train_parser.add_argument('--epochs', type=int, default=200,
                             help='Max number of epochs per model')
    train_parser.add_argument('--batch-size', type=int, default=128,
                             help='Batch size')
    train_parser.add_argument('--lr', type=float, default=1e-3,
                             help='Learning rate')
    train_parser.add_argument('--clip', type=float, default=0.25,
                             help='Gradient norm clip value')
    train_parser.add_argument('--early-stopping-patience', type=int, default=10,
                             help='Early stopping patience')
    train_parser.add_argument('--resume', action='store_true', default=True,
                             help='Resume from progress file by skipping completed model combos')
    train_parser.add_argument('--progress-file', default='./saved_models/train_progress.json',
                             help='Path to training progress JSON file')
    train_parser.add_argument('--checkpoint-dir', default='./saved_models/checkpoints',
                             help='Path to save per-combo checkpoints')
    train_parser.add_argument('--sync-cmd', default=os.environ.get('LTSM_SYNC_CMD', ''),
                             help='Optional shell command to sync artifacts (e.g., gsutil rsync ...)')
    train_parser.add_argument('--sync-every-n', type=int, default=1,
                             help='Run sync command every N trained model combos')
    train_parser.add_argument('--smoke-test', action='store_true',
                             help='Run a tiny 1-model, 1-epoch training smoke test')
    train_parser.set_defaults(func=train_command)
    
    # Evaluate command
    eval_parser = subparsers.add_parser('evaluate', help='Evaluate trained models')
    eval_parser.add_argument('--data-folder', default='../LTSM_Research/datasets/LM-training-datasets',
                            help='Path to training data folder')
    eval_parser.add_argument('--saved-models-folder', default='./saved_models',
                            help='Path to saved models')
    eval_parser.add_argument('--wordlist-file', default='../LTSM_Research/chosen_wordlists/big_wfuzz.txt',
                            help='Path to wordlist file')
    eval_parser.add_argument('--request-limit', type=int, default=100000,
                            help='Max requests per attack')
    eval_parser.add_argument('--prediction-sweep', nargs='+', type=int,
                            default=[100, 250, 500, 750, 1000, 2000, 5000, 10000],
                            help='Prediction limits to sweep (paper defaults applied automatically)')
    eval_parser.add_argument('--results-folder', default='./results',
                            help='Path to save results')
    eval_parser.set_defaults(func=evaluate_command)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == '__main__':
    main()

"""
Small-model diagnostic grid for the fair V2 transformer pipeline.

This combines:
  - 0C: fair path-wise training regime
  - 0B: smaller transformer capacity search
"""

from .grid_search import TransformerGridSearch


class DiagnosticTransformerGridSearch(TransformerGridSearch):
    """
    Fair V2 grid search restricted to LSTM-scale transformer capacities.
    """

    TRAINING_REGIME = 'pathwise_smallgrid_v2'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.d_models = [64, 128]
        self.n_heads_list = [2, 4]
        self.n_layers_list = [2, 3]
        self.dropout_rates = [0.2, 0.4]

        if self.smoke_test:
            self.d_models = [self.d_models[0]]
            self.n_heads_list = [self.n_heads_list[0]]
            self.n_layers_list = [self.n_layers_list[0]]
            self.dropout_rates = [self.dropout_rates[0]]

import numpy as np
import pandas as pd
from scipy import stats


def binomial_test(model_correct: np.ndarray, baseline_rate: float) -> float:
    """One-sided test: is the model's hit rate greater than a fixed
    baseline rate, treating each prediction as an independent trial?

    This ignores pairing and dependency structure -- it's the simplest,
    least powerful test here, included as a cheap sanity check alongside
    the paired McNemar test and the block bootstrap CI.
    """
    result = stats.binomtest(
        int(model_correct.sum()), len(model_correct), p=baseline_rate, alternative="greater"
    )
    return float(result.pvalue)


def mcnemar_test(model_correct: np.ndarray, baseline_correct: np.ndarray) -> float:
    """Exact McNemar's test: does the model win more of the rows where
    it and the baseline disagree than it loses?

    More appropriate than a plain binomial test here since the model
    and the majority-class baseline both predict on the same rows --
    this is a paired comparison, not two independent samples.
    """
    n10 = int(np.sum(model_correct & ~baseline_correct))
    n01 = int(np.sum(~model_correct & baseline_correct))
    if n10 + n01 == 0:
        return 1.0
    result = stats.binomtest(n10, n10 + n01, p=0.5, alternative="greater")
    return float(result.pvalue)


def block_bootstrap_ci(
    correct: np.ndarray,
    tickers: pd.Series,
    n_bootstrap: int = 1000,
    block_size: int = 20,
    ci: float = 0.95,
    seed: int = 0,
) -> tuple[float, float]:
    """95% CI on accuracy via block bootstrap.

    Resamples contiguous blocks of rows (within each ticker, preserving
    date order) instead of individual rows. Rows aren't independent --
    overlapping-horizon labels create serial correlation within a
    ticker, and pooling tickers adds cross-ticker correlation from
    shared calendar-date market moves -- so a naive per-row bootstrap
    would understate uncertainty.
    """
    rng = np.random.default_rng(seed)
    tickers_arr = tickers.to_numpy()

    blocks: list[np.ndarray] = []
    for ticker in pd.unique(tickers_arr):
        ticker_correct = correct[tickers_arr == ticker]
        for start in range(0, len(ticker_correct), block_size):
            blocks.append(ticker_correct[start : start + block_size])

    n_total = len(correct)
    accuracies = np.empty(n_bootstrap)
    for i in range(n_bootstrap):
        sample_blocks = []
        sample_size = 0
        while sample_size < n_total:
            block = blocks[rng.integers(len(blocks))]
            sample_blocks.append(block)
            sample_size += len(block)
        sample = np.concatenate(sample_blocks)[:n_total]
        accuracies[i] = sample.mean()

    lower = (1 - ci) / 2
    return float(np.quantile(accuracies, lower)), float(np.quantile(accuracies, 1 - lower))


def evaluate_with_significance(
    y_test: pd.Series, y_pred: np.ndarray, tickers: pd.Series
) -> dict:
    """Bundle accuracy with the significance checks that should
    accompany it. An accuracy delta on its own can't tell you whether
    a result is real signal or one noisy train/test split -- see
    docs/JOURNAL.mdx for the case that motivated this."""
    majority_label = 1 if y_test.mean() >= 0.5 else 0
    y_test_arr = y_test.to_numpy()
    baseline_pred = np.full(len(y_test_arr), majority_label)

    model_correct = y_pred == y_test_arr
    baseline_correct = baseline_pred == y_test_arr

    accuracy = float(model_correct.mean())
    majority_baseline = float(baseline_correct.mean())
    ci_low, ci_high = block_bootstrap_ci(model_correct, tickers)

    return {
        "n_test": len(y_test_arr),
        "accuracy": accuracy,
        "majority_baseline": majority_baseline,
        "accuracy_ci_95": (ci_low, ci_high),
        "binomial_p": binomial_test(model_correct, majority_baseline),
        "mcnemar_p": mcnemar_test(model_correct, baseline_correct),
    }


def format_significance(result: dict) -> str:
    ci_low, ci_high = result["accuracy_ci_95"]
    significant = result["mcnemar_p"] < 0.05
    return (
        f"n={result['n_test']}  "
        f"accuracy={result['accuracy']:.3f} (95% CI [{ci_low:.3f}, {ci_high:.3f}])  "
        f"majority_baseline={result['majority_baseline']:.3f}\n"
        f"  binomial p={result['binomial_p']:.3f}  mcnemar p={result['mcnemar_p']:.3f}  "
        f"{'SIGNIFICANT (p<0.05)' if significant else 'not significant'}"
    )

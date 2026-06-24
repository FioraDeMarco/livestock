from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from models.baseline_xgboost import PUBLIC_TICKERS, walk_forward_eval
from models.significance import format_significance


def logistic_model():
    """Standardize features, then a plain logistic regression.

    Sanity-check baseline: if this performs statistically the same as
    XGBoost (see walk_forward_eval results in baseline_xgboost.py),
    that's evidence the data doesn't yet support XGBoost's nonlinear
    capacity -- prefer the simpler, more interpretable model until
    there's evidence the complexity is earning its keep.
    """
    return make_pipeline(StandardScaler(), LogisticRegression())


if __name__ == "__main__":
    horizon = 30
    print(f"Logistic regression, {horizon}-day horizon, 5 expanding folds: {PUBLIC_TICKERS}")
    for fold_result in walk_forward_eval(
        horizon=horizon, n_folds=5, model_factory=logistic_model
    ):
        print(
            f"Fold {fold_result['fold']}: train from {fold_result['train_start']}, "
            f"test {fold_result['test_start']} to {fold_result['test_end']}"
        )
        print(f"  {format_significance(fold_result)}")

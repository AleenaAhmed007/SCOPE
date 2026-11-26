"""Small one-step LSTM forecaster for weekly SCOPE series.

Uses PyTorch. Kept intentionally small so it can be compared fairly against
naive / mean / ARIMA on the same chronological holdout without claiming a
large-data neural advantage.
"""

from __future__ import annotations

from typing import Any

import numpy as np

try:
    import torch
    from torch import nn
except ImportError as exc:  # pragma: no cover - optional dependency
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


def torch_available() -> bool:
    return torch is not None


if torch is not None:

    class _LSTMNet(nn.Module):
        def __init__(self, hidden: int = 32, num_layers: int = 1, dropout: float = 0.0) -> None:
            super().__init__()
            self.lstm = nn.LSTM(
                input_size=1,
                hidden_size=hidden,
                num_layers=num_layers,
                batch_first=True,
                dropout=dropout if num_layers > 1 else 0.0,
            )
            self.head = nn.Linear(hidden, 1)

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":
            out, _ = self.lstm(x)
            return self.head(out[:, -1, :]).squeeze(-1)


class LSTMForecaster:
    """Sklearn-ish one-step forecaster over a univariate series.

    ``fit`` trains on an array of targets. ``predict_from_history`` rolls
    one-step forecasts over a holdout segment, appending realised values after
    each step (same protocol as the classical candidates).
    """

    def __init__(
        self,
        lookback: int = 12,
        hidden: int = 32,
        num_layers: int = 1,
        epochs: int = 80,
        batch_size: int = 32,
        lr: float = 1e-3,
        patience: int = 12,
        seed: int = 42,
        device: str | None = None,
    ) -> None:
        if not torch_available():
            raise ImportError(
                "PyTorch is required for LSTMForecaster. Install torch (CPU wheel is fine)."
            ) from _IMPORT_ERROR
        self.lookback = lookback
        self.hidden = hidden
        self.num_layers = num_layers
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self.patience = patience
        self.seed = seed
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_: Any = None
        self.y_mean_: float = 0.0
        self.y_std_: float = 1.0
        self.history_: np.ndarray | None = None
        self.train_loss_: list[float] = []
        self.val_loss_: list[float] = []

    def _scale(self, y: np.ndarray) -> np.ndarray:
        return (y - self.y_mean_) / self.y_std_

    def _unscale(self, y: np.ndarray) -> np.ndarray:
        return y * self.y_std_ + self.y_mean_

    @staticmethod
    def _sequences(y: np.ndarray, lookback: int) -> tuple[np.ndarray, np.ndarray]:
        xs, ys = [], []
        for i in range(lookback, len(y)):
            xs.append(y[i - lookback : i])
            ys.append(y[i])
        return np.asarray(xs, dtype=np.float32), np.asarray(ys, dtype=np.float32)

    def fit(
        self,
        y_train: np.ndarray,
        y_val: np.ndarray | None = None,
    ) -> "LSTMForecaster":
        torch.manual_seed(self.seed)
        np.random.seed(self.seed)

        y_train = np.asarray(y_train, dtype=float)
        if len(y_train) <= self.lookback + 2:
            raise ValueError("Training series too short for the configured LSTM lookback.")

        self.y_mean_ = float(np.mean(y_train))
        self.y_std_ = float(np.std(y_train) or 1.0)
        train_s = self._scale(y_train)
        x_tr, y_tr = self._sequences(train_s, self.lookback)

        val_loader = None
        if y_val is not None and len(y_val):
            # Continuity: validation sequences may start from the end of train.
            joined = np.concatenate([train_s[-(self.lookback) :], self._scale(np.asarray(y_val, dtype=float))])
            x_va, y_va = self._sequences(joined, self.lookback)
            # Keep only sequences whose target falls in the val segment.
            if len(x_va):
                val_loader = (x_va, y_va)

        model = _LSTMNet(hidden=self.hidden, num_layers=self.num_layers).to(self.device)
        opt = torch.optim.Adam(model.parameters(), lr=self.lr)
        loss_fn = nn.L1Loss()

        best_state = None
        best_val = float("inf")
        stale = 0
        self.train_loss_ = []
        self.val_loss_ = []

        n = len(x_tr)
        for epoch in range(self.epochs):
            model.train()
            perm = np.random.permutation(n)
            epoch_losses = []
            for start in range(0, n, self.batch_size):
                idx = perm[start : start + self.batch_size]
                xb = torch.tensor(x_tr[idx][:, :, None], device=self.device)
                yb = torch.tensor(y_tr[idx], device=self.device)
                opt.zero_grad()
                pred = model(xb)
                loss = loss_fn(pred, yb)
                loss.backward()
                opt.step()
                epoch_losses.append(float(loss.item()))
            tr_loss = float(np.mean(epoch_losses)) if epoch_losses else float("nan")
            self.train_loss_.append(tr_loss)

            va_loss = tr_loss
            if val_loader is not None:
                model.eval()
                with torch.no_grad():
                    xv = torch.tensor(val_loader[0][:, :, None], device=self.device)
                    yv = torch.tensor(val_loader[1], device=self.device)
                    va_loss = float(loss_fn(model(xv), yv).item())
            self.val_loss_.append(va_loss)

            monitor = va_loss if val_loader is not None else tr_loss
            if monitor + 1e-8 < best_val:
                best_val = monitor
                best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
                stale = 0
            else:
                stale += 1
                if stale >= self.patience:
                    break

        if best_state is not None:
            model.load_state_dict(best_state)
        model.eval()
        self.model_ = model
        self.history_ = y_train.copy()
        self.epochs_ran_ = epoch + 1
        self.best_val_loss_ = best_val
        return self

    def _predict_one_scaled(self, window: np.ndarray) -> float:
        assert self.model_ is not None
        x = torch.tensor(window.astype(np.float32)[None, :, None], device=self.device)
        with torch.no_grad():
            return float(self.model_(x).cpu().numpy()[0])

    def predict_from_history(self, history: np.ndarray, n_ahead: int, realised: np.ndarray) -> np.ndarray:
        """Roll ``n_ahead`` one-step forecasts; after each step append ``realised[i]``."""
        if self.model_ is None:
            raise RuntimeError("LSTMForecaster must be fit before predict.")
        if len(realised) != n_ahead:
            raise ValueError("realised length must equal n_ahead")
        hist = list(np.asarray(history, dtype=float))
        preds = np.empty(n_ahead, dtype=float)
        for i in range(n_ahead):
            window = self._scale(np.asarray(hist[-self.lookback :], dtype=float))
            preds[i] = float(self._unscale(np.asarray([self._predict_one_scaled(window)]))[0])
            hist.append(float(realised[i]))
        return preds


def evaluate_lstm_weekly(
    series: np.ndarray,
    weights: np.ndarray | None = None,
    lookback: int = 12,
    n_test: int | None = None,
    n_val: int | None = None,
    seed: int = 42,
) -> dict[str, Any]:
    """Chronological train/val/test evaluation for a weekly univariate series."""
    y = np.asarray(series, dtype=float)
    n = len(y)
    if n_test is None:
        n_test = max(26, int(n * 0.2))  # ~half year weekly holdout minimum
    if n_val is None:
        n_val = max(26, int((n - n_test) * 0.2))
    if n - n_test - n_val <= lookback + 5:
        return {"trained": False, "reason": "insufficient_weekly_history_for_lstm_splits"}

    train = y[: n - n_test - n_val]
    val = y[n - n_test - n_val : n - n_test]
    test = y[n - n_test :]
    w_test = None if weights is None else np.asarray(weights[n - n_test :], dtype=float)

    model = LSTMForecaster(lookback=lookback, seed=seed)
    model.fit(train, val)

    # Validation rolling MAE (for selection vs classical)
    val_pred = model.predict_from_history(train, len(val), val)
    val_mae = float(np.mean(np.abs(val - val_pred)))

    # Refit on train+val, score test
    model.fit(np.concatenate([train, val]), None)
    test_pred = model.predict_from_history(np.concatenate([train, val]), len(test), test)
    abs_err = np.abs(test - test_pred)
    test_mae = float(np.average(abs_err, weights=w_test) if w_test is not None else abs_err.mean())
    test_rmse = float(
        np.sqrt(np.average(abs_err**2, weights=w_test) if w_test is not None else np.mean(abs_err**2))
    )

    naive_pred = y[n - n_test - 1 : n - 1]
    naive_mae = float(
        np.average(np.abs(test - naive_pred), weights=w_test)
        if w_test is not None
        else np.mean(np.abs(test - naive_pred))
    )
    mean_pred = np.full(len(test), float(np.mean(np.concatenate([train, val]))))
    mean_mae = float(
        np.average(np.abs(test - mean_pred), weights=w_test)
        if w_test is not None
        else np.mean(np.abs(test - mean_pred))
    )

    return {
        "trained": True,
        "model": "lstm",
        "lookback": lookback,
        "hidden": model.hidden,
        "epochs_ran": model.epochs_ran_,
        "best_val_loss_scaled": model.best_val_loss_,
        "n_train": len(train),
        "n_validation": len(val),
        "n_test": len(test),
        "validation_mae": val_mae,
        "test_mae": test_mae,
        "test_rmse": test_rmse,
        "naive_lag1_test_mae": naive_mae,
        "mean_baseline_test_mae": mean_mae,
        "beats_naive_on_test": test_mae < naive_mae,
        "beats_mean_on_test": test_mae < mean_mae,
        "last_actual": test.tolist(),
        "last_pred": test_pred.tolist(),
        "metric_weighting": "shipment_count_weighted" if w_test is not None else "unweighted",
    }

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import correlate
from pathlib import Path

# Output directory
OUT = Path(r"C:\Trading\Ehlers\TradingSystems\backtests")
OUT.mkdir(parents=True, exist_ok=True)

def laguerre_series(price, gamma=0.85):
    """
    Minimal Laguerre smoother (L0 only) for synthetic demo.
    We'll extend to the full L0-L3 composite later.
    """
    L0 = np.zeros_like(price, dtype=float)
    L0[0] = price[0]
    for t in range(1, len(price)):
        L0[t] = (1 - gamma) * price[t] + gamma * L0[t - 1]
    return L0

def estimate_lag(clean, out):
    """
    Cross-correlation argmax lag in bars between clean signal and indicator output.
    Positive means indicator lags the clean reference.
    """
    # out vs clean so positive means out is delayed (lags) w.r.t. clean
    c = correlate((out - out.mean()), (clean - clean.mean()), mode='full')
    return c.argmax() - (len(out) - 1)


# --- synthetic signal: smooth trend + cycle + noise ---
np.random.seed(7)
N = 4000
t = np.arange(N)
clean = 0.002 * t + 2.0 * np.sin(2 * np.pi * t / 128.0)  # slow trend + cycle
noise = 0.8 * np.random.randn(N)
price = clean + noise

# Compare two gammas
g1, g2 = 0.65, 0.85
L1 = laguerre_series(price, gamma=g1)
L2 = laguerre_series(price, gamma=g2)
WARMUP = 25  # ~5x half-life for gamma around 0.85
lag1 = estimate_lag(clean, L1)
lag2 = estimate_lag(clean, L2)

# Save a tiny CSV with results
csv_path = OUT / "laguerre_lag_report.csv"
with open(csv_path, "w", encoding="utf-8") as f:
    f.write("gamma,lag_bars\n")
    f.write(f"{g1},{lag1}\n")
    f.write(f"{g2},{lag2}\n")

# Plot for visual sanity
def save_plot(series, title, filename):
    plt.figure(figsize=(10, 3))
    plt.plot(price, linewidth=0.6, label="price (noisy)")
    plt.plot(series, linewidth=1.0, label=title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT / filename, dpi=140)
    plt.close()

save_plot(L1, f"Laguerre gamma={g1}", "laguerre_gamma_65.png")
save_plot(L2, f"Laguerre gamma={g2}", "laguerre_gamma_85.png")

print("Wrote:", csv_path)
print("PNG:", OUT / "laguerre_gamma_65.png")
print("PNG:", OUT / "laguerre_gamma_85.png")
print("Lag results -> gamma", g1, ":", lag1, ";  gamma", g2, ":", lag2)

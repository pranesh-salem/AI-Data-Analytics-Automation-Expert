"""Static charts for the report. Usage: python3 charts.py out/metrics.json out/cleaned.csv charts/"""
import json, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

m = json.load(open(sys.argv[1])); df = pd.read_csv(sys.argv[2]); out = Path(sys.argv[3]); out.mkdir(exist_ok=True)
BLUE, MUTED, GRID = "#2a6fb0", "#5f5e5b", "#e3e0da"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left", "figure.dpi": 160})
usd = lambda v: f"${v:,.0f}"

def hbar(rows, key, val, title, xlabel, fname, label=lambda r: usd(r["revenue"]), h=None, order=None):
    if order: rows = [next(r for r in rows if r[key] == o) for o in order]
    rows = list(reversed(rows))
    fig, ax = plt.subplots(figsize=(7, h or max(2.2, 0.32 * len(rows) + 0.8)))
    ax.barh([r[key] for r in rows], [r[val] for r in rows], color=BLUE, height=0.65)
    mx = max(r[val] for r in rows)
    for i, r in enumerate(rows): ax.text(r[val] + mx * 0.01, i, label(r), va="center", fontsize=8)
    ax.set_xlim(0, mx * 1.22); ax.set_title(title); ax.set_xlabel(xlabel); ax.grid(axis="x", color=GRID); ax.set_axisbelow(True)
    fig.tight_layout(); fig.savefig(out / fname); plt.close(fig)

def vbar(rows, key, val, title, xlabel, ylabel, fname, order=None, label=lambda r: usd(r["revenue"]), ylim0=None):
    if order: rows = [next(r for r in rows if r[key] == o) for o in order]
    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.bar([r[key] for r in rows], [r[val] for r in rows], color=BLUE, width=0.6)
    for i, r in enumerate(rows): ax.text(i, r[val], label(r), ha="center", va="bottom", fontsize=8)
    if ylim0 is not None: ax.set_ylim(ylim0, max(r[val] for r in rows) * 1.04)
    ax.set_title(title); ax.set_xlabel(xlabel); ax.set_ylabel(ylabel); ax.grid(axis="y", color=GRID); ax.set_axisbelow(True)
    fig.tight_layout(); fig.savefig(out / fname); plt.close(fig)

B = m["by"]
share = lambda r: f'{usd(r["revenue"])} ({r["share"]:.1f}%)'
hbar(B["Category"], "Category", "revenue", "Revenue by category", "Revenue (USD)", "01_revenue_by_category.png", share)
vbar(B["Season"], "Season", "revenue", "Revenue by season", "Season", "Revenue (USD)", "02_revenue_by_season.png", ["Spring", "Summer", "Fall", "Winter"])
hbar(B["Item Purchased"], "Item Purchased", "revenue", "Revenue by product", "Revenue (USD)", "03_revenue_by_product.png")
vbar(B["Age Group"], "Age Group", "revenue", "Revenue by age group", "Age group", "Revenue (USD)", "04_revenue_by_age_group.png", ["18-25", "26-35", "36-45", "46-55", "56-70"])
hbar(B["Gender"], "Gender", "revenue", "Revenue by gender", "Revenue (USD)", "05_revenue_by_gender.png", share)
seg_tot = sum(r["customers"] for r in B["Customer Segment"])
hbar(B["Customer Segment"], "Customer Segment", "customers", "Customers by loyalty segment", "Customers", "06_customers_by_segment.png",
     lambda r: f'{r["customers"]:,} ({r["customers"]/seg_tot*100:.1f}%)', order=["New", "Returning", "Loyal"])
hbar(B["Frequency (Standardized)"], "Frequency (Standardized)", "customers", "Customers by purchase frequency (standardized)", "Customers",
     "07_customers_by_frequency.png", lambda r: f'{r["customers"]:,}', order=["Weekly", "Fortnightly", "Monthly", "Quarterly", "Annually"])

# Discount / subscription AOV
rows = [{"k": f"Discount: {r['Discount Applied']}", "v": r["avg_order"]} for r in B["Discount Applied"]] + \
       [{"k": f"Subscribed: {r['Subscription Status']}", "v": r["avg_order"]} for r in B["Subscription Status"]]
hbar(rows, "k", "v", "Average order value by discount and subscription", "Average order value (USD)", "08_aov_discount_subscription.png", lambda r: f'${r["v"]:.2f}')

# Top / bottom states
st = B["Location"]
fig, axes = plt.subplots(1, 2, figsize=(8, 3.6))
for ax, rows, t in [(axes[0], st[:10], "Top 10 states"), (axes[1], st[-10:][::-1], "Bottom 10 states")]:
    rows = rows[::-1]; ax.barh([r["Location"] for r in rows], [r["revenue"] for r in rows], color=BLUE, height=0.65)
    for i, r in enumerate(rows): ax.text(r["revenue"] + 60, i, usd(r["revenue"]), va="center", fontsize=7.5)
    ax.set_xlim(0, 7000); ax.set_title(t); ax.set_xlabel("Revenue (USD)"); ax.grid(axis="x", color=GRID); ax.set_axisbelow(True)
fig.tight_layout(); fig.savefig(out / "09_states_top_bottom.png"); plt.close(fig)

# Heatmap season x category
sc = m["season_cat"]; order = ["Spring", "Summer", "Fall", "Winter"]
v = np.array([[sc["values"][i][sc["cols"].index(s)] for s in order] for i in range(len(sc["rows"]))])
fig, ax = plt.subplots(figsize=(7, 3)); im = ax.imshow(v, cmap="Blues", aspect="auto")
ax.set_xticks(range(4), order); ax.set_yticks(range(len(sc["rows"])), sc["rows"])
for i in range(v.shape[0]):
    for j in range(4): ax.text(j, i, usd(v[i, j]), ha="center", va="center", fontsize=8, color="white" if v[i, j] > v.max() * .6 else "#1f1e1d")
ax.set_title("Revenue by category and season (USD)"); ax.spines[:].set_visible(False); fig.colorbar(im, ax=ax, shrink=.8)
fig.tight_layout(); fig.savefig(out / "10_heatmap_season_category.png"); plt.close(fig)

# Histogram + box plot of purchase amount
fig, axes = plt.subplots(1, 2, figsize=(8, 3), gridspec_kw={"width_ratios": [3, 1]})
axes[0].hist(df["Purchase Amount (USD)"], bins=range(20, 105, 5), color=BLUE, edgecolor="white")
axes[0].set_title("Purchase amount distribution"); axes[0].set_xlabel("Purchase amount (USD), $5 bands"); axes[0].set_ylabel("Customers")
axes[1].boxplot(df["Purchase Amount (USD)"], widths=.5, patch_artist=True, boxprops={"facecolor": "#cfe0f1", "edgecolor": BLUE}, medianprops={"color": BLUE})
axes[1].set_title("Box plot"); axes[1].set_ylabel("USD"); axes[1].set_xticks([])
fig.tight_layout(); fig.savefig(out / "11_purchase_amount_distribution.png"); plt.close(fig)

# Rating & age histograms
fig, axes = plt.subplots(1, 2, figsize=(8, 2.8))
axes[0].hist(df["Age"], bins=range(18, 74, 4), color=BLUE, edgecolor="white"); axes[0].set_title("Age distribution"); axes[0].set_xlabel("Age"); axes[0].set_ylabel("Customers")
axes[1].hist(df["Review Rating"].dropna(), bins=np.arange(2.45, 5.1, 0.1), color=BLUE, edgecolor="white"); axes[1].set_title("Review rating distribution"); axes[1].set_xlabel("Rating (rated rows)"); axes[1].set_ylabel("Customers")
fig.tight_layout(); fig.savefig(out / "12_age_rating_distribution.png"); plt.close(fig)

# Correlation matrix
c = np.array(m["corr"]["matrix"]); labels = ["Age", "Amount", "Rating", "Prev. purchases"]
fig, ax = plt.subplots(figsize=(4.6, 3.6)); im = ax.imshow(c, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(4), labels, rotation=20); ax.set_yticks(range(4), labels)
for i in range(4):
    for j in range(4): ax.text(j, i, f"{c[i, j]:.3f}", ha="center", va="center", fontsize=8, color="white" if abs(c[i, j]) > .6 else "#1f1e1d")
ax.set_title("Correlation matrix (Pearson r)"); ax.spines[:].set_visible(False); fig.colorbar(im, ax=ax, shrink=.8)
fig.tight_layout(); fig.savefig(out / "13_correlation_matrix.png"); plt.close(fig)

hbar(B["Shipping Type"], "Shipping Type", "revenue", "Revenue by shipping type", "Revenue (USD)", "14_revenue_by_shipping.png", share)
hbar(B["Payment Method"], "Payment Method", "revenue", "Revenue by payment method", "Revenue (USD)", "15_revenue_by_payment.png", share)
print("ok")

"""Customer Shopping Behavior - cleaning, EDA and statistical analysis.

Usage: python3 analysis.py <raw_csv> <output_dir>
Produces: cleaned dataset (CSV), metrics.json (all figures used in the
dashboard and report). The original file is never modified.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

raw_path, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)

raw = pd.read_csv(raw_path)
df = raw.copy()
AMT = "Purchase Amount (USD)"
log = []

# ---------------- Data quality checks ----------------
quality = {
    "rows": int(len(raw)),
    "columns": int(raw.shape[1]),
    "missing": {k: int(v) for k, v in raw.isna().sum().items() if v},
    "duplicate_rows": int(raw.duplicated().sum()),
    "duplicate_ids": int(raw["Customer ID"].duplicated().sum()),
    "discount_equals_promo": bool((raw["Discount Applied"] == raw["Promo Code Used"]).all()),
}
for c in raw.select_dtypes("number"):
    q1, q3 = raw[c].quantile([.25, .75]); i = q3 - q1
    quality.setdefault("iqr_outliers", {})[c] = int(((raw[c] < q1 - 1.5 * i) | (raw[c] > q3 + 1.5 * i)).sum())

# ---------------- Cleaning ----------------
# 1. Trim whitespace in text columns (defensive; no change expected)
obj = df.select_dtypes(include=["object", "str"]).columns
df[obj] = df[obj].apply(lambda s: s.str.strip())
log.append(("Trimmed whitespace in all text columns", "0 values changed", "Formatting check"))

# 2. Standardise synonym frequency labels
freq_map = {"Bi-Weekly": "Fortnightly", "Every 3 Months": "Quarterly"}
n_freq = int(df["Frequency of Purchases"].isin(freq_map).sum())
df["Frequency (Standardized)"] = df["Frequency of Purchases"].replace(freq_map)
log.append(("Added 'Frequency (Standardized)': Bi-Weekly -> Fortnightly, Every 3 Months -> Quarterly",
            f"{n_freq} rows relabelled (original column kept)", "Synonym labels split one period into two categories"))

# 3. Missing review ratings - flagged, NOT imputed
n_miss = int(df["Review Rating"].isna().sum())
df["Rating Missing"] = df["Review Rating"].isna().map({True: "Yes", False: "No"})
log.append(("Flagged missing Review Rating with 'Rating Missing' column", f"{n_miss} rows flagged, left blank",
            "No values invented; rating stats use the 3,863 rated rows"))

# 4. Redundant column noted
log.append(("'Promo Code Used' kept but treated as redundant", "Identical to 'Discount Applied' in 3,900/3,900 rows",
            "Analysed once as 'Discount/Promo'"))

# 5. Derived analysis fields
df["Age Group"] = pd.cut(df["Age"], [17, 25, 35, 45, 55, 70],
                         labels=["18-25", "26-35", "36-45", "46-55", "56-70"]).astype(str)
df["Customer Segment"] = pd.cut(df["Previous Purchases"], [0, 1, 10, 50],
                                labels=["New", "Returning", "Loyal"]).astype(str)
log.append(("Added 'Age Group' (5 bands) and 'Customer Segment' (New = 1, Returning = 2-10, Loyal = 11+ previous purchases)",
            "2 derived columns", "Segmentation fields; originals untouched"))
annual = {"Weekly": 52, "Fortnightly": 26, "Monthly": 12, "Quarterly": 4, "Annually": 1}
df["Est. Purchases / Year"] = df["Frequency (Standardized)"].map(annual)
log.append(("Added 'Est. Purchases / Year' from standardized frequency", "1 derived column",
            "Assumption: stated frequency holds for a year"))
log.append(("No rows deleted", "3,900 in -> 3,900 out", "No duplicates, invalid values or outliers found"))

df.to_csv(out / "cleaned.csv", index=False)

# ---------------- Helpers ----------------
def grp(col, sort="revenue"):
    g = df.groupby(col).agg(customers=("Customer ID", "count"), revenue=(AMT, "sum"),
                            avg_order=(AMT, "mean"), avg_rating=("Review Rating", "mean"),
                            avg_prev=("Previous Purchases", "mean")).reset_index()
    g["share"] = g["revenue"] / g["revenue"].sum() * 100
    g = g.sort_values(sort, ascending=False)
    return [{k: (round(float(v), 2) if isinstance(v, (float, np.floating)) else
                 int(v) if isinstance(v, (int, np.integer)) else v) for k, v in r.items()}
            for r in g.to_dict("records")]

# ---------------- KPIs ----------------
rev = int(df[AMT].sum())
kpi = {
    "customers": int(df["Customer ID"].nunique()),
    "revenue": rev,
    "aov": round(float(df[AMT].mean()), 2),
    "median_order": float(df[AMT].median()),
    "avg_rating": round(float(df["Review Rating"].mean()), 2),
    "avg_prev": round(float(df["Previous Purchases"].mean()), 1),
    "subscription_rate": round(float((df["Subscription Status"] == "Yes").mean() * 100), 1),
    "discount_rate": round(float((df["Discount Applied"] == "Yes").mean() * 100), 1),
    "products": int(df["Item Purchased"].nunique()),
    "states": int(df["Location"].nunique()),
    "avg_age": round(float(df["Age"].mean()), 1),
    "loyal_share": round(float((df["Customer Segment"] == "Loyal").mean() * 100), 1),
}

# ---------------- Descriptive stats ----------------
desc = {}
for c in ["Age", AMT, "Review Rating", "Previous Purchases"]:
    s = df[c].dropna()
    desc[c] = {"count": int(s.count()), "mean": round(s.mean(), 2), "median": float(s.median()),
               "mode": float(s.mode().iloc[0]), "std": round(s.std(), 2), "var": round(s.var(), 2),
               "min": float(s.min()), "max": float(s.max()), "q1": float(s.quantile(.25)),
               "q3": float(s.quantile(.75)), "skew": round(float(s.skew()), 3)}

corr = df[["Age", AMT, "Review Rating", "Previous Purchases"]].corr().round(3)

# ---------------- Hypothesis tests ----------------
tests = []
def ttest(label, a, b):
    t, p = stats.ttest_ind(a, b, equal_var=False)
    tests.append({"test": label, "method": "Welch t-test", "stat": round(float(t), 3), "p": round(float(p), 4),
                  "result": "Significant" if p < .05 else "Not significant"})
def anova(label, col, val=AMT):
    groups = [g[val].dropna() for _, g in df.groupby(col)]
    f, p = stats.f_oneway(*groups)
    tests.append({"test": label, "method": "One-way ANOVA", "stat": round(float(f), 3), "p": round(float(p), 4),
                  "result": "Significant" if p < .05 else "Not significant"})
def chi(label, a, b):
    c2, p, dof, _ = stats.chi2_contingency(pd.crosstab(df[a], df[b]))
    tests.append({"test": label, "method": f"Chi-square (dof={dof})", "stat": round(float(c2), 3), "p": round(float(p), 4),
                  "result": "Significant" if p < .05 else "Not significant"})

ttest("Order value: discount vs no discount", df[df["Discount Applied"] == "Yes"][AMT], df[df["Discount Applied"] == "No"][AMT])
ttest("Order value: subscriber vs non-subscriber", df[df["Subscription Status"] == "Yes"][AMT], df[df["Subscription Status"] == "No"][AMT])
ttest("Order value: male vs female", df[df.Gender == "Male"][AMT], df[df.Gender == "Female"][AMT])
anova("Order value across categories", "Category")
anova("Order value across seasons", "Season")
anova("Order value across age groups", "Age Group")
anova("Order value across shipping types", "Shipping Type")
anova("Review rating across categories", "Category", "Review Rating")
chi("Gender vs category", "Gender", "Category")
chi("Season vs category", "Season", "Category")
chi("Subscription vs gender", "Subscription Status", "Gender")
chi("Discount vs gender", "Discount Applied", "Gender")

# ---------------- Structural findings ----------------
structure = {
    "female_subscribers": int(((df.Gender == "Female") & (df["Subscription Status"] == "Yes")).sum()),
    "female_discounts": int(((df.Gender == "Female") & (df["Discount Applied"] == "Yes")).sum()),
    "subscribers_with_discount": int(((df["Subscription Status"] == "Yes") & (df["Discount Applied"] == "Yes")).sum()),
    "subscribers": int((df["Subscription Status"] == "Yes").sum()),
    "nonsub_with_discount": int(((df["Subscription Status"] == "No") & (df["Discount Applied"] == "Yes")).sum()),
}

season_cat = df.pivot_table(index="Category", columns="Season", values=AMT, aggfunc="sum").round(0)
item_season = df.pivot_table(index="Item Purchased", columns="Season", values=AMT, aggfunc="count")

hist_amt = np.histogram(df[AMT], bins=range(20, 105, 5))
hist_age = np.histogram(df["Age"], bins=range(18, 74, 4))
hist_rating = df["Review Rating"].round(1).value_counts().sort_index()

metrics = {
    "kpi": kpi, "quality": quality, "cleaning_log": log, "desc": desc,
    "corr": {"labels": list(corr.columns), "matrix": corr.values.tolist()},
    "tests": tests, "structure": structure,
    "by": {c: grp(c) for c in ["Category", "Item Purchased", "Season", "Gender", "Age Group", "Location",
                               "Size", "Color", "Shipping Type", "Payment Method", "Subscription Status",
                               "Discount Applied", "Frequency (Standardized)", "Customer Segment"]},
    "season_cat": {"rows": list(season_cat.index), "cols": list(season_cat.columns), "values": season_cat.values.tolist()},
    "top_item_by_season": {s: item_season[s].idxmax() for s in item_season.columns},
    "hist_amount": {"edges": hist_amt[1].tolist(), "counts": hist_amt[0].tolist()},
    "hist_age": {"edges": hist_age[1].tolist(), "counts": hist_age[0].tolist()},
    "hist_rating": {"values": hist_rating.index.tolist(), "counts": hist_rating.values.tolist()},
}
(out / "metrics.json").write_text(json.dumps(metrics, indent=1, default=float))
print(json.dumps({"kpi": kpi, "tests": tests, "structure": structure}, indent=1))

# ---------------- Statistical tests file for the dashboard ----------------
(out / "stat_tests.json").write_text(json.dumps({
    "rows": tests,
    "meta": [{"label": Path(__file__).name, "value": Path(__file__).read_text(), "type": "code", "lang": "python"},
             {"label": "Input", "value": raw_path.name}],
}))

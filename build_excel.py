"""Workbook: original data, cleaned data, cleaning log, KPI and summary tables (live formulas), stats tests."""
import json, sys
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

raw = pd.read_csv(sys.argv[1]); clean = pd.read_csv(sys.argv[2]); m = json.load(open(sys.argv[3])); outp = sys.argv[4]
F = "Arial"; H = Font(name=F, bold=True, color="FFFFFF"); HF = PatternFill("solid", fgColor="2A6FB0")
B = Font(name=F); BB = Font(name=F, bold=True); T = Font(name=F, bold=True, size=14); NOTE = Font(name=F, italic=True, color="666666", size=9)
thin = Border(bottom=Side(style="thin", color="DDDDDD"))
wb = Workbook()

def data_sheet(ws, df, name):
    ws.append(list(df.columns))
    for row in df.itertuples(index=False): ws.append([None if (isinstance(v, float) and pd.isna(v)) else v for v in row])
    for c in ws[1]: c.font = H; c.fill = HF; c.alignment = Alignment(wrap_text=True, vertical="center")
    for col in ws.iter_cols(min_row=2):
        for c in col: c.font = B
    for i, col in enumerate(df.columns, 1): ws.column_dimensions[get_column_letter(i)].width = max(11, min(26, len(col) + 2))
    ws.freeze_panes = "A2"
    t = Table(displayName=name, ref=f"A1:{get_column_letter(df.shape[1])}{len(df) + 1}")
    t.tableStyleInfo = TableStyleInfo(name="TableStyleLight9", showRowStripes=True); ws.add_table(t)

ws0 = wb.active; ws0.title = "README"
ws1 = wb.create_sheet("Original Data"); data_sheet(ws1, raw, "OriginalData")
ws2 = wb.create_sheet("Cleaned Data"); data_sheet(ws2, clean, "CleanedData")
N = len(clean) + 1  # last data row
col = {c: get_column_letter(i + 1) for i, c in enumerate(clean.columns)}
rng = lambda c: f"'Cleaned Data'!${col[c]}$2:${col[c]}${N}"
AMT, RAT = rng("Purchase Amount (USD)"), rng("Review Rating")

# Cleaning log
ws3 = wb.create_sheet("Cleaning Log")
ws3.append(["#", "Operation", "Effect", "Reason / note"])
for i, (a, b, c) in enumerate(m["cleaning_log"], 1): ws3.append([i, a, b, c])
for c in ws3[1]: c.font = H; c.fill = HF
for r in ws3.iter_rows(min_row=2):
    for c in r: c.font = B; c.alignment = Alignment(wrap_text=True, vertical="top")
for k, w in zip("ABCD", [5, 60, 38, 50]): ws3.column_dimensions[k].width = w
q = m["quality"]
ws3.append([]); ws3.append(["", "Quality checks on the original file"]); ws3.cell(ws3.max_row, 2).font = BB
for label, v in [("Rows", q["rows"]), ("Columns", q["columns"]), ("Missing Review Rating", q["missing"].get("Review Rating", 0)),
                 ("Duplicate rows", q["duplicate_rows"]), ("Duplicate Customer IDs", q["duplicate_ids"]),
                 ("Discount Applied identical to Promo Code Used", "Yes" if q["discount_equals_promo"] else "No")] + \
                [(f"IQR outliers: {k}", v) for k, v in q["iqr_outliers"].items() if k != "Customer ID"]:
    ws3.append(["", label, v]); ws3.cell(ws3.max_row, 2).font = B; ws3.cell(ws3.max_row, 3).font = B

# KPI sheet with formulas
ws4 = wb.create_sheet("KPI Summary")
ws4["A1"] = "Executive KPIs"; ws4["A1"].font = T
ws4["A2"] = "All values are live formulas on the 'Cleaned Data' sheet."; ws4["A2"].font = NOTE
kpis = [("Customers", f"=COUNTA({rng('Customer ID')})", "#,##0"),
        ("Total revenue (USD)", f"=SUM({AMT})", "$#,##0"),
        ("Average order value (USD)", "=B5/B4", "$#,##0.00"),
        ("Median order value (USD)", f"=MEDIAN({AMT})", "$#,##0.00"),
        ("Order value std dev (USD)", f"=STDEV({AMT})", "$#,##0.00"),
        ("Average review rating", f"=AVERAGE({RAT})", "0.00"),
        ("Rated purchases", f"=COUNT({RAT})", "#,##0"),
        ("Subscription rate", f"=COUNTIF({rng('Subscription Status')},\"Yes\")/B4", "0.0%"),
        ("Discount / promo usage", f"=COUNTIF({rng('Discount Applied')},\"Yes\")/B4", "0.0%"),
        ("Average previous purchases", f"=AVERAGE({rng('Previous Purchases')})", "0.0"),
        ("Loyal customers (11+ previous)", f"=COUNTIF({rng('Customer Segment')},\"Loyal\")/B4", "0.0%"),
        ("Average age", f"=AVERAGE({rng('Age')})", "0.0"),
        ("Female customers subscribed (data check)", f"=COUNTIFS({rng('Gender')},\"Female\",{rng('Subscription Status')},\"Yes\")", "#,##0"),
        ("Female customers discounted (data check)", f"=COUNTIFS({rng('Gender')},\"Female\",{rng('Discount Applied')},\"Yes\")", "#,##0")]
ws4.append(["KPI", "Value"])
for c in ws4[4 - 1]: pass
for c in ws4[3]: c.font = H; c.fill = HF
for label, f, fmt in kpis:
    ws4.append([label, f]); r = ws4.max_row; ws4.cell(r, 1).font = B; ws4.cell(r, 2).font = B; ws4.cell(r, 2).number_format = fmt
ws4.column_dimensions["A"].width = 44; ws4.column_dimensions["B"].width = 16

# Summary tables with formulas
ws5 = wb.create_sheet("Summary Tables")
ws5["A1"] = "Performance by dimension"; ws5["A1"].font = T
ws5["A2"] = "Customers, revenue, average order, share and average rating are formulas on 'Cleaned Data'."; ws5["A2"].font = NOTE
row = 4
orders = {"Season": ["Spring", "Summer", "Fall", "Winter"], "Age Group": ["18-25", "26-35", "36-45", "46-55", "56-70"],
          "Customer Segment": ["New", "Returning", "Loyal"], "Frequency (Standardized)": ["Weekly", "Fortnightly", "Monthly", "Quarterly", "Annually"]}
for dim in ["Category", "Item Purchased", "Season", "Gender", "Age Group", "Customer Segment", "Frequency (Standardized)",
            "Subscription Status", "Discount Applied", "Shipping Type", "Payment Method", "Size", "Location"]:
    vals = orders.get(dim) or [r[dim] for r in m["by"][dim]]
    ws5.cell(row, 1, dim).font = BB; row += 1
    for j, h in enumerate([dim, "Customers", "Revenue (USD)", "Avg order (USD)", "Revenue share", "Avg rating"], 1):
        c = ws5.cell(row, j, h); c.font = H; c.fill = HF
    first = row + 1
    for v in vals:
        row += 1; D = rng(dim)
        ws5.cell(row, 1, v).font = B
        ws5.cell(row, 2, f'=COUNTIF({D},A{row})').number_format = "#,##0"
        ws5.cell(row, 3, f'=SUMIF({D},A{row},{AMT})').number_format = "$#,##0"
        ws5.cell(row, 4, f'=IF(B{row}=0,0,C{row}/B{row})').number_format = "$#,##0.00"
        ws5.cell(row, 5, f"=C{row}/'KPI Summary'!$B$5").number_format = "0.0%"
        ws5.cell(row, 6, f'=IFERROR(AVERAGEIF({D},A{row},{RAT}),"")').number_format = "0.00"
        for j in range(2, 7): ws5.cell(row, j).font = B
    row += 1
    ws5.cell(row, 1, "Total").font = BB
    for j, L in [(2, "B"), (3, "C"), (5, "E")]:
        c = ws5.cell(row, j, f"=SUM({L}{first}:{L}{row - 1})"); c.font = BB
        c.number_format = {"B": "#,##0", "C": "$#,##0", "E": "0.0%"}[L]
    row += 2
for k, w in zip("ABCDEF", [26, 12, 15, 15, 14, 11]): ws5.column_dimensions[k].width = w

# Season x Category
ws6 = wb.create_sheet("Season x Category")
ws6["A1"] = "Revenue (USD) by category and season"; ws6["A1"].font = T
seasons = ["Spring", "Summer", "Fall", "Winter"]; cats = ["Clothing", "Accessories", "Footwear", "Outerwear"]
for j, h in enumerate(["Category"] + seasons + ["Total"], 1): c = ws6.cell(3, j, h); c.font = H; c.fill = HF
for i, cat in enumerate(cats, 4):
    ws6.cell(i, 1, cat).font = B
    for j, s in enumerate(seasons, 2):
        ws6.cell(i, j, f'=SUMIFS({AMT},{rng("Category")},$A{i},{rng("Season")},{get_column_letter(j)}$3)').number_format = "$#,##0"
    ws6.cell(i, 6, f"=SUM(B{i}:E{i})").number_format = "$#,##0"
ws6.cell(8, 1, "Total").font = BB
for j in range(2, 7):
    L = get_column_letter(j); c = ws6.cell(8, j, f"=SUM({L}4:{L}7)"); c.number_format = "$#,##0"; c.font = BB
ws6.column_dimensions["A"].width = 16

# Descriptive stats + tests (values from Python)
ws7 = wb.create_sheet("Statistics")
ws7["A1"] = "Descriptive statistics"; ws7["A1"].font = T
ws7["A2"] = "Computed in Python (pandas); Review Rating uses the 3,863 rated rows."; ws7["A2"].font = NOTE
hdr = ["Measure", "Count", "Mean", "Median", "Mode", "Std dev", "Variance", "Min", "Q1", "Q3", "Max", "Skew"]
for j, h in enumerate(hdr, 1): c = ws7.cell(4, j, h); c.font = H; c.fill = HF
r = 4
for k, d in m["desc"].items():
    r += 1; vals = [k, d["count"], d["mean"], d["median"], d["mode"], d["std"], d["var"], d["min"], d["q1"], d["q3"], d["max"], d["skew"]]
    for j, v in enumerate(vals, 1): ws7.cell(r, j, v).font = B
r += 2; ws7.cell(r, 1, "Hypothesis tests (alpha = 0.05)").font = T; r += 2
for j, h in enumerate(["Question", "Method", "Statistic", "p-value", "Result"], 1): c = ws7.cell(r, j, h); c.font = H; c.fill = HF
for t in m["tests"]:
    r += 1
    for j, v in enumerate([t["test"], t["method"], t["stat"], t["p"], t["result"]], 1): ws7.cell(r, j, v).font = B
    ws7.cell(r, 4).number_format = "0.0000"
r += 2; ws7.cell(r, 1, "Correlation matrix (Pearson r)").font = T; r += 2
labs = m["corr"]["labels"]
for j, h in enumerate([""] + labs, 1): c = ws7.cell(r, j, h); c.font = H; c.fill = HF
for i, lab in enumerate(labs):
    r += 1; ws7.cell(r, 1, lab).font = BB
    for j, v in enumerate(m["corr"]["matrix"][i], 2): ws7.cell(r, j, v).font = B; ws7.cell(r, j).number_format = "0.000"
ws7.column_dimensions["A"].width = 44; ws7.column_dimensions["B"].width = 20
for k in "CDEFGHIJKL": ws7.column_dimensions[k].width = 11

# README
ws0["A1"] = "Customer Shopping Behavior: cleaned dataset and analysis"; ws0["A1"].font = T
lines = [("Original Data", "The uploaded file, unchanged (3,900 rows, 18 columns)."),
         ("Cleaned Data", "Same 3,900 rows plus 5 added columns: Frequency (Standardized), Rating Missing, Age Group, Customer Segment, Est. Purchases / Year. Blank ratings stay blank."),
         ("Cleaning Log", "Every cleaning step and the quality checks run."),
         ("KPI Summary", "Headline KPIs as live formulas."),
         ("Summary Tables", "Customers, revenue, average order, share and rating by each dimension (live formulas)."),
         ("Season x Category", "Revenue cross-tab (live formulas)."),
         ("Statistics", "Descriptive statistics, hypothesis tests and correlations computed in Python."),
         ("Note", "Est. Purchases / Year assumes the stated purchase frequency holds for a full year; it is an estimate, not an observed count."),
         ("Note", "No female customer is recorded as subscribed or discounted, and every subscriber has a discount. Verify these fields at source.")]
for i, (a, b) in enumerate(lines, 3):
    ws0.cell(i, 1, a).font = BB; ws0.cell(i, 2, b).font = B; ws0.cell(i, 2).alignment = Alignment(wrap_text=True, vertical="top")
ws0.column_dimensions["A"].width = 20; ws0.column_dimensions["B"].width = 110
wb.save(outp); print("saved")

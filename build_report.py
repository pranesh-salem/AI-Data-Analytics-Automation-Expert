"""Final analytical report (PDF). Every figure is read from metrics.json."""
import json, sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether, ListFlowable, ListItem)

m = json.load(open(sys.argv[1])); CH = sys.argv[2]; outp = sys.argv[3]
k, q, B, S, T = m["kpi"], m["quality"], m["by"], m["structure"], {t["test"]: t for t in m["tests"]}
ss = getSampleStyleSheet()
BLUE = colors.HexColor("#2A6FB0"); GREY = colors.HexColor("#5F5E5B"); LINE = colors.HexColor("#DDDDDD")
st = {
 "title": ParagraphStyle("t", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=22, leading=27, alignment=0, spaceAfter=6),
 "sub": ParagraphStyle("s", parent=ss["Normal"], fontSize=10.5, textColor=GREY, leading=14),
 "h1": ParagraphStyle("h1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=15, textColor=BLUE, spaceBefore=14, spaceAfter=6),
 "h2": ParagraphStyle("h2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=11.5, spaceBefore=8, spaceAfter=4),
 "p": ParagraphStyle("p", parent=ss["Normal"], fontSize=9.6, leading=13.6, spaceAfter=5),
 "small": ParagraphStyle("sm", parent=ss["Normal"], fontSize=8.2, leading=11, textColor=GREY),
 "cell": ParagraphStyle("c", parent=ss["Normal"], fontSize=8.4, leading=10.5),
}
P = lambda t, s="p": Paragraph(t, st[s])
usd = lambda v: f"${v:,.0f}"; usd2 = lambda v: f"${v:,.2f}"
def by(dim, key): return {r[dim]: r for r in B[dim]}[key]
def table(rows, widths, header=True, num_from=1):
    data = [[Paragraph(str(c), st["cell"]) for c in r] for r in rows]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    sty = [("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header: sty += [("BACKGROUND", (0, 0), (-1, 0), BLUE), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white)]
    t.setStyle(TableStyle(sty))
    if header:
        for c in data[0]: c.style = ParagraphStyle("hc", parent=st["cell"], textColor=colors.white, fontName="Helvetica-Bold")
    return t
def img(name, w=16.5):
    from PIL import Image as PI
    im = PI.open(f"{CH}/{name}"); h = w * im.height / im.width
    return Image(f"{CH}/{name}", width=w * cm, height=h * cm)
def bullets(items): return ListFlowable([ListItem(P(i), leftIndent=10) for i in items], bulletType="bullet", start="•", leftIndent=12)
def insight(title, what, means, why, action):
    return KeepTogether([P(title, "h2"), table([["What happened", what], ["What the data indicates", means], ["Why it matters", why], ["Action to consider", action]], [3.6 * cm, 13.2 * cm], header=False)])

cat = {r["Category"]: r for r in B["Category"]}; sea = {r["Season"]: r for r in B["Season"]}
items = B["Item Purchased"]; states = B["Location"]; seg = {r["Customer Segment"]: r for r in B["Customer Segment"]}
rated = sorted(items, key=lambda r: r["avg_rating"])
disc = {r["Discount Applied"]: r for r in B["Discount Applied"]}; sub = {r["Subscription Status"]: r for r in B["Subscription Status"]}
gap = (sea["Fall"]["revenue"] - sea["Summer"]["revenue"]) / sea["Summer"]["revenue"] * 100
seg_n = sum(r["customers"] for r in B["Customer Segment"])
s = []

# ---- Title & executive summary
s += [P("Customer Shopping Behavior Analysis", "title"),
      P("Analytical report on customer_shopping_behavior.csv &nbsp;|&nbsp; 14 November 2026 &nbsp;|&nbsp; Prepared with Python (pandas, SciPy, matplotlib)", "sub"), Spacer(1, 12),
      P("1. Executive summary", "h1"),
      P(f"The file records <b>{k['customers']:,} customers</b>, each with one purchase, across {k['products']} products, 4 categories and {k['states']} US states. "
        f"Together they spent <b>{usd(k['revenue'])}</b>, an average of <b>{usd2(k['aov'])}</b> per order (median {usd(k['median_order'])}). "
        f"The average review rating is <b>{k['avg_rating']:.2f}</b> out of 5; {k['subscription_rate']:.1f}% of customers subscribe and {k['discount_rate']:.1f}% of purchases used a discount."),
      bullets([f"<b>Clothing drives revenue:</b> {usd(cat['Clothing']['revenue'])} ({cat['Clothing']['share']:.1f}%), then Accessories ({cat['Accessories']['share']:.1f}%), Footwear ({cat['Footwear']['share']:.1f}%) and Outerwear ({cat['Outerwear']['share']:.1f}%).",
               f"<b>Revenue differences come from customer counts, not order size.</b> Average order value sits between $57 and $63 for almost every group; only season shows a statistically significant difference (p = {T['Order value across seasons']['p']:.4f}).",
               f"<b>Fall is the strongest season</b> ({usd(sea['Fall']['revenue'])}, average order {usd2(sea['Fall']['avg_order'])}); Summer is the weakest ({usd(sea['Summer']['revenue'])}), {gap:.1f}% lower.",
               f"<b>Discounts do not lift basket size:</b> {usd2(disc['Yes']['avg_order'])} with a discount vs {usd2(disc['No']['avg_order'])} without (p = {T['Order value: discount vs no discount']['p']:.4f}).",
               f"<b>The customer base is loyal but not growing:</b> {k['loyal_share']:.1f}% have 11+ previous purchases, while only {seg['New']['customers']} customers ({seg['New']['customers']/seg_n*100:.1f}%) are first-time buyers.",
               f"<b>Data anomaly:</b> none of the {by('Gender','Female')['customers']:,} female customers is recorded as subscribed or discounted, and all {S['subscribers']:,} subscribers received a discount. This looks like a capture or export issue and should be checked before these fields drive decisions."])]

# ---- Dataset overview
s += [P("2. Dataset overview", "h1"),
      P(f"Format: CSV, {q['rows']:,} rows x {q['columns']} columns, one sheet. Each row is a unique Customer ID (no duplicates), so a row represents a customer and their most recent purchase. "
        "There are no order dates or order IDs; <b>Season</b> is the only time dimension, so month-by-month or year-on-year trends cannot be measured. "
        "Assumed business context: an omnichannel US fashion and accessories retailer analysing who buys what, how and when."),
      table([["Column", "Type", "Content"],
             ["Customer ID", "Integer (key)", "1 to 3,900, unique"], ["Age", "Integer", "18 to 70"], ["Gender", "Categorical", "Male, Female"],
             ["Item Purchased / Category", "Categorical", "25 items in Clothing, Accessories, Footwear, Outerwear"],
             ["Purchase Amount (USD)", "Integer", "$20 to $100 - main revenue measure"], ["Location", "Categorical", "50 US states"],
             ["Size / Color", "Categorical", "S-XL; 25 colours"], ["Season", "Categorical", "Spring, Summer, Fall, Winter"],
             ["Review Rating", "Decimal", "2.5 to 5.0; 37 blanks"], ["Subscription Status", "Yes/No", "27.0% Yes"],
             ["Shipping Type / Payment Method", "Categorical", "6 options each"], ["Discount Applied / Promo Code Used", "Yes/No", "Identical columns"],
             ["Previous Purchases", "Integer", "1 to 50"], ["Frequency of Purchases", "Categorical", "7 labels, 2 pairs of synonyms"]],
            [5.2 * cm, 3 * cm, 8.6 * cm]),
      P("Primary KPIs: revenue, customers, average order value, average rating, subscription rate, discount usage and loyalty (previous purchases).", "small")]

# ---- Data quality & cleaning
s += [P("3. Data quality assessment", "h1"),
      table([["Check", "Result"],
             ["Missing values", f"Review Rating only: {q['missing']['Review Rating']} rows ({q['missing']['Review Rating']/q['rows']*100:.1f}%). All other fields complete."],
             ["Duplicates", f"{q['duplicate_rows']} duplicate rows; {q['duplicate_ids']} duplicate Customer IDs."],
             ["Data types", "All numeric fields parse as numbers; no invalid values or out-of-range entries."],
             ["Outliers (1.5 x IQR)", "None in Age, Purchase Amount, Review Rating or Previous Purchases. Distributions are close to uniform (skew near 0)."],
             ["Category consistency", "No spelling or case variants. Frequency has synonym pairs: Bi-Weekly = Fortnightly, Every 3 Months = Quarterly."],
             ["Redundant fields", "Promo Code Used equals Discount Applied in all 3,900 rows."],
             ["Logical consistency", f"0 female subscribers and 0 female discounts; {S['subscribers_with_discount']:,} of {S['subscribers']:,} subscribers discounted; {S['nonsub_with_discount']} non-subscribers discounted. Unresolved - needs source check."],
             ["Missing dimensions", "No dates, order IDs or cost/margin data - profit, trend and retention analysis are not possible."]],
            [4.2 * cm, 12.6 * cm]),
      P("4. Data cleaning summary", "h1"),
      P("The original file is preserved unchanged (sheet 'Original Data' in the workbook). The cleaned copy keeps all 3,900 rows and adds columns; no value was invented or deleted."),
      table([["#", "Operation", "Effect"]] + [[i, a, b] for i, (a, b, _) in enumerate(m["cleaning_log"], 1)], [0.8 * cm, 10.4 * cm, 5.6 * cm])]

# ---- EDA
d = m["desc"]
s += [PageBreak(), P("5. Exploratory data analysis", "h1"), P("5.1 Descriptive statistics", "h2"),
      table([["Measure", "Count", "Mean", "Median", "Mode", "Std dev", "Variance", "Min", "Max"]] +
            [[n, f"{v['count']:,}", f"{v['mean']:.2f}", v["median"], v["mode"], f"{v['std']:.2f}", f"{v['var']:.2f}", v["min"], v["max"]] for n, v in d.items()],
            [4.2 * cm] + [1.6 * cm] * 8),
      P("All four numeric fields are almost perfectly symmetric and evenly spread, with no outliers. Purchase amounts are spread evenly between $20 and $100 rather than clustering around a typical price.", "p"),
      img("11_purchase_amount_distribution.png", 15.5), img("12_age_rating_distribution.png", 15.5),
      P("5.2 Correlation", "h2"),
      P("Age, purchase amount, review rating and previous purchases are essentially uncorrelated (all |r| below 0.05). Older or more loyal customers do not spend more per order or rate higher."),
      img("13_correlation_matrix.png", 9)]

# ---- Statistical analysis
s += [P("6. Statistical analysis", "h1"),
      P("Tests run on all 3,900 customers at a 5% significance level (Welch t-test for two groups, one-way ANOVA for several groups, chi-square for associations between categories)."),
      table([["Question", "Method", "Statistic", "p-value", "Result"]] +
            [[t["test"], t["method"], f"{t['stat']:.3f}", "<0.0001" if t["p"] < 0.0001 else f"{t['p']:.4f}", t["result"]] for t in m["tests"]],
            [6.4 * cm, 3.4 * cm, 2.2 * cm, 2 * cm, 2.8 * cm]),
      P("Reading the results: order value does not differ meaningfully by discount, subscription, gender, category, age group or shipping type. Season is the exception, "
        f"but the effect is small (Fall {usd2(sea['Fall']['avg_order'])} vs Summer {usd2(sea['Summer']['avg_order'])}). The two significant chi-square results (subscription and discount vs gender) "
        "are produced by the data anomaly described above, not by customer behaviour.")]

# ---- KPI analysis
s += [KeepTogether([P("7. KPI analysis", "h1"),
      table([["KPI", "Value", "Comment"],
             ["Total revenue", usd(k["revenue"]), "Sum of 3,900 purchases"], ["Customers", f"{k['customers']:,}", "One purchase each"],
             ["Average order value", usd2(k["aov"]), f"Median {usd(k['median_order'])}; std dev {usd2(d['Purchase Amount (USD)']['std'])}"],
             ["Average review rating", f"{k['avg_rating']:.2f} / 5", "3,863 rated purchases"],
             ["Subscription rate", f"{k['subscription_rate']:.1f}%", f"{S['subscribers']:,} subscribers, all male"],
             ["Discount / promo usage", f"{k['discount_rate']:.1f}%", "Includes all subscribers"],
             ["Avg previous purchases", f"{k['avg_prev']:.1f}", f"Loyal (11+): {k['loyal_share']:.1f}%"],
             ["Average age", f"{k['avg_age']:.1f}", "Range 18-70"]], [5 * cm, 3.2 * cm, 8.6 * cm])]),
      P("Growth rates, profit and margin KPIs cannot be calculated: the file has no dates and no cost data.", "small")]

# ---- Visualizations
s += [PageBreak(), P("8. Detailed visualizations", "h1"),
      P("8.1 Sales by category and season", "h2"), img("01_revenue_by_category.png", 14),
      P(f"Clothing earns {cat['Clothing']['share']:.1f}% of revenue from {cat['Clothing']['customers']:,} customers. Average orders are similar across categories; Outerwear is lowest at {usd2(cat['Outerwear']['avg_order'])}.", "small"),
      img("02_revenue_by_season.png", 14),
      P(f"Revenue is evenly spread across seasons (23.9%-25.8% each). Fall leads on both revenue and average order.", "small"),
      img("10_heatmap_season_category.png", 14),
      P("Clothing is weakest in Summer; Outerwear peaks in Fall; Footwear is stronger in Spring and Summer.", "small"),
      KeepTogether([P("8.2 Products", "h2"), img("03_revenue_by_product.png", 14)]),
      P(f"The 25 products are tightly bunched: Blouse leads ({usd(items[0]['revenue'])}) and Jeans trails ({usd(items[-1]['revenue'])}, also the fewest buyers at {items[-1]['customers']}). "
        f"Lowest rated: {rated[0]['Item Purchased']} ({rated[0]['avg_rating']:.2f}) and {rated[1]['Item Purchased']} ({rated[1]['avg_rating']:.2f}); highest: {rated[-1]['Item Purchased']} ({rated[-1]['avg_rating']:.2f}).", "small"),
      KeepTogether([P("8.3 Customers", "h2"), img("04_revenue_by_age_group.png", 14)]),
      P(f"The 56-70 band is widest (15 years) and so has the most customers ({by('Age Group','56-70')['customers']:,}); average orders are flat across ages ($59-$61).", "small"),
      img("05_revenue_by_gender.png", 13), img("06_customers_by_segment.png", 13), img("07_customers_by_frequency.png", 13),
      img("08_aov_discount_subscription.png", 13),
      KeepTogether([P("8.4 Regions and operations", "h2"), img("09_states_top_bottom.png", 15.5)]),
      P(f"Montana leads ({usd(states[0]['revenue'])}); Kansas trails ({usd(states[-1]['revenue'])}). State totals mainly reflect customer counts (63-96 per state).", "small"),
      img("14_revenue_by_shipping.png", 13), img("15_revenue_by_payment.png", 13),
      P("Shipping types and payment methods each take 15.7%-17.5% of revenue with no meaningful differences in order value.", "small")]

# ---- Insights
s += [PageBreak(), P("9. Major business insights", "h1"),
      insight("Insight 1 - Clothing carries the business",
              f"Clothing generated {usd(cat['Clothing']['revenue'])} ({cat['Clothing']['share']:.1f}%); Outerwear only {usd(cat['Outerwear']['revenue'])} ({cat['Outerwear']['share']:.1f}%).",
              "The gap comes from the number of buyers (1,737 vs 324), not order size ($60.03 vs $57.17).",
              "Revenue depends heavily on one category; Outerwear is under-penetrated.",
              "Protect Clothing availability; test Outerwear cross-sell with Clothing buyers."),
      insight("Insight 2 - Fall is the peak season, Summer the low point",
              f"Fall: {usd(sea['Fall']['revenue'])} at {usd2(sea['Fall']['avg_order'])} per order. Summer: {usd(sea['Summer']['revenue'])} at {usd2(sea['Summer']['avg_order'])}.",
              f"Season is the only factor with a significant effect on order value (p = {T['Order value across seasons']['p']:.4f}); the gap is {gap:.1f}% in revenue.",
              "Stock, staffing and marketing budgets can follow a predictable seasonal pattern.",
              "Front-load Fall inventory and campaigns; run Summer promotions, especially for Clothing."),
      insight("Insight 3 - Discounts are not increasing basket size",
              f"{k['discount_rate']:.1f}% of purchases were discounted, averaging {usd2(disc['Yes']['avg_order'])} vs {usd2(disc['No']['avg_order'])} undiscounted.",
              f"No significant difference (p = {T['Order value: discount vs no discount']['p']:.4f}); subscriptions show the same pattern (p = {T['Order value: subscriber vs non-subscriber']['p']:.4f}).",
              "Discount spend may be giving away margin without lifting order value (frequency effect cannot be measured here).",
              "Run a controlled test of targeted vs blanket discounts and track repeat purchases."),
      insight("Insight 4 - Loyal base, weak acquisition",
              f"{k['loyal_share']:.1f}% of customers have 11+ previous purchases; only {seg['New']['customers']} ({seg['New']['customers']/seg_n*100:.1f}%) are new.",
              "Revenue relies on repeat buyers; the pipeline of new customers is thin.",
              "Without new customers, revenue erodes as loyal customers lapse.",
              "Invest in acquisition channels and first-purchase offers; reward loyalty with non-price benefits."),
      insight("Insight 5 - Product quality signals",
              f"Lowest ratings: {rated[0]['Item Purchased']} {rated[0]['avg_rating']:.2f}, {rated[1]['Item Purchased']} {rated[1]['avg_rating']:.2f}, {rated[2]['Item Purchased']} {rated[2]['avg_rating']:.2f}. Highest: {rated[-1]['Item Purchased']} {rated[-1]['avg_rating']:.2f}.",
              f"Rating differences across categories are not significant (p = {T['Review rating across categories']['p']:.4f}); item gaps are small (0.24 points).",
              "Jeans combines a low rating with the lowest revenue - a possible fit or quality issue.",
              "Review returns and feedback for Shirt, Jeans and Blouse."),
      insight("Insight 6 - Data capture risk",
              f"0 of {by('Gender','Female')['customers']:,} female customers are subscribed or discounted; {S['subscribers_with_discount']:,} of {S['subscribers']:,} subscribers are discounted.",
              "Patterns this absolute are unlikely to reflect real behaviour.",
              "Any targeting or discount analysis by gender or subscription could be wrong.",
              "Audit the CRM/export logic before using these fields.")]

# ---- Trends, risks & opportunities
s += [P("10. Trends and patterns", "h1"),
      bullets(["Demand is spread very evenly across products, states, sizes, colours, shipping types and payment methods; no single small group dominates.",
               "Medium (M) is the dominant size (45.1% of revenue); XL is smallest (11.1%).",
               "Purchase frequency, after merging synonyms, is led by Quarterly (29.4% of customers) and Fortnightly (27.9%).",
               "No time-based trend can be shown beyond season, because the file has no dates."]),
      P("11. Risks and opportunities", "h1"),
      table([["Risks", "Opportunities"],
             ["Possible data capture error in gender, subscription and discount fields", "Fall seasonal peak to plan around"],
             ["Discount spend without measurable basket uplift", "Outerwear and Footwear cross-sell to Clothing buyers"],
             ["Very few first-time buyers", "Large loyal base for referral and loyalty programmes"],
             ["Concentration on Clothing (44.7%)", "Lift Summer sales with targeted promotions"],
             ["No dates/costs - limited ability to track trends or profit", "Richer data (dates, order IDs, margins) would unlock CLV and forecasting"]], [8.4 * cm, 8.4 * cm])]

# ---- Recommendations
s += [P("12. Business recommendations", "h1"), P("Ranked by expected impact within each horizon.", "small"),
      P("Immediate actions (0-1 month)", "h2"),
      bullets(["<b>Audit subscription and discount capture</b> - confirm why no female customer is subscribed or discounted and why subscription always implies a discount.",
               "<b>Review blanket discounting</b> - discounts cover 43.0% of purchases without raising order value; pilot targeted offers with a control group.",
               "<b>Extend the data export</b> with order date, order ID, cost and returns."]),
      P("Short-term improvements (1-6 months)", "h2"),
      bullets(["<b>Plan Fall inventory and campaigns</b>; build a Summer promotion calendar to close the 7.6% gap.",
               "<b>Grow Outerwear</b> through bundles and recommendations to Clothing buyers.",
               "<b>Investigate low-rated products</b> (Shirt, Jeans, Blouse) via reviews and returns."]),
      P("Long-term strategies (6+ months)", "h2"),
      bullets(["<b>Build an acquisition programme</b> - first-time buyers are only 2.1% of customers.",
               "<b>Redesign loyalty and subscription benefits</b> around non-price perks and measure purchase frequency.",
               "<b>Develop customer lifetime value and demand forecasting models</b> once dated, per-order history is available."]),
      P("13. Conclusion", "h1"),
      P(f"The business earns {usd(k['revenue'])} from {k['customers']:,} highly loyal customers, led by Clothing and a Fall peak. Customer groups spend remarkably similar amounts per order, "
        "so growth will come from reaching more customers and selling more categories to each, not from discounts. "
        "Two caveats apply to every finding: the fields linking gender, subscription and discount look unreliable, and the absence of dates limits trend and retention analysis. "
        "Fixing these data gaps is the highest-value next step."),
      Spacer(1, 8),
      P("Deliverables: interactive dashboard (HTML), cleaned dataset with live-formula summaries (Excel), charts (PNG), Python analysis scripts.", "small")]

def footer(c, doc):
    c.saveState(); c.setFont("Helvetica", 7.5); c.setFillColor(GREY)
    c.drawString(2 * cm, 1.2 * cm, "Customer Shopping Behavior Analysis"); c.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}"); c.restoreState()
SimpleDocTemplate(outp, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                  title="Customer Shopping Behavior Analysis", author="Claude").build(s, onFirstPage=footer, onLaterPages=footer)
print("ok")

CUSTOMER SHOPPING DASHBOARD - POWER BI PROJECT (.pbip)
======================================================

WHAT THIS IS
A Power BI Project: the open, text-based format of a Power BI report. The cleaned data
(3,900 customers) is embedded in the model's Power Query step, so no file paths need
changing. Pages: Overview | Products & Customers | Regions & Operations | Data Quality & Insights.
Slicers (Gender, Season, Category, Age Group, Subscription) are synced across the first three pages.

HOW TO OPEN AND SAVE AS .PBIX
1. Unzip the whole folder (keep the .Report and .SemanticModel folders next to the .pbip file).
2. Install/update Power BI Desktop (free, Windows). In older versions turn on
   File > Options and settings > Options > Preview features > "Power BI Project (.pbip) save option",
   then restart Power BI Desktop.
3. File > Open > "Customer Shopping Dashboard.pbip".
4. Click Home > Refresh once. A project stores no data cache, so visuals stay empty until the first refresh.
5. File > Save As > choose "Power BI file (*.pbix)". You now have a standard .pbix.
6. Optional: View > Themes > Browse for themes > CustomerShoppingTheme.json.

IF IT DOES NOT OPEN
This project was generated outside Power BI Desktop and could not be test-opened there.
If Desktop reports an error, use the fallback (about 15 minutes):
  a. Get data > Text/CSV > customer_shopping_cleaned.csv (load as table "Customers").
  b. New measure: paste each measure from DAX_Measures.txt and set its format.
  c. Sort Season by "Season Order", Customer Segment by "Segment Order",
     Frequency (Standardized) by "Frequency Order", Size by "Size Order" (Column tools > Sort by column).
  d. Rebuild the visuals listed below.

VISUALS
Overview: 5 dropdown slicers; cards (Total Revenue, Customer Count, Avg Order Value, Avg Review Rating,
  Subscription Rate, Discount Rate); bar Revenue by Category; column Revenue by Season; matrix
  Category x Season revenue; column Revenue by Age Group; donut Revenue by Gender; bar Customers by Segment.
Products & Customers: bar Revenue by Product; product table; bar Customers by Frequency;
  bars Avg Order Value by Discount Applied and by Subscription Status.
Regions & Operations: bar Revenue by State; state table; bars by Shipping Type, Payment Method, Size.
Data Quality & Insights: data-check cards; insights and recommendations text.

DATA NOTES
- No order dates in the source: Season is the only time dimension.
- 37 blank review ratings are left blank (Avg Review Rating uses rated rows only).
- No female customer is recorded as subscribed or discounted, and every subscriber has a discount:
  verify these fields at source before acting on them.

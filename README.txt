# 🚀 Automated Data Analysis & EDA Agent

An intelligent, automated Data Analysis Agent designed to streamline Exploratory Data Analysis (EDA), extract key business metrics, and generate visual insights seamlessly.

---

## 📊 Key Performance Insights & Visualizations

### 1. Revenue & Category Analysis
* **Category Breakdown:** Clothing leads total revenue at **$104,264 (44.7%)**, followed by Accessories at **$74,200 (31.8%)**[cite: 1].
* **Seasonal Trends:** Revenue remains steady across seasons, with Fall peaking slightly at **$60,018** and Summer at **$55,777**[cite: 2].
* **Season vs Category Heatmap:** Highest single revenue cluster is observed in **Spring - Clothing ($27,692)** and **Winter - Clothing ($27,274)**[cite: 10].
* **Top Products & Bottom Products:** Blouse (**$10,410**), Shirt (**$10,332**), and Dress (**$10,320**) lead product sales, while Jeans brings in **$7,548**[cite: 3].
* **AOV by Discount & Subscriptions:** Average Order Value remains consistent across subscriptions (~**$59.49** vs **$59.87**) and discounts (~**$59.28** vs **$60.13**)[cite: 8].

### 2. Customer Segmentation & Behavior
* **Loyalty Segments:** **Loyal customers** form the majority backbone at **3,116 customers (79.9%)**, while Returning users account for **701 (18.0%)** and New users account for **83 (2.1%)**[cite: 6].
* **Purchase Frequency:** Quarterly (**1,147**) and Fortnightly (**1,089**) shopping frequencies dominate, followed by Annually (**572**), Monthly (**553**), and Weekly (**539**)[cite: 7].
* **Demographics:** Male buyers drive **$157,890 (67.7%)** of revenue compared to Female buyers at **$75,191 (32.3%)**[cite: 5]. Age group **56–70** generates the highest spend (**$65,256**), followed by 46–55 (**$45,619**) and 26–35 (**$44,342**)[cite: 4].

### 3. Geographic Performance
* **Top States:** Montana (**$5,784**), Illinois (**$5,617**), and California (**$5,605**) lead regional sales[cite: 9].
* **Bottom States:** Kansas (**$3,437**) and Hawaii (**$3,752**) trail at the bottom[cite: 9].

---

## 📁 Repository Structure

```text
auto-eda-analytics-agent/
│
├── README.md               # Main project documentation & overview
├── assets/                 # Folder containing all generated charts/images
│   ├── 01_revenue_by_category.png
│   ├── 02_revenue_by_season.png
│   ├── 03_revenue_by_product.png
│   ├── 04_revenue_by_age_group.png
│   ├── 05_revenue_by_gender.png
│   ├── 06_customers_by_segment.png
│   ├── 07_customers_by_frequency.png
│   ├── 08_aov_discount_subscription.png
│   ├── 09_states_top_bottom.png
│   └── 10_heatmap_season_category.png
├── src/                    # Source code / Agent scripts
└── requirements.txt        # Dependencies

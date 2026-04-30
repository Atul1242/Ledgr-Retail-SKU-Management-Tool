# Sunrise Demand AI — Intelligent Inventory Optimization System

**AI-powered demand forecasting and inventory optimization for FMCG distributors**

Built for Sunrise Consumer Goods — Pune & Nashik distribution network (320 outlets, 40 SKUs)

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat-square&logo=flask)
![LightGBM](https://img.shields.io/badge/LightGBM-ML-green?style=flat-square)
![Tabler](https://img.shields.io/badge/Tabler-UI-206bc4?style=flat-square)

---

## Problem Statement

**PS 5 — The Demand Mirage**

FMCG distributors face a critical data quality challenge: when sales show zero, does it mean genuine lack of demand, or is data simply missing? Misclassification leads to either devastating stockouts during peak seasons (Diwali 2023) or costly overstock situations with trapped capital.

This system solves the **True Zero vs Missing Data** classification problem and builds an end-to-end demand forecasting and reorder optimization pipeline — with a retrospective analysis of the Diwali 2023 stockout event.

---

## System Architecture

```
+-----------------------------------------------------------+
|                    Flask Web Server                        |
|              Tabler UI Dashboard (6 pages)                 |
+----------+----------+----------+-----------+--------------+
| Overview | Forecast | Reorder  | Retro-    | Classification|
| KPIs     | Explorer | Plan     | spective  | & Accuracy    |
+----+-----+----+-----+----+-----+----+------+------+-------+
     |          |          |          |              |
+----v----------v----------v----------v--------------v-------+
|              6-Step Backend Pipeline                        |
|                                                            |
|  Step 1: Data Classification (True Zero / Missing Data)    |
|  Step 2: LightGBM Demand Forecasting (SKU-level, 6-week)  |
|  Step 3: Diwali 2023 Retrospective (No-lookahead)          |
|  Step 4: Reorder Engine (MOQ / Shelf-life / Safety Stock)  |
|  Step 5: SKU Classification (Movement + ABC Analysis)      |
|  Step 6: Monday Morning Report Generator                   |
+------------------------------------------------------------+
```

---

## Key Features

### 1. True Zero vs Missing Data Classification

The raw dataset contains only observed sales rows. The system reconstructs the **complete grid** of all `week x SKU x outlet` combinations (1.99M rows from 93.6K observed), then classifies each row through a 3-step rule-based pipeline:

| Step | Logic | Classification |
|------|-------|---------------|
| Outlet Reporting | Outlet reports zero across ALL SKUs in a week | `missing_data` |
| Stockout Gap | Warehouse stock <= 20 units + zero sales | `stockout_gap` |
| Channel Frequency | sell_frequency > 0.6 → `true_zero`, < 0.2 → `missing_data`, else → `uncertain` |

Only `observed`, `true_zero`, `uncertain`, and `stockout_gap` rows are included in forecasting. `missing_data` rows are excluded to prevent systematic demand underestimation.

### 2. SKU-Level Demand Forecasting

- Individual **LightGBM** model per SKU (40 models) with 14 engineered features
- Feature set includes: lag variables, rolling averages, festive calendar flags, promotional uplift, channel mix, seasonality
- **95% confidence intervals** computed from training residual distribution: `forecast +/- 1.96 x residual_std`
- Rolling average fallback for SKUs with insufficient data
- Overall MAPE: **10.4%** across all SKUs

### 3. Diwali 2023 Retrospective Analysis

Detects stockout SKUs using a 5-signal scoring system with **no lookahead bias** — detection cutoff is strictly 2 weeks post-Diwali (November 7, 2023):

| Signal | Points | Detection Method |
|--------|--------|-----------------|
| Sales Dropout | +3 | >=80% drop from rolling average for 2+ consecutive weeks post-Diwali |
| Demand Surge | +2 | Pre-Diwali sales spike > 1.5x baseline |
| Diwali 2022 Pattern | +2 | Historical festive sensitivity > 1.3x normal |
| Inventory Low | +1 | Available stock below lead-time safety threshold |
| Promo Overlap | +1 | Active promotion during Diwali period |

All signals use only pre-Diwali 2023 or historical 2022 data. No post-event information is used for detection.

### 4. Intelligent Reorder Engine

- **Hard constraints enforced**: MOQ compliance, lead-time coverage, safety stock (2 weeks)
- **Shelf-life validation**: `assert final_reorder_qty <= shelf_life_max` — guaranteed 0 violations
- **Business impact metrics** per SKU: `revenue_at_risk` (for stockout SKUs) and `overstock_value` (for excess inventory)
- Plain-English reasoning text for every recommendation

### 5. SKU Classification and ABC Analysis

- Movement classification: Fast Mover / Slow Mover / Seasonal / Dead Stock
- ABC revenue analysis with cumulative contribution percentages (A: top 70%, B: 70-90%, C: tail)

### 6. Enterprise Dashboard

- 6 interactive pages built with Tabler UI and ApexCharts
- Real-time pipeline execution from the dashboard
- Filterable reorder table with risk flags and reasoning modal
- CSV export for reorder recommendations

---

## Quick Start

### Prerequisites

- Python 3.10 or higher
- pip

### Installation

```bash
git clone https://github.com/Atul1242/dimand_Mirage.git
cd dimand_Mirage/project
pip install -r requirements.txt
python app.py
```

Open **http://localhost:5000** in your browser. The pipeline runs automatically on startup.

### Input Data Files

The following CSV files should be present in the `data/` directory:

| File | Description |
|------|-------------|
| `sales_history.csv` | Weekly sales by outlet x SKU (93,600 rows, 156 weeks) |
| `inventory_snapshot.csv` | Current warehouse stock, in-transit, committed quantities |
| `sku_master.csv` | Product metadata: shelf life, MOQ, lead time, pricing |
| `outlet_master.csv` | Outlet details: channel type, city, tier |
| `festive_calendar.csv` | Festival dates with demand impact scores |
| `promotions_calendar.csv` | Promotional periods with expected uplift percentages |

---

## Dashboard Pages

| Page | Description |
|------|-------------|
| **Overview** | Executive KPIs (stockout risk, revenue at risk, order value), top-10 stockout chart, movement donut, ABC distribution |
| **Diwali Retrospective** | Top-14 predicted stockout SKUs with signal breakdown, per-SKU sales timeline with Diwali annotations, AI reasoning |
| **6-Week Forecast** | SKU-level forecast with historical trend, 95% confidence bands, model type indicator |
| **Reorder Plan** | Full recommendations table with risk flags, filterable by category (Urgent/Shelf-Life/Overstock/Perishable), reasoning modal, CSV download |
| **SKU Classification** | Movement categories with top-20 volume chart, velocity vs consistency scatter plot, ABC revenue table with progress bars |
| **Forecast Accuracy** | Overall MAPE score, per-SKU accuracy table with ratings, MAPE distribution histogram |

---

## Project Structure

```
project/
├── app.py                          # Flask server and API endpoints
├── pipeline.py                     # 6-step pipeline orchestrator
├── requirements.txt                # Python dependencies
├── README.md
├── .gitignore
│
├── backend/
│   ├── 1_clean_data.py             # True Zero classifier with full grid reconstruction
│   ├── 2_forecast.py               # LightGBM demand forecaster with residual-based CI
│   ├── 3_retrospective.py          # Diwali stockout detector (no lookahead bias)
│   ├── 4_reorder_engine.py         # Constraint-based reorder calculator
│   ├── 5_sku_classifier.py         # Movement + ABC classifier
│   └── 6_report_generator.py       # Monday morning report generator (JSON)
│
├── templates/
│   ├── base.html                   # Tabler UI base layout
│   ├── overview.html               # Overview dashboard
│   ├── retrospective.html          # Diwali retrospective
│   ├── forecast.html               # Forecast explorer
│   ├── reorder.html                # Reorder recommendations
│   ├── classification.html         # SKU classification
│   └── accuracy.html               # Forecast accuracy
│
├── data/
│   ├── *.csv                       # Source data files
│   └── processed/                  # Generated pipeline outputs
│
├── docs/
│   └── true_zero_methodology.md    # Classification methodology documentation
│
└── logs/
    └── pipeline_*.log              # Timestamped execution logs
```

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.12, Flask |
| ML Engine | LightGBM, scikit-learn, NumPy, Pandas |
| Frontend | Tabler UI (CDN), ApexCharts, Inter font |
| Pipeline | APScheduler-ready orchestration |

---

## Methodology

### True Zero Classification

```
Step 1: Outlet reported ZERO across ALL SKUs that week?
        → missing_data (non-reporting outlet)

Step 2: Warehouse stock <= 20 units AND sales = 0?
        → stockout_gap (unfulfilled demand)

Step 3: sell_frequency = weeks_with_sales / total_reporting_weeks
        > 0.6 → true_zero (genuine zero demand)
        < 0.2 → missing_data (product not carried)
        else  → uncertain (treated conservatively as true_zero)
```

### Confidence Interval Computation

```
residuals     = actual_training_values - predicted_training_values
residual_std  = std(residuals)
lower_bound   = max(0, forecast - 1.96 * residual_std)   # 95% CI
upper_bound   = forecast + 1.96 * residual_std
```

### Shelf-Life Validation

```python
shelf_life_max = daily_velocity * shelf_life_days
if final_reorder_qty > shelf_life_max:
    final_reorder_qty = floor(shelf_life_max / moq) * moq
assert final_reorder_qty <= shelf_life_max  # Must NEVER fail
# Result: 0 shelf-life violations guaranteed
```

---

## Latest Pipeline Results

| Metric | Value |
|--------|-------|
| Total data points (full grid) | 1,996,800 |
| Observed sales rows | 93,600 |
| Reconstructed missing rows | 1,903,200 |
| SKUs analyzed | 40 |
| Outlets covered | 320 |
| Time range | 156 weeks |
| Overall forecast MAPE | 10.4% |
| LightGBM models trained | 40 |
| SKUs at stockout risk | 35 |
| Shelf-life violations | 0 |
| Total recommended order value | Rs. 13.9M |
| Revenue at risk (stockout) | Rs. 19.1M |

---

## License

MIT License

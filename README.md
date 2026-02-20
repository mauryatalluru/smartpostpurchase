# Smart Post-Purchase Rules (OrderEditing Companion Demo)

A production-ready Streamlit web app that computes explainable recommendations for post-purchase order editing: suggested edit windows, upsell prompts, strict address validation, and early order locking.

**No machine learning**—uses deterministic, rule-based logic that is easy to understand and demo.

## How to Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## What It Does

Given a table of Shopify-like orders, the app computes:

1. **Suggested edit window (minutes)** – 10, 15, 20, 25, or 30 minutes based on customer type, discounts, past edits, and shipping speed
2. **Show upsell** – Yes/No based on order value, industry, and customer type
3. **Strict address validation** – Yes/No based on address change history and customer type
4. **Lock order early** – Yes/No based on fraud-risk signals (e.g., first-time + discount + address changes, past cancels)

Each row includes an **explanation** summarizing the top 2 reasons for the recommendations.

## Schema (Expected Columns)

| Column                 | Type   | Description                                      |
|------------------------|--------|--------------------------------------------------|
| `order_id`             | string | Unique order identifier                          |
| `customer_type`        | string | `first_time`, `repeat`, or `vip`                 |
| `order_value`          | float  | Order total in currency units                    |
| `discount_used`        | 0/1    | Whether a discount code was used                 |
| `past_edits`           | int    | Number of past order edits by customer           |
| `past_cancels`         | int    | Number of past cancellations                     |
| `shipping_speed`       | string | `standard` or `express`                          |
| `minutes_since_checkout` | int  | Minutes elapsed since checkout                   |
| `address_change_requests` | int  | Number of address change requests for this order |

## Uploading Your Own CSV

1. Select **Upload CSV** in the Data source section.
2. Upload a CSV file.
3. If your column names differ from the schema, use the **Column mapping** UI to map your columns to the expected names.
4. If required columns are missing, the app shows a friendly error and provides an example template to download.

### Example CSV Template

```csv
order_id,customer_type,order_value,discount_used,past_edits,past_cancels,shipping_speed,minutes_since_checkout,address_change_requests
ORD-0001,first_time,45.50,0,0,0,standard,12,0
ORD-0002,repeat,89.00,1,1,0,express,5,0
```

## Dependencies

- **streamlit** – Web app framework
- **pandas** – Data handling
- **numpy** – Numeric operations

No external APIs, database, or images required.

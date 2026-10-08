import pandas as pd, numpy as np, random
from datetime import date, timedelta, datetime
random.seed(42); np.random.seed(42)

# ---- Dimensions ----
dates = pd.date_range("2025-01-01", "2025-12-31")
dim_date = pd.DataFrame({
    "date_key": dates.strftime("%Y%m%d").astype(int),
    "date": dates.date, "week": dates.isocalendar().week.values,
    "month": dates.month, "month_name": dates.strftime("%b"),
    "quarter": dates.quarter, "is_weekend": (dates.dayofweek >= 5).astype(int)})

cities = ["Karachi","Lahore","Islamabad","Faisalabad","Multan","Peshawar"]
sup_names = ["Alpha Traders","Bright Foods","City Packaging","Delta Electronics","Eagle Textiles",
             "Fast Chemicals","Global Plastics","Habib Steel","Indus Pharma","Jinnah Paper",
             "Kohat Cement","Lakson Goods","Metro Auto Parts","Noor Beverages","Orient Tools"]
cats = ["Food","Electronics","Textiles","Chemicals","Packaging","Pharma","Auto Parts"]
dim_supplier = pd.DataFrame({
    "supplier_key": range(1, 16), "supplier_name": sup_names,
    "city": [random.choice(cities) for _ in sup_names],
    "category": [random.choice(cats) for _ in sup_names],
    "reliability": np.random.uniform(0.55, 0.97, 15)})  # hidden driver for lateness

sku_cat = {"Food":(50,400),"Electronics":(2000,30000),"Textiles":(300,3000),"Chemicals":(500,5000),
           "Packaging":(20,200),"Pharma":(100,2500),"Auto Parts":(800,12000)}
rows = []
for i in range(1, 201):
    c = random.choice(cats); lo, hi = sku_cat[c]
    rows.append((i, f"SKU-{i:04d}", f"{c} Item {i}", c, round(random.uniform(lo, hi), 2),
                 np.random.choice([1,2,3,4], p=[.2,.3,.3,.2])))  # demand tier
dim_sku = pd.DataFrame(rows, columns=["sku_key","sku_id","sku_name","category","unit_cost","demand_tier"])

dim_wh = pd.DataFrame({"warehouse_key":[1,2,3], "warehouse_name":["Karachi DC","Lahore DC","Islamabad DC"],
                       "city":["Karachi","Lahore","Islamabad"], "capacity_units":[60000,45000,30000]})

# ---- fact_shipments ----
N = 8000; recs = []
for sid in range(1, N+1):
    sup = dim_supplier.sample(1).iloc[0]; sku = dim_sku.sample(1).iloc[0]
    order_dt = datetime(2025,1,1) + timedelta(days=int(np.random.randint(0, 340)))
    promised = order_dt + timedelta(days=int(np.random.randint(3, 11)))
    late = np.random.rand() > sup.reliability
    delay = int(np.random.randint(1, 6)) if late else int(np.random.choice([0,0,0,-1]))
    delivered = promised + timedelta(days=delay)
    scan_in = delivered.replace(hour=int(np.random.randint(7, 18)), minute=int(np.random.randint(0, 60)))
    dwell_h = max(2, np.random.gamma(2, 12) * (1 + (5 - sku.demand_tier) * 0.6))  # low demand = longer dwell
    scan_out = scan_in + timedelta(hours=float(dwell_h))
    qty_rec = int(np.random.randint(20, 500))
    qty_disp = int(qty_rec * np.random.uniform(0.85, 1.0))
    recs.append((sid, int(order_dt.strftime("%Y%m%d")), int(delivered.strftime("%Y%m%d")),
                 sup.supplier_key, sku.sku_key, int(np.random.choice([1,2,3], p=[.5,.3,.2])),
                 qty_rec, qty_disp, order_dt.date(), promised.date(), delivered.date(),
                 scan_in, scan_out))
fact_ship = pd.DataFrame(recs, columns=["shipment_id","order_date_key","date_key","supplier_key","sku_key",
    "warehouse_key","qty_received","qty_dispatched","order_date","promised_date","delivered_date","scan_in_time","scan_out_time"])

# ---- fact_inventory_daily (weekly snapshots keep file small; change step for daily) ----
inv = []
for _, s in dim_sku.iterrows():
    wh = random.choice([1,2,3]); stock = int(np.random.randint(200, 1500))
    for d in dates[::1]:
        usage = np.random.poisson(max(1, (5 - s.demand_tier) * 0 + s.demand_tier * 6))
        stock -= usage
        if stock < 50: stock += int(np.random.randint(300, 1200)) if np.random.rand() < .25 else 0
        stock = max(stock, 0)
        inv.append((int(d.strftime("%Y%m%d")), int(s.sku_key), wh, stock))
fact_inv = pd.DataFrame(inv, columns=["date_key","sku_key","warehouse_key","stock_on_hand"])

# ---- Deliberately dirty a copy of shipments for the cleaning step ----
dirty = fact_ship.copy()
idx = dirty.sample(60, random_state=1).index
dirty.loc[idx[:20], "delivered_date"] = None
dirty = pd.concat([dirty, dirty.sample(40, random_state=2)])  # duplicates

for name, df in [("dim_date",dim_date),("dim_supplier",dim_supplier.drop(columns="reliability")),
                 ("dim_sku",dim_sku.drop(columns="demand_tier")),("dim_warehouse",dim_wh),
                 ("fact_shipments",fact_ship),("fact_inventory_daily",fact_inv),
                 ("raw_shipments_dirty",dirty)]:
    df.to_csv(f"{name}.csv", index=False); print(name, len(df))

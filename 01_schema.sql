-- PostgreSQL star schema
CREATE TABLE dim_date (date_key INT PRIMARY KEY, date DATE, week INT, month INT, month_name VARCHAR(3), quarter INT, is_weekend INT);
CREATE TABLE dim_supplier (supplier_key INT PRIMARY KEY, supplier_name VARCHAR(60), city VARCHAR(40), category VARCHAR(40));
CREATE TABLE dim_sku (sku_key INT PRIMARY KEY, sku_id VARCHAR(10), sku_name VARCHAR(80), category VARCHAR(40), unit_cost NUMERIC(12,2));
CREATE TABLE dim_warehouse (warehouse_key INT PRIMARY KEY, warehouse_name VARCHAR(40), city VARCHAR(40), capacity_units INT);
CREATE TABLE fact_shipments (
  shipment_id INT PRIMARY KEY, order_date_key INT, date_key INT REFERENCES dim_date,
  supplier_key INT REFERENCES dim_supplier, sku_key INT REFERENCES dim_sku, warehouse_key INT REFERENCES dim_warehouse,
  qty_received INT, qty_dispatched INT, order_date DATE, promised_date DATE, delivered_date DATE,
  scan_in_time TIMESTAMP, scan_out_time TIMESTAMP);
CREATE TABLE fact_inventory_daily (
  date_key INT REFERENCES dim_date, sku_key INT REFERENCES dim_sku, warehouse_key INT REFERENCES dim_warehouse,
  stock_on_hand INT, PRIMARY KEY (date_key, sku_key));
-- Load: \copy dim_date FROM 'dim_date.csv' CSV HEADER;  (repeat per table, dimensions first)

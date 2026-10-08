-- 1. Supplier scorecard: on-time %, avg lead time, avg delay
SELECT s.supplier_name,
  COUNT(*) AS shipments,
  ROUND(100.0*SUM(CASE WHEN f.delivered_date <= f.promised_date THEN 1 ELSE 0 END)/COUNT(*),1) AS on_time_pct,
  ROUND(AVG(f.delivered_date - f.order_date),1) AS avg_lead_days,
  ROUND(AVG(GREATEST(f.delivered_date - f.promised_date,0)),2) AS avg_days_late
FROM fact_shipments f JOIN dim_supplier s USING (supplier_key)
GROUP BY s.supplier_name ORDER BY on_time_pct;

-- 2. Dwell time (scan-in to dispatch) by warehouse
SELECT w.warehouse_name,
  ROUND(AVG(EXTRACT(EPOCH FROM (f.scan_out_time - f.scan_in_time))/3600)::numeric,1) AS avg_dwell_hours
FROM fact_shipments f JOIN dim_warehouse w USING (warehouse_key) GROUP BY 1;

-- 3. Slow-moving SKUs: turnover = dispatched / avg stock
WITH d AS (SELECT sku_key, SUM(qty_dispatched) AS dispatched FROM fact_shipments GROUP BY 1),
     i AS (SELECT sku_key, AVG(stock_on_hand) AS avg_stock FROM fact_inventory_daily GROUP BY 1)
SELECT k.sku_id, k.category, d.dispatched, ROUND(i.avg_stock,0) AS avg_stock,
       ROUND(d.dispatched/NULLIF(i.avg_stock,0),2) AS turnover
FROM d JOIN i USING (sku_key) JOIN dim_sku k USING (sku_key)
ORDER BY turnover ASC LIMIT 20;

-- 4. Stockout days per SKU
SELECT k.sku_id, COUNT(*) AS stockout_days
FROM fact_inventory_daily i JOIN dim_sku k USING (sku_key)
WHERE stock_on_hand = 0 GROUP BY 1 ORDER BY 2 DESC LIMIT 20;

-- 5. Monthly on-time trend
SELECT d.month, ROUND(100.0*AVG((f.delivered_date <= f.promised_date)::int),1) AS on_time_pct
FROM fact_shipments f JOIN dim_date d USING (date_key) GROUP BY 1 ORDER BY 1;

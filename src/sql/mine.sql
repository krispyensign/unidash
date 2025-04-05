WITH weights (weight) AS (
    SELECT top(@period)
        ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS weight
    FROM 
        [dbo].[ohlchistory]
),
weighted_values (cn, weight, rn) AS (
    SELECT 
        t.high as cn,
        w.weight as weight,
        ROW_NUMBER() OVER (ORDER BY t.id) AS rn
    FROM 
        [dbo].[ohlchistory] t
    JOIN 
        weights w ON w.weight <= @period
)
SELECT 
    t.id,
    SUM(wv * wv.weight) / SUM(wv.weight) AS WMA
FROM 
    weighted_values wv
JOIN 
    [dbo].[ohlchistory] t ON wv.rn BETWEEN t.id - @period + 1 AND t.id
GROUP BY 
    t.id
ORDER BY 
    t.id;select top(100) * from ohlchistory
order by timestamp
desc


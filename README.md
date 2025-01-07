# setup 

python3 cbsetup.py 

python3 reindex.py 

./update.sh

python3 reindex_analytics.py 

python3 app.py 



# queries 

## engineer mode 

What are common defects on our production line related to wafers?

What is the product SKU with most customer tickets associated in 2023?

fetch me the CAD file of IC-001 from PLM system


## tools management 

SELECT 
    annotation_key,
    COUNT(1) AS total
FROM `audits`.`agent_catalog`.`tool_catalog`
UNNEST OBJECT_PAIRS(annotations) AS annotation
GROUP BY annotation.name AS annotation_key;


SELECT a.version.timestamp
FROM `audits`.`agent_catalog`.`tool_catalog` as a


## look at source code of "provider.get_tools_for"

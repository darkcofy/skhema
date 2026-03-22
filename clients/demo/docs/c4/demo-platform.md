# Data Platform Overview

A simplified view showing how client-specific legacy systems integrate with the shared data platform primitives. The Legacy ERP exports data via CSV/FTP to the Batch ETL layer, which loads it into the Data Lake as Parquet files. dbt transforms the data into the Data Warehouse for analytics consumption.

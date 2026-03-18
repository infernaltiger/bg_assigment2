# Database Experiment Reproduction

This repository contains the code and scripts to reproduce an experiment comparing data loading and query performance across three different database systems: **PostgreSQL**, **MongoDB**, and **Neo4j**.

## Prerequisites

Before starting, ensure the following software is installed locally on your machine:

- **Python** (compatible with `pyproject.toml`)
- **uv** (recommended for dependency management)
- **PostgreSQL**
- **MongoDB**
- **Neo4j**

## Installation & Setup

### Option 1: Using `uv` (Recommended)

1. Clone or download the project.
2. Initialize the project and sync dependencies:
   ```bash
   uv init
   uv sync
   ```
   This will create a `.venv` virtual environment and install all required libraries.

### Option 2: Manual Virtual Environment    
If you do not have `uv` installed:
1. Create a virtual environment named `.venv` in the root directory:
 ```bash
python -m venv .venv
 ```
2. Activate the environment.
3. Install the libraries listed in pyproject.toml manually (e.g., using pip).


## Data Preparation
Before loading data into the databases, you must prepare the raw data files.
1. Navigate to the `data` folder.
2. Open the `.txt` file located there to find the download link for the dataset.
3. Download the data and place it inside the `data` folder.
4. Run the data cleaning script:
```bash
    python scripts/scripts_for_data_proccecing/clean_data.py
```

## Database Loading

You need to have PostgreSQL, MongoDB, and Neo4j running locally.
1. Navigate to the folder: scripts/db_create_load_data.
2. Open each .py script in this folder.
3. Configuration: At the beginning of each script, locate the configuration section. You must update the connection parameters (e.g., database user password) to match your local setup.
4. Once configured, run the shell scripts to create tables/collections and load the data
```bash
    # Run all loading scripts
./load_data_psql.sh
./load_data_mongodb.sh
./load_data_neo4j.sh
```
*Note: These scripts may take some time depending on your machine specifications.*
**Neo4j Warning**: The Neo4j loading script uses the CREATE operator. If the script fails and you need to run it again, you must clear the data from the Neo4j database first. Otherwise, the script may fail due to existing constraints or data.

## Running Queries

After successfully loading the data, you can execute queries against the databases.

1. Navigate to the specific query folders:
```
    scripts/psql_queries
    scripts/mongo_queries
    scripts/neo4j_queries
 ```
2. Configuration: Similar to the loading scripts, you must update the database connection configuration at the start of each Python script.
3. Execution: It is recommended to run the wrapper scripts (e.g., `run_q*_[dbname].py`) using Python:
```bash
#example
  python scripts/psql_queries/run_q1_psql.py
```

These scripts will display the execution time and save the results to the `output` folder.

## Benchmarking

To get same experiments results, you need to run all 4 benchmark scripts.

1. Benchmark scripts are available in:
```
    scripts/psql_queries/benchmark_psql.py
    scripts/mongo_queries/benchmark_mongo.py
    scripts/neo4j_queries/benchmark_neo4j.py
    scripts/final_benchmark.py
 ```

2. Configuration: Update the database connection settings at the start of each script.
3. Execution: Run the scripts using Python.
Each script will run every query 5 times for the respective database.
Results will be saved to the `output` folder.
import re

import re

import re

def extract_sql_components(query):
    # Remove comments and normalize whitespace
    query = re.sub(r'--.*$|\s+', ' ', query, flags=re.MULTILINE).strip()
    query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)  # Remove multi-line comments

    # Extract table names
    table_pattern = r'\b(?:FROM|JOIN|INTO|UPDATE|INSERT\s+INTO)\s+(\w+(?:\s*\.\s*\w+)?(?:\s+(?:AS\s+)?\w+)?(?:\s*,\s*\w+(?:\s*\.\s*\w+)?(?:\s+(?:AS\s+)?\w+)?)*)'
    tables = set()
    for match in re.finditer(table_pattern, query, re.IGNORECASE):
        table_clause = match.group(1)
        table_names = re.findall(r'\b(\w+)(?:\s*\.\s*\w+)?(?:\s+(?:AS\s+)?\w+)?', table_clause)
        tables.update(table_names)

    # Extract column names
    column_pattern = r'\bSELECT\s+(.*?)(?:\s+FROM|\s*$)'
    columns_match = re.search(column_pattern, query, re.IGNORECASE | re.DOTALL)
    
    if columns_match:
        columns = columns_match.group(1)
        if '*' in columns:
            columns = ['*']
        else:
            # Split columns and clean them
            columns = re.findall(r'(\w+(?:\s*\.\s*\w+)?)\s*(?:,|$|\s+AS\s+)', columns)
            columns = [col.split('.')[-1] for col in columns]
    else:
        # Handle INSERT, UPDATE, DELETE statements
        column_matches = re.findall(r'\b(?:INSERT\s+INTO|UPDATE).*?\(([^)]+)\)', query, re.IGNORECASE)
        if column_matches:
            columns = [col.strip() for col in column_matches[0].split(',')]
        else:
            columns = []

    # Handle WITH clause
    with_pattern = r'\bWITH\s+(\w+(?:\s*\([^)]*\))?\s+AS\s*\([^)]+\)\s*,?\s*)+' 
    with_match = re.search(with_pattern, query, re.IGNORECASE)
    if with_match:
        cte_names = re.findall(r'\b(\w+)(?:\s*\([^)]*\))?\s+AS', with_match.group(0), re.IGNORECASE)
        tables.update(cte_names)

    return list(tables), list(set(columns))

# Example usage
queries = [
    "SELECT r.rule_id, k.robinhood FROM lauda WHERE xyz condition",
    "SELECT t1.col1, t2.col2 AS alias FROM table1 t1 JOIN table2 t2 ON t1.id = t2.id",
    "SELECT * FROM users",
    "INSERT INTO users (name, email) VALUES ('John', 'john@example.com')",
    "UPDATE employees SET salary = 5000 WHERE id = 1",
    "SELECT COUNT(*) AS total FROM (SELECT DISTINCT user_id FROM orders) AS subquery",
    "WITH cte AS (SELECT id FROM customers) SELECT cte.id, orders.order_id FROM cte JOIN orders ON cte.id = orders.customer_id"
]

for i, query in enumerate(queries, 1):
    tables, columns = extract_sql_components(query)
    print(f"\nQuery {i}:")
    print("Table names:", tables)
    print("Column names:", columns)

# Example usage
queries = [
    "SELECT r.rule_id, k.robinhood FROM lauda WHERE xyz condition",
    "SELECT t1.col1, t2.col2 AS alias FROM table1 t1 JOIN table2 t2 ON t1.id = t2.id",
    "SELECT * FROM users",
    "INSERT INTO users (name, email) VALUES ('John', 'john@example.com')",
    "UPDATE employees SET salary = 5000 WHERE id = 1",
    "SELECT COUNT(*) AS total FROM (SELECT DISTINCT user_id FROM orders) AS subquery",
    "WITH cte AS (SELECT id FROM customers) SELECT cte.id, orders.order_id FROM cte JOIN orders ON cte.id = orders.customer_id"
]

for i, query in enumerate(queries, 1):
    tables, columns = extract_sql_components(query)
    print(f"\nQuery {i}:")
    print("Table names:", tables)
    print("Column names:", columns)

# Example usage
queries = [
    "SELECT r.rule_id, k.robinhood FROM lauda WHERE xyz condition",
    "SELECT t1.col1, t2.col2 AS alias FROM table1 t1 JOIN table2 t2 ON t1.id = t2.id",
    "SELECT * FROM users",
    "INSERT INTO users (name, email) VALUES ('John', 'john@example.com')",
    "UPDATE employees SET salary = 5000 WHERE id = 1",
    "SELECT COUNT(*) AS total FROM (SELECT DISTINCT user_id FROM orders) AS subquery",
    "WITH cte AS (SELECT id FROM customers) SELECT cte.id, orders.order_id FROM cte JOIN orders ON cte.id = orders.customer_id"
]

for i, query in enumerate(queries, 1):
    tables, columns = extract_sql_components(query)
    print(f"\nQuery {i}:")
    print("Query:", query)
    print("Table names:", tables)
    print("Column names:", columns)

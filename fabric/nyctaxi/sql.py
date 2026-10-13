"""Run a T-SQL query against the lakehouse SQL endpoint with an az CLI token. Usage: uv run --no-project --with pyodbc python sql.py "SELECT ..." """
import struct
import sys

import pyodbc

import fabric

SERVER = fabric.call("GET", f"/workspaces/{fabric.WS}/lakehouses/{fabric.LH_ID}")[2][
    "properties"]["sqlEndpointProperties"]["connectionString"]
token = fabric.az_token("https://database.windows.net").encode("utf-16-le")
driver = [d for d in pyodbc.drivers() if "SQL Server" in d and "ODBC" in d][-1]
conn = pyodbc.connect(f"Driver={{{driver}}};Server={SERVER},1433;Database={fabric.LH_NAME};Encrypt=yes",
                      attrs_before={1256: struct.pack(f"<I{len(token)}s", len(token), token)})
cur = conn.cursor()
cur.execute(sys.argv[1])
print([c[0] for c in cur.description])
for row in cur.fetchall():
    print(list(row))

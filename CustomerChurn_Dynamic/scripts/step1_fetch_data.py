import pyodbc
import pandas as pd
from pathlib import Path

def fetch_data():
    try:
        server = r'DELL-BVOELMRLLM\SQLEXPRESS'
        database = 'db_churn'
        table_name = 'stg_Churn'  # Without dbo.

        # Check if data already exists
        output_path = Path.cwd() / 'data' / 'fetched_data.xlsx'
        if output_path.exists():
            print(f"✅ Data file already exists at {output_path}")
            return

        try:
            conn = pyodbc.connect(
                f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;',
                timeout=10
            )

            # Check if table exists
            tables = pd.read_sql("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES", conn)
            if table_name not in tables['TABLE_NAME'].values:
                raise ValueError(f"Table '{table_name}' not found in database")

            # Check row count
            count = pd.read_sql(f"SELECT COUNT(*) AS cnt FROM dbo.{table_name}", conn).iloc[0,0]
            print(f"Found {count} records in {table_name}")

            if count == 0:
                raise ValueError("Table is empty - no data to export")

            # Fetch all data
            df = pd.read_sql(f"SELECT * FROM dbo.{table_name}", conn)

            # Save to Excel in your project folder data/
            output_path.parent.mkdir(exist_ok=True)
            df.to_excel(output_path, index=False)

            if output_path.stat().st_size < 1024:
                raise ValueError("Exported file is too small - possible export failure")

            print(f"✅ Success! {len(df)} records saved to {output_path}")

        except Exception as db_error:
            print(f"⚠️  Database unavailable: {db_error}")
            if output_path.exists():
                print(f"✅ Using existing data file from {output_path}")
            else:
                raise

    except Exception as e:
        print(f"❌ Failed: {e}")
        print("\nTroubleshooting:")
        print("1. Verify table name is correct")
        print("2. Check SQL Server Management Studio for data")
        print("3. Try a simpler query like 'SELECT TOP 10 * FROM table'")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fetch_data()

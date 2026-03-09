from sqlalchemy import create_engine

SERVER = r'.\SQLEXPRESS'
DATABASE = 'CustomerChurnDB'

CONNECTION_STRING = f'mssql+pyodbc://{SERVER}/{DATABASE}?driver=ODBC+Driver+17+for+SQL+Server'


engine = create_engine(
    CONNECTION_STRING,
)
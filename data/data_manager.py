import pandas as pd
import os
from typing import List
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import table as sql_table, column as sql_column

# --- Database Setup ---
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, 'tradeflow.db')

# Optional PostgreSQL/Timescale configuration via env vars
PG_HOST = os.getenv('PG_HOST')
PG_PORT = os.getenv('PG_PORT', '5432')
PG_DB = os.getenv('PG_DB')
PG_USER = os.getenv('PG_USER')
PG_PASSWORD = os.getenv('PG_PASSWORD')
PG_SSLMODE = os.getenv('PG_SSLMODE', 'prefer')

class DataManager:
    """
    Handles all database operations for market data using a SQLAlchemy engine.
    """
    def __init__(self, db_path=DB_PATH):
        """Initializes the DataManager, creating the DB and table if they don't exist."""
        from core.lock import FileLock  # Local import to resolve path issues when run directly
        
        self.db_path = db_path
        self.lock = FileLock(self.db_path + '.lock')
        self.engine = None  # Initialize engine as None

        try:
            with self.lock:
                print("Lock acquired, initializing database...")
                if PG_HOST and PG_DB and PG_USER:
                    # PostgreSQL/Timescale engine
                    pg_url = (
                        f'postgresql+psycopg2://{PG_USER}:{PG_PASSWORD or ""}'
                        f'@{PG_HOST}:{PG_PORT}/{PG_DB}?sslmode={PG_SSLMODE}'
                    )
                    self.engine = create_engine(pg_url)
                else:
                    # Fallback to SQLite local file
                    self.engine = create_engine(
                        f'sqlite:///{self.db_path}',
                        connect_args={'timeout': 15}
                    )
                self._initialize_database()
        except TimeoutError as e:
            print(f"Could not acquire database lock: {e}")
            # Depending on desired behavior, you might want to exit or disable DB features
            raise
        except Exception as e:
            print(f"An error occurred during DataManager initialization: {e}")
            raise

    def _initialize_database(self):
        """
        Creates the database file and the necessary tables if they
        do not already exist, using the SQLAlchemy engine.
        """
        try:
            # The engine is now guaranteed to be initialized here
            inspector = inspect(self.engine)
            if not inspector.has_table('market_data'):
                with self.engine.connect() as conn:
                    if self.engine.url.get_backend_name().startswith('postgresql'):
                        # Enable TimescaleDB extension and create hypertable
                        conn.execute(text('CREATE EXTENSION IF NOT EXISTS timescaledb'))
                        conn.execute(text('''
                            CREATE TABLE market_data (
                                timestamp TIMESTAMPTZ NOT NULL,
                                symbol TEXT NOT NULL,
                                timeframe TEXT NOT NULL,
                                open DOUBLE PRECISION NOT NULL,
                                high DOUBLE PRECISION NOT NULL,
                                low DOUBLE PRECISION NOT NULL,
                                close DOUBLE PRECISION NOT NULL,
                                volume BIGINT,
                                PRIMARY KEY (timestamp, symbol, timeframe)
                            )
                        '''))
                        conn.execute(text('SELECT create_hypertable(''market_data'', ''timestamp'', if_not_exists => TRUE)'))
                        conn.execute(text('CREATE INDEX IF NOT EXISTS idx_symbol_timeframe ON market_data (symbol, timeframe)'))
                    else:
                        conn.execute(text('''
                            CREATE TABLE market_data (
                                timestamp DATETIME NOT NULL,
                                symbol TEXT NOT NULL,
                                timeframe TEXT NOT NULL,
                                open REAL NOT NULL,
                                high REAL NOT NULL,
                                low REAL NOT NULL,
                                close REAL NOT NULL,
                                volume INTEGER,
                                PRIMARY KEY (timestamp, symbol, timeframe)
                            )
                        '''))
                        conn.execute(text('''
                            CREATE INDEX idx_symbol_timeframe
                            ON market_data (symbol, timeframe)
                        '''))
                    conn.commit()
                print("Database table 'market_data' created successfully")
            else:
                print("Database already initialized")
        except Exception as e:
            print(f"Database initialization failed: {e}")
            raise

    def save_bars(self, symbol: str, timeframe: str, bars_df: pd.DataFrame):
        """
        Saves a DataFrame of bar data to the database using an UPSERT strategy.
        Now primarily intended for saving high-resolution (1-min) data.
        """
        if self.engine is None:
            print("Database engine not initialized. Cannot save bars.")
            return

        if not isinstance(bars_df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame index must be a DatetimeIndex.")

        df_copy = bars_df.copy()
        
        # ---> START FIX: Force DataFrame to match the database schema <---
        
        # 1. Reset index to make 'timestamp' a column to work with
        df_copy.reset_index(inplace=True)
        
        # 2. Define the exact columns of the database table
        db_schema = {
            'timestamp': 'timestamp', 'date': 'timestamp', # Allow 'date' as an alias for 'timestamp'
            'open': 'open', 'Open': 'open',
            'high': 'high', 'High': 'high',
            'low': 'low', 'Low': 'low',
            'close': 'close', 'Close': 'close',
            'volume': 'volume', 'Volume': 'volume'
        }
        df_copy.rename(columns=db_schema, inplace=True)

        # 3. Add symbol and timeframe
        df_copy['symbol'] = symbol
        df_copy['timeframe'] = '1min' # Always save as base timeframe

        # 4. Keep only the columns that exist in the database and are required.
        final_columns = ['timestamp', 'symbol', 'timeframe', 'open', 'high', 'low', 'close', 'volume']
        cols_to_keep = [col for col in final_columns if col in df_copy.columns]
        df_copy = df_copy[cols_to_keep]
        # ---> END FIX <---
        
        try:
            if self.engine.url.get_backend_name().startswith('postgresql'):
                # Use PostgreSQL upsert
                self._pg_bulk_upsert('market_data', df_copy, conflict_cols=['timestamp','symbol','timeframe'])
            else:
                df_copy.to_sql(
                    'market_data', 
                    self.engine, 
                    if_exists='append', 
                    index=False,
                    method=self._sqlite_upsert
                )
            print(f"Successfully saved {len(df_copy)} base bars for {symbol}.")
        except Exception as e:
            print(f"Failed to save bars for {symbol}: {e}")
            raise

    @staticmethod
    def _sqlite_upsert(table, conn, keys, data_iter):
        """
        Performs an 'INSERT ... ON CONFLICT DO UPDATE' for SQLite.
        This is compatible with the SQLAlchemy connection provided by pandas.
        """
        sql_tbl = sql_table(table.name, *[sql_column(k) for k in keys])
        
        stmt = sqlite_insert(sql_tbl).values(list(data_iter))
        
        # The pandas `table` object does not have a `primary_key` attribute.
        # We know the primary keys for our 'market_data' table, so we specify them directly.
        primary_keys = ['timestamp', 'symbol', 'timeframe']
        
        update_cols = {
            c.name: c for c in stmt.excluded if c.name not in primary_keys
        }
        
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=primary_keys,
            set_=update_cols
        )
        conn.execute(upsert_stmt)

    def _pg_bulk_upsert(self, table_name: str, df: pd.DataFrame, conflict_cols: List[str]):
        """Efficient bulk upsert into PostgreSQL using native ON CONFLICT.
        Requires SQLAlchemy connection and psycopg2 driver.
        """
        if df.empty:
            return
        cols = list(df.columns)
        sql_tbl = sql_table(table_name, *[sql_column(c) for c in cols])
        records = df.to_dict(orient='records')
        stmt = pg_insert(sql_tbl).values(records)
        update_cols = {c: stmt.excluded[c] for c in cols if c not in conflict_cols}
        upsert_stmt = stmt.on_conflict_do_update(index_elements=conflict_cols, set_=update_cols)
        with self.engine.begin() as conn:
            conn.execute(upsert_stmt)

    def fetch_bars(self, symbol: str, timeframe: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetches high-resolution (1-min) data and resamples it to the desired timeframe.
        """
        if self.engine is None:
            print("Database engine not initialized. Cannot fetch bars.")
            return pd.DataFrame()

        # Always fetch the base '1min' data from the database
        base_timeframe = '1min'
        query = text("""
            SELECT timestamp, open, high, low, close, volume
            FROM market_data
            WHERE symbol = :symbol AND timeframe = :base_timeframe AND timestamp BETWEEN :start_date AND :end_date
            ORDER BY timestamp ASC
        """)
        try:
            params = {"symbol": symbol, "base_timeframe": base_timeframe, "start_date": start_date, "end_date": end_date}
            with self.engine.connect() as conn:
                df = pd.read_sql_query(query, conn, params=params)
            
            if df.empty:
                return pd.DataFrame()

            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # If the requested timeframe is the same as the base, just rename and return
            if timeframe == base_timeframe:
                df.rename(columns={
                    'open': 'Open', 'high': 'High', 'low': 'Low',
                    'close': 'Close', 'volume': 'Volume'
                }, inplace=True)
                print(f"Successfully fetched {len(df)} base bars for {symbol} ({timeframe}).")
                return df

            # --- Resampling Logic ---
            # Define the aggregation rules for resampling
            agg_rules = {
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }
            
            # Resample the DataFrame to the target timeframe
            resampled_df = df.resample(timeframe).agg(agg_rules)
            
            # Drop rows with no data (e.g., weekends, holidays)
            resampled_df.dropna(inplace=True)

            resampled_df.rename(columns={
                'open': 'Open', 'high': 'High', 'low': 'Low',
                'close': 'Close', 'volume': 'Volume'
            }, inplace=True)

            print(f"Successfully fetched and resampled {len(resampled_df)} bars for {symbol} to {timeframe}.")
            return resampled_df

        except Exception as e:
            print(f"Failed to fetch or resample bars for {symbol}: {e}")
            return pd.DataFrame()

# You can run this file directly to test its functionality
if __name__ == '__main__':
    # To make the script runnable, we need to adjust the Python path
    # to ensure that relative imports work correctly.
    if __package__ is None:
        import sys
        import os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    print("--- Testing DataManager ---")
    
    # 1. Initialize the manager
    # This will now work because the import is local to __init__
    data_manager = DataManager()
    
    # 2. Create some fake data to save
    test_symbol = 'TEST'
    # We save as 1-minute data, our new base format.
    base_timeframe = '1min' 
    
    date_rng = pd.date_range(start='2023-01-01 09:30:00', end='2023-01-01 16:00:00', freq='min')
    fake_data = {
        'Open': [150 + i*0.01 for i in range(len(date_rng))],
        'High': [150.05 + i*0.01 for i in range(len(date_rng))],
        'Low': [149.95 + i*0.01 for i in range(len(date_rng))],
        'Close': [150.02 + i*0.01 for i in range(len(date_rng))],
        'Volume': [1000 + i*10 for i in range(len(date_rng))]
    }
    test_df = pd.DataFrame(index=date_rng, data=fake_data)
    
    # 3. Save the base 1-minute data
    data_manager.save_bars(test_symbol, base_timeframe, test_df)
    
    # 4. Fetch and resample to a longer timeframe (e.g., 15min)
    resampled_timeframe = '15min'
    fetched_df = data_manager.fetch_bars(test_symbol, resampled_timeframe, '2023-01-01', '2023-01-02')
    
    print(f"\n--- Original 1-minute data (first 5 rows) ---")
    print(test_df.head())
    
    print(f"\n--- Fetched and Resampled {resampled_timeframe} DataFrame ---")
    print(fetched_df.head())
    
    # Verification
    first_15min_high = test_df.head(15)['High'].max()
    if fetched_df.iloc[0]['High'] == first_15min_high:
         print(f"\nSUCCESS: Resampling logic appears correct. High matches ({first_15min_high}).")
    else:
        print("\nERROR: Resampling logic failed.")
        
    # Test fetching the base timeframe directly
    base_df = data_manager.fetch_bars(test_symbol, base_timeframe, '2023-01-01', '2023-01-02')
    if not base_df.empty:
        print("\nSUCCESS: Fetching base timeframe directly is working.")
    else:
        print("\nERROR: Failed to fetch base timeframe.")

    # 6. Test updating data
    print("\n--- Testing Upsert ---")
    test_df.iloc[0, 3] = 999.99 # Modify the 'Close' of the first bar
    data_manager.save_bars(test_symbol, base_timeframe, test_df.head(1))
    updated_df = data_manager.fetch_bars(test_symbol, base_timeframe, '2023-01-01', '2023-01-02')
    print("\n--- Updated DataFrame ---")
    print(updated_df.head())
    if updated_df.iloc[0]['Close'] == 999.99:
        print("\nSUCCESS: Upsert functionality is working.")
    else:
        print("\nERROR: Upsert functionality failed.") 
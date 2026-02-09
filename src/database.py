"""Database connection and utilities"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://agent:agent_password@localhost:5432/pipeline_data"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)


def init_database():
    """Initialize database tables"""
    with engine.connect() as conn:
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS pipeline_data (
                id SERIAL PRIMARY KEY,
                smx_location_id INTEGER,
                gas_day DATE,
                cycle_lookup VARCHAR(50),
                cycle_desc VARCHAR(100),
                pipeline_name VARCHAR(255),
                location_name VARCHAR(255),
                flow_indicator VARCHAR(10),
                total_scheduled_quantity DOUBLE PRECISION,
                design_capacity DOUBLE PRECISION,
                operating_capacity DOUBLE PRECISION,
                operationally_available_capacity DOUBLE PRECISION,
                location_category VARCHAR(100),
                region_nat_gas VARCHAR(100),
                sub_region_nat_gas VARCHAR(100),
                location_county_composite VARCHAR(255),
                location_county VARCHAR(255),
                location_state_ab VARCHAR(10),
                location_latitude DOUBLE PRECISION,
                location_longitude DOUBLE PRECISION,
                flow_indicator_long VARCHAR(50),
                rec_del INTEGER,
                mean_basis_desc VARCHAR(100),
                interconnect_location_id VARCHAR(100),
                interconnect_company_name VARCHAR(255),
                interconnect_location_name VARCHAR(255),
                smx_tsp_id VARCHAR(100),
                source VARCHAR(100),
                created_dt TIMESTAMP,
                posting_dt TIMESTAMP
            )
        """)
        )
        conn.commit()

        # Create indexes for common queries
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_pipeline_name ON pipeline_data(pipeline_name)
        """)
        )
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_gas_day ON pipeline_data(gas_day)
        """)
        )
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_region ON pipeline_data(region_nat_gas)
        """)
        )
        conn.commit()

    print("✓ Database initialized")


def load_parquet_to_db(parquet_path: str, use_copy: bool = True, chunk_size: int = 500000):
    """Load parquet file into PostgreSQL"""
    print(f"Loading {parquet_path} into database...")

    df = pd.read_parquet(parquet_path)
    total_rows = len(df)

    # Check if data already exists
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM pipeline_data"))
        existing_rows = result.scalar()

        if existing_rows > 0:
            print(f"✓ Database already contains {existing_rows:,} rows, skipping load")
            return

    if use_copy:
        import io

        print("Using COPY method (faster)...")
        columns = ", ".join(df.columns)

        # Process in chunks to avoid memory issues
        for i in range(0, total_rows, chunk_size):
            chunk = df.iloc[i : i + chunk_size]

            # Convert chunk to CSV in memory
            buffer = io.StringIO()
            chunk.to_csv(buffer, index=False, header=False, na_rep="\\N")
            buffer.seek(0)

            # Get raw connection for COPY
            raw_conn = engine.raw_connection()
            cursor = raw_conn.cursor()

            try:
                cursor.copy_expert(
                    f"COPY pipeline_data ({columns}) FROM STDIN WITH (FORMAT CSV, NULL '\\N')",
                    buffer,
                )
                raw_conn.commit()
            except Exception as e:
                raw_conn.rollback()
                raise e
            finally:
                cursor.close()
                raw_conn.close()

            print(f"  Loaded {min(i + chunk_size, total_rows):,} / {total_rows:,} rows")

        print(f"✓ Loaded {total_rows:,} rows into database using COPY")
    else:
        # Fallback to batch inserts
        batch_size = 50000
        for i in range(0, total_rows, batch_size):
            batch = df.iloc[i : i + batch_size]
            batch.to_sql(
                "pipeline_data",
                engine,
                if_exists="append",
                index=False,
                method="multi",
            )
            print(f"  Loaded {min(i + batch_size, total_rows):,} / {total_rows:,} rows")

        print(f"✓ Loaded {total_rows:,} rows into database")


def get_dataframe_from_db(query: str = None, limit: int = None) -> pd.DataFrame:
    """Get data from database as DataFrame"""
    if query is None:
        query = "SELECT * FROM pipeline_data"
        if limit:
            query += f" LIMIT {limit}"

    return pd.read_sql(query, engine)


def execute_query(query: str) -> pd.DataFrame:
    """Execute a SQL query and return results as DataFrame"""
    return pd.read_sql(query, engine)


def get_table_info() -> dict:
    """Get information about the pipeline_data table"""
    with engine.connect() as conn:
        # Row count
        result = conn.execute(text("SELECT COUNT(*) FROM pipeline_data"))
        row_count = result.scalar()

        # Column info
        result = conn.execute(
            text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'pipeline_data'
            ORDER BY ordinal_position
        """)
        )
        columns = [(row[0], row[1]) for row in result]

    return {
        "row_count": row_count,
        "columns": columns,
    }

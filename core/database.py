from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

username = os.getenv("db_username")
password = os.getenv("db_pass")

# ----------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------
# REPLACE with your actual MySQL credentials
# Format: mysql+pymysql://<username>:<password>@<host>/<db_name>
DATABASE_URL = f"mysql+pymysql://{username}:{password}@localhost/judgemenot_db"

# ----------------------------------------------------------------
# ENGINE SETUP
# ----------------------------------------------------------------
# pool_recycle=3600 prevents MySQL "Gone Away" errors for long events
engine = create_engine(DATABASE_URL, pool_recycle=3600)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency function to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
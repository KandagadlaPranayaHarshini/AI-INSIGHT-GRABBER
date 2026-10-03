from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Update 'root' and 'password' with your local MySQL password if needed
MYSQL_URL = "mysql+pymysql://root:root@localhost:3306/insights"

engine = create_engine(
    MYSQL_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Modern SQLAlchemy 2.0 Base declaration (resolves MovedIn20Warning)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
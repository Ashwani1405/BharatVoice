import databases
import sqlalchemy
from app.config import settings

database = databases.Database(settings.DATABASE_URL)
metadata = sqlalchemy.MetaData()

# SQLAlchemy models will be defined in app.models and bound to this metadata.
engine = sqlalchemy.create_engine(
    # create_engine expects a synchronous URL for schema definitions, 
    # but since we're only using asyncpg for the runtime app, we can just declare the metadata here.
    # We will let databases handle the async connections.
    settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql") 
)

def fetch_one(query, values=None):
    return database.fetch_one(query=query, values=values)

def fetch_all(query, values=None):
    return database.fetch_all(query=query, values=values)

def execute(query, values=None):
    return database.execute(query=query, values=values)

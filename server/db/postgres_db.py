from core.config import settings

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# models
from .models.papers import Paper, Base
from .models.citation_edges import CitationEdge
from .models.author_scores import AuthorScore


DATABASE_URL=settings.POSTGRES_URL

engine=create_engine(DATABASE_URL,echo=False)
    
SessionLocal= sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)

def clear_db():
    Base.metadata.drop_all(engine)

if __name__ == "__main__":
    init_db()
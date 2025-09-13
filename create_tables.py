from app.database import Base, engine
from app import models

# Create all tables from your SQLAlchemy models
Base.metadata.create_all(bind=engine)

print("✅ All tables created successfully!")

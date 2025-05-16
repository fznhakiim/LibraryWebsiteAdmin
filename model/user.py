from sqlalchemy import Column, Integer, String
from utils.database import Base  # Sesuai struktur folder kamu

class User(Base):
    __tablename__ = "User"  # Sesuaikan dengan nama tabel di database kamu

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)

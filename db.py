from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///users.db', echo=True)
Base = declarative_base()
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String)
    ref_url = Column(String)
    ref_count = Column(Integer, default = 0)
    balance = Column(Integer, default = 0)
    wallet = Column(String, default = "")

    def __repr__(self):
        return f"<User(name='{self.name}', age={self.age})>"

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

from email.policy import default

from flask_sqlalchemy.session import Session
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Table
from sqlalchemy.orm import relationship, sessionmaker, declarative_base

# Define the database connection string.  Use an in-memory database for testing.
TEST_DB_URL = "sqlite:///:memory:"  # This could also be in a config.py

engine = create_engine(TEST_DB_URL)

Session = sessionmaker(bind=engine)
session = Session()


# Base for declarative models
Base = declarative_base()

# Define the association table
class UserMovie(Base):
    __tablename__ = 'user_movies'
    id = Column(Integer, primary_key=True)
    user_id = Column('user_id', Integer, ForeignKey('users.id'))
    movie_id = Column('movie_id', Integer, ForeignKey('movies.id'))
    rating = Column(Float)
    user_rating = Column('user_rating', Float, default=0.0 )# Add the rating column here

    def __repr__(self):
        result = ""
        for user in session.query(User).all():
            result += (f"<UserMovie(user_id={self.user_id}, movie_id={self.movie_id}, "
                       f"rating={self.rating})>\n")
        return result

# Define the User model
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    movies = relationship("Movie", secondary="user_movies",
                          back_populates="users")

    def __repr__(self):
        return f"<User(name='{self.name}', id={self.id if self.id else 'None'})>"


# Define the Movie model
class Movie(Base):
    __tablename__ = 'movies'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    director = Column(String)
    year = Column(Integer)
    poster = Column(String)
    rating = Column(Float)
    users = relationship("User", secondary="user_movies",
                         back_populates="movies")

    def __repr__(self):
        return f"<Movie(name='{self.name}', id={self.id if self.id else 'None'})>"


if __name__ == "__main__":
    # This block is for creating the tables if you want to do it directly.
    Base.metadata.create_all(engine)
    print("Tables created!")
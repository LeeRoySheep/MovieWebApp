
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from typing import List, Dict, Any, Type

from data_models import Base, User, Movie, UserMovie
from movie_api import OMDBClient
from datamanager.data_manager_interface import DataManagerInterface


# Define the database connection string.
TEST_DB_URL = "sqlite:///:memory:"



# Data manager class to handle database operations
class SQliteDataManager(DataManagerInterface):
    def __init__(self, db_url: str):
        """
        Initialize the data manager with a database URL.
        """
        self.engine = create_engine(db_url)
        self.SessionFactory = sessionmaker(bind=self.engine, expire_on_commit=False)
        Base.metadata.create_all(self.engine)

    @contextmanager
    def get_db(self):
        """
        Provide a database session as a context manager.
        """
        session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise ConnectionError("Database connection error!")
        finally:
            session.close()


    @property
    def users(self) -> list[Type[User]]:
        """
        Getter for users.
        Returns: a list of User objects.
        """
        with self.SessionFactory() as session:
            users = session.query(User).all()
            return users


    def get_user(self, user_id: int) -> List[User] | None:
        """
        Get a user by ID.
        :param user_id:
        :return: User
        """
        with self.SessionFactory() as session:
            user = session.query(User).filter_by(id=user_id).first()
            return user

    def add_user(self, user: User) -> None:
        """
        Add a user to the database.
        """
        with self.SessionFactory() as session:
            session.add(user)
            session.commit()


    @property
    def movies(self) -> list[Type[Movie]]:
        """
        Getter for movies.
        Returns: a list of Movie objects
        """
        with self.SessionFactory() as session:
            return session.query(Movie).all()

    def set_user_movies(self, user_id: int, movie_id: int, user_rating: float = 0.0)\
            -> str | None:
        """
        Set (add) a movie to a user's list with a rating,
        either create a new association or update the rating if it exists (self-contained session).
        """

        with self.SessionFactory() as session:
            user = session.query(User).filter_by(id=user_id).first()
            movie = session.query(Movie).filter_by(id=movie_id).first()

            if user and movie:
                existing_associations = session.query(UserMovie).filter_by(
                    user_id=user_id, movie_id=movie_id
                ).first()  #check if the association already exists
                if existing_associations:
                    #  existing association update
                    session.query(UserMovie).filter_by(user_id=user_id, movie_id=movie_id).update(
                        {"user_rating": user_rating}
                    )
                else:
                    # create new association
                    association = UserMovie(user_id=user_id, movie_id=movie_id,
                                            user_rating=user_rating)
                    session.add(association)

                session.commit()  # Commit within the function


            elif movie is None:
                return "Failed to add movie, check ID and try again!"

            else:
                return "User not found."

    def get_user_movies(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get movies for a specific user with their ratings.
        Returns: A list of dictionaries, where each dictionary contains movie details
        (name, director, year, poster) and the user's rating.
        """
        with self.SessionFactory() as session:
            user_movies = session.query(UserMovie).filter_by(user_id=user_id).all()
            if user_movies:
                movies_with_ratings = []
                for association in user_movies:
                    movie = session.query(Movie).filter_by(id=association.movie_id).first()
                    if movie:
                        movies_with_ratings.append({
                            "id": movie.id,
                            "name": movie.name,
                            "director": movie.director,
                            "year": movie.year,
                            "poster": movie.poster,
                            "genre": movie.genre,
                            "country": movie.country,
                            "plot": movie.plot,
                            "rating": movie.rating,
                            "user_rating": association.user_rating,
                            "user_comment": association.user_comment if association.user_comment
                            else None
                        })
                return movies_with_ratings
            return []


    def get_user_movie(self, user_id: int, movie_id: int) -> Dict[str, Any]:
        with self.SessionFactory() as session:
            user_movie = session.query(UserMovie).filter_by(user_id=user_id, movie_id=movie_id).first()
            if user_movie:
                movie = session.query(Movie).filter_by(id=movie_id).first()
                return {
                    "id": movie.id,
                    "name": movie.name,
                    "director": movie.director,
                    "year": movie.year,
                    "poster": movie.poster,
                    "genre": movie.genre,
                    "country": movie.country,
                    "plot": movie.plot,
                    "rating": movie.rating,
                    "user_rating": user_movie.user_rating,
                    "user_comment": user_movie.user_comment if user_movie.user_comment else None
                }
            return {}


    def set_movie(self, movie_title: str) -> Type[Movie] | Movie:
        """
        Add a new movie to the database.
        :param movie_title: The title of the movie to add.
        """
        with self.SessionFactory() as session:
            movie = session.query(Movie).filter_by(name=movie_title).first()
            if movie:
                return movie
            new_movie = OMDBClient().get_movie(title=movie_title)
            if new_movie is None:
                raise ValueError("Movie not found")
            movie = Movie(**new_movie)
            session.add(movie)
            session.commit()
        return movie

    def update_user_movie(self, user_id: int, movie_id: int, update_data: dict) -> dict | None:
        with self.SessionFactory() as session:
            movie = session.query(Movie).filter_by(id=movie_id).first()
            if movie:
                session.query(UserMovie).filter_by(user_id=user_id,
                                                   movie_id=movie_id).update(update_data)
                session.commit()
                return {
                    "id": movie.id,
                    "name": movie.name,
                    "director": movie.director,
                    "year": movie.year,
                    "poster": movie.poster,
                    "genre": movie.genre,
                    "country": movie.country,
                    "plot": movie.plot,
                    "rating": movie.rating,
                    "user_rating": update_data["user_rating"] if "user_rating" in update_data
                    else 0.0,
                    "user_comment": update_data["user_comment"] if "user_comment" in update_data
                    else None
                }
            return None

    def delete_movie(self, movie_id: int) -> bool:
        """
        Delete a movie from the movies table in the database
        :param movie_id:
        :return:
        """
        with self.SessionFactory() as session:
            movie = session.query(Movie).filter_by(id = movie_id).first()
            if movie:
                session.flush()  # Make sure pending updates are flushed
                session.query(UserMovie).filter_by(movie_id = movie_id).delete()
                session.query(Movie).filter_by(id = movie_id).delete()
                session.commit()
                return True
            return False

    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user from the users table in the database
        :param user_id:
        :return:
        """
        with self.SessionFactory() as session:
            user = session.query(User).filter_by(id = user_id).first()
            if user:
                session.flush()  # Make sure pending updates are flushed
                session.query(UserMovie).filter_by(user_id = user_id).delete()
                session.query(User).filter_by(id = user_id).delete()
                session.commit()
                return True
            return False


    def delete_user_movie(self, user_id: int, movie_id: int) -> bool:
        with self.SessionFactory() as session:
            association = session.query(UserMovie).filter_by(user_id=user_id, movie_id=movie_id).first()
            if association:
                session.delete(association)
                session.commit()
                return True
            return False

    def get_movie(self, movie_id: int) -> Movie | None:
        """
        Get a movie from the movies table in the database
        :param movie_id:
        :return:
        """
        with self.SessionFactory() as session:
            movie = session.query(Movie).filter_by(id = movie_id).first()
            return movie

def main():
    data_manager = SQliteDataManager("sqlite:///movie_app.db")

    with data_manager.SessionFactory() as session:
        # Create some users
        user1 = User(name="Alice")
        user2 = User(name="Bob")
        data_manager.add_user(user1)
        data_manager.add_user(user2)
        session.add_all([user1, user2])
        session.commit()

        # Create some movies
        movie1 = data_manager.set_movie("The Matrix")
        movie2 = data_manager.set_movie("Interstellar")

        # Associate movies with users and assign ratings
        print(f"user1:{user1}, movie1:{movie1}")
        data_manager.set_user_movies(user1.id, movie1.id)
        print(data_manager.get_user_movies(user1.id))
        data_manager.set_user_movies(user1.id, movie2.id, 8.5)
        data_manager.set_user_movies(user2.id, movie2.id, 9.2)

        # Get and print user movies (use a new session for querying)

        print("Alice's movies:", data_manager.get_user_movies(user1.id))
        print("Bob's movies:", data_manager.get_user_movies(user2.id))

        # Get and print all movies
        print("All movies:", session.query(Movie).all())

        # Example of updating a movie (use a new session)
        updated_movie = data_manager.update_user_movie(user1.id, movie1.id,
                                                      {"user_rating":
                                                          7.2})
        print("Updated movie:", updated_movie)

        # Example of deleting a movie (use a new session)
        deleted = data_manager.delete_movie(movie1.id)
        print("Deleted movie1:", deleted)

        print("All movies after deletion:", session.query(Movie).all())


if __name__ == "__main__":
    main()


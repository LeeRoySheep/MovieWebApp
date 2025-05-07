
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload, Session
from contextlib import contextmanager
from typing import List, Dict, Any
from data_models import Base, User, Movie, UserMovie
from data_manager_interface import DataManagerInterface


# Define the database connection string.
TEST_DB_URL = "sqlite:///:memory:"



# Data manager class to handle database operations
class SQliteDataManager(DataManagerInterface):
    def __init__(self, db_url: str):
        """
        Initialize the data manager with a database URL.
        """
        self.engine = create_engine(db_url)
        self.SessionFactory = sessionmaker(bind=self.engine)
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
            raise
        finally:
            session.close()

    @property
    def users(self) -> List[User]:
        """
        Getter for users.
        Returns: a list of User objects.
        """
        with self.get_db() as db:
            return db.query(User).all()

    def add_user(self, user: User) -> None:
        """
        Add a user to the database.
        """
        with self.get_db() as db:
            db.add(user)
            db.commit()

    @property
    def movies(self) -> List[Movie]:
        """
        Getter for movies.
        Returns: a list of Movie objects
        """
        with self.get_db() as db:
            return db.query(Movie).options(joinedload(Movie.users)).all()

    def set_user_movies(self, user_id: int, movie_id: int, rating: float, user_rating: float = 0.0)\
            -> None:
        """
        Set (add) a movie to a user's list with a rating, or update the rating if it exists (self-contained session).
        """
        engine = self.engine
        with Session(engine) as db:
            user = db.query(User).filter_by(id=user_id).first()
            movie = db.query(Movie).filter_by(id=movie_id).first()

            if user and movie:
                existing_associations = db.query(UserMovie).filter_by(
                    user_id=user_id, movie_id=movie_id
                ).all()  #check if the association already exists

                if existing_associations:
                    #  existing association update
                    db.execute(
                        UserMovie.update().
                        where(UserMovie.user_id == user_id).
                        where(UserMovie.movie_id == movie_id).
                        values(rating=rating, user_rating=user_rating)
                    )
                    if user_rating:
                        print(f"Updated rating for user {user_id} and movie {movie_id} to "
                              f"{rating} and also updated user rating to {user_rating}")
                    else:
                        print(f"Updated rating for user {user_id} and movie {movie_id} to {rating}")
                else:
                    # create new association
                    association = UserMovie(user_id=user_id, movie_id=movie_id, rating=rating,
                                            user_rating=user_rating)
                    db.add(association)
                    print(f"Added movie {movie_id} to user {user_id} with rating {rating}")

                db.commit()  # Commit within the function
            else:
                print("User or movie not found.")

    def get_user_movies(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get movies for a specific user with their ratings.
        Returns: A list of dictionaries, where each dictionary contains movie details and the user's rating.
        """
        with self.get_db() as db:
            user = db.query(User).options(joinedload(User.movies)).filter_by(id=user_id).first()
            if user:
                movies_with_ratings = []
                for movie in user.movies:
                    association = db.query(UserMovie).filter_by(user_id=user.id,
                                                          movie_id=movie.id).first()
                    if association:
                        movies_with_ratings.append({
                            "id": movie.id,
                            "name": movie.name,
                            "director": movie.director,
                            "year": movie.year,
                            "poster": movie.poster,
                            "rating": association.rating,
                        })
                return movies_with_ratings
            return []


    def set_movie(self, movie: Movie) -> None:
        """
        Add a new movie to the database.
        """
        with self.get_db() as db:
            db.add(movie)
            db.commit()

    def update_movie(self, movie_id: int, update_data: dict) -> Movie | None:
        session = self.SessionFactory()
        try:
            movie = session.query(Movie).filter_by(id=movie_id).first()
            if movie:
                for key, value in update_data.items():
                    setattr(movie, key, value)
                session.commit()
                return movie
            return None
        finally:
            session.close()

    def delete_movie(self, movie_id: int) -> bool:
        """
        Delete a movie and its associations.

        Args:
            movie_id: The ID of the movie to delete.

        Returns:
            True if the movie was successfully deleted, False otherwise.
        """
        engine = self.engine
        with Session(engine) as db:
            movie = db.query(Movie).options(joinedload(Movie.users)).filter_by(id=movie_id).first()
            if movie:
                # Remove the movie from all associated users' movie lists
                for user in movie.users:
                    user.movies.remove(movie)
                db.delete(movie)
                db.commit()
                return True
            return False

def main():
    data_manager = SQliteDataManager(TEST_DB_URL)

    with data_manager.SessionFactory() as session:
        # Create some users
        user1 = User(name="Alice")
        user2 = User(name="Bob")
        data_manager.add_user(user1)
        data_manager.add_user(user2)
        session.add_all([user1, user2])
        session.commit()

        # Create some movies
        movie1 = Movie(name="The Matrix", director="Wachowskis", year=1999, poster="matrix.jpg",
                       rating=8.7)
        movie2 = Movie(name="Inception", director="Nolan", year=2010, poster="inception.jpg",
                       rating=8.8)
        data_manager.set_movie(movie1)
        data_manager.set_movie(movie2)
        session.add_all([movie1, movie2])
        session.commit()

        # Associate movies with users and assign ratings
        data_manager.set_user_movies(user1.id, movie1.id, 9.0,8.9)
        print(data_manager.get_user_movies(user1.id))
        data_manager.set_user_movies(user1.id, movie2.id, 8.5)
        data_manager.set_user_movies(user2.id, movie2.id, 9.2)

        # Get and print user movies (use a new session for querying)

        print("Alice's movies:", data_manager.get_user_movies(user1.id))
        print("Bob's movies:", data_manager.get_user_movies(user2.id))

        # Get and print all movies
        print("All movies:", session.query(Movie).all())

        # Example of updating a movie (use a new session)
        with data_manager.SessionFactory() as session_helper:
            updated_movie = data_manager.update_movie(movie1.id,
                                                      {"name": "The Matrix Reloaded", "rating": 7.2})
            session_helper.add(updated_movie)
            session_helper.commit()
            print("Updated movie:", updated_movie)

        # Example of deleting a movie (use a new session)
        with data_manager.SessionFactory() as session_helper:
            deleted = data_manager.delete_movie(movie1.id)
            session_helper.commit()
            print("Deleted movie1:", deleted)

        print("All movies after deletion:", session.query(Movie).all())













if __name__ == "__main__":
    main()


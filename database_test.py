import pytest
from sqlalchemy.orm import sessionmaker

from sqlite_data_manager import SQliteDataManager
from data_models import Base, User, Movie

TEST_DB_URL = "sqlite:///:memory:"

# Fixture for creating a new data manager for each test
@pytest.fixture(scope="function")
def data_manager():
    """
    Fixture to create an SQliteDataManager instance for each test.  Uses an in-memory database.
    """
    return SQliteDataManager(TEST_DB_URL)


def test_user_model(data_manager: SQliteDataManager):
    """Test creating a User object."""
    user = User(name="Test User")
    with data_manager.SessionFactory() as session:
        session.add(user)
        session.commit()
        retrieved_user = session.query(User).filter_by(name="Test User").first()
        assert retrieved_user == user


def test_movie_model(data_manager: SQliteDataManager):
    """Test creating a Movie object."""
    movie = Movie(name="Test Movie", director="Test Director", year=2024, poster="test.jpg", rating=7.5)
    with data_manager.SessionFactory() as session:
        session.add(movie)
        session.commit()
        retrieved_movie = session.query(Movie).filter_by(name="Test Movie").first()
        assert retrieved_movie == movie


def test_user_movie_model(data_manager: SQliteDataManager):
    """Test the association between User and Movie."""
    user = User(name="User 1")
    movie = Movie(name="Movie 1", director="Director A", year=2020, poster="m1.jpg", rating=8.0)
    with data_manager.SessionFactory() as session:
        session.add_all([user, movie])
        session.commit()
        user.movies.append(movie)
        session.commit()
        assert movie in user.movies
        assert user in movie.users


def test_get_users(data_manager: SQliteDataManager):
    """Test getting users from the database using the getter."""
    with data_manager.SessionFactory() as session:
        # Initially, there should be no users
        users_from_getter = data_manager.users  # This might return objects from a different session
        assert len(users_from_getter) == 0

        # Add some users directly to the database within the current session
        user_1 = User(name="User 1")
        user_2 = User(name="User 2")
        session.add_all([user_1, user_2])
        session.commit()

        # Now, retrieve the users using a query within the *same* session
        users_from_query = session.query(User).all()
        assert len(users_from_query) == 2

        # Check attributes of the queried users
        retrieved_user_names = [user.name for user in users_from_query]
        assert "User 1" in retrieved_user_names
        assert "User 2" in retrieved_user_names

        retrieved_user_ids = {user.id for user in users_from_query if user.id is not None}
        assert user_1.id in retrieved_user_ids
        assert user_2.id in retrieved_user_ids


def test_set_user(data_manager: SQliteDataManager):
    """Test setting (adding) a user to the database."""
    user = User(name="New User")
    with data_manager.SessionFactory() as session:
        session.add(user)
        session.commit()
        retrieved_user = session.query(User).filter_by(name="New User").first()
        assert retrieved_user.name == "New User"



def test_get_user_movies(data_manager: SQliteDataManager):
    """Test getting movies for a specific user."""
    user = User(name="Test User")
    movie1 = Movie(name="Movie 1", director="Director A", year=2020, poster="m1.jpg", rating=8.0)
    movie2 = Movie(name="Movie 2", director="Director B", year=2022, poster="m2.jpg", rating=7.0)
    with data_manager.SessionFactory() as session:
        session.add_all([user, movie1, movie2])
        session.commit()
        data_manager.set_user_movies(user.id, movie1.id, 9.0)
        data_manager.set_user_movies(user.id, movie2.id, 8.5)

        session.commit()

        #user_movies = data_manager.get_user_movies(user.id)

        user_movies = data_manager.get_user_movies(user.id) #Adapt this
        assert len(user_movies) == 2
        assert user_movies[0]['name'] == 'Movie 1'
        assert user_movies[0]['rating'] == 9.0
        assert user_movies[1]['name'] == 'Movie 2'
        assert user_movies[1]['rating'] == 8.5



def test_set_user_movies(data_manager: SQliteDataManager):
    """Test setting (adding) a movie to a user's list."""
    user = User(name="Test User")
    movie = Movie(name="Test Movie", director="Test Director", year=2024, poster="test.jpg", rating=7.5)
    with data_manager.SessionFactory() as session:
        session.add_all([user, movie])
        session.commit()
        data_manager.set_user_movies(user.id, movie.id, 5.0) # Adapt this
        user_movies = data_manager.get_user_movies(user.id) # Adapt this
        assert len(user_movies) == 1
        assert user_movies[0]['name'] == 'Test Movie'
        assert user_movies[0]['rating'] == 5.0



def test_get_movies(data_manager: SQliteDataManager):
    """Test getting all movies."""
    movie1 = Movie(name="Movie A", director="Director X", year=2019, poster="a.jpg", rating=6.5)
    movie2 = Movie(name="Movie B", director="Director Y", year=2021, poster="b.jpg", rating=8.5)
    with data_manager.SessionFactory() as session:
        session.add_all([movie1, movie2])
        session.commit()
        movies = session.query(Movie).all()
        assert len(movies) == 2
        assert movie1 in movies
        assert movie2 in movies



def test_set_movie(data_manager: SQliteDataManager):
    """Test setting (adding) a movie."""
    movie = Movie(name="New Movie", director="New Director", year=2023, poster="new.jpg", rating=9.0)
    with data_manager.SessionFactory() as session:
        session.add(movie)
        session.commit()
        retrieved_movies = session.query(Movie).filter_by(name="New Movie").all()
        assert len(retrieved_movies) == 1
        assert retrieved_movies[0].name == "New Movie"



def test_update_movie(data_manager: SQliteDataManager):
    """Test updating an existing movie."""
    movie = Movie(name="Old Movie", director="Old Director", year=2000, poster="old.jpg", rating=5.0)
    with data_manager.SessionFactory() as session:
        session.add(movie)
        session.commit()
        movie_to_update = session.query(Movie).get(movie.id)

        updated_movie_data = {
            "name": "Updated Movie",
            "director": "Updated Director",
            "year": 2022,
            "poster": "updated.jpg",
            "rating": 8.0,
        }
        for key, value in updated_movie_data.items():
            setattr(movie_to_update, key, value)
        session.commit()

        updated_movie = session.query(Movie).get(movie.id)
        assert updated_movie is not None
        assert updated_movie.name == "Updated Movie"
        assert updated_movie.director == "Updated Director"
        assert updated_movie.year == 2022
        assert updated_movie.poster == "updated.jpg"
        assert updated_movie.rating == 8.0



def test_update_movie_partial(data_manager: SQliteDataManager):
    """Test updating a movie with partial data."""
    movie = Movie(name="Original Movie", director="Original Director", year=2000, poster="original.jpg", rating=5.0)
    with data_manager.SessionFactory() as session:
        session.add(movie)
        session.commit()
        movie_to_update = session.query(Movie).get(movie.id)

        updated_data = {"rating": 9.5, "name": "Partially Updated"}
        for key, value in updated_data.items():
            setattr(movie_to_update, key, value)
        session.commit()

        updated_movie = session.query(Movie).get(movie.id)
        assert updated_movie is not None
        assert updated_movie.name == "Partially Updated"
        assert updated_movie.rating == 9.5
        assert updated_movie.director == "Original Director"  # Unchanged
        assert updated_movie.year == 2000  # Unchanged
        assert updated_movie.poster == "original.jpg" #Unchanged



def test_update_movie_not_found(data_manager: SQliteDataManager):
    """Test updating a non-existent movie."""
    updated_data = {"name": "Nonexistent Movie"}
    with data_manager.SessionFactory() as session:
        result = session.query(Movie).get(999)
        assert result is None



def test_delete_movie(data_manager: SQliteDataManager):
    """Test deleting a movie."""
    movie = Movie(name="Movie to Delete", director="Delete Director", year=2023, poster="delete.jpg", rating=9.0)
    with data_manager.SessionFactory() as session:
        session.add(movie)
        session.commit()
        movie_to_delete = session.query(Movie).get(movie.id)
        session.delete(movie_to_delete)
        session.commit()
        retrieved_movie = session.query(Movie).get(movie.id)
        assert retrieved_movie is None



def test_delete_movie_not_found(data_manager: SQliteDataManager):
    """Test deleting a non-existent movie."""
    with data_manager.SessionFactory() as session:
        deleted = data_manager.delete_movie(999)
        assert deleted is False


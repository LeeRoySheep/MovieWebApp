

from flask import Flask, render_template, request
from datamanager.sqlite_data_manager import SQliteDataManager
from data_models import User, Movie, UserMovie

app = Flask(__name__)
data_manager = SQliteDataManager("sqlite:///movie_app.db")

@app.route('/')
def home():
    return render_template("home.html")


@app.route('/users')
def list_users():
    users = data_manager.users

    return render_template("users.html",users=users)

@app.route('/users/<user_id>', methods=["GET", "POST"])
def user_movies(user_id):
    if request.method == "GET":
        chosen_user = data_manager.get_user(user_id)
        user_movies_list = data_manager.get_user_movies(user_id)
        return render_template("user_movies.html", user_movies=user_movies_list,
                    user=chosen_user)
    elif request.method == "POST":
        chosen_user = data_manager.get_user(user_id)
        movie_title = request.form["movie_title"]
        with data_manager.SessionFactory() as session:
            movie = session.query(Movie).filter_by(name=movie_title).first()

        data_manager.set_user_movies(user_id, movie.id, movie.rating, movie.user_rating)
        success = True
        user_movies_list = data_manager.get_user_movies(user_id)
        return render_template("user_movies.html", user_movies=user_movies_list,
                    user=chosen_user, success=success)

@app.route('/users/new', methods=["GET", "POST"])
def new_user():
    if request.method == "GET":
        return render_template("new_user.html")
    elif request.method == "POST":
        name = request.form["name"]
        user = User(name=name)
        with data_manager.SessionFactory() as session:
            try:
                session.add(user)
                session.commit()
                success = True
            except Exception():
                session.rollback()
                success = False
        return render_template("new_user.html", success=success)

@app.route('/movies/new', methods=["GET", "POST"])
def new_movie():
    if request.method == "GET":
        return render_template("new_movie.html")
    elif request.method == "POST":
        title = request.form["name"]
        movie = data_manager.set_movie(title)
        if movie:
            success = True
        else:
            success = False
        return render_template("new_movie.html", movie=movie, success=success)

@app.route('/movies', methods=["GET", "POST"])
def list_movies():
    if request.method == "GET":
        movies = data_manager.movies
        return render_template("movies.html",movies=movies)
    elif request.method == "POST":
        movie_id = request.form["movie_id"]
        data_manager.delete_movie(movie_id)
        movies = data_manager.movies
        return render_template("movies.html",movies=movies)

if __name__ == "__main__":

    app.run(debug=True, host="127.0.0.1",port=5000)


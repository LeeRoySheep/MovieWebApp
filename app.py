from flask import Flask, render_template, request

from ai_request import AIRequest
from datamanager.sqlite_data_manager import SQliteDataManager
from data_models import User, Movie
from movie_api import OMDBClient

app = Flask(__name__)
app.config['ENV'] = 'production'

data_manager = SQliteDataManager("sqlite:///movie_app.db")

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500


# Home Route with simple navigation
@app.route('/')
def home():
    return render_template("home.html")


# Users in a list view
@app.route('/users')
def list_users():
    users = data_manager.users
    return render_template("users.html",users=users)


# User movies in a list view
@app.route('/users/<user_id>', methods=["GET", "POST"])
def user_movies(user_id):
    if request.method == "GET":
        chosen_user = data_manager.get_user(user_id)
        user_movies_list = data_manager.get_user_movies(user_id)
        return render_template("user_movies.html", user_movies=user_movies_list,
                    user=chosen_user)
    elif request.method == "POST":
        chosen_user = data_manager.get_user(user_id)
        movie_title = request.form["name"]
        with data_manager.SessionFactory() as session:
            movie = session.query(Movie).filter_by(name=movie_title).first()
            if movie is None:
                try:
                    movie = data_manager.set_movie(movie_title)
                    if movie is None:
                        raise Exception("Movie not found")
                    data_manager.set_user_movies(user_id=user_id, movie_id=movie.id)
                    user_movies_list = data_manager.get_user_movies(user_id)
                    return render_template("user_movies.html",
                                           user_movies=user_movies_list,
                                           user=chosen_user, success=True)
                except Exception as e:
                    session.rollback()
                    user_movies_list = data_manager.get_user_movies(user_id)
                    return render_template("user_movies.html",
                                           user_movies=user_movies_list,
                                           user=chosen_user, success=False, error=e)
            else:
                if data_manager.get_user_movie(user_id, movie.id):
                    return render_template("user_movies.html",
                                           user_movies=data_manager.get_user_movies(user_id),
                                           user=chosen_user, success=False,
                                           error="Movie already exists")
                try:
                    data_manager.set_user_movies(user_id=user_id, movie_id=movie.id)
                    user_movies_list = data_manager.get_user_movies(user_id)
                    return render_template("user_movies.html",
                                           user_movies=user_movies_list,
                                           user=chosen_user, success=True)
                except Exception as e:
                    session.rollback()
                    return render_template("user_movies.html",
                                           user_movies=data_manager.get_user_movies(user_id),
                                           user=chosen_user, success=False, error=e)


# single user movie view for updating
@app.route('/users/<user_id>/<movie_id>', methods=["GET", "POST"])
def update_user_movie(user_id, movie_id):
    if request.method == "GET":
        chosen_user = data_manager.get_user(user_id)
        movie = data_manager.get_movie(movie_id)
        user_movie = data_manager.get_user_movie(user_id, movie_id)
        return render_template("user_movie.html", user_movie=user_movie,
                               user=chosen_user, movie=movie)
    elif request.method == "POST":
        chosen_user = data_manager.get_user(user_id)
        movie = data_manager.get_movie(movie_id)
        user_movie = data_manager.get_user_movie(user_id, movie_id)
        user_rating = request.form["user_rating"]
        user_comment = request.form["user_comment"] if "user_comment" in request.form else None
        try:
            data_manager.update_user_movie(user_id=user_id, movie_id=movie_id,
                                           update_data={"user_rating": user_rating,
                                                        "user_comment": user_comment})
            new_user_movie = data_manager.get_user_movie(user_id, movie_id)
            return render_template("user_movie.html", user_movie=new_user_movie,
                                   user=chosen_user, movie=movie, success=True)
        except Exception as e:
            return render_template("user_movie.html", user_movie=user_movie,
                                   user=chosen_user, movie=movie, success=False, error=e)


# Adding new users
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
                return render_template("new_user.html", success=True)
            except Exception as e:
                session.rollback()
                return render_template("new_user.html", success=False, error=e)


# Adding new movies
@app.route('/movies/new', methods=["GET", "POST"])
def new_movie():
    if request.method == "GET":
        return render_template("new_movie.html")
    elif request.method == "POST":
        title = request.form["name"]
        try:
            newest_movie = data_manager.set_movie(title)
            return render_template("new_movie.html",
                                   movie_name=newest_movie.name, success=True)
        except Exception as e:
            error_msg = str(e)
            return render_template("new_movie.html", movie_name=title,
                                   success=False, error = error_msg)


# see list of all movies in database
@app.route('/movies', methods=["GET", "POST"])
def list_movies():
    if request.method == "GET":
        movies = data_manager.movies
        return render_template("movies.html",movies=movies)
    elif request.method == "POST":
        movie_id = request.form["movie_id"]
        deleted = data_manager.delete_movie(int(movie_id))
        movies = data_manager.movies
        return render_template("movies.html", movies=movies, success=deleted)


# get details of a single movie
@app.route('/movies/<movie_id>', methods=["GET", "POST"])
def movie_details(movie_id):
    if request.method == "GET":
        movie = data_manager.get_movie(movie_id)
        return render_template("movie_details.html", movie=movie)
    elif request.method == "POST":
        movie_id = request.form["movie_id"]
        deleted = data_manager.delete_movie(int(movie_id))
        movies = data_manager.movies
        return render_template("movies.html", movies=movies, success=deleted)

# delete user movie from database
@app.route('/users/<user_id>/delete/<movie_id>', methods=["GET", "POST"])
def delete_user_movie(user_id, movie_id):
    if request.method == "GET":
        chosen_user = data_manager.get_user(user_id)
        movie = data_manager.get_movie(movie_id)
        user_movie = data_manager.get_user_movie(user_id, movie_id)
        return render_template("user_movie.html", user_movie=user_movie,
                               user=chosen_user, movie=movie)
    elif request.method == "POST":
        deleted = data_manager.delete_user_movie(user_id, movie_id)
        chosen_user = data_manager.get_user(user_id)
        movie = data_manager.get_movie(movie_id)
        user_movies_list = data_manager.get_user_movies(user_id)
        return render_template("user_movies.html", user_movies=user_movies_list,
                               user=chosen_user, movie=movie, movie_deleted=deleted)


# movie recommendation from AI
@app.route('/users/<user_id>/recommend_movie', methods=["GET", "POST"])
def recommendation(user_id):
    if request.method == "GET":
        chosen = data_manager.get_user(user_id)
        return render_template("recommend.html", user=chosen)
    elif request.method == "POST":
        chosen= data_manager.get_user(user_id)
        data_string = ""
        for movie in data_manager.get_user_movies(user_id):
            data_string += f"Title: {movie["name"]} User Rating: {movie['user_rating']},"
        if "name" in request.form:
            recommend = AIRequest().ai_excluded_movie_request(data_string,request.form[
                "name"])
        else:
            recommend = AIRequest().ai_request(data_string)
        poster = OMDBClient().get_movie(recommend["movie"]["title"])
        recommend["movie"]["poster"] = poster["poster"]
        recommend["movie"]["imdb"] = poster["rating"]
        return render_template("recommend.html", user=chosen, movie=recommend["movie"], reasoning=recommend["reasoning"])


if __name__ == "__main__":

    app.run(debug=True,host="127.0.0.1",port=5000)


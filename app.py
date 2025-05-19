from django.contrib.messages import success
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
                    return render_template("user_movies.html",
                                           user_movies=user_movies_list,
                                           user=chosen_user, success=False)
            else:
                if data_manager.get_user_movie(user_id, movie.id):
                    return render_template("user_movies.html",
                                           user_movies=data_manager.get_user_movies(user_id),
                                           user=chosen_user, success=False)
                try:
                    data_manager.set_user_movies(user_id=user_id, movie_id=movie.id)
                    user_movies_list = data_manager.get_user_movies(user_id)
                    return render_template("user_movies.html",
                                           user_movies=user_movies_list,
                                           user=chosen_user, success=True)
                except Exception as e:
                    session.rollback()
                    return render_template("user_movies.html",
                                           user_movies=user_movies_list,
                                           user=chosen_user, success=False)


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
        try:
            data_manager.update_user_movie(user_id=user_id, movie_id=movie_id,
                                           update_data={"user_rating": user_rating})
            new_user_movie = data_manager.get_user_movie(user_id, movie_id)
            return render_template("user_movie.html", user_movie=new_user_movie,
                                   user=chosen_user, movie=movie, success=True)
        except Exception as e:
            return render_template("user_movie.html", user_movie=user_movie,
                                   user=chosen_user, movie=movie, success=False)



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
            movie_added = True
        else:
            movie_added = False
        return render_template("new_movie.html", movie=movie, success=movie_added)

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

if __name__ == "__main__":

    app.run(debug=True,port=5000)


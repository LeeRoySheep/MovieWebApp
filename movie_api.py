import dotenv
import os
import requests


dotenv.load_dotenv()

API_KEY = os.getenv("OMDB_API_KEY")

BASE_URL = "http://www.omdbapi.com/?apikey=" + API_KEY

class OMDBClient:
    def __init__(self):
        self.BASE_URL = BASE_URL

    def get_movie(self, title: str) -> dict | None:
        url = self.BASE_URL + "&t=" + title
        response = requests.get(url)
        if response.status_code == 200:
            new_movie = {"name": response.json()["Title"], "director": response.json()["Director"],
                         "year": response.json()["Year"], "poster": response.json()["Poster"],
                         "rating": response.json()["imdbRating"]}
            return new_movie
        return None
from abc import ABC, abstractmethod

class DataManagerInterface(ABC):

    @abstractmethod
    def users(self):
        pass

    @abstractmethod
    def users(self, user):
        pass

    @abstractmethod
    def get_user_movies(self, user_id):
        pass

    @abstractmethod
    def set_user_movies(self, user_id, movie):
        pass


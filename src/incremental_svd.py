# Project: Recommender System
# Author(s): Calvin Feng

from movie import Movie
from user import User
from data_reducer import DataReducer
from progress import Progress

from pdb import set_trace as debugger
from math import sqrt

class IncrementalSVD:
    def __init__(self, movie_csv_filepath, rating_csv_filepath, link_csv_filepath):
        reducer = DataReducer(movie_csv_filepath, rating_csv_filepath, link_csv_filepath)
        self.movies = dict()
        for movie_id in reducer.movies:
            movie = reducer.movies[movie_id]
            self.movies[movie_id] = Movie(movie_id, movie['title'], movie['user_ratings'])

        self.users = dict()
        for user_id in reducer.users:
            user = reducer.users[user_id]
            self.users[user_id] = User(user_id, user['movie_ratings'])

        self.regularized_factor = None
        self.learning_rate = None

    def configure(self, regularized_factor, learning_rate):
        self.regularized_factor = regularized_factor
        self.learning_rate = learning_rate

    # The cost property represents the value of cost/loss function
    @property
    def cost(self):
        if self.regularized_factor is None:
            return None
        # m denotes number of training examples
        sq_error = 0
        m = 0
        for movie_id in self.movies:
            movie = self.movies[movie_id]
            for user_id in movie.viewer_ids:
                user = self.users[user_id]
                if user.movie_ratings.get(movie.id):
                    sq_error += (movie.hypothesis(user) - float(user.movie_ratings[movie.id]))**2
                    m += 1
        sq_error *= (0.5 / m)

        regularized_term = 0
        for movie_id in self.movies:
            movie = self.movies[movie_id]
            for k in range(0, len(movie.feature)):
                regularized_term += movie.feature[k]**2

        for user_id in self.users:
            user = self.users[user_id]
            for k in range(0, len(user.theta)):
                regularized_term += user.theta[k]**2
        regularized_term *= (0.5 * self.regularized_factor / m)

        return regularized_term + sq_error

    # RMSE stands for Root-mean-squared-error
    @property
    def rmse(self):
        sq_error = 0
        m = 0
        for user_id in self.users:
            user = self.users[user_id]
            for movie_id in user.movie_ratings:
                movie = self.movies[movie_id]
                sq_error += (movie.hypothesis(user) - float(user.movie_ratings[movie_id]))**2
                m += 1
        return sqrt(sq_error / m)

    '''
    Partial derivatives, wrt => with respect to
    '''
    def dj_wrt_movie_feature_k(self, movie, k):
        derivative_sum = 0
        m = 0
        for user_id in movie.viewer_ids:
            user = self.users[user_id]
            if user.movie_ratings.get(movie.id):
                derivative_sum += (movie.hypothesis(user) - float(user.movie_ratings[movie.id])) * user.theta[k]
                m += 1

        if m == 0:
            return derivative_sum + (self.regularized_factor * movie.feature[k])

        return (derivative_sum / m) + (self.regularized_factor * movie.feature[k] / m)

    def dj_wrt_user_theta_k(self, user, k):
        derivative_sum = 0
        m = 0
        for movie_id in user.movie_ratings:
            movie = self.movies[movie_id]
            if movie.user_ratings.get(user.id):
                derivative_sum += (movie.hypothesis(user) - float(user.movie_ratings[movie_id])) * movie.feature[k]
                m += 1

        if m == 0:
            return derivative_sum + (self.regularized_factor * user.theta[k])

        return (derivative_sum / m) + (self.regularized_factor * user.theta[k] / m)

    '''
    Only necessary for computing content-based gradient descent
    '''
    def dj_wrt_user_theta_k0(self, user):
        derivative_sum = 0
        m = 0
        for movie_id in user.movie_ratings:
            movie = self.movies[movie_id]
            derivative_sum += (movie.hypothesis(user) - float(user.movie_ratings[movie_id])) * movie.feature[0]
            m += 1

        if m == 0:
            return derivative_sum

        return (derivative_sum / m)

    def batch_gradient_descent(self):
        if self.learning_rate is None or self.regularized_factor is None:
            return False

        total_iteration = 1500
        progress = Progress('Gradient Descent', total_iteration)

        log = []
        current_iteration = 1
        while current_iteration <= total_iteration:
            progress.report(current_iteration, self.cost)

            # ==> Compute partial derivatives
            # Derivative of cost function wrt movie features
            dj_dmovies = dict()
            for movie_id in self.movies:
                movie = self.movies[movie_id]
                n = len(movie.feature)
                dj_dmovies[movie.id] = []
                for k in range(0, n):
                    dj_dmovies[movie.id].append(self.dj_wrt_movie_feature_k(movie, k))

            # Derivative of cost function wrt user preferences
            dj_dusers = dict()
            for user_id in self.users:
                user = self.users[user_id]
                n = len(user.theta)
                dj_dusers[user.id] = []
                for k in range(0, n):
                    dj_dusers[user.id].append(self.dj_wrt_user_theta_k(user, k))

            # Apply gradient_descent
            for movie_id in dj_dmovies:
                dj_dfeature = dj_dmovies[movie_id]
                movie = self.movies[movie_id]
                n = len(movie.feature)
                for k in range(0, n):
                    movie.feature[k] = movie.feature[k] - (self.learning_rate * dj_dfeature[k])

            for user_id in dj_dusers:
                dj_dtheta = dj_dusers[user_id]
                user = self.users[user_id]
                n = len(user.theta)
                for k in range(0, n):
                    user.theta[k] = user.theta[k] - (self.learning_rate * dj_dtheta[k])

            current_iteration +=1

        return log

if __name__ == '__main__':
    svd = IncrementalSVD(
                    '../data/20k-users/training_movies.csv',
                    '../data/20k-users/training_ratings.csv',
                    '../data/20k-users/training_links.csv'
                )
    svd.configure(0.1, 0.15)
    print svd.cost
    print svd.rmse
    print svd.batch_gradient_descent()

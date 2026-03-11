from geopy.distance import geodesic

def find_nearest_worker(user_location, workers):

    nearest = None
    min_distance = 999

    for worker in workers:

        worker_location = worker["coordinates"]

        dist = geodesic(user_location, worker_location).km

        if dist < min_distance:
            min_distance = dist
            nearest = worker

    return nearest
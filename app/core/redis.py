from redis import Redis

def get_redis():
    return Redis(host="localhost", port=6379)


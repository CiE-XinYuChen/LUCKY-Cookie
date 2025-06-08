import redis
import time
import uuid
from contextlib import contextmanager
from flask import current_app

class RedisLock:
    def __init__(self, redis_client, key, timeout=10, sleep_time=0.1):
        self.redis_client = redis_client
        self.key = key
        self.timeout = timeout
        self.sleep_time = sleep_time
        self.identifier = str(uuid.uuid4())
        
    def acquire(self):
        end_time = time.time() + self.timeout
        while time.time() < end_time:
            if self.redis_client.set(self.key, self.identifier, nx=True, ex=self.timeout):
                return True
            time.sleep(self.sleep_time)
        return False
    
    def release(self):
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        return self.redis_client.eval(script, 1, self.key, self.identifier)

@contextmanager
def redis_lock(redis_client, key, timeout=10, sleep_time=0.1):
    lock = RedisLock(redis_client, key, timeout, sleep_time)
    acquired = lock.acquire()
    if not acquired:
        raise Exception(f"Could not acquire lock for key: {key}")
    try:
        yield
    finally:
        lock.release()

def get_redis_client():
    redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
    return redis.from_url(redis_url, decode_responses=True)
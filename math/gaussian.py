import math
import random

pi2 = math.pi * 2

def std(mu=0, sigma=1):
    u1 = random.random()
    u2 = random.random()
    rand_std_normal = math.sqrt(-2.0 * math.log(u1)) * math.sin(pi2 * u2)
    return mu + sigma * rand_std_normal

def std_seed(rnd, mu=0, sigma=1):
    u1 = rnd.randFloat()
    u2 = rnd.randFloat()
    while u1 <= 0:
        u1 = rnd.randFloat()
    while u2 <= 0:
        u2 = rnd.randFloat()
    rand_std_normal = math.sqrt(-2.0 * math.log(u1)) * math.sin(pi2 * u2)
    return mu + sigma * rand_std_normal

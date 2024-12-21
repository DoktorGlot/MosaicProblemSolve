class XorShift:

    def __init__(self, w=0, x=123456789, y=362436069, z=521288629):
        self.w = w + 1
        self.x = (self.w << 13) & 0xFFFFFFFF
        self.y = ((self.w >> 9) ^ (self.x << 6)) & 0xFFFFFFFF
        self.z = (self.y >> 7) & 0xFFFFFFFF

    def next_(self):
        t = self.x ^ (self.x << 11) & 0xFFFFFFFF
        self.x = self.y
        self.y = self.z
        self.z = self.w
        self.w = ((self.w ^ (self.w >> 19) ^ (t ^ (t >> 8)))) & 0xFFFFFFFF
        return self.w

    def rand(self):
        return self.next_()

    def randInt(self, min_val=0, max_val=0x7FFFFFFF):
        r = abs(self.rand())
        return r % (max_val - min_val) + min_val

    def randFloat(self, min_val=0.0, max_val=1.0):
        return (self.rand() % 0xFFFF) / 0xFFFF * (max_val - min_val) + min_val

    def shuffle(self, arr):
        shuffled = arr[:]
        for i in range(len(shuffled) - 1):
            r = self.rand_int(i, len(shuffled) - 1)
            shuffled[i], shuffled[r] = shuffled[r], shuffled[i]
        return shuffled

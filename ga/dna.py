from math import floor
import sys
sys.path.append(r"C:\Users\nadto\Desktop\Kursach_TIMP\math")
from gaussian import std_seed

class DNA:

    def __init__(self, genes=None):
        self.genes = genes if genes is not None else []
        self.cost = 1e5  # initial value for a failed case
        self.options = {}

    def clone(self):
        cloned = DNA(self.genes[:])  # Create a shallow copy of the genes list
        cloned.cost = self.cost
        cloned.options = self.options
        return cloned

    def evaluate(self, cost, options=None):
        self.cost = cost
        self.options = options if options is not None else {}

    def cross_over(self, rnd, partner):
        child_genes = []
        #print(vars(rnd))
        mid = floor(rnd.randFloat() * len(self.genes))

        # Take "half" from one and "half" from the other
        for i in range(len(self.genes)):
            if i > mid:
                child_genes.append(self.genes[i])
            else:
                child_genes.append(partner.genes[i])

        return DNA(child_genes)

    def mutate(self, rnd, mutation_rate, steps):
        genes = []
        for v in self.genes:
            if rnd.randFloat() <= mutation_rate:
                delta = std_seed(rnd, 0, 1) * steps
                v = floor(v + delta) % steps
                if v < 0:
                    v = (steps + v) % steps
            genes.append(v)
        return DNA(genes)

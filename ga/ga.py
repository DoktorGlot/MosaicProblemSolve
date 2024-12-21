from dna import DNA

class GA:

    def __init__(self, rnd, gene, config=None):
        if config is None:
            config = {'steps': 4, 'population': 30, 'mutationRate': 0.2}

        self.rnd = rnd
        self.generations = 0
        self.population = []
        self.config = config
        self.config['steps'] = self.config.get('steps', 4)
        self.config['mutationRate'] = self.config.get('mutationRate', 0.2)

        count = max(3, int(self.config.get('population', 0)))
        for _ in range(count):
            self.population.append(self.adam(gene, self.config['steps']))
        #print(vars(self.population[0]))

    def adam(self, length, steps=4):
        gene = []
        for _ in range(length):
            v = int(self.rnd.randFloat() * steps) % steps
            gene.append(v)
        #print(gene)
        return DNA(gene)

    def step(self):
        self.generations += 1

        pool = self.select()
        if len(pool) <= 0:
            # Handle empty pool case
            pool = self.population

        for i in range(len(self.population)):
            mi = self.rnd.randInt(0, len(pool))
            di = self.rnd.randInt(0, len(pool))

            mon = pool[mi]
            dad = pool[di]
            child = mon.cross_over(self.rnd, dad)
            child = child.mutate(self.rnd, self.config['mutationRate'], self.config['steps'])

            self.population[i] = child

    def select(self):
        pool = []
        range_cost = self.get_min_max_cost()
        l = range_cost['max'] - range_cost['min']
        for dna in self.population:
            # Normalize
            if l == 0:
                cost01 = 100.0
            else:
                cost01 = 1.0 - (dna.cost - range_cost['min']) / l
            n = int(cost01 * 50)
            pool.extend([dna] * n)

        return pool

    def get_dominant(self):
        dominant = None
        min_cost = float('inf')
        for dna in self.population:
            if dna.cost < min_cost:
                min_cost = dna.cost
                dominant = dna
        #print(vars(self.population[0].options['result']['placements'][0]))
        return dominant

    def get_min_max_cost(self):
        min_cost = float('inf')
        max_cost = float('-inf')

        for dna in self.population:
            max_cost = max(max_cost, dna.cost)
            min_cost = min(min_cost, dna.cost)

        return {'min': min_cost, 'max': max_cost}

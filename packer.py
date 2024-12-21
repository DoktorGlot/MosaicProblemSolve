import sys
import asyncio
sys.path.append(r"C:\Users\nadto\Desktop\Kursach_TIMP\math")
sys.path.append(r"C:\Users\nadto\Desktop\Kursach_TIMP\ga")
sys.path.append(r"C:\Users\nadto\Desktop\Kursach_TIMP\workers")
from ga import GA
from place_worker import place, postMessage
from xorshift import XorShift
from nfp_worker import addEventListener
from util import createUniqueKey, offsetPolygon
from part import Part
from bins import Bin


class Packer:

    def __init__(self):
        self.running = False
        self.bins = []
        self.parts = []
        self.config = {}

    def start(self, bins, parts, config, callbacks=None):
        if self.running:
            self.stop()

        self.running = True

        # Disable sort for bins
        self.bins = bins
        self.source = self.parts = sorted(parts, key=lambda p: p.area())
        #print(vars(self.parts[1]))

        self.config = config or {}
        self.rnd = XorShift(self.config.get('seed', 0))

        self.group(self.bins, 'bin')
        self.group(self.source, 'polygon')

        if callbacks and 'onStart' in callbacks:
            callbacks['onStart']()

        if self.config.get('spacing', 0) > 0:
            self.parts = [offsetPolygon(part, config['spacing']) for part in self.parts]

        return self.pack_async({
            'onEvaluation': lambda e: callbacks['onEvaluation'](e) if callbacks and 'onEvaluation' in callbacks else None,
            'onPacking': lambda e: callbacks['onPacking'](e) if callbacks and 'onPacking' in callbacks else None,
            'onPackingCompleted': lambda e: callbacks['onPackingCompleted'](e) if callbacks and 'onPackingCompleted' in callbacks else None
        })

    def group(self, polygons, prefix=''):
        polygons = polygons[:]  # Create a shallow copy of the list

        groups = []
        groups.append([polygons.pop()])

        for poly in polygons:
            found = False
            for grp in groups:
                head = grp[0]
                if head.approximately(poly):
                    grp.append(poly)
                    found = True
                    break

            if not found:
                groups.append([poly])

        for idx, grp in enumerate(groups):
            for poly in grp:
                poly.groupId = f"{prefix}{idx}"

    def on_packing(self, e, callback):
        placed = self.apply_placements(e['placements'], [p.clone() for p in self.source])
        e['bins'] = self.bins
        e['placed'] = placed
        e['unplaced'] = [next(part for part in self.source if part.id == p['id']) for p in e['unplaced']]
        callback(e)


    def stop(self):
        self.running = False

        if hasattr(self, 'nfp_worker') and self.nfp_worker is not None:
            self.nfp_worker.terminate()

        if hasattr(self, 'place_worker') and self.place_worker is not None:
            self.place_worker.terminate()



    def transform(self, dna, parts, range_):
        return [part.transform(dna.genes[idx], range_) for idx, part in enumerate(parts)]

    def format_(self, args):
        placed = self.apply_placements(args['placements'], [p.clone() for p in self.source])
        args['bins'] = self.bins
        args['placed'] = placed
        args['unplaced'] = [next(part for part in self.source if part.id == p.id) for p in args['unplaced']]
        return args

    def apply_placements(self, placements, parts):
        packed = []
        for placement in placements:
            #print(placement.position.x)
            id_ = placement.part
            idx = next((i for i, part in enumerate(parts) if part.id == id_), -1)
            if idx != -1:
                parts[idx] = parts[idx].rotate(placement.rotation).translate(placement.position.x, placement.position.y)
                packed.append(parts[idx])
        return packed

    def add_bin(self, bin_):
        self.bins.append(bin_)


    async def pack_async(self, callbacks=None):
        cache = {}
        #print(vars(self.parts[0]))
        ga = GA(self.rnd, len(self.parts), {
            'population': self.config['population'],
            'mutationRate': self.config['mutationRate'],
            'steps': self.config['rotationSteps']
        })
        #print(vars(self.rnd))
        generations = self.config['generations']
        # The stepAsync method is assumed to be asynchronous, hence using await
        result = await self.step_async(None, 0, generations, ga, cache, callbacks)
        # Clear cache
        cache.clear()
        return result['placements']

    async def step_async(self, dominant, current, generations, ga, cache, callbacks):
        await self.evaluate_all_async(current, ga.population, 0, cache, callbacks)
        #if dominant != None:
            #print(vars(dominant.options['result']['placements'][0]))
        
        cand = ga.get_dominant()

        # Keep dominant dna
        if dominant is None or cand.cost < dominant.cost:
            dominant = cand.clone()
        #print(dominant.options)

        args = {
            'generation': current,
            'placements': dominant.options['result']['placements'],
            'unplaced': dominant.options['result']['unplaced'],
            'dominant': dominant
        }
        result = self.format_(args)

        if current < generations:
            if 'onPacking' in callbacks:
                callbacks['onPacking'](result)
            #print(vars(result['placements'][0]))
            ga.step()
            return await self.step_async(dominant, current + 1, generations, ga, cache, callbacks)

        else:
            if 'onPackingCompleted' in callbacks:
                callbacks['onPackingCompleted'](result)

            return result

    async def evaluate_all_async(self, generation, population, current, cache, callbacks):
        length = len(population)
        # Если обработали все элементы
        if current >= length:
            return

        # Текущий элемент популяции
        dna = population[current]

        # Асинхронная оценка текущего элемента
        await self.evaluate_async(dna, cache, lambda progress: (
            callbacks.get('onEvaluation', lambda e: None)({
                'generation': generation,
                'progress': (1 / length) * progress + (current / length)
            })
            if callbacks and 'onEvaluation' in callbacks else None
        ))

        # Колбек после завершения обработки текущего элемента
        if callbacks and 'onEvaluation' in callbacks:
            callbacks['onEvaluation']({
                'generation': generation,
                'progress': (current + 1) / length
            })

        # Рекурсивный вызов для следующего элемента
        await self.evaluate_all_async(generation, population, current + 1, cache, callbacks)
        
    async def evaluate_async(self, dna, cache, on_progress):
        #print(vars(self.parts[0]))
        transformed = self.transform(dna, self.parts, self.config.get('rotationSteps', 4))
        #print(vars(transformed[0]))
        # Assuming create_nfps_async is an asynchronous function
        await self.create_nfps_async(transformed, cache, False, False, on_progress)
        # Assuming place_async is an asynchronous function
        result = await self.place_async(transformed, cache)
        #print(vars(result['result']['placements'][0]))
        transformed = []
        dna.evaluate(result["result"]['cost'], result)
        return dna


    async def place_async(self, parts, cache):
        # Мимика постинга сообщения в worker
        #print(vars(parts[0]))
        #print(cache)
        return postMessage({
            'bins': self.bins,
            'parts': parts,
            'nfpCache': cache
        })

    async def create_nfps_async(self, parts, cache, inside=False, edges=False, on_progress=None):
        pairs = []
        #print(vars(parts[0]))
        # Loop through bins and parts to generate pairs
        for bin_ in self.bins:
            for polygon in parts:
                key = createUniqueKey(bin_, polygon, inside, edges)
                if  not (key in cache):
                    pairs.append({
                        'A': bin_, 'B': polygon, 'inside': inside, 'edges': edges
                    })
                
        # Loop through parts and create pairs
        for i in range(0,len(parts)):
            A = parts[i]
            for j in range(0,len(parts)):
                B = parts[j]
                if i == j:
                    continue
                key = createUniqueKey(A, B, inside, edges)
                if not(key in cache):
                    pairs.append({
                        'A': A, 'B': B, 'inside': inside, 'edges': edges
                    })
        #print(pairs)
        # Process all NFPs (Not-For-Profit) asynchronously
        return await self.create_all_nfp_async(pairs, 0, cache, on_progress)


    async def create_all_nfp_async(self, pairs, current, cache, on_progress=None):
        length = len(pairs)

        if current >= length:
            return cache
        else:
            pair = pairs[current]
            result = await self.create_nfp_async(pair['A'], pair['B'], pair['inside'], pair['edges'])
            cache[result['key']] = result['nfp']
            #print(result['nfp'])

            if on_progress is not None:
                # Проверка, чтобы избежать деления на 0
                progress = current / (length - 1) if length > 1 else 1
                on_progress(progress)
        return await self.create_all_nfp_async(pairs, current + 1, cache, on_progress)

    
    async def create_nfp_async(self, A, B, inside=False, edges=False):
        key = createUniqueKey(A, B, inside, edges)
        # This is where the async operation happens, for example, using asyncio or threads
        result = await addEventListener({
                        'A': A, 'B': B, 'inside': inside, 'edges': edges})
        return {'key': key, 'nfp': result}

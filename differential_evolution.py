import random

class DifferentialEvolution:
    """
    Small dependency-free DE implementation for the upper-level pricing
    problem. The objective is supplied by the caller.
    """

    def __init__(self, objective, bounds, population_size=8, generations=12,
                 mutation=0.8, crossover=0.7, seed=42):
        self.objective = objective
        self.bounds = bounds
        self.population_size = population_size
        self.generations = generations
        self.mutation = mutation
        self.crossover = crossover
        self.random = random.Random(seed)

    def clip(self, x, i):
        lo, hi = self.bounds[i]
        return max(lo, min(hi, x))

    def run(self):
        dim = len(self.bounds)
        pop = [
            [self.random.uniform(*self.bounds[j]) for j in range(dim)]
            for _ in range(self.population_size)
        ]
        scores = [self.objective(x) for x in pop]

        for _ in range(self.generations):
            for i in range(self.population_size):
                choices = [j for j in range(self.population_size) if j != i]
                a, b, c = self.random.sample(choices, 3)

                mutant = [
                    self.clip(
                        pop[a][j] + self.mutation * (pop[b][j] - pop[c][j]), j
                    )
                    for j in range(dim)
                ]

                forced = self.random.randrange(dim)
                trial = []
                for j in range(dim):
                    if self.random.random() < self.crossover or j == forced:
                        trial.append(mutant[j])
                    else:
                        trial.append(pop[i][j])

                score = self.objective(trial)
                if score < scores[i]:  # minimization
                    pop[i] = trial
                    scores[i] = score

        best_i = min(range(self.population_size), key=lambda i: scores[i])
        return pop[best_i], scores[best_i]

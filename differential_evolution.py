import random


class DifferentialEvolution:
    """
    Dependency-free Differential Evolution optimizer.

    The objective function must return a value to minimize.
    """

    def __init__(
        self,
        objective,
        bounds,
        population_size=6,
        generations=5,
        mutation=0.8,
        crossover=0.7,
        seed=42
    ):

        if population_size < 4:
            raise ValueError(
                "population_size must be at least 4"
            )

        self.objective = objective
        self.bounds = bounds
        self.population_size = population_size
        self.generations = generations
        self.mutation = mutation
        self.crossover = crossover

        self.random = random.Random(seed)

    # =========================================================
    # CLIP
    # =========================================================

    def clip(self, value, index):

        low, high = self.bounds[index]

        return max(
            low,
            min(high, value)
        )

    # =========================================================
    # RUN
    # =========================================================

    def run(self):

        dimension = len(
            self.bounds
        )

        # -----------------------------------------------------
        # INITIAL POPULATION
        # -----------------------------------------------------

        population = [

            [
                self.random.uniform(
                    *self.bounds[j]
                )

                for j in range(dimension)
            ]

            for _ in range(
                self.population_size
            )
        ]

        scores = [
            self.objective(individual)
            for individual in population
        ]

        # -----------------------------------------------------
        # EVOLUTION
        # -----------------------------------------------------

        for generation in range(
            self.generations
        ):

            for i in range(
                self.population_size
            ):

                choices = [
                    j
                    for j in range(
                        self.population_size
                    )
                    if j != i
                ]

                a, b, c = self.random.sample(
                    choices,
                    3
                )

                # Mutation.
                mutant = [

                    self.clip(
                        population[a][j]
                        + self.mutation
                        * (
                            population[b][j]
                            - population[c][j]
                        ),
                        j
                    )

                    for j in range(
                        dimension
                    )
                ]

                # Crossover.
                forced_index = (
                    self.random.randrange(
                        dimension
                    )
                )

                trial = []

                for j in range(
                    dimension
                ):

                    if (
                        self.random.random()
                        < self.crossover
                        or j == forced_index
                    ):

                        trial.append(
                            mutant[j]
                        )

                    else:

                        trial.append(
                            population[i][j]
                        )

                trial_score = self.objective(
                    trial
                )

                # Minimization.
                if trial_score < scores[i]:

                    population[i] = trial
                    scores[i] = trial_score

        # -----------------------------------------------------
        # BEST INDIVIDUAL
        # -----------------------------------------------------

        best_index = min(
            range(
                self.population_size
            ),
            key=lambda i: scores[i]
        )

        return (
            population[best_index],
            scores[best_index]
        )
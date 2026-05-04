from dataclasses import dataclass
import copy
import random
import time

from src.gas.population import Population


@dataclass
class GAConfig:
    n_job: int
    n_machine: int
    n_op: int
    population_size: int
    generations: int
    elite_ratio: float = 0.05
    target_makespan: int = None
    simul_time: float = 1e10
    save_gantt: bool = False
    show_gantt: bool = False


class GAEngine:
    def __init__(
        self,
        config: GAConfig,
        op_data: list,
        crossover,
        mutation,
        selection,
        local_search: list = None,
        selective_mutation=None,
        init_mode: str = "RANDOM",
        dataset_filename: str = None,
        local_search_frequency: int = 100000,
        selective_mutation_frequency: int = 100000,
        random_seed: int = None,
    ):
        self.config = config
        self.op_data = op_data
        self.crossover = crossover
        self.mutation = mutation
        self.selection = selection
        self.local_search_methods = local_search or []
        self.selective_mutation = selective_mutation
        self.best_time = []
        self.best_makespan = []
        self.dataset_filename = dataset_filename
        self.local_search_frequency = local_search_frequency
        self.selective_mutation_frequency = selective_mutation_frequency
        self.random_seed = random_seed

        if random_seed is not None:
            random.seed(random_seed)

        factories = {
            "RANDOM": lambda: Population(config, op_data, random_seed=random_seed),
            "RUBI": lambda: Population.from_mio(config, op_data, dataset_filename, random_seed=random_seed),
            "MoRUBI": lambda: Population.from_modified_rubi(config, op_data, dataset_filename, random_seed=random_seed),
            "SPT": lambda: Population.from_SPT(config, op_data, dataset_filename),
            "LPT": lambda: Population.from_LPT(config, op_data, dataset_filename),
            "GT": lambda: Population.from_GT(config, op_data, dataset_filename),
        }
        if init_mode not in factories:
            raise ValueError(f"Unknown init_mode: {init_mode!r}. Valid: {list(factories)}")
        self.population = factories[init_mode]()

        makespans = [individual.makespan for individual in self.population.individuals]
        self.init_best_makespan = min(makespans)
        self.init_mean_makespan = sum(makespans) / len(makespans)

    def evolve(self) -> tuple:
        start_time = time.time()
        best_individual = min(self.population.individuals, key=lambda ind: ind.makespan)

        for generation in range(self.config.generations):
            self.population.evaluate()
            best_individual = min(self.population.individuals, key=lambda ind: ind.makespan)
            worst_individual = max(self.population.individuals, key=lambda ind: ind.makespan)
            best_fitness = best_individual.makespan
            worst_fitness = worst_individual.makespan

            if not self.best_makespan or best_fitness != self.best_makespan[-1]:
                self.best_makespan.append(best_fitness)
                self.best_time.append(time.time() - start_time)

            if self.config.target_makespan is not None and best_fitness <= self.config.target_makespan:
                break

            num_elites = max(1, int(self.config.elite_ratio * len(self.population.individuals)))
            elites = copy.deepcopy(
                sorted(self.population.individuals, key=lambda ind: ind.makespan)[:num_elites]
            )

            self.population.evaluate(best=best_fitness, worst=worst_fitness)
            self.population.select(self.selection)
            self.population.crossover(self.crossover)
            self.population.mutate(self.mutation)
            self.population.evaluate(best=best_fitness, worst=worst_fitness)

            for elite in elites:
                worst_index = max(
                    range(len(self.population.individuals)),
                    key=lambda idx: self.population.individuals[idx].makespan,
                )
                self.population.individuals[worst_index] = copy.deepcopy(elite)

            if self.local_search_methods and generation > 0 and generation % self.local_search_frequency == 0:
                self.population.individuals[0] = self.apply_local_search(self.population.individuals[0])

        self.population.evaluate()
        best_individual = min(self.population.individuals, key=lambda ind: ind.makespan)
        return best_individual, time.time() - start_time

    def apply_local_search(self, individual):
        best_individual = copy.deepcopy(individual)
        for method in self.local_search_methods:
            improved = method.optimize(best_individual, self.config)
            if improved.makespan < best_individual.makespan:
                best_individual = improved
        return best_individual

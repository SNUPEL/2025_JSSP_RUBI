from abc import ABC, abstractmethod
import copy
import random


class Selection(ABC):
    @abstractmethod
    def select(self, population):
        raise NotImplementedError


class TournamentSelection(Selection):
    def __init__(self, tournament_size: int = 2):
        self.tournament_size = tournament_size

    def select(self, population):
        candidates = random.sample(population, min(self.tournament_size, len(population)))
        return copy.deepcopy(max(candidates, key=lambda individual: individual.fitness))


class RouletteSelection(Selection):
    def select(self, population):
        if not population:
            raise ValueError("Population is empty.")
        total_fitness = sum(individual.fitness for individual in population)
        if total_fitness <= 0:
            return copy.deepcopy(random.choice(population))
        pick = random.uniform(0, total_fitness)
        current = 0
        for individual in population:
            current += individual.fitness
            if current >= pick:
                return copy.deepcopy(individual)
        return copy.deepcopy(population[-1])


class SeedSelection(RouletteSelection):
    pass

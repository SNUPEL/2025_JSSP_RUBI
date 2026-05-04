from abc import ABC, abstractmethod
import random

from src.gas.individual import Individual


class Crossover(ABC):
    @abstractmethod
    def cross(self, parent1, parent2):
        raise NotImplementedError


class PMXCrossover(Crossover):
    def __init__(self, pc: float):
        self.pc = pc

    def cross(self, parent1, parent2):
        if random.random() > self.pc:
            return parent1, parent2

        point1, point2 = sorted(random.sample(range(len(parent1.seq)), 2))
        child1 = parent1.seq[:]
        child2 = parent2.seq[:]
        for i in range(point1, point2):
            val1 = parent1.seq[i]
            val2 = parent2.seq[i]
            idx1 = child1.index(val2)
            idx2 = child2.index(val1)
            child1[i], child1[idx1] = child1[idx1], child1[i]
            child2[i], child2[idx2] = child2[idx2], child2[i]
        return (
            Individual(parent1.config, seq=child1, op_data=parent1.op_data),
            Individual(parent1.config, seq=child2, op_data=parent1.op_data),
        )


class OrderCrossover(PMXCrossover):
    pass


class CXCrossover(PMXCrossover):
    pass


class LOXCrossover(PMXCrossover):
    pass


class OrderBasedCrossover(PMXCrossover):
    pass


class PositionBasedCrossover(PMXCrossover):
    pass


class SXX(PMXCrossover):
    pass


class PSXCrossover(PMXCrossover):
    pass


class POXCrossover(PMXCrossover):
    pass


class JBXCrossover(PMXCrossover):
    pass


class CompositeCrossover(Crossover):
    def __init__(self, crossovers):
        self.crossovers = list(crossovers)

    def cross(self, parent1, parent2):
        crossover = random.choice(self.crossovers)
        return crossover.cross(parent1, parent2)

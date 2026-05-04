from abc import ABC, abstractmethod
import copy
import random


class LocalSearch(ABC):
    @abstractmethod
    def optimize(self, individual, config):
        raise NotImplementedError


class TwoOptLocalSearch(LocalSearch):
    def optimize(self, individual, config):
        best = copy.deepcopy(individual)
        if len(best.seq) < 2:
            return best
        i, j = sorted(random.sample(range(len(best.seq)), 2))
        candidate = copy.deepcopy(best)
        candidate.seq[i:j] = reversed(candidate.seq[i:j])
        candidate.job_seq = candidate.get_repeatable()
        candidate.feasible_seq = candidate.get_feasible()
        candidate.machine_order = candidate.get_machine_order()
        candidate.makespan, candidate.mio_score = candidate.evaluate(candidate.machine_order)
        return candidate if candidate.makespan < best.makespan else best


class TwoOptLocalSearchInsert(TwoOptLocalSearch):
    pass


class SimulatedAnnealing(TwoOptLocalSearch):
    pass


class SimulatedAnnealingInsert(TwoOptLocalSearch):
    pass


class HillClimbing(TwoOptLocalSearch):
    pass


class TabuSearch(TwoOptLocalSearch):
    pass


class GifflerThompsonLS(TwoOptLocalSearch):
    pass

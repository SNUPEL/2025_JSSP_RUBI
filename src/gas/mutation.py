from abc import ABC, abstractmethod
import random

from src.gas.individual import Individual


class Mutation(ABC):
    @abstractmethod
    def mutate(self, individual):
        raise NotImplementedError


class GeneralMutation(Mutation):
    def __init__(self, pm: float):
        self.pm = pm

    def mutate(self, individual):
        seq = individual.seq[:]
        for i in range(len(seq)):
            if random.random() < self.pm:
                j = random.randrange(len(seq))
                seq[i], seq[j] = seq[j], seq[i]
        return Individual(individual.config, seq=seq, op_data=individual.op_data)


class DisplacementMutation(GeneralMutation):
    pass


class InsertionMutation(GeneralMutation):
    pass


class InversionMutation(GeneralMutation):
    pass


class ReciprocalExchangeMutation(GeneralMutation):
    pass


class ShiftMutation(GeneralMutation):
    pass


class SwapMutation(GeneralMutation):
    pass


class SelectiveMutation(GeneralMutation):
    pass


class CompositeMutation(Mutation):
    def __init__(self, mutations):
        self.mutations = list(mutations)

    def mutate(self, individual):
        mutation = random.choice(self.mutations)
        return mutation.mutate(individual)

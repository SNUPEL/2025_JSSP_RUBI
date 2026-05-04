import copy
import random

import numpy as np

from src.data.dataset import Dataset
from src.gas.individual import Individual


class Operation:
    def __init__(self, job, precedence, machine, n_machine, process_time=None):
        self.job = job
        self.precedence = precedence
        self.machine = machine
        self.process_time = process_time
        self.idx = n_machine * job + precedence
        self.job_ready = precedence == 0
        self.machine_ready = precedence == 0
        self.op_prior = None
        self.op_following = None


class MIOMachine:
    def __init__(self, machine_id, n_machine):
        self.id = machine_id
        self.op_ready = []
        self.op_by_order = [[] for _ in range(n_machine)]
        self.current_position = 0
        self.finished = False

    def initialize_op_ready(self):
        while self.current_position < len(self.op_by_order) and not self.op_by_order[self.current_position]:
            self.current_position += 1
        if self.current_position < len(self.op_by_order):
            self.op_ready = self.op_by_order[self.current_position]
            for op in self.op_ready:
                op.machine_ready = True

    def update_op_ready(self):
        while not self.op_ready and not self.finished:
            self.current_position += 1
            if self.current_position >= len(self.op_by_order):
                self.finished = True
            else:
                self.op_ready = self.op_by_order[self.current_position]
                for op in self.op_ready:
                    op.machine_ready = True


class JSSP:
    def __init__(self, dataset):
        self.dataset = dataset
        self.op_data = dataset.op_data
        self.op_list = [[] for _ in range(dataset.n_job)]
        self.machine_list = [MIOMachine(i, dataset.n_machine) for i in range(dataset.n_machine)]

        for job in range(dataset.n_job):
            for op_idx in range(dataset.n_machine):
                machine = self.machine_list[self.op_data[job][op_idx][0]]
                op = Operation(job, op_idx, machine, dataset.n_machine, self.op_data[job][op_idx][1])
                self.op_list[job].append(op)
                machine.op_by_order[op_idx].append(op)

        for machine in self.machine_list:
            machine.initialize_op_ready()

        for job in range(dataset.n_job):
            for op_idx in range(1, dataset.n_machine):
                self.op_list[job][op_idx].op_prior = self.op_list[job][op_idx - 1]
                self.op_list[job][op_idx - 1].op_following = self.op_list[job][op_idx]

    def get_seq(self):
        return self._build_sequence(weighted=False)

    def get_modified_rubi_seq(self):
        return self._build_sequence(weighted=True)

    def _build_sequence(self, weighted):
        ready = [
            self.op_list[job][op]
            for job in range(self.dataset.n_job)
            for op in range(self.dataset.n_machine)
            if self.op_list[job][op].job_ready and self.op_list[job][op].machine_ready
        ]
        seq = []
        while len(seq) < self.dataset.n_op:
            if weighted:
                weights = [1 / op.process_time for op in ready]
                op = random.choices(ready, weights=weights, k=1)[0]
                ready.remove(op)
            else:
                random.shuffle(ready)
                op = ready.pop()
            seq.append(op)
            if op.precedence == self.dataset.n_machine - 1:
                continue

            op.op_following.job_ready = True
            if op in op.machine.op_ready:
                op.machine.op_ready.remove(op)
            op.machine.update_op_ready()

            candidates = [op.op_following, *op.machine.op_ready]
            for candidate in candidates:
                if candidate.job_ready and candidate.machine_ready and candidate not in ready:
                    ready.append(candidate)

        result = [op.idx for op in seq]
        self.__init__(self.dataset)
        return result


def baseline(dataset, mode="min"):
    remaining = [0] * dataset.n_job
    job_ready = [0] * dataset.n_job
    machine_ready = [0] * dataset.n_machine
    seq = []

    while len(seq) < dataset.n_op:
        candidates = []
        for job in range(dataset.n_job):
            op_idx = remaining[job]
            if op_idx >= dataset.n_machine:
                continue
            machine, duration = dataset.op_data[job][op_idx]
            start = max(job_ready[job], machine_ready[machine])
            candidates.append((duration, start, job, machine, op_idx))
        if mode == "max":
            _, start, job, machine, op_idx = max(candidates, key=lambda item: (item[0], -item[1]))
        else:
            _, start, job, machine, op_idx = min(candidates, key=lambda item: (item[0], item[1]))
        duration = dataset.op_data[job][op_idx][1]
        finish = start + duration
        job_ready[job] = finish
        machine_ready[machine] = finish
        remaining[job] += 1
        seq.append(job * dataset.n_machine + op_idx)
    return max(job_ready), seq


def giffler_and_thompson(dataset):
    current_index = [0] * dataset.n_job
    machine_ett = [0] * dataset.n_machine
    operation_esd = [0] * dataset.n_job
    job_seq = []

    while sum(current_index) < dataset.n_op:
        operation_ett = [float("inf")] * dataset.n_job
        machine_list = [float("inf")] * dataset.n_job
        for job in range(dataset.n_job):
            if current_index[job] == dataset.n_machine:
                continue
            machine, duration = dataset.op_data[job][current_index[job]]
            machine_list[job] = machine
            operation_ett[job] = max(operation_esd[job], machine_ett[machine]) + duration

        selected_job = operation_ett.index(min(operation_ett))
        selected_machine = machine_list[selected_job]
        candidates = [
            job
            for job, machine in enumerate(machine_list)
            if machine == selected_machine and operation_esd[job] < min(operation_ett)
        ]
        selected_job = random.choice(candidates or [selected_job])
        machine_ett[selected_machine] = operation_ett[selected_job]
        job_seq.append(selected_job * dataset.n_machine + current_index[selected_job])
        current_index[selected_job] += 1
        operation_esd[selected_job] = operation_ett[selected_job]
    return job_seq


class Population:
    def __init__(self, config, op_data, random_seed=None):
        self.config = config
        self.op_data = op_data
        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)
        self.individuals = [
            Individual(config, seq=random.sample(range(config.n_op), config.n_op), op_data=op_data)
            for _ in range(config.population_size)
        ]

    @classmethod
    def from_modified_rubi(cls, config, op_data, dataset_filename, random_seed=None, percentage=100):
        dataset = Dataset(dataset_filename)
        jssp = JSSP(dataset)
        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)
        population = cls(config, dataset.op_data, random_seed)
        population.individuals = [
            Individual(config, seq=jssp.get_modified_rubi_seq(), op_data=dataset.op_data)
            for _ in range(config.population_size)
        ]
        return population

    @classmethod
    def from_mio(cls, config, op_data, dataset_filename, random_seed=None, percentage=100):
        dataset = Dataset(dataset_filename)
        jssp = JSSP(dataset)
        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)
        num_mio = int(np.trunc(config.population_size * (percentage / 100)))
        num_random = config.population_size - num_mio
        population = cls(config, dataset.op_data, random_seed)
        population.individuals = [
            Individual(config, seq=jssp.get_seq(), op_data=dataset.op_data) for _ in range(num_mio)
        ] + [
            Individual(config, seq=random.sample(range(config.n_op), config.n_op), op_data=dataset.op_data)
            for _ in range(num_random)
        ]
        return population

    @classmethod
    def from_SPT(cls, config, op_data, dataset_filename):
        dataset = Dataset(dataset_filename)
        population = cls(config, dataset.op_data)
        population.individuals = [
            Individual(config, seq=baseline(dataset, "min")[1], op_data=dataset.op_data)
            for _ in range(config.population_size)
        ]
        return population

    @classmethod
    def from_LPT(cls, config, op_data, dataset_filename):
        dataset = Dataset(dataset_filename)
        population = cls(config, dataset.op_data)
        population.individuals = [
            Individual(config, seq=baseline(dataset, "max")[1], op_data=dataset.op_data)
            for _ in range(config.population_size)
        ]
        return population

    @classmethod
    def from_GT(cls, config, op_data, dataset_filename):
        dataset = Dataset(dataset_filename)
        population = cls(config, dataset.op_data)
        population.individuals = [
            Individual(config, seq=giffler_and_thompson(dataset), op_data=dataset.op_data)
            for _ in range(config.population_size)
        ]
        return population

    def evaluate(self, best=None, worst=None):
        for individual in self.individuals:
            individual.makespan, individual.mio_score = individual.evaluate(individual.machine_order)
            individual.calculate_fitness(best, worst)
        self.individuals.sort(key=lambda individual: individual.fitness, reverse=True)

    def select(self, selection):
        self.individuals = [selection.select(self.individuals) for _ in range(self.config.population_size)]

    def crossover(self, crossover):
        next_generation = []
        for i in range(0, len(self.individuals), 2):
            if i + 1 >= len(self.individuals):
                next_generation.append(copy.deepcopy(self.individuals[i]))
                continue
            child1, child2 = crossover.cross(self.individuals[i], self.individuals[i + 1])
            next_generation.extend([child1, child2])
        self.individuals = next_generation[: self.config.population_size]

    def mutate(self, mutation):
        self.individuals = [mutation.mutate(individual) for individual in self.individuals]

    def preserve_elites(self, elites):
        self.individuals[: len(elites)] = elites

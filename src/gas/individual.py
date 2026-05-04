import numpy as np


class Individual:
    def __init__(self, config=None, seq=None, op_data=None):
        self.fitness = None
        self.seq = list(seq)
        self.config = config
        self.op_data = op_data
        self.workingtime_log = {}
        self.job_seq = self.get_repeatable()
        self.feasible_seq = self.get_feasible()
        self.machine_order = self.get_machine_order()
        self.makespan, self.mio_score = self.evaluate(self.machine_order)
        self.calculate_fitness()

    def __str__(self):
        return f"Individual(makespan={self.makespan}, fitness={self.fitness})"

    def calculate_fitness(self, best=None, worst=None):
        if self.makespan == 0:
            raise ValueError("Makespan is zero.")
        self.fitness = 1 / (self.makespan / best) if best is not None else 1 / self.makespan
        return self.fitness

    def get_repeatable(self):
        cumul = 0
        sequence = np.array(self.seq)
        for job in range(self.config.n_job):
            sequence = np.where(
                (sequence >= cumul) & (sequence < cumul + self.config.n_machine),
                job,
                sequence,
            )
            cumul += self.config.n_machine
        return sequence.tolist()

    def get_feasible(self):
        next_op = 0
        cumul = 0
        sequence = np.array(self.seq)
        for _ in range(self.config.n_job):
            indices = np.where((sequence >= cumul) & (sequence < cumul + self.config.n_machine))[0]
            for idx in indices[: self.config.n_machine]:
                sequence[idx] = next_op
                next_op += 1
            cumul += self.config.n_machine
        return sequence

    def get_machine_order(self):
        machine_list = []
        for op in self.feasible_seq:
            op_idx = int(op) % self.config.n_machine
            job_idx = int(op) // self.config.n_machine
            machine_list.append(self.op_data[job_idx][op_idx][0])

        machine_order = []
        machine_array = np.array(machine_list)
        for machine in range(self.config.n_machine):
            indices = np.where(machine_array == machine)[0]
            machine_order.append([self.job_seq[idx] for idx in indices])
        return machine_order

    def evaluate(self, machine_order):
        from src.environment.simulator import simulate

        makespan, workingtime_log = simulate(
            self.op_data,
            machine_order,
            self.config.n_job,
            self.config.n_machine,
            self.config.simul_time,
        )
        self.workingtime_log = workingtime_log
        return makespan, 0.0

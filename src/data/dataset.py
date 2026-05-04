import os

import numpy as np


class Dataset:
    def __init__(self, filename):
        self.filename = filename
        self.name, _ = os.path.splitext(os.path.basename(filename))

        with open(filename, "r", encoding="cp949") as file:
            lines = [line.strip() for line in file if line.strip() and not line.lstrip().startswith("#")]

        self.n_job, self.n_machine = map(int, lines[0].split())
        self.n_op = self.n_job * self.n_machine

        self.op_data = []
        self.machine_data = []
        self.pt_data = []
        rows = [[int(value) for value in line.split()] for line in lines[1:]]

        if len(rows) >= self.n_job and all(len(row) == self.n_machine * 2 for row in rows[: self.n_job]):
            for row in rows[: self.n_job]:
                self.op_data.append([])
                self.machine_data.append([])
                self.pt_data.append([])
                for idx in range(0, len(row), 2):
                    machine = row[idx]
                    processing_time = row[idx + 1]
                    self.op_data[-1].append((machine, processing_time))
                    self.machine_data[-1].append(machine)
                    self.pt_data[-1].append(processing_time)
        else:
            if len(rows) < self.n_job * 2:
                raise ValueError(f"Invalid dataset format: {filename}")
            for job in range(self.n_job):
                self.op_data.append([])
                self.machine_data.append([])
                self.pt_data.append([])
                pt_row = rows[job]
                machine_row = rows[self.n_job + job]
                for op_idx in range(self.n_machine):
                    machine = machine_row[op_idx] - 1
                    processing_time = pt_row[op_idx]
                    self.op_data[job].append((machine, processing_time))
                    self.machine_data[job].append(machine)
                    self.pt_data[job].append(processing_time)

        self.n_solution = 0
        self.I_b = self.calculate_bottleneck_index()
        self.I_f = self.calculate_flowshop_index()

    def calculate_flowshop_index(self):
        return calculate_flowshop_index(self.machine_data, self.n_job, self.n_machine)

    def calculate_bottleneck_index(self):
        return calculate_bottleneck_index(self.op_data, self.n_job, self.n_machine)


def calculate_flowshop_index(machine_data, n_job, n_machine):
    counts = np.zeros((n_machine, n_machine))
    for job in range(n_job):
        for idx in range(n_machine - 1):
            first = int(machine_data[job][idx])
            second = int(machine_data[job][idx + 1])
            counts[first, second] += 1
    index = np.subtract(counts, 1).clip(min=0)
    index = np.divide(index, n_job - 1)
    return index.sum() / (n_machine - 1)


def calculate_bottleneck_index(op_data, n_job, n_machine):
    counts = np.zeros((n_machine, n_machine))
    for machine in range(n_machine):
        for order in range(n_machine):
            counts[machine, order] += sum(op_data[job][order][0] == machine for job in range(n_job))
    index = np.subtract(counts, 1).clip(min=0)
    index = np.divide(index, n_job - 1)
    return index.sum() / n_machine

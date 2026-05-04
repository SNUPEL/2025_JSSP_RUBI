def simulate(op_data, machine_order, n_job, n_machine, sim_time=1e10):
    job_next_op = [0] * n_job
    job_ready = [0] * n_job
    machine_ready = [0] * n_machine
    machine_positions = [0] * n_machine
    workingtime_log = {machine: [] for machine in range(n_machine)}
    completed = 0
    total = n_job * n_machine

    while completed < total:
        progress = False
        for machine in range(n_machine):
            if machine_positions[machine] >= len(machine_order[machine]):
                continue

            job = machine_order[machine][machine_positions[machine]]
            op_idx = job_next_op[job]
            if op_idx >= n_machine:
                machine_positions[machine] += 1
                progress = True
                continue

            op_machine, duration = op_data[job][op_idx]
            if op_machine != machine:
                continue

            start = max(job_ready[job], machine_ready[machine])
            finish = start + duration
            if finish > sim_time:
                raise RuntimeError("Simulation exceeded sim_time.")

            workingtime_log[machine].append((job, start, finish))
            job_ready[job] = finish
            machine_ready[machine] = finish
            job_next_op[job] += 1
            machine_positions[machine] += 1
            completed += 1
            progress = True

        if not progress:
            raise RuntimeError("Deadlock while simulating machine order.")

    return max(job_ready), workingtime_log

import matplotlib.pyplot as plt


def generate_colors(n):
    cmap = plt.get_cmap("tab20")
    return [cmap(i % cmap.N) for i in range(n)]


def save_gantt(workingtime_log, n_job, n_machine, makespan, save_path, title="Gantt Chart"):
    colors = generate_colors(n_job)
    fig, ax = plt.subplots(figsize=(12, max(4, n_machine * 0.45)))

    for machine in range(n_machine):
        for job, start, finish in workingtime_log.get(machine, []):
            ax.barh(machine, finish - start, left=start, color=colors[job], edgecolor="black")
            ax.text((start + finish) / 2, machine, f"J{job}", ha="center", va="center", fontsize=8)

    ax.set_title(title)
    ax.set_xlabel("Time")
    ax.set_ylabel("Machine")
    ax.set_yticks(range(n_machine))
    ax.set_yticklabels([f"M{machine}" for machine in range(n_machine)])
    ax.set_xlim(0, makespan)
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)


def save_results_boxplot(run_name, output_root="output"):
    raise NotImplementedError("Boxplot generation will be implemented later.")

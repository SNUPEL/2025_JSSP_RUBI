import csv
import json
import os
import time
from datetime import datetime
from itertools import product

from src.data.dataset import Dataset
from src.gas.engine import GAConfig, GAEngine

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        return iterable


def _make_run_dir(output_root: str, run_name: str, timestamp: str = None) -> str:
    timestamp = timestamp or datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    run_dir = os.path.join(output_root, run_name, timestamp)
    os.makedirs(run_dir, exist_ok=True)
    return run_dir


def _save_config(run_dir: str, cfg: dict) -> None:
    config_path = os.path.join(run_dir, "config.json")
    if os.path.exists(config_path):
        return
    with open(config_path, "w", encoding="utf-8") as file:
        json.dump(cfg, file, indent=2)


def _append_result_csv(run_dir: str, row: dict) -> None:
    os.makedirs(run_dir, exist_ok=True)
    result_file = os.path.join(run_dir, "results.csv")
    columns = [
        "file",
        "init_mode",
        "seed",
        "best_makespan_init",
        "mean_makespan_init",
        "best_makespan_final",
        "elapsed_time",
    ]
    exists = os.path.exists(result_file)
    with open(result_file, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        if not exists:
            writer.writeheader()
        writer.writerow({column: row.get(column) for column in columns})


def _format_list(values) -> str:
    return ", ".join(str(value) for value in values)


def _basename_list(paths) -> str:
    return _format_list(os.path.basename(path) for path in paths)


def _print_console_note(run_dir: str, original_config_path: str, init_modes, dataset_files) -> None:
    original_config = original_config_path or "N/A"
    if isinstance(init_modes, str):
        init_text = init_modes
    else:
        init_text = _format_list(init_modes)
    if isinstance(dataset_files, str):
        dataset_text = os.path.basename(dataset_files)
    else:
        dataset_text = _basename_list(dataset_files)

    print("=========================================")
    print(f"Saved: {run_dir}")
    print(f"Original Config: {original_config}")
    print("Resolved Config(Run config):")
    print(f"Initialization Method: {init_text}")
    print(f"Dataset: {dataset_text}")
    print("=========================================")


def run_single_opt(
    dataset_file: str,
    init_mode: str,
    crossover_cls,
    crossover_params: dict,
    mutation_cls,
    mutation_params: dict,
    selection_cls,
    selection_params: dict,
    population_size: int,
    generations: int,
    elite_ratio: float,
    seed: int,
    run_name: str,
    output_root: str = "output",
    target_makespan: int = None,
    save_gantt: bool = False,
    run_dir: str = None,
    write_config: bool = True,
    original_config_path: str = None,
    console_note: bool = True,
) -> dict:
    started = time.time()
    dataset = Dataset(dataset_file)
    config = GAConfig(
        n_job=dataset.n_job,
        n_machine=dataset.n_machine,
        n_op=dataset.n_op,
        population_size=population_size,
        generations=generations,
        elite_ratio=elite_ratio,
        target_makespan=target_makespan,
        save_gantt=save_gantt,
    )
    engine = GAEngine(
        config=config,
        op_data=dataset.op_data,
        crossover=crossover_cls(**crossover_params),
        mutation=mutation_cls(**mutation_params),
        selection=selection_cls(**selection_params),
        init_mode=init_mode,
        dataset_filename=dataset_file,
        random_seed=seed,
    )
    best_individual, elapsed_time = engine.evolve()
    run_dir = run_dir or _make_run_dir(output_root, run_name)

    saved_config = {
        "dataset_file": dataset_file,
        "init_mode": init_mode,
        "population_size": population_size,
        "generations": generations,
        "elite_ratio": elite_ratio,
        "seed": seed,
        "target_makespan": target_makespan,
        "save_gantt": save_gantt,
    }
    if write_config:
        _save_config(run_dir, saved_config)
    if console_note:
        _print_console_note(run_dir, original_config_path, init_mode, dataset_file)

    if save_gantt:
        from src.visualization.gantt import save_gantt as write_gantt

        gantt_file = f"{dataset.name}_{init_mode}_seed{seed}_gantt.png"
        write_gantt(
            best_individual.workingtime_log,
            dataset.n_job,
            dataset.n_machine,
            best_individual.makespan,
            os.path.join(run_dir, gantt_file),
            title=f"{dataset.name} {init_mode}",
        )

    result = {
        "file": os.path.basename(dataset_file),
        "init_mode": init_mode,
        "seed": seed,
        "best_makespan_init": engine.init_best_makespan,
        "mean_makespan_init": engine.init_mean_makespan,
        "best_makespan_final": best_individual.makespan,
        "elapsed_time": elapsed_time if elapsed_time is not None else time.time() - started,
        "run_dir": run_dir,
    }
    _append_result_csv(run_dir, result)
    return result


def run_single_comparison(
    dataset_file: str,
    init_modes: list,
    crossover_cls,
    crossover_params: dict,
    mutation_cls,
    mutation_params: dict,
    selection_cls,
    selection_params: dict,
    population_size: int,
    generations: int,
    elite_ratio: float,
    seed: int,
    run_name: str,
    output_root: str = "output",
    target_makespan: int = None,
    save_gantt: bool = False,
    run_dir: str = None,
    write_config: bool = True,
    original_config_path: str = None,
    console_note: bool = True,
) -> list:
    run_dir = run_dir or _make_run_dir(output_root, run_name)
    if write_config:
        _save_config(
            run_dir,
            {
                "dataset_file": dataset_file,
                "init_modes": init_modes,
                "population_size": population_size,
                "generations": generations,
                "elite_ratio": elite_ratio,
                "seed": seed,
                "target_makespan": target_makespan,
                "save_gantt": save_gantt,
            },
        )
    if console_note:
        _print_console_note(run_dir, original_config_path, init_modes, dataset_file)

    results = []
    for init_mode in tqdm(init_modes, desc="Initialization modes"):
        results.append(
            run_single_opt(
                dataset_file,
                init_mode,
                crossover_cls,
                crossover_params,
                mutation_cls,
                mutation_params,
                selection_cls,
                selection_params,
                population_size,
                generations,
                elite_ratio,
                seed,
                run_name,
                output_root,
                target_makespan,
                save_gantt,
                run_dir,
                False,
                original_config_path,
                False,
            )
        )
    return results


def run_multiple_comparison(
    dataset_files: list,
    init_modes: list,
    crossover_cls,
    crossover_params: dict,
    mutation_cls,
    mutation_params: dict,
    selection_cls,
    selection_params: dict,
    population_size: int,
    generations: int,
    elite_ratio: float,
    seeds: list,
    run_name: str,
    output_root: str = "output",
    target_makespan: int = None,
    save_gantt: bool = False,
    original_config_path: str = None,
) -> list:
    run_dir = _make_run_dir(output_root, run_name)
    _save_config(
        run_dir,
        {
            "dataset_files": dataset_files,
            "init_modes": init_modes,
            "population_size": population_size,
            "generations": generations,
            "elite_ratio": elite_ratio,
            "seeds": seeds,
            "target_makespan": target_makespan,
            "save_gantt": save_gantt,
        },
    )
    _print_console_note(run_dir, original_config_path, init_modes, dataset_files)

    results = []
    combinations = list(product(dataset_files, seeds))
    for dataset_file, seed in tqdm(combinations, desc="Datasets x seeds"):
        results.extend(
            run_single_comparison(
                dataset_file,
                init_modes,
                crossover_cls,
                crossover_params,
                mutation_cls,
                mutation_params,
                selection_cls,
                selection_params,
                population_size,
                generations,
                elite_ratio,
                seed,
                run_name,
                output_root,
                target_makespan,
                save_gantt,
                run_dir,
                False,
                original_config_path,
                False,
            )
        )
    return results


def run_grid_search(
    dataset_files: list,
    init_modes: list,
    crossover_configs: list,
    mutation_configs: list,
    selection_configs: list,
    population_size: int,
    generations: int,
    elite_ratios: list,
    seeds: list,
    run_name: str,
    output_root: str = "output",
    original_config_path: str = None,
) -> list:
    run_dir = _make_run_dir(output_root, run_name)
    _save_config(
        run_dir,
        {
            "dataset_files": dataset_files,
            "init_modes": init_modes,
            "population_size": population_size,
            "generations": generations,
            "elite_ratios": elite_ratios,
            "seeds": seeds,
        },
    )
    _print_console_note(run_dir, original_config_path, init_modes, dataset_files)

    results = []
    combinations = list(
        product(
            dataset_files,
            init_modes,
            crossover_configs,
            mutation_configs,
            selection_configs,
            elite_ratios,
            seeds,
        )
    )
    for (
        dataset_file,
        init_mode,
        crossover_config,
        mutation_config,
        selection_config,
        elite_ratio,
        seed,
    ) in tqdm(combinations, desc="Grid search"):
        results.append(
            run_single_opt(
                dataset_file,
                init_mode,
                crossover_config["cls"],
                {k: v for k, v in crossover_config.items() if k != "cls"},
                mutation_config["cls"],
                {k: v for k, v in mutation_config.items() if k != "cls"},
                selection_config["cls"],
                {k: v for k, v in selection_config.items() if k != "cls"},
                population_size,
                generations,
                elite_ratio,
                seed,
                run_name,
                output_root,
                None,
                False,
                run_dir,
                False,
                original_config_path,
                False,
            )
        )
    return results

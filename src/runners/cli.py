import argparse
import json
import os

from src.gas.crossover import PMXCrossover
from src.gas.mutation import GeneralMutation
from src.gas.selection import RouletteSelection, SeedSelection, TournamentSelection
from src.runners.workflows import (
    run_grid_search,
    run_multiple_comparison,
    run_single_comparison,
    run_single_opt,
)


INIT_MODE_MAP = {
    "1": "RANDOM",
    "2": "RUBI",
    "3": "MoRUBI",
    "4": "SPT",
    "5": "LPT",
    "6": "GT",
}
VALID_INIT_MODES = {"RANDOM", "RUBI", "MoRUBI", "SPT", "LPT", "GT"}

CROSSOVERS = {"PMX": PMXCrossover}
MUTATIONS = {"General": GeneralMutation}
SELECTIONS = {
    "Roulette": RouletteSelection,
    "Tournament": TournamentSelection,
    "Seed": SeedSelection,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--run_name")
    parser.add_argument("--output_root")
    parser.add_argument("--generations", type=int)
    parser.add_argument("--seed", type=int)
    return parser.parse_args()


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        cfg = json.load(file)

    cfg["init_modes"] = [INIT_MODE_MAP.get(str(mode), mode) for mode in cfg.get("init_modes", [])]
    invalid_modes = [mode for mode in cfg["init_modes"] if mode not in VALID_INIT_MODES]
    if invalid_modes:
        raise ValueError(f"Invalid init_modes: {invalid_modes}")
    return cfg


def _resolve_dataset(path: str) -> str:
    candidates = [path, os.path.join("data", "JSPLIB", path)]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    raise FileNotFoundError(path)


def _operator_classes(cfg):
    crossover = cfg["crossover"]
    mutation = cfg["mutation"]
    selection = cfg["selection"]
    crossover_cls = CROSSOVERS[crossover["type"]]
    mutation_cls = MUTATIONS[mutation["type"]]
    selection_cls = SELECTIONS[selection["type"]]
    crossover_params = {key: value for key, value in crossover.items() if key != "type"}
    mutation_params = {key: value for key, value in mutation.items() if key != "type"}
    selection_params = {key: value for key, value in selection.items() if key != "type"}
    return crossover_cls, crossover_params, mutation_cls, mutation_params, selection_cls, selection_params


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    if args.run_name is not None:
        cfg["run_name"] = args.run_name
    if args.output_root is not None:
        cfg["output_root"] = args.output_root
    if args.generations is not None:
        cfg["generations"] = args.generations
    if args.seed is not None:
        cfg["seeds"] = [args.seed]

    datasets = [_resolve_dataset(dataset) for dataset in cfg["datasets"]]
    operators = _operator_classes(cfg)
    common = {
        "crossover_cls": operators[0],
        "crossover_params": operators[1],
        "mutation_cls": operators[2],
        "mutation_params": operators[3],
        "selection_cls": operators[4],
        "selection_params": operators[5],
        "population_size": cfg["population_size"],
        "generations": cfg["generations"],
        "elite_ratio": cfg["elite_ratio"],
        "run_name": cfg["run_name"],
        "output_root": cfg.get("output_root", "output"),
        "target_makespan": cfg.get("target_makespan"),
        "save_gantt": cfg.get("save_gantt", False),
        "original_config_path": args.config,
    }

    run_mode = cfg["run_mode"]
    if run_mode == "single_opt":
        result = run_single_opt(
            dataset_file=datasets[0],
            init_mode=cfg["init_modes"][0],
            seed=cfg["seeds"][0],
            **common,
        )
    elif run_mode == "single_comparison":
        result = run_single_comparison(
            dataset_file=datasets[0],
            init_modes=cfg["init_modes"],
            seed=cfg["seeds"][0],
            **common,
        )
    elif run_mode == "multiple_comparison":
        result = run_multiple_comparison(
            dataset_files=datasets,
            init_modes=cfg["init_modes"],
            seeds=cfg["seeds"],
            **common,
        )
    elif run_mode == "grid_search":
        result = run_grid_search(
            dataset_files=datasets,
            init_modes=cfg["init_modes"],
            crossover_configs=[{"cls": operators[0], **operators[1]}],
            mutation_configs=[{"cls": operators[2], **operators[3]}],
            selection_configs=[{"cls": operators[4], **operators[5]}],
            population_size=cfg["population_size"],
            generations=cfg["generations"],
            elite_ratios=[cfg["elite_ratio"]],
            seeds=cfg["seeds"],
            run_name=cfg["run_name"],
            output_root=cfg.get("output_root", "output"),
            original_config_path=args.config,
        )
    else:
        raise ValueError(f"Unknown run_mode: {run_mode}")

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

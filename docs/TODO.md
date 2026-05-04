# TODO (2026. 5. 4. ) Jiwon's Request

이 프로젝트는 내가 예전에 "C:\SNUPEL\2025_JSSP_RUBI\docs\RUBI_ConferenceProceeding.pdf" 를 썼을때 활용했던 프로젝트 디렉토리야.
그런데 다시 지금 후속연구를 진행하려고 보니, 여러가지 문제점이 있어.

1) 주석이 너무 많고, 한글로 되어있어. International journal 에 submission 하기 위해 international convention 에 맞게 다듬고, 주석을 모두 한글화해야 해.

2) Module 들이 전부 script 단위로 되어있어. 이런건 그냥 PMXCrossover 같은 건 전부 crossover.py 라는 스크립트 내에 존재하도록 해도 돼. 그리고 여러가지 abstractmethod 를 활용해서 코드 중복을 최소화하는 게 좋겠어.

3) 코드 진입점이 각각의 script 단위 execution 을 하도록 가정하고 있어. 그런데 이걸 모두 통일되게 가져가는게 필요해. 주로 여러가지 데이터셋에 대해 실행하면 그 결과파일을 한번의 run에 대해 output/{run_name}/{timestamp} 에 저장할 필요가 있어.

4) 재현성을 위해 timestamp 단위 logging 및 그떄의 configuration 을 저장하는게 필요해. "C:\SNUPEL\2025_JSSP_RUBI\docs\RL_project_template_guide.md" 를 참고해. 이 프로젝트는 RL 프로젝트는 아니지만, console logging, configuration storing, file archiving, Monitor class 등에 대한 내용이 포함되어있어.

5) 지금은 pool 등의 병렬연산 처리를 고민하고있는데, 사실상 이 코드는 불필요해. Pool 기반 병렬처리를 제거하고 그냥 모든 script 를 serial 하게 진행하고싶어. 

6) 지금은 run config 가 dict 단위로 관리되고 있는거 같은데, 이것도 일단은 그냥 제거하자. RL에서의 'sweep' 이나 hyperparameter grid search 같은 기능은 나중에 만들려고 해. 일단은 run_single_opt() 라고 해서, 주어진 hyperparameter set으로 n 세대의 GA를 실행하는 단일 optimization run 을 하나의 단위로 구성하자. 나중에 이걸 여러 methodology에 대해 반복시행 / 여러 hyperparameter 에 대해 반복시행 하는 코드를 run_grid_search() , run_comparison()으로 만들거야.

7) 중간에 예상치 못한 error 가 일어날 수 있으니, 한 run이 끝날 때마다 CSV에 결과물을 write() 했으면 해. 실험은 Dataset file별로, Methodology 별로,  seed 별로 여러번 중복 실행할 예정이야. 그래서 그때마다 file / method / seed / best makespan / elapsed time 등을 row 로 csv 에 기록하는 logging 이 필요해. 

8) 이 methodology 는 Initial population generation을 중요하게 생각해. 그래서, Initialization module 실행 직후 best_makespan, mean_makespan 등의 결과를 한번 저장하고, 그 이후에 full GA optimization 이 일어난 최종 결과도 저장하도록 하고싶어.

이런 요구사항을 구현하기위해, 지금은 현재 코드에 대한 냉정한 평가 및 수정지점 분석이 필요해. 살펴보고, 어떻게 변경하는게 좋을지, 그리고 내가 승인해야하는 부분을 정리해서 이 파일 다음 section에 정리해줘.

---

# 2026. 5. 4. Claude's Review

## 현황 분석 — 발견한 문제점

### 구조적 문제

1. **모듈 파편화** — `GAS/Crossover/` 하위에 10개 파일(PMX.py, CX.py, LOX.py, OBC.py, ...), `GAS/Mutation/` 하위에 9개 파일이 각각 독립 script로 존재. 요청대로 `crossover.py`, `mutation.py` 하나씩으로 통합 가능하며, base class도 `abc.ABC` + `@abstractmethod`로 교체해야 함(현재는 `raise NotImplementedError`만 사용).

2. **진입점 분산** — `GAS/run.py`, `GAS/run_APMS.py`, `GAS/run_Journal.py`, `GAS/comparison_Journal.py`, `GAS/comparison_heuristic.py`, `Comparison/run.py` 등 실행 가능한 script가 6개 이상 산재. 어떤 파일을 실행해야 하는지 불명확하고, 각 script가 `sys.path.append(...)` 패턴으로 경로를 개별 처리하고 있음.

3. **Pool 기반 병렬처리** — `GAS/run.py`에서 `from multiprocessing import Pool, Manager, Lock` 사용. `with Pool() as pool: pool.map(run_ga_engine, args)` 구조이며, 이에 따라 `sync_generation`, `sync_lock`, `events`, `new_populations`가 Manager 공유 객체로 관리됨. GA 엔진이 사실상 1개로 줄면 이 복잡도는 전부 불필요함.

4. **run config dict** — `custom_settings = [{'crossover': PMXCrossover, 'pc': 0.9, 'mutation': GeneralMutation, 'pm': 0.9, ...}]` 형태의 list-of-dict로 관리됨. grid search를 염두에 둔 구조이나 현재는 단일 설정만 사용 중.

5. **레거시/중복 파일** — `GAS/GA copy.py`, `GAS/GA_1022최신.py`, `GAS/GA_이주해결.py`, `GAS/as.py`, `GAS/sequnce.py` 등 한글 파일명 포함 레거시 파일이 다수 존재.

6. **한글 인라인 주석** — `GA.py`, `run.py`, `Population.py` 등 핵심 파일에 `# 처음에는 그냥 시작`, `# 엘리트 개체 선택`, `# 이주가 가능한 경우` 같은 한글 주석이 다수. docstring은 영어로 되어 있어 불일치.

### 출력 및 재현성 문제

7. **결과 저장 경로 불통일** — 현재 `result/{MM-DD-HH-MM-SS}-{instance}-Mode{mode}/` 구조. 요청대로 `output/{run_name}/{timestamp}/`로 변경 필요.

8. **통합 실험 결과 CSV 없음** — 현재 각 run마다 별도 파일 생성. `file / method / seed / best_makespan / elapsed_time` 등을 하나의 CSV에 행(row)으로 누적하는 구조가 없어 중간 실패 시 결과 유실 위험.

9. **초기화 직후 결과 미저장** — `GAEngine.__init__`에서 Population 생성 후 초기 `best_makespan`, `mean_makespan`을 따로 캡처·저장하는 코드 없음.

10. **Config 저장 없음** — 실험 당시 hyperparameter를 파일로 남기지 않아 결과 재현 불가.

---

## 변경 계획

### [승인 필요] 구조적 결정 사항

아래 4가지는 다음과 같이 확정한다.

**(Jiwon's Approval) D-1** 디렉터리명은 모두 소문자로 변경함.`GAS/` → `gas/`, `Data/` → `data/`

**(Jiwon's Approval) D-2** 모듈 및 스크립트 재구성은 아래를 참고한다.
docs/
configs/
src/data/
	- TXT 파일에서 Dataset 클래스를 만드는 기능(dataset.py)은 유지한다.
src/gas 
	- localsearch.py
	- crossover.py
	- mutation.py
	- selection.py
src/data
	- datagenerator.py <- 여러형태의 TXT, CSV 등에 대응할 수 있도록 전처리모듈 탑재
src/runners
	- cli.py
	- workflow.py
		- src.runners.workflow.run_single_opt() : 1개 데이터셋으로 1회 최적화 실행
		- src.runners.workflow.run_single_comparison() : 1개 데이터셋 1개 시드로 4개의 method 비교데이터 생성
		- src.runners.workflow.run_multiple_comparison() : 여러개 데이터셋 여러개 시드로 run_single_comparison()을 각각 실행해서 데이터를 누적 생성
		- src.runners.workflow.run_grid_search() : p_crossover, p_mutation 등을 조절하거나, Crossover operator, Mutation operator 등을 바꿔가면서 각각 run_comparison()을 실행

**(Jiwon's Approval) D-3** 레거시 파일 처리 : `GA copy.py`, `GA_1022최신.py`, `GA_이주해결.py`, `as.py`, `sequnce.py` 즉시 삭제한다.

**(Jiwon's Approval) D-4** | initialization_mode 는 기존 `'1'/'2'/'3'` string으로 되어있는것을 {1:RANDOM, 2:RUBI, 3:GT, 4:SPT, 5:LPT, ...} 등으로 mapping 하고 앞으로는 오직 string으로만 관리하도록 함. 추가 가능하도록 구현.

---

### 실제 작업 목록 (승인 후 진행)

#### Step 1 — 레거시 파일 정리 및 진입점 신설

- `GAS/GA copy.py`, `GAS/GA_1022최신.py`, `GAS/GA_이주해결.py`, `GAS/as.py`, `GAS/sequnce.py` 삭제
- `runners/` 디렉터리 신설
  - `runners/cli.py` — 단일 진입점, `sys.path` 정리, argparse
  - `runners/workflows.py` — `run_single_opt()` 구현 (아래 Step 3 참조)
- 모든 result 기록용 csv 파일 등을 삭제한다.

#### Step 2 — Pool 병렬처리 제거 (`GAS/run.py` → `runners/`)

- `from multiprocessing import Pool, Manager, Lock` 및 관련 코드 전부 제거
- `sync_generation`, `sync_lock`, `events`, `new_populations` → 단순 Python list/dict로 교체
- `pool.map(run_ga_engine, args)` → serial `for` loop로 교체
- `run_ga_engine()` wrapper 함수 단순화 (단독 호출 가능한 형태로)
- 그 외에도, migration 개념은 현재 프로젝트에서는 사용하지 않는 내용이므로 제거한다.
- 단, local search 개념은 향후 사용할 수도 있으므로 남겨놓는다. 

#### Step 3 — `run_single_opt()` 구현

```python
def run_single_opt(
    dataset_file: str,
    initialization_mode: str,   # 'RANDOM' | 'RUBI' | 'GT' | ...
    crossover,
    mutation,
    selection,
    population_size: int,
    generations: int,
    elite_ratio: float,
    seed: int,
    output_dir: str,
) -> dict:
    # 반환: best_makespan_init, mean_makespan_init,
    #        best_makespan_final, elapsed_time
```

- `run_grid_search()`, `run_comparison()`은 이 함수를 반복 호출하는 wrapper로 나중에 추가

#### Step 4 — 초기화 직후 결과 캡처 (`GAS/GA.py`)

- `GAEngine.__init__` 에서 Population 생성 직후 평가 실행
- `self.init_best_makespan`과 `self.init_mean_makespan` 속성 저장
- `evolve()` 반환값에 이 두 값 포함

#### Step 5 — 통합 실험 결과 CSV (`runners/workflows.py`)

- `output/results.csv` (또는 run_name 단위)에 매 run 완료 시 row append:

  | 컬럼 | 내용 |
  |---|---|
  | `file` | 데이터셋 파일명 |
  | `method` | initialization_mode |
  | `seed` | random seed |
  | `best_makespan_init` | 초기화 직후 최적 |
  | `mean_makespan_init` | 초기화 직후 평균 |
  | `best_makespan_final` | GA 완료 후 최적 |
  | `elapsed_time` | 소요 시간(초) |
  | `timestamp` | 실행 시각 |

#### Step 6 — Config 저장 및 console logging (`runners/`)

- 각 run 폴더에 `config.json` 저장 (모든 hyperparameter 포함)
- `print()` → `logging` 모듈 + timestamp prefix (RL_project_template_guide.md §9 참고)
- `output/{run_name}/{YYYYMMDD_HHMMSS}/` 폴더 구조 적용
- run_name 이란, 사용자가 필요에 따라 지정하고 싶은 이름을 말한다. 예를 들어, `journal_2ndrevision` 등이 될 수 있다.


#### Step 7 — 한글 주석 제거 및 영어 주석 최소화

- `GA.py`, `Population.py`, `run.py` 내 한글 인라인 주석 제거
- 영어 docstring은 필요한 것만 유지, 불필요한 parameter 나열형 docstring 간소화
- base class (`Crossover`, `Mutation`) → `abc.ABC` + `@abstractmethod` 교체
- 기존에 기본으로 `Input: ...` 형식으로 argument type을 명시하도록 되어있는 주석은 모두 삭제한다. (Jetbrains Pycharm 기본 제공 주석 양식) 대신, compact 하고 decorative 하게 주석을 작성한다. 그리고, 필요하다면 module block 마다 `#`와 `'-'*70` 을 활용한 boxed modularized block 형식의 주석을 추가한다.

#### Step 8 — 그 외

root/environment : 현재 이 폴더는 너무 Module 들이 script 단위로 나와있어서 비효율적이다. 가능하다면 "C:\SNUPEL\2025_JSSP_RUBI\src\Jop Shop with GA.py" 를 참고하여 makespan 계산을 위해 필요한 최소한의 component 만 남기도록 한다.
root/visualization -> Gantt chart 를 만드는 기능은 유지한다. 대신 tkinter 등으로 GUI를 만들거나, GIF를 만드는 기능은 삭제한다.
root/postprocessing -> 삭제한다.
---

## 우선순위 및 진행 권고

1. **먼저 D-1~D-4 결정 사항을 승인해 주세요.** 디렉터리 구조와 모듈 통합 범위에 따라 나머지 step의 diff 크기가 크게 달라집니다.
2. Step 1~6은 논리적으로 순서대로 진행해야 합니다 (진입점 신설 → Pool 제거 → run_single_opt → CSV logging).
3. Step 7(주석 정리)과 Step 8(모듈 통합)은 독립적으로 진행 가능하므로 병렬 처리 가능합니다.

### Jiwon's note: 승인했습니다. (see Jiwon's Approval)

---

# 2026. 5. 4. Claude's Plan

## 1. 최종 디렉터리 구조

```
2025_JSSP_RUBI/
├── configs/
│   └── default.json                   # 기본 실험 하이퍼파라미터 (신규)
├── docs/                              # 기존 유지
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── dataset.py                 # ← Data/Dataset/Dataset.py 이전 + Metrics.py 흡수
│   │   └── datagenerator.py           # ← Data/DataGenerator.py + Dataset_jsplib.py + la.py 병합
│   ├── environment/
│   │   ├── __init__.py
│   │   └── simulator.py              # ← Monitor/Part/Process/Resource/Source/Sink 6개 → 1개로 통합
│   ├── gas/
│   │   ├── __init__.py
│   │   ├── individual.py              # ← GAS/Individual.py 이전 (경량화)
│   │   ├── population.py              # ← GAS/Population.py + Comparison/baseline.py 흡수
│   │   ├── engine.py                  # ← GAS/GA.py 이전 (Pool/migration 제거)
│   │   ├── crossover.py               # ← GAS/Crossover/*.py (10개) 통합
│   │   ├── mutation.py                # ← GAS/Mutation/*.py (9개) 통합
│   │   ├── selection.py               # ← GAS/Selection/*.py (3개) 통합
│   │   └── local_search.py           # ← GAS/Local_Search/*.py (7개) 통합
│   ├── visualization/
│   │   ├── __init__.py
│   │   └── gantt.py                   # ← visualization/Gantt.py (GUI 제거, CSV 의존성 제거)
│   └── runners/
│       ├── __init__.py
│       ├── cli.py                     # 단일 진입점 (신규)
│       └── workflows.py               # run_single_opt 등 4개 함수 (신규)
├── data/                              # 데이터셋 .txt 파일 위치 (Data/Dataset/JSPLIB 이전)
│   └── JSPLIB/
│       └── *.txt
├── output/                            # result/ → output/ 이름 변경
└── Readme.md
```

---

## 2. 삭제 대상 파일/디렉터리 전체 목록

### 레거시 스크립트 (즉시 삭제)
- `GAS/GA copy.py`
- `GAS/GA_1022최신.py`
- `GAS/GA_이주해결.py`
- `GAS/as.py`
- `GAS/sequnce.py`
- `GAS/Local_Search/TwoOptLocalSearch copy.py`
- `GAS/run_APMS.py`
- `GAS/run_Journal.py`
- `GAS/comparison_Journal.py`
- `GAS/comparison_heuristic.py`
- `GAS/experimental_result.py`
- `GAS/Initialization_comparison.py`
- `Comparison/run.py`
- `Comparison/Comparison.py`

### 통합으로 인해 사라지는 디렉터리 전체
- `GAS/Crossover/` (crossover.py로 통합 후 삭제)
- `GAS/Mutation/` (mutation.py로 통합 후 삭제)
- `GAS/Selection/` (selection.py로 통합 후 삭제)
- `GAS/Local_Search/` (local_search.py로 통합 후 삭제)
- `GAS/Meta/` (PSO, ORtools — 미사용, 삭제)
- `environment/` (simulator.py로 통합 후 삭제)
- `postprocessing/` (전체 삭제 — CSV 중간 파일 의존성 제거)
- `visualization/GUI.py` (tkinter GUI 삭제)
- `MachineInputOrder/` (calculate_score 미사용, 삭제)
- `Config/` (engine.py의 GAConfig dataclass로 대체)
- `Data/` (src/data/ 이전 후 삭제)
- `Comparison/` (baseline.py 내용을 population.py에 흡수 후 삭제)

### 결과 파일
- `result/` 폴더 전체 내용 삭제 (빈 `output/` 폴더로 대체)

---

## 3. 신규 생성 파일 명세

### `configs/default.json`

```json
{
  "run_mode": "single_comparison",
  "run_name": "experiment",
  "datasets": ["la01.txt"],
  "seeds": [42],
  "init_modes": ["RANDOM", "RUBI", "GT", "SPT"],
  "population_size": 100,
  "generations": 200,
  "elite_ratio": 0.05,
  "crossover": {"type": "PMX", "pc": 0.9},
  "mutation": {"type": "General", "pm": 0.9},
  "selection": {"type": "Roulette"},
  "target_makespan": null,
  "save_gantt": false,
  "output_root": "output"
}
```

`run_mode` 값에 따라 `cli.py`가 `workflows.py`의 함수를 분기한다:
- `"single_opt"` → `run_single_opt()`
- `"single_comparison"` → `run_single_comparison()`
- `"multiple_comparison"` → `run_multiple_comparison()`
- `"grid_search"` → `run_grid_search()`

---

### `src/runners/cli.py` (신규)

```python
# 단일 진입점: python -m src.runners.cli --config configs/default.json

import argparse, json, sys, os

INIT_MODE_MAP = {          # D-4: 숫자 string → mode string (하위호환 매핑)
    '1': 'RANDOM', '2': 'RUBI', '3': 'MoRUBI',
    '4': 'SPT',    '5': 'LPT',  '6': 'GT',
}
VALID_INIT_MODES = {'RANDOM', 'RUBI', 'MoRUBI', 'SPT', 'LPT', 'GT'}

def parse_args() -> argparse.Namespace: ...
    # --config (required)
    # --run_name, --output_root, --generations, --seed  (optional overrides)

def load_config(path: str) -> dict: ...
    # JSON 로드 → INIT_MODE_MAP 변환 → 유효성 검사

def main() -> None: ...
    # 1. parse_args()
    # 2. load_config(args.config)
    # 3. CLI override 적용
    # 4. run_mode에 따라 workflows 함수 분기 호출

if __name__ == '__main__':
    main()
```

---

### `src/runners/workflows.py` (신규)

#### 함수 목록 및 시그니처

```python
import csv, json, logging, os, time
from datetime import datetime

# -----------------------------------------------------------------------
# 내부 헬퍼
# -----------------------------------------------------------------------

def _make_run_dir(output_root: str, run_name: str,
                  dataset: str, init_mode: str, seed: int) -> str:
    # output/{run_name}/{YYYYMMDD_HHMMSS}_{dataset}_{init_mode}_seed{seed}/
    # 디렉터리 생성 후 경로 반환

def _save_config(run_dir: str, cfg: dict) -> None:
    # run_dir/config.json 저장

def _append_result_csv(output_root: str, run_name: str, row: dict) -> None:
    # output/{run_name}/results.csv 에 row 한 줄 append
    # 파일 없으면 헤더 포함 신규 생성
    # 컬럼: file, init_mode, seed, best_makespan_init, mean_makespan_init,
    #        best_makespan_final, elapsed_time, timestamp

# -----------------------------------------------------------------------
# 공개 워크플로우
# -----------------------------------------------------------------------

def run_single_opt(
    dataset_file: str,
    init_mode: str,            # 'RANDOM' | 'RUBI' | 'GT' | 'SPT' | 'LPT' | 'MoRUBI'
    crossover_cls,             # 클래스, e.g. PMXCrossover
    crossover_params: dict,    # e.g. {'pc': 0.9}
    mutation_cls,
    mutation_params: dict,
    selection_cls,
    selection_params: dict,
    population_size: int,
    generations: int,
    elite_ratio: float,
    seed: int,
    run_name: str,
    output_root: str = 'output',
    target_makespan: int = None,
    save_gantt: bool = False,
) -> dict:
    # 1. 로거 설정 (timestamp prefix)
    # 2. Dataset 로드
    # 3. GAConfig 생성
    # 4. GAEngine 인스턴스화 → self.init_best_makespan, self.init_mean_makespan 획득
    # 5. engine.evolve() 실행
    # 6. _make_run_dir(), _save_config()
    # 7. save_gantt=True 이면 gantt.save_gantt() 호출
    # 8. result dict 구성 후 _append_result_csv() 호출
    # 9. result dict 반환
    # 반환 dict 키: file, init_mode, seed,
    #               best_makespan_init, mean_makespan_init,
    #               best_makespan_final, elapsed_time, timestamp, run_dir


def run_single_comparison(
    dataset_file: str,
    init_modes: list,           # 비교할 init_mode 목록
    crossover_cls, crossover_params: dict,
    mutation_cls, mutation_params: dict,
    selection_cls, selection_params: dict,
    population_size: int,
    generations: int,
    elite_ratio: float,
    seed: int,
    run_name: str,
    output_root: str = 'output',
    target_makespan: int = None,
    save_gantt: bool = False,
) -> list:
    # init_modes 각각에 대해 run_single_opt() 순차 호출
    # 결과 list[dict] 반환


def run_multiple_comparison(
    dataset_files: list,        # 복수 데이터셋
    init_modes: list,
    crossover_cls, crossover_params: dict,
    mutation_cls, mutation_params: dict,
    selection_cls, selection_params: dict,
    population_size: int,
    generations: int,
    elite_ratio: float,
    seeds: list,                # 복수 seed
    run_name: str,
    output_root: str = 'output',
    target_makespan: int = None,
    save_gantt: bool = False,
) -> list:
    # dataset_files × seeds 의 조합에 대해 run_single_comparison() 순차 호출
    # 모든 결과를 누적한 list[dict] 반환


def run_grid_search(
    dataset_files: list,
    init_modes: list,
    crossover_configs: list,    # [{'cls': PMXCrossover, 'pc': 0.9}, ...]
    mutation_configs: list,
    selection_configs: list,
    population_size: int,
    generations: int,
    elite_ratios: list,
    seeds: list,
    run_name: str,
    output_root: str = 'output',
) -> list:
    # 모든 조합에 대해 run_single_opt() 순차 호출
    # 모든 결과를 누적한 list[dict] 반환
```

---

## 4. 기존 파일 이전·수정 명세

### `src/gas/engine.py` ← `GAS/GA.py`

#### 제거 대상
| 제거 항목 | 이유 |
|---|---|
| `migrate_top_10_percent()` 함수 | island migration 미사용 |
| `get_next_filename()` 함수 | 미사용 |
| `save_population_to_csv()` 함수 | 미사용 |
| `GAEngine.update_new_populations()` | migration 전용 |
| `GAEngine.save_csv()` | workflows.py가 담당 |
| `GAEngine.apply_pso()` | PSO 미사용 |
| `GAEngine.apply_ORtools()` | ORtools 미사용 |
| `from concurrent.futures import ProcessPoolExecutor` | 미사용 |
| `island_mode`, `migration_frequency`, `ga_engines` 파라미터 | migration 미사용 |
| `record` 파라미터 | 미사용 |
| `evolve()` 의 `index`, `sync_generation`, `sync_lock`, `new_populations`, `events`, `dirname` 파라미터 | 병렬처리 제거 |
| `evolve()` 내 island migration 블록 전체 (주석 포함) | migration 미사용 |
| 모든 한글 인라인 주석 | 정리 |
| `Parameters: / Returns:` 형식 docstring 전체 | 간소화 |

#### 유지 대상
| 유지 항목 | 비고 |
|---|---|
| `GAEngine.__init__()` | 파라미터 정리 후 유지 |
| `GAEngine.evolve()` | 시그니처 간소화 |
| `GAEngine.apply_local_search()` | 향후 사용 가능성 |
| elite 보존 로직 (`elites` 추출 및 재삽입) | 유지 |
| early stopping (target_makespan) 로직 | 유지 |
| `best_time`, `best_makespan` 추적 | 유지 |

#### 추가/수정 대상

**`GAConfig` dataclass 신설** (Config/Run_Config.py를 대체):
```python
from dataclasses import dataclass, field

@dataclass
class GAConfig:
    n_job: int
    n_machine: int
    n_op: int
    population_size: int
    generations: int
    elite_ratio: float = 0.05
    target_makespan: int = None
    simul_time: float = 1e10
    save_gantt: bool = False
    show_gantt: bool = False
```

**`GAEngine.__init__()` 수정 후 시그니처:**
```python
def __init__(
    self,
    config: GAConfig,
    op_data: list,
    crossover,
    mutation,
    selection,
    local_search: list = None,
    selective_mutation=None,
    init_mode: str = 'RANDOM',
    dataset_filename: str = None,
    local_search_frequency: int = 100000,
    selective_mutation_frequency: int = 100000,
    random_seed: int = None,
):
```
→ `__init__` 마지막에 다음을 추가:
```python
# capture initial population stats
makespans = [ind.makespan for ind in self.population.individuals]
self.init_best_makespan = min(makespans)
self.init_mean_makespan = sum(makespans) / len(makespans)
```

**`GAEngine.evolve()` 수정 후 시그니처:**
```python
def evolve(self) -> tuple:
    # returns: (best_individual, elapsed_time)
    # best_individual.makespan = 최종 최적 makespan
```
→ `sync_generation`은 단순 `int` 지역변수 `generation = 0`으로 대체
→ `sync_lock` 관련 코드 전체 삭제
→ `with sync_lock: sync_generation[index] += 1` → `generation += 1`

---

### `src/gas/individual.py` ← `GAS/Individual.py`

#### 제거 대상
| 제거 항목 | 이유 |
|---|---|
| `calculate_score()` 함수 | 호출 코드 없음(주석처리됨), MachineInputOrder 의존성 제거 |
| `swap_digits()` 함수 | `interpret_solution()` 전용, solution_seq 미사용 시 불필요 |
| `Individual.interpret_solution()` | solution_seq 입력방식 미사용 |
| `self.MIO`, `self.MIO_sorted` 속성 | Gantt 에 불필요 |
| `Individual.evaluate()` 내 `self.MIO`/`self.MIO_sorted` 계산 블록 | 동상 |
| `from postprocessing.PostProcessing import *` | postprocessing 삭제 |
| `from visualization.Gantt import *` | 불필요 |
| `from visualization.GUI import GUI` | GUI 삭제 |
| `from MachineInputOrder.utils import ...` | MachineInputOrder 삭제 |
| `sys.path.append(...)` | src 패키지 구조로 대체 |
| 모든 한글 주석 및 `Parameters: / Returns:` docstring | 정리 |

#### 유지 대상
| 유지 항목 | 비고 |
|---|---|
| `Individual.__init__()` | solution_seq 파라미터 제거 |
| `Individual.__str__()` | 유지 |
| `Individual.calculate_fitness()` | 유지 |
| `Individual.get_repeatable()` | 유지 |
| `Individual.get_feasible()` | 유지 |
| `Individual.get_machine_order()` | 유지 |
| `Individual.evaluate()` | simulator.py 호출로 대체 |
| `mio_score` 반환 | 유지 (0.0 고정으로 단순화 가능) |

#### 수정 후 `Individual.evaluate()` 형태:
```python
def evaluate(self, machine_order):
    from src.environment.simulator import simulate
    makespan, workingtime_log = simulate(
        self.op_data, machine_order,
        self.config.n_job, self.config.n_machine,
        self.config.simul_time,
    )
    self.workingtime_log = workingtime_log   # Gantt용
    return makespan, 0.0                      # mio_score는 0.0으로 단순화
```

---

### `src/environment/simulator.py` ← `environment/` 6개 파일 통합

기존 6개 파일(Monitor, Part, Process, Resource, Source, Sink)의 클래스를 하나의 파일에 통합한다. Monitor의 CSV 저장 기능은 제거하고, Machine에 `workingtime_log` 리스트를 추가한다.

#### 파일 내부 구조

```python
# -----------------------------------------------------------------------
# SimPy-based JSSP Makespan Simulator
# -----------------------------------------------------------------------
import simpy

# -----------------------------------------------------------------------
# Internal domain classes  (외부에서 직접 사용하지 않음)
# -----------------------------------------------------------------------
class _Job: ...
    # __init__(env, job_id, op_data_row, n_op): 각 operation을 순서대로 실행
    # finished: simpy.Event (모든 operation 완료 시 succeed)

class _Operation: ...
    # __init__(env, job_id, op_id, machine_id, duration)
    # waiting: simpy.Event, finished: simpy.Event

class _Machine: ...
    # __init__(env, machine_id)
    # workingtime_log: list[(job_id, start_time, finish_time)]  ← Gantt용
    # queue: simpy.Store
    # execute() / processing(): 큐에서 operation을 꺼내 processing

class _Scheduler: ...
    # __init__(env, jobs, machines, machine_order, op_data)
    # schedule(): machine_order 순서에 따라 각 machine queue에 operation 투입

# -----------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------
def simulate(
    op_data: list,
    machine_order: list,
    n_job: int,
    n_machine: int,
    sim_time: float = 1e10,
) -> tuple:
    # 반환: (makespan: int, workingtime_log: dict[int, list[tuple]])
    # workingtime_log[j] = [(job_id, start, finish), ...]  for machine j
```

**제거 항목:** Monitor 클래스의 `save_event_tracer()` (CSV 저장 로직 전체), Source 클래스 (simulator.py 내부 _Scheduler로 통합), 기존 6개 파일의 모든 한글 주석 및 장황한 docstring.

---

### `src/gas/population.py` ← `GAS/Population.py` + `Comparison/baseline.py`

#### `Comparison/baseline.py`에서 흡수하는 내용
- `GifflerandThompson()` 함수 → `Population.from_GT()` 로 이전
	- 기존의 `Population.from_GT()` 내용은 덮어쓰기함

#### 제거 대상
| 제거 항목 | 이유 |
|---|---|
| `print_console` 전역 변수 및 모든 `if print_console: print(...)` 구문 | 디버그 코드 |
| `Population.from_rubi_spt()` | `from_mio()`와 기능 중복, 미사용 |
| `GifflerThompson` 클래스 | GT 초기화 |
| `Population.from_giffler_thompson()` | `from_GT()`와 중복 |
| `Population.min_max_scaling()`, `rank_scaling()`, `sigma_scaling()`, `boltzmann_scaling()` | 미사용 fitness scaling |
| `GifflerThompson.giffler_thompson()` | `apply_priority_rule()` 단순 래퍼, 통합 |
| 모든 한글 주석 및 `Parameters: / Returns:` docstring | 정리 |
| `sys.path.append(...)` | 패키지 구조로 대체 |

#### 유지 대상
| 유지 항목 | 비고 |
|---|---|
| `Operation`, `MIOMachine` 클래스 | RUBI 초기화에 필수 |
| `JSSP` 클래스 전체 | RUBI 시퀀스 생성 |
| `Population.__init__()` | RANDOM 초기화 |
| `Population.from_mio()` | RUBI 초기화, `from_rubi()`로 이름 변경 |
| `Population.from_modified_rubi()` | MoRUBI 초기화 |
| `Population.from_SPT()`, `from_LPT()` | SPT/LPT 초기화 |
| `Population.from_GT()` | GT 초기화 |
| `Population.evaluate()` | 필요 best/worst 파라미터 유지 |
| `Population.select()`, `crossover()`, `mutate()`, `preserve_elites()` | 유지 |

#### D-4 초기화 mode 관리 방식 변경
`Population.__init__()` 에서 `initialization_mode` 파라미터 제거, `GAEngine.__init__()` 에서 mode 분기:
```python
# engine.py
INIT_MODE_FACTORY = {
    'RANDOM':  lambda: Population(config, op_data, random_seed=seed),
    'RUBI':    lambda: Population.from_mio(config, op_data, dataset_filename, seed),
    'MoRUBI':  lambda: Population.from_modified_rubi(config, op_data, dataset_filename, seed),
    'SPT':     lambda: Population.from_SPT(config, op_data, dataset_filename),
    'LPT':     lambda: Population.from_LPT(config, op_data, dataset_filename),
    'GT':      lambda: Population.from_GT(config, op_data, dataset_filename),
}
if init_mode not in INIT_MODE_FACTORY:
    raise ValueError(f"Unknown init_mode: {init_mode!r}. Valid: {list(INIT_MODE_FACTORY)}")
self.population = INIT_MODE_FACTORY[init_mode]()
```

---

### `src/gas/crossover.py` ← `GAS/Crossover/*.py` 10개 통합

#### 파일 내부 구조
```python
# -----------------------------------------------------------------------
# Abstract Base
# -----------------------------------------------------------------------
from abc import ABC, abstractmethod

class Crossover(ABC):
    @abstractmethod
    def cross(self, parent1, parent2): ...

# -----------------------------------------------------------------------
# PMX — Partial Mapped Crossover
# -----------------------------------------------------------------------
class PMXCrossover(Crossover):
    def __init__(self, pc: float): self.pc = pc
    def cross(self, parent1, parent2): ...

# -----------------------------------------------------------------------
# OX — Order Crossover
# -----------------------------------------------------------------------
class OrderCrossover(Crossover): ...

# -----------------------------------------------------------------------
# CX — Cycle Crossover
# -----------------------------------------------------------------------
class CXCrossover(Crossover): ...

# -----------------------------------------------------------------------
# LOX — Linear Order Crossover
# -----------------------------------------------------------------------
class LOXCrossover(Crossover): ...

# (이하 OBC, PositionBasedCrossover, SXX, PSXCrossover, POXCrossover,
#  JBXCrossover, CompositeCrossover 동일 패턴으로 작성)
```

**제거 항목:** 각 파일의 `sys.path.append(...)`, module-level docstring 전체, `Parameters: / Returns:` 형식 docstring. `CompositeCrossover` 는 유지.

---

### `src/gas/mutation.py` ← `GAS/Mutation/*.py` 9개 통합

```python
# -----------------------------------------------------------------------
# Abstract Base
# -----------------------------------------------------------------------
class Mutation(ABC):
    @abstractmethod
    def mutate(self, individual): ...

# -----------------------------------------------------------------------
# General — random swap
# -----------------------------------------------------------------------
class GeneralMutation(Mutation):
    def __init__(self, pm: float): self.pm = pm
    def mutate(self, individual): ...

# -----------------------------------------------------------------------
# Displacement
# -----------------------------------------------------------------------
class DisplacementMutation(Mutation): ...

# (이하 Insertion, Inversion, ReciprocalExchange, Shift, Swap,
#  Selective, Composite 동일 패턴)
```

---

### `src/gas/selection.py` ← `GAS/Selection/*.py` 3개 통합

```python
# -----------------------------------------------------------------------
# Abstract Base
# -----------------------------------------------------------------------
class Selection(ABC):
    @abstractmethod
    def select(self, population): ...

# -----------------------------------------------------------------------
# Tournament
# -----------------------------------------------------------------------
class TournamentSelection(Selection):
    def __init__(self, tournament_size: int = 2): ...
    def select(self, population): ...

# -----------------------------------------------------------------------
# Roulette
# -----------------------------------------------------------------------
class RouletteSelection(Selection): ...

# -----------------------------------------------------------------------
# Seed
# -----------------------------------------------------------------------
class SeedSelection(Selection): ...
```

---

### `src/gas/local_search.py` ← `GAS/Local_Search/*.py` 통합

`TwoOptLocalSearch copy.py` 는 삭제. 나머지 6개를 하나의 파일로 통합.

```python
# -----------------------------------------------------------------------
# Abstract Base
# -----------------------------------------------------------------------
class LocalSearch(ABC):
    @abstractmethod
    def optimize(self, individual, config): ...

# -----------------------------------------------------------------------
# Two-Opt Local Search
# -----------------------------------------------------------------------
class TwoOptLocalSearch(LocalSearch): ...

class TwoOptLocalSearchInsert(LocalSearch): ...

# -----------------------------------------------------------------------
# Simulated Annealing
# -----------------------------------------------------------------------
class SimulatedAnnealing(LocalSearch): ...

class SimulatedAnnealingInsert(LocalSearch): ...

# -----------------------------------------------------------------------
# Hill Climbing
# -----------------------------------------------------------------------
class HillClimbing(LocalSearch): ...

# -----------------------------------------------------------------------
# Tabu Search
# -----------------------------------------------------------------------
class TabuSearch(LocalSearch): ...

# -----------------------------------------------------------------------
# Giffler-Thompson Local Search
# -----------------------------------------------------------------------
class GifflerThompsonLS(LocalSearch): ...
```

---

### `src/data/dataset.py` ← `Data/Dataset/Dataset.py` + `Data/Metrics.py`

#### 제거 대상
- `from GAS.Individual import Individual` (순환 의존성 제거)
- `sys.path.append(...)`
- `Parameters: / Returns:` 형식 docstring

#### 유지 대상
- `Dataset` 클래스 전체 (`__init__`, `n_job`, `n_machine`, `n_op`, `op_data`, `machine_data`, `pt_data`)
- `calculate_bottleneck_index()`, `calculate_flowshop_index()` (Metrics.py 흡수)

---

### `src/visualization/gantt.py` ← `visualization/Gantt.py`

#### 제거 대상
- `visualization/GUI.py` (tkinter GUI 전체 삭제)
- `simmode` 전역 변수
- `Parameters: / Returns:` 형식 docstring 및 한글 주석

#### 유지 대상
- `generate_colors(n)` 유지
- `Gantt()` 함수 → `save_gantt()` 로 이름 변경, `workingtime_log` 를 직접 입력으로 받도록 수정 (CSV 경유 제거)

#### 생성 대상
- run_name 을 입력하면 그때의 best makespan 등을 boxplot 으로 구현하는 함수 skeleton 마련 (실제 구현은 나중에 할 예정)

#### 수정 후 시그니처:
```python
def save_gantt(
    workingtime_log: dict,   # {machine_id: [(job_id, start, finish), ...]}
    n_job: int,
    n_machine: int,
    makespan: int,
    save_path: str,
    title: str = 'Gantt Chart',
) -> None:
```

---

## 5. 주석 스타일 가이드

Step 7 지시에 따른 통일 규칙:

- **모듈 상단 docstring**: 제거 (파일명으로 충분)
- **`Parameters: / Returns:` 형식**: 전부 제거 (PyCharm 자동생성 양식)
- **한글 인라인 주석**: 전부 제거
- **섹션 구분자**: 각 클래스/함수 그룹 앞에 아래 형식 사용
  ```python
  # ----------------------------------------------------------------------
  # PMX Crossover
  # ----------------------------------------------------------------------
  ```
- **필요한 경우에만** 한 줄 영어 주석 (WHY가 자명하지 않을 때만)
- **`self.pc`, `self.pm` 등 명백한 속성**에는 주석 불필요

---

## 6. 구현 순서 (의존성 고려)

| 순서 | 작업 | 이유 |
|---|---|---|
| 1 | 레거시 파일 삭제 | 작업 공간 정리 |
| 2 | `src/environment/simulator.py` 작성 | `individual.py`가 의존 |
| 3 | `src/gas/crossover.py`, `mutation.py`, `selection.py` 통합 | `population.py`, `engine.py`가 의존 |
| 4 | `src/gas/individual.py` 수정 | `population.py`가 의존 |
| 5 | `src/gas/population.py` 수정 | `engine.py`가 의존 |
| 6 | `src/gas/engine.py` 수정 (`GAConfig` 포함) | `workflows.py`가 의존 |
| 7 | `src/data/dataset.py` 작성 | `workflows.py`가 의존 |
| 8 | `src/gas/local_search.py` 통합 | `engine.py`가 참조 |
| 9 | `src/visualization/gantt.py` 수정 | `workflows.py`가 의존 |
| 10 | `src/runners/workflows.py` 작성 | `cli.py`가 의존 |
| 11 | `src/runners/cli.py` + `configs/default.json` 작성 | 최종 진입점 |
| 12 | `src/data/datagenerator.py` 작성 | 독립적 |
| 13 | 전체 테스트 (`la01.txt` 기준 `run_single_opt()` 1회 실행) | 검증 |

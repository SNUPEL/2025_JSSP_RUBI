# RL Project Template Guide

이 문서는 `2026_MAS_KSOE` 프로젝트를 개인 RL 프로젝트 템플릿으로 재사용할 때, 다른 AI agent가 코드의 의도와 작성 습관을 빠르게 이해하도록 돕기 위한 가이드다. 단순 사용법보다 “이 코드베이스에서 유지해야 할 구조적 취향”을 설명하는 데 초점을 둔다.

## 1. 이 템플릿의 기본 철학

이 프로젝트는 일반적인 multi-agent RL 실험 템플릿으로 재사용할 수 있다.

핵심 원칙은 다음과 같다.

- 실험 설정은 config 파일에 모으고, 실행 코드는 config를 해석하는 쪽으로 둔다.
- 학습, 평가, 비교, 그리고 여러 hyperparameter 에 대한 sweep (혹은 grid search)은 모두 `runners/workflows.py`에서 run mode로 분기한다.
- 에이전트 이름 문자열과 실제 클래스 연결은 `config/registry.py`가 담당한다.
- 설정 오류는 학습 도중이 아니라 시작 전에 `config/schema.py`에서 fail-fast한다.
- 결과 폴더에는 항상 timestamp와 `config_resolved.yaml`을 남겨 재현성을 확보한다.
- training episode와 validation episode는 겉으로 비슷해도 계약이 다르므로 함부로 합치지 않는다.

## 2. 폴더 구조를 유지하는 방식

프로젝트를 새 RL 과제에 맞게 바꿀 때도 아래 큰 폴더 구조는 대체로 유지하는 것을 권장한다.

```text
2026_MAS_KSOE/
├── Agent/                  정책, 휴리스틱, LLM agent, 공통 네트워크
│   ├── Agent0/             CP baseline, 분석용 레거시/보조 코드
│   ├── Agent1/             첫 번째 의사결정 agent
│   ├── Agent2/             두 번째 의사결정 agent
│   ├── Agent3/             공간배치 또는 후속 의사결정 heuristic
│   ├── Common/             CTCE 등 공통 정책용 PPO/network
│   └── LLM/                LLM backend, parser, prompt, LLM agent support
├── Environment/            데이터 생성, 환경, 시뮬레이션
│   ├── data.py
│   ├── environment.py
│   └── simulation.py
├── Utils/                  seed, KPI, visualization 등 순수 유틸
├── config/                 설정 로더, schema, registry, sweep
│   ├── loader.py
│   ├── schema.py
│   ├── registry.py
│   └── sweep.py
├── runners/                사용자가 실제로 실행하는 workflow 계층
│   ├── cli.py
│   ├── workflows.py
│   ├── run_episode.py
│   ├── validate.py
│   ├── commons.py
│   └── writer.py
├── input/                  configuration data와 validation instances
├── outputs/                실행 결과 자동 생성 위치
├── docs/                   온보딩, TODO, 발표/설명 자료
└── README.md
```

새 프로젝트로 바꿀 때 가장 먼저 바꿔야 하는 곳은 보통 `Environment/`, `Agent/Agent*/`, `config/base_config*.json`이다. 반면 `runners/`, `config/loader.py`, `config/schema.py`, `config/registry.py`는 가능한 한 템플릿의 골격으로 유지하는 편이 좋다.

## 3. 실행 진입점과 run mode

사용자는 직접 여러 스크립트를 고르는 대신, 기본적으로 아래 진입점을 사용한다.

```bash
python -m runners.cli --config config/base_config_ctce.json
```

`runners/cli.py`는 프로젝트 루트를 `sys.path`에 넣고, Matplotlib 설정 디렉터리를 프로젝트 내부 `.mplconfig`로 강제한다. 이는 Linux/WSL/권한 이슈가 있는 환경에서도 plotting이 깨지지 않도록 하기 위한 습관이다.

실제 실행 분기는 `runners/workflows.py`의 `run_from_args()`에서 처리한다.

| `cfg.run.run_mode` | 담당 함수 | 의미 |
|---|---|---|
| `single_train` | `run_single_train()` | 하나의 학습 run 실행 |
| `single_run` | `run_single_run()` | validation instance에 대해 평가만 수행 |
| `comparison` | `run_comparison()` | 여러 agent 조합을 같은 validation set에서 비교 |
| `sweep` | `run_sweep()` | hyperparameter 후보 조합을 전부 학습 |

이 구조는 `docs/TODO.md`의 고민이 반영된 결정이다. 이전처럼 train/run/comparison/sweep 스크립트가 분산되면 사용자가 어떤 파일을 실행해야 하는지 헷갈리므로, `run_mode`를 config에 두고 `workflows.py`가 분기하는 형태를 선호한다.

## 4. `run_single_train()`에서 드러나는 modularize 습관

`runners/workflows.py`의 `run_single_train()`은 이 템플릿에서 가장 중요한 스타일 샘플이다. 함수 내부는 긴 training loop지만, 큰 단계가 명확히 나뉘고 반복 작업은 helper로 빠져 있다.

대표적인 구조는 다음과 같다.

```text
1. Load Configuration And Initialize Runtime Context
1-2. Resolve Agent Handles
2. Main Training Loop
  2-1. Log Current Learning Rate
  2-2. Run One Episode
  2-3. Calculate and Collect Episode Metrics
  2-4. Print, Save, And Export Episode Results
  2-5. Advance Scheduler
  2-6. Run Validation, Save, And Reset Tasks
3. Finalize Resources
```

이 스타일에서 중요한 점은 다음이다.

- 초기화는 `_prepare_training_runtime()`으로 분리한다.
- episode 실행은 `run_CTCE_episode()` / `run_DTDE_episode()`에 맡긴다.
- 출력, CSV 저장, TensorBoard/VESSL logging은 `commons.py`와 `writer.py`에 맡긴다.
- validation, checkpoint 저장, env reset 같은 주기 작업은 `run_periodic_tasks()`로 묶는다.
- episode에서 나온 값은 흩어두지 않고 `episode_summary` dict로 모은 뒤, downstream helper에 넘긴다.

다른 AI agent가 새 기능을 추가할 때는 `run_single_train()` 안에 모든 코드를 직접 늘어놓기보다, 같은 수준의 helper를 만들고 training loop에는 “읽히는 순서”만 남기는 것이 이 코드의 취향에 맞다.

## 5. Training episode와 validation episode를 구분하는 이유

`docs/TODO.md`에는 `run_episode.py`와 `validate.py`의 중복을 줄이고 싶다는 고민이 있다. 결론은 “바로 교체하지 말고, 공통 rollout core를 추출한 뒤 wrapper를 분리하자”이다.

이유는 함수 계약이 다르기 때문이다.

- `run_CTCE_episode()` / `run_DTDE_episode()`는 학습 함수다.
- 이 함수들은 rollout 중 `put_sample()`, `train()`, `T_horizon` flush, bootstrap용 `last_value` 계산을 수행한다.
- 반환값도 reward, loss, step처럼 training log에 필요한 값이다.
- 반면 `validate.run_single_episode()`는 `torch.no_grad()`에서 실행되는 평가 함수다.
- 반환값은 `tardiness`, `load_deviation`, `arrangement_fail`, `allocation_penalty`, `spatial_deviation`, `computing_time` 같은 KPI dict다.

따라서 validation 함수를 training loop에 직접 끼워 넣으면 학습이 멈출 수 있다. 중복 제거를 하려면 공통부와 전용부를 다음처럼 나누는 방향이 맞다.

- 공통부: agent mode 전환, action 선택, rework, spatial arrangement 실패 처리, SimPy queue 진행
- 학습 전용부: sample 저장, PPO update, loss/step 집계
- 평가 전용부: `torch.no_grad()`, validation path 기반 환경 생성, KPI 계산

## 6. Config 설계 취향

설정은 자유로운 dict로 끝내지 않고 `config/schema.py`의 dataclass로 변환한다. 이 프로젝트에서는 config가 단순 옵션 모음이 아니라 실험 계약이다.

중요한 선호는 다음과 같다.

- 실행 전에 type casting과 validation을 끝낸다.
- 잘못된 실험은 몇 시간 뒤가 아니라 시작 시점에 실패해야 한다.
- `run.use_cuda=True`인데 `run.device="cpu"`인 조합처럼 모순된 설정을 막는다.
- `use_spatial_arrangement`가 꺼져 있으면 `use_spatial_characteristics`, `apply_rework`, `algorithm_agent3` 같은 하위 기능을 허용하지 않는다.
- `reward_weight_tardiness + reward_weight_loaddev == 1.0`을 강제한다.
- `lr_decay`, `gamma`, `eps_clip`, `lmbda`는 `[0, 1]` 범위로 제한한다.
- `eval_every`, `save_every`, `reset_every`는 1 이상의 정수여야 한다.
- 허용되지 않은 heuristic 이름은 조용히 fallback하지 말고 에러를 낸다.

`docs/TODO.md`의 `config/schema.py` 요청 사항이 이 방향을 만들었다. 앞으로 새 config field를 추가할 때도 `schema.py`에 타입, 기본값, 허용 범위, 상호 의존성을 같이 추가하는 것이 좋다.

## 7. Registry 설계 취향

`config/registry.py`는 문자열 설정을 실제 객체로 바꾸는 곳이다.

예를 들어 config에는 다음처럼 쓴다.

```json
{
  "agent": {
    "algorithm_agent1": "RL",
    "algorithm_agent2": "MCR"
  }
}
```

실제 객체 생성은 `AGENT1_REGISTRY`, `AGENT2_REGISTRY`, `AGENT3_REGISTRY`가 담당한다. 이 방식의 장점은 `cli.py`나 `workflows.py`가 agent 종류별 `if/elif`로 길어지지 않는다는 점이다.

새 agent를 추가할 때는 보통 다음 순서를 따른다.

1. `Agent/Agent*/` 아래에 구현 파일을 추가한다.
2. `config/schema.py`의 허용 목록에 이름을 추가한다.
3. `config/registry.py`의 registry dict에 factory를 한 줄 추가한다.
4. 필요한 config field를 dataclass와 validation에 추가한다.

## 8. 변수 네이밍 특징

이 프로젝트의 변수명은 길더라도 역할을 노골적으로 드러내는 쪽을 선호한다.

자주 보이는 패턴은 다음과 같다.

- `cfg`: 전체 config dataclass
- `env`: `Factory`로 생성된 RL environment
- `agent_system`: `{"agent1": ..., "agent2": ..., "agent3": ...}` 또는 `{"global_agent": ...}` 형태의 agent container
- `agent1`, `agent2`, `agent3`: 의사결정 단계별 agent
- `global_agent`: CTCE에서 joint action을 담당하는 공통 agent
- `joint_action`: CTCE 여부를 나타내는 boolean
- `use_multi_agent`: DTDE 또는 mixed RL 조합 여부
- `block_data_src`: `DataGenerator(cfg)` 결과
- `dirs`: `output_dir`, `model_dir`, `log_dir`, `model_dir_agent1`, `model_dir_agent2`를 모은 dict
- `episode_summary`: 한 episode의 reward/loss/step/time/KPI를 모은 dict
- `detail_df`, `summary`, `summary_df`: validation/comparison 결과 테이블
- `*_path`, `*_dir`: 파일과 디렉터리 구분을 이름에서 드러냄

네이밍은 약어보다 역할 설명을 우선한다. 예를 들어 `avg_arr_fail`, `avg_alloc_penalty`, `sum_spatial_load_deviation`처럼 metric 이름을 길게 써도 후처리에서 의미가 바로 보이게 한다.

다만 RL domain에서 관용적인 약어는 그대로 쓴다.

- `CTCE`, `DTDE`
- `PPO`
- `K_epoch`
- `T_horizon`
- `gamma`, `lmbda`, `eps_clip`
- `state`, `action`, `reward`, `done`, `log_prob`, `value`

## 9. Logging과 timestamp 특징

이 템플릿은 실험 재현성과 사후 분석을 중요하게 본다.

### 출력 폴더 규칙

`runners/commons.py`의 `make_output_dir()`는 실행 시점 timestamp를 사용한다.

```text
outputs/<run.name>/<agent_setup>/<YYYYMMDD_HHMMSS>/
```

comparison 모드는 학습 산출물이 아니라 batch evaluation이므로 더 얕은 구조를 쓴다.

```text
outputs/<run.name>/<YYYYMMDD_HHMMSS>/
```

이 결정은 comparison 결과를 사람이 바로 찾기 쉽게 하려는 취향이 반영된 것이다.

### Runtime timestamp field

`_prepare_training_runtime()`은 다음 값을 `cfg`에 기록한다.

- `cfg.ymd`
- `cfg.hour`
- `cfg.minute`
- `cfg.second`

현재 출력 디렉터리 생성은 `make_output_dir()`의 `datetime.now().strftime("%Y%m%d_%H%M%S")`가 담당하지만, runtime context에도 날짜/시간을 남겨 두는 습관이 있다. 다른 코드에서 파일명, 로그명, 실험 식별자에 timestamp가 필요할 때 이 패턴을 따른다.

### CSV log

training log는 mode에 따라 파일이 나뉜다.

- CTCE: `train_log.csv`
- DTDE 또는 mixed RL: `train_log_agent1.csv`, `train_log_agent2.csv`
- 공통 validation: `validation_log.csv`

CSV header는 `write_log_header()`에서 먼저 생성하고, episode마다 append한다. training row에는 reward, average loss, learning rate, spatial 관련 metric을 기록한다. validation row에는 tardiness, load deviation, arrangement fail, allocation penalty, spatial deviation을 기록한다.

### TensorBoard/VESSL writer

`runners/writer.py`의 `RunnerWriter`는 TensorBoard와 VESSL logging 차이를 감춘다. 외부에서는 `log_scalar()`, `log_training_metrics()`, `log_validation_metrics()`만 호출한다.

중요한 습관은 값이 `None`이면 logging하지 않는 것이다. spatial feature가 꺼진 실험에서 의미 없는 0을 계속 남기지 않기 위함이다. 단, CSV에는 테이블 형태 유지를 위해 `None` metric을 `0.0`으로 채우는 경우가 있다.

### Resolved config 저장

모든 주요 run은 `save_resolved_config(cfg, output_dir)`를 호출해 `config_resolved.yaml`을 저장한다. 이 파일은 override와 CLI `--set`까지 반영된 최종 설정이다.

나중에 checkpoint나 결과 폴더만 남아 있어도 어떤 설정으로 실행했는지 복원할 수 있어야 한다는 재현성 선호가 반영되어 있다.

## 10. Sweep과 comparison 설계

`sweep`은 base config와 별도 sweep 후보 JSON을 조합한다. `config/sweep.py`는 중첩 dict를 dot-path 후보로 flatten하고, `itertools.product()`로 모든 조합을 만든다.

각 sweep run은 다음처럼 label을 가진다.

```text
run_001__num_heads-4__num_HGT_layers-2
```

이 label은 output folder name으로도 쓰이므로, value는 `/`, `\`, `.`, `:` 같은 문자를 안전하게 sanitize한다.

`comparison`은 여러 agent 조합을 같은 validation set에서 평가한다. 기본 case에는 LLM 조합을 넣지 않는다는 주석이 있다. 이유는 실행 시간이 매우 길 수 있기 때문이다. 다만 schema, registry, runner는 LLM 조합을 처리할 수 있도록 유지한다.

## 11. Pretraining과 checkpoint 호환성

이 프로젝트는 pretrained checkpoint를 단순히 `torch.load()`하지 않고, 가능한 한 구조 호환성을 먼저 검사한다.

관련 함수는 `runners/commons.py`에 있다.

- `_find_resolved_config_for_checkpoint()`
- `_validate_checkpoint_config_compatibility()`
- `_validate_state_dict_shapes()`
- `_load_pretrained_agent_checkpoint()`
- `check_pretraining()`

중요한 취향은 다음이다.

- checkpoint 옆의 `config_resolved.yaml`을 찾아 현재 config와 구조를 비교한다.
- `embed_dim`, `num_heads`, `num_HGT_layers`, actor/critic layer 수 같은 구조 parameter mismatch를 명확히 에러로 보여준다.
- 최종적으로 state dict key와 tensor shape까지 확인한다.
- mixed comparison에서는 RL agent 쪽 checkpoint만 골라서 로드한다.

다른 AI agent가 checkpoint load 코드를 바꿀 때는 이 사전 검증을 제거하지 않는 편이 좋다.

## 12. Agent mode와 episode loop 사고방식

환경은 `env.agent_mode`로 현재 의사결정 주체를 알려준다.

일반 흐름은 다음과 같다.

```text
agent1 -> agent2 -> agent3 -> agent1 -> ...
```

각 단계의 의미는 현재 프로젝트 기준으로 다음과 같다.

- `agent1`: 블록 선별
- `agent2`: 정반 배정
- `agent3`: 공간 배치

CTCE에서는 `global_agent`가 joint action을 만들고, `action // env.num_bays`, `action % env.num_bays`로 agent1/agent2 action을 분해한다. DTDE/mixed에서는 각 agent가 자기 state에서 action을 고른다.

spatial arrangement 실패와 rework는 episode loop에서 가장 조심해야 하는 부분이다. `action_agent3[0] == -1`이면 배치 실패로 보고, `apply_rework=True`일 때는 Agent2를 다시 호출하도록 `env.agent_mode`와 mask를 수정한다.

이 로직은 training과 validation 양쪽에 유사하게 존재하지만, 학습용 sample 저장 여부가 다르기 때문에 무리하게 한 함수로 합치면 안 된다.

## 13. 코드 추가 시 권장 작업 순서

새 RL 문제나 새 agent를 추가할 때는 다음 순서를 권장한다.

1. `config/schema.py`에 필요한 설정 field와 validation을 추가한다.
2. `config/base_config*.json`에 실험 기본값을 추가한다.
3. `Agent/Agent*/` 또는 `Agent/Common/`에 agent/network를 구현한다.
4. `config/registry.py`에 문자열 이름과 factory를 등록한다.
5. 환경 state/action/reward가 바뀌면 `Environment/environment.py`와 `runners/run_episode.py`의 계약을 같이 확인한다.
6. logging이 필요한 metric은 `episode_summary`에 먼저 모은 뒤 `commons.py`와 `writer.py`에 연결한다.
7. validation KPI는 `runners/validate.py`와 `Utils/kpi_calculator.py`에서 별도 관리한다.
8. 결과 재현을 위해 `config_resolved.yaml`, CSV log, checkpoint 저장 위치가 유지되는지 확인한다.

## 14. 피해야 할 변경

다른 AI agent가 이 템플릿을 수정할 때 특히 피해야 할 작업은 다음이다.

- `run_single_train()` 안에 임시 출력, 파일 저장, validation logic을 계속 직접 추가하는 것
- `schema.py` validation 없이 config field만 늘리는 것
- registry를 우회해 `workflows.py`에 agent별 `if/elif`를 추가하는 것
- training episode를 validation episode로 단순 대체하는 것
- timestamp 없는 output path를 쓰는 것
- 최종 config snapshot 없이 checkpoint만 저장하는 것
- spatial/rework 관련 mask 수정 로직을 충분히 이해하지 않고 정리하는 것
- comparison output을 training output처럼 깊은 폴더 구조로 만드는 것

## 15. 문체와 주석 스타일

코드 주석은 한국어와 영어가 섞여 있다. 큰 단계 주석은 영어 title case로 남기는 경우가 많고, 세부 의사결정 배경은 한국어 주석으로 설명한다.

선호하는 주석은 “왜 이렇게 했는지”를 남기는 주석이다.

예:

- comparison은 배치 평가이므로 얕은 output 구조를 쓴다.
- LLM 조합은 실행 시간이 길어 기본 comparison case에서 제외한다.
- checkpoint config path는 agent 생성 override source로 사용한다.

반대로 코드가 그대로 말해주는 내용을 반복하는 주석은 추가하지 않는 편이 좋다.

## 16. 요약

이 템플릿의 핵심은 `config -> schema -> registry -> workflows -> episode/validate -> logs/outputs`의 흐름이다. 실험이 커져도 사용자는 `runners.cli`와 config만 주로 만지고, 내부 구현은 agent, environment, runner helper로 나뉘어 있어야 한다.

새 AI agent가 이 repo를 다룰 때는 `docs/TODO.md`의 문제의식처럼 중복을 줄이되, training/evaluation 계약 차이와 실험 재현성 장치를 보존하는 방향으로 작업해야 한다.

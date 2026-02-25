# CLAUDE.md — 경인교육대학교 중장기 발전계획 IPA 분석 프로젝트

## Project Overview

This repository implements an **Importance-Performance Analysis (IPA)** system for 경인교육대학교 (Gyeongin National University of Education)'s Mid-to-Long-Term Development Plan (2026–2035). It processes survey data from three respondent groups and visualizes results in an interactive HTML dashboard.

**Live dashboard:** https://edu-data.github.io/2026-2035-Plan/ipa_dashboard.html

---

## Repository Structure

```
2026-2035-Plan/
├── ipa_analyzer.py           # Python IPA analysis script (data → JSON)
├── ipa_analysis_results.json # Pre-computed analysis output (~108 KB)
├── ipa_dashboard.html        # Self-contained interactive dashboard (~135 KB)
└── README.md                 # Korean-language project documentation
```

**No build system, no package manager, no test suite.** The workflow is:
1. Run `ipa_analyzer.py` against raw Excel survey data → produces `ipa_analysis_results.json`
2. `ipa_dashboard.html` reads and visualizes the JSON

---

## Data Architecture

### Survey Data (NOT in repo)
Raw Excel files are located at `d:/plan/data/` (Windows path, external to repo):
- `교직원.xlsx` — Staff respondents
- `졸업생.xlsx` — Alumni respondents
- `학부생.xlsx` — Undergraduate students

These files are **not committed** to the repository. The JSON output is committed instead.

### Survey Question Mapping
Questions follow a strict naming convention `ques_N(M)` where N is the question group and M is the sub-item index:

| Question Group | Area | Importance cols | Performance cols |
|---|---|---|---|
| ques_2 / ques_3 | 핵심가치 (Core Values) | ques_2(1–5) | ques_3(1–5) |
| ques_5 / ques_6 | 위기요인 (Risk Factors) | ques_5(1–5) | ques_6(1–5) |
| ques_8 / ques_9 | 대응방향 (Response Directions) | ques_8(1–5) | ques_9(1–5) |
| ques_11 / ques_12 | 5대발전전략 (5 Strategies) | ques_11(1–5) | ques_12(1–5) |
| ques_14–ques_23 | Individual strategy sub-tasks (I–V) | paired odd/even | — |

---

## Analysis Framework

### IPA Quadrant Classification
Baseline = mean importance / mean performance across all items in scope.

| Quadrant | Condition | Strategic Direction |
|---|---|---|
| I. 집중개선 (Focus Improvement) | Importance ≥ baseline, Performance < baseline | Priority improvement needed |
| II. 유지강화 (Maintain & Strengthen) | Importance ≥ baseline, Performance ≥ baseline | Maintain current level |
| III. 저우선 (Low Priority) | Importance < baseline, Performance < baseline | Gradual improvement |
| IV. 과잉투자 (Over-investment) | Importance < baseline, Performance ≥ baseline | Consider resource reallocation |

### Gap Score
`gap = importance_mean - performance_mean`
Higher gap = greater discrepancy between what respondents consider important vs. what the university currently delivers. Gap ranking drives prioritization.

### The 5 Development Strategies (5대 발전전략)
| Code | Strategy | Sub-tasks |
|---|---|---|
| I | AI·스마트 캠퍼스 혁신 | I-1 through I-4 |
| II | 교육연구 선도 연구체제 선진화 | II-1 through II-4 |
| III | 포용성·공공성(사회문제해결) 고도화 | III-1 through III-4 |
| IV | 학생 역량·행복 증진 | IV-1 through IV-4 |
| V | 글로벌 허브 | V-1 through V-5 |

---

## Key Modules (`ipa_analyzer.py`)

| Function | Purpose |
|---|---|
| `load_data()` | Loads three Excel files, adds `group` column, returns dict of DataFrames |
| `calculate_ipa_scores(df, mapping)` | Area-level means (flattens all sub-items into a single importance/performance mean per area) |
| `calculate_item_ipa(df, mapping)` | Item-level means with quadrant data for individual survey items |
| `classify_quadrant(imp, perf, imp_baseline, perf_baseline)` | Returns quadrant string for a single data point |
| `analyze_group_detail(df, group_name)` | Full IPA for one respondent group: detail areas + 5 strategies + 21 tasks |
| `analyze_ipa(datasets)` | Orchestrates the full analysis across all groups and aggregated |
| `run_ipa_analysis()` | Entry point: loads data, runs analysis, saves JSON to `d:/plan/ipa_analysis_results.json` |

### Output JSON Structure
```
ipa_analysis_results.json
├── summary.areas            # Aggregated importance/performance/gap per area
├── by_group                 # Per-group (교직원/졸업생/학부생) full analysis
│   └── {group}
│       ├── areas            # Area-level scores
│       ├── detail_areas     # 핵심가치/위기요인/대응방향/5대발전전략 item breakdown
│       ├── strategies_5     # 5 strategy IPA with quadrants
│       └── tasks_21         # 21 task IPA with gap ranking
├── items                    # All individual survey items (aggregated)
├── quadrants                # Aggregated quadrant classification
├── detail_areas             # Aggregated detail area breakdown
├── strategies_5             # Aggregated 5-strategy analysis
├── tasks_21                 # Aggregated 21-task analysis with gap_ranking
├── baselines                # Global importance/performance baselines
└── gap_ranking              # Sorted area-level gap list
```

---

## Dashboard (`ipa_dashboard.html`)

### Architecture
- Single-file, self-contained HTML — no server required
- Uses **Chart.js** (loaded from CDN: `cdn.jsdelivr.net/npm/chart.js`)
- Inline JSON data (or fetches `ipa_analysis_results.json` from same directory)
- Dark theme: `--bg-dark: #0f0f23`, `--bg-card: #1a1a2e`

### UI Structure
1. **Group selector** — 종합(전체) / 교직원 / 졸업생 / 학부생 (pill buttons)
2. **Tab navigation** — 4 analysis tabs:
   - 종합: 9-area scatter IPA chart
   - 세부영역별: Per-area item breakdown (핵심가치/위기요인/대응방향/5대발전전략)
   - 5대 발전전략: Strategy comparison + bar chart
   - 21개 세부과제: Full task IPA + gap ranking table
3. **IPA scatter plots** — rendered via Chart.js scatter charts with quadrant annotations
4. **Gap ranking tables** — sorted descending by gap score

### Color Coding
- Q1 집중개선: `#e53935` (red)
- Q2 유지강화: `#43a047` (green)
- Q3 저우선: `#757575` (gray)
- Q4 과잉투자: `#1e88e5` (blue)
- Accent/interactive: `#ff6f00` (orange)

---

## Development Workflow

### Updating Analysis Results
When new survey data is available:
```bash
# 1. Place updated Excel files at d:/plan/data/
python ipa_analyzer.py
# Output: d:/plan/ipa_analysis_results.json

# 2. Copy result to repo
cp d:/plan/ipa_analysis_results.json ./ipa_analysis_results.json
```

### Viewing the Dashboard Locally
```bash
# macOS
open ipa_dashboard.html

# Linux
xdg-open ipa_dashboard.html

# Windows
start ipa_dashboard.html

# Or serve with Python to avoid CORS issues
python -m http.server 8000
# Then open http://localhost:8000/ipa_dashboard.html
```

### Python Dependencies
`ipa_analyzer.py` requires:
- `pandas` — Excel file reading and data manipulation
- `numpy` — Mean calculations and NaN handling
- Standard library: `json`, `pathlib`, `warnings`

No `requirements.txt` exists; install manually:
```bash
pip install pandas numpy openpyxl
```
(`openpyxl` is required by pandas for `.xlsx` reading)

---

## Conventions and Constraints

### Data Handling
- All numeric coercion uses `pd.to_numeric(errors='coerce')` — non-numeric values become NaN and are dropped silently
- NaN values are excluded from means via `dropna()` or boolean masking
- All output values are rounded to 2 decimal places

### Column Naming
Survey columns follow `ques_N(M)` format. Parentheses are part of the column name. If column names in the Excel differ from expected, `calculate_ipa_scores` silently skips missing columns — always verify column names match `IPA_MAPPING` keys when updating data.

### Output Paths
`ipa_analyzer.py` hardcodes Windows paths (`d:/plan/...`). When running on a different machine, update `DATA_DIR` and `output_path` at the top and bottom of the script before executing.

### Dashboard Data Loading
The dashboard HTML reads from `ipa_analysis_results.json` in the same directory. When deployed to GitHub Pages, ensure the JSON file is committed alongside the HTML.

### Language
- Code comments and variable names: Korean domain terms in Unicode (UTF-8)
- Script encoding declaration: `# -*- coding: utf-8 -*-` at top of Python files
- All user-facing labels are in Korean

---

## Branch and Deployment

- **Main branch:** `master`
- **Remote:** `origin` → `http://local_proxy@127.0.0.1:54232/git/edu-data/2026-2035-Plan`
- **GitHub Pages:** Served from `master` branch root — `ipa_dashboard.html` is the primary deliverable

When making changes, develop on feature branches prefixed with `claude/` and merge to `master` via pull request.

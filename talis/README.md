# TALIS-IPA 정책 우선순위 분석 (코드 골격)

TALIS 2024 한국 초등교원 자료로 **정책 레버별 중요도(I) × 수행도(P)** 를 계산하고 IPA 4분면으로 분류합니다. 모든 표준오차는 **BRR(Fay 수정) 반복가중치**로 구합니다.

방법론은 [연구계획서 4.5절과 부록 B](../docs/TALIS2024_초등교원_분석틀_연구계획서.md)에 있습니다.

> ⚠️ `--demo` 결과는 **가상(합성) 자료**로 만든 것입니다. 실제 TALIS 결과가 아니므로 인용하면 안 됩니다.

## 실행

```bash
pip install pandas numpy            # .sav 파일을 읽으려면 pyreadstat 추가

# 가상 자료로 파이프라인 검증
python talis/talis_ipa_analyzer.py --demo

# 실제 자료 (국제 비교를 하려면 여러 국가의 교사 자료를 한 파일로)
python talis/talis_ipa_analyzer.py --data <교사자료.csv|.sav> --out talis/output/talis_ipa_results.json

# 중요도 지표를 |표준화 β|로 바꿀 때
python talis/talis_ipa_analyzer.py --demo --metric beta
```

결과 JSON은 `talis/output/`에 저장되며, 이 폴더는 git에서 제외됩니다.

## 실제 자료에 적용하기 전에 수정할 것

| 설정 | 내용 |
|---|---|
| `CONFIG` | 국가·학교 변수, 최종가중치(`TCHWGT`), 반복가중치 접두어(`TRWGT`), Fay 계수, 설계 자유도. 2018 기준이므로 **2024 코드북 확인 필요** |
| `VARIABLE_MAP` | 코드북 변수명을 분석용 이름(`out_*`, `lev_*`)으로 바꾸는 매핑 |
| `LEVERS` | 레버별 지표, 방향(+1이면 높을수록 유리, −1이면 불리), 정책 주체, **근거 등급**(준인과 분석을 통과하면 `"준인과"`로 갱신) |
| `OUTCOMES` | 결과 지표와 방향 |
| `EXTERNAL_BENCHMARKS` | 국제 자료 없이 한국 자료만 있을 때, 보고서 표에서 옮긴 TALIS 평균과 표준편차 |

## 산출 내용

| 항목 | 내용 |
|---|---|
| `importance` | 일반 지배 가중치(합 = R²) 또는 \|표준화 β\|, BRR 표준오차 |
| `beta_std`, `sign_warning` | 표준화 β. 부호가 기대와 반대이면 경고 |
| `performance` | 한국과 TALIS 평균의 차이를 통합 표준편차로 나눈 값(유리한 방향이 +). 한국이 평균에 포함된 점을 반영한 표준오차 |
| `quadrant` | I. 집중개선 / II. 유지강화 / III. 점진개선 / IV. 재배치검토 |
| `priority_flag` | 사분면 I이면서 근거 등급이 "준인과"이고 부호 경고가 없을 때만 true |
| `heterogeneity` | 하위집단(예: 경력 구간)별 β와, β가 같은지에 대한 설계 자유도 보정 Wald F 검정 |
| `design_effect` | BRR 표준오차와 단순무작위 표준오차 비교(deff) |

## 검증 결과 (가상 자료)

| 점검 | 결과 |
|---|---|
| 지배 가중치 합 = 전체 R² | 0.3018 vs 0.3019 ✔ |
| BRR 표준오차 vs 독립 계산한 층-군집 선형화 표준오차 | 0.0371 vs 0.0368 ✔ |
| F 분포 꼬리확률 (F₂,₆₀ = 3.150, F₁,₁₀₀ = 3.936) | 둘 다 0.0500 ✔ |
| 집단 간 효과가 같은 가상 자료에서 이질성 검정 | 모두 비유의 (p > .05) ✔ |

## 남은 과제 (TODO)

- [ ] 결측 처리: 목록별 삭제를 다중대체(MI) + Rubin 규칙(결합 검정은 D₁)으로 교체
- [ ] 척도의 측정 동일성 확인 결과에 따라 국제 비교 지표 선별
- [ ] 2수준 모형, 잠재프로파일분석(LPA), 준인과 분석(AIPW)은 R 또는 Stata로 별도 수행한 뒤 근거 등급에 반영
- [ ] 결과 JSON을 기존 `ipa_dashboard.html` 형식의 TALIS-IPA 대시보드로 시각화

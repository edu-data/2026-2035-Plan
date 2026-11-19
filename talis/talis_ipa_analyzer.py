# -*- coding: utf-8 -*-
"""
TALIS-IPA 정책 우선순위 분석 (코드 골격)
경인교육대학교 중장기 발전계획 2026-2035 참고 분석

목적
    TALIS 2024 한국 초등교원 자료를 이용해 정책 레버별
    - 중요도(I): 교사 결과(웰빙 등)에 대한 상대적 중요도 (일반 지배분석 또는 표준화 β)
    - 수행도(P): 한국이 TALIS 초등 평균에서 얼마나 떨어져 있는지 (표준화 편차, 유리한 방향 = +)
    를 산출하고 IPA 4분면으로 분류한다.

표준오차
    모든 추정치는 BRR(Fay 수정) 반복가중치로 표준오차를 구한다.
    반복가중치마다 전체 추정 과정(표준화 → 회귀/지배분석)을 다시 수행한다.

중요
    - 변수명은 TALIS 2018 관례를 참고한 '자리표시자'이다. 2024 코드북에서 실제 변수명으로
      VARIABLE_MAP 과 LEVERS 를 교체해야 한다.
    - --demo 모드는 '가상(합성) 자료'로 파이프라인만 검증한다. 결과 수치는 실제 결과가 아니다.
    - 결측은 현재 목록별 삭제(listwise)이다. 최종 분석은 다중대체(MI) + Rubin 규칙으로 교체할 것.

사용법
    python talis/talis_ipa_analyzer.py --demo
    python talis/talis_ipa_analyzer.py --data <교사자료.csv|.sav> --out talis/output/talis_ipa.json
"""

import argparse
import itertools
import json
import math
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 1. 설정 (2024 코드북 확인 후 수정)
# ---------------------------------------------------------------------------

CONFIG = {
    "country_var": "CNTRY",          # 국가 코드 변수 (2018: CNTRY)
    "target_country": "KOR",
    "school_var": "IDSCHOOL",
    "final_weight": "TCHWGT",        # 교사 최종가중치 (2018 기준)
    "replicate_prefix": "TRWGT",     # 반복가중치 접두어 (2018: TRWGT1–TRWGT100)
    "fay_k": 0.5,                    # Fay 계수
    "design_df": None,               # 설계 자유도. None 이면 반복가중치 수 사용 (분산 층 수로 교체 권장)
    "importance_metric": "dominance",  # "dominance"(일반 지배분석) 또는 "beta"(|표준화 β|)
    "performance_baseline": "zero",  # "zero"(TALIS 평균과 같음) 또는 "mean"(레버 평균)
    "group_var": "exp_band",         # 하위집단 분석 변수 (예: 경력 구간)
}

# 결과 변수: 높을수록 바람직하도록 direction 지정
OUTCOMES = {
    "out_wellbeing": {"label": "교사 웰빙 지수", "direction": +1},
    "out_intent_stay": {"label": "교직 유지 의향", "direction": +1},
}

# 정책 레버: direction = +1 (높을수록 유리), -1 (높을수록 불리, 예: 업무 부담)
# evidence: "기술" / "연관" / "준인과" — 준인과 분석과 민감도 분석을 통과한 레버만 "준인과"로 갱신
LEVERS = {
    "L1": {"var": "lev_induction", "label": "양성교육·입직 지원", "direction": +1,
           "actor": "양성기관·교육청", "evidence": "연관"},
    "L2": {"var": "lev_pd_effective", "label": "전문성 개발(효과적 연수)", "direction": +1,
           "actor": "교육청·연수원", "evidence": "연관"},
    "L3": {"var": "lev_admin_load", "label": "행정업무 부담", "direction": -1,
           "actor": "교육부·교육청", "evidence": "연관"},
    "L4": {"var": "lev_student_parent_burden", "label": "학생 관리·학부모 민원 부담", "direction": -1,
           "actor": "교육청·학교", "evidence": "연관"},
    "L5": {"var": "lev_autonomy_participation", "label": "수업 자율성·의사결정 참여", "direction": +1,
           "actor": "교육부·학교", "evidence": "연관"},
    "L6": {"var": "lev_digital_support", "label": "디지털·AI 교육적 활용 지원", "direction": +1,
           "actor": "교육청·양성기관", "evidence": "연관"},
    "L7": {"var": "lev_inclusion_prep", "label": "포용교육 준비도·지원", "direction": +1,
           "actor": "교육청·양성기관", "evidence": "연관"},
    "L8": {"var": "lev_feedback_recognition", "label": "피드백·인정·보상", "direction": +1,
           "actor": "교육부", "evidence": "연관"},
}

# 코드북 변수명 → 분석용 변수명 (실제 자료 사용 시 채울 것)
# 예: {"T4XXXXX": "out_wellbeing", ...}  ※ 2024 코드북에서 확인
VARIABLE_MAP = {}

# 국제 자료가 없을 때 사용할 외부 기준값 (보고서 표에서 입력)
# 예: {"lev_admin_load": {"talis_avg": 10.2, "sd": 2.0}}
EXTERNAL_BENCHMARKS = {}

QUADRANT_LABELS = ["I. 집중개선", "II. 유지강화", "III. 점진개선", "IV. 재배치검토"]


# ---------------------------------------------------------------------------
# 2. BRR 유틸리티
# ---------------------------------------------------------------------------

def replicate_columns(df, prefix):
    cols = [c for c in df.columns if c.startswith(prefix) and c[len(prefix):].isdigit()]
    return sorted(cols, key=lambda c: int(c[len(prefix):]))


def weight_matrix(df, cfg):
    """(n × (G+1)) 가중치 행렬. 0열 = 최종가중치, 1..G열 = 반복가중치."""
    reps = replicate_columns(df, cfg["replicate_prefix"])
    if not reps:
        raise ValueError(f"반복가중치({cfg['replicate_prefix']}*)를 찾을 수 없습니다.")
    return df[[cfg["final_weight"]] + reps].to_numpy(dtype=float)


def brr_variance(theta0, theta_reps, k):
    """Fay 수정 BRR 분산(공분산). theta_reps: (G × p)."""
    theta_reps = np.atleast_2d(theta_reps)
    G = theta_reps.shape[0]
    dev = theta_reps - np.asarray(theta0)[None, :]
    return dev.T @ dev / (G * (1 - k) ** 2)


def brr_run(func, W, k):
    """func(w) -> 1차원 추정치 벡터. 모든 가중치 열에 대해 반복 실행."""
    est = np.asarray(func(W[:, 0]), dtype=float)
    reps = np.vstack([np.asarray(func(W[:, g]), dtype=float) for g in range(1, W.shape[1])])
    V = brr_variance(est, reps, k)
    return est, np.sqrt(np.clip(np.diag(V), 0, None)), reps, V


def _betacf(a, b, x, max_iter=300, eps=3e-14):
    """정칙화 불완전 베타함수의 연분수 전개 (Numerical Recipes)."""
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > 1e-300 else 1e-300)
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > 1e-300 else 1e-300)
        c = 1.0 + aa / c if abs(c) > 1e-300 else 1e-300
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > 1e-300 else 1e-300)
        c = 1.0 + aa / c if abs(c) > 1e-300 else 1e-300
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def betainc_reg(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log(1 - x))
    if x < (a + 1) / (a + b + 2):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1 - x) / b


def f_sf(F, d1, d2):
    """F 분포 상측 확률 P(F_{d1,d2} > F)."""
    if F <= 0:
        return 1.0
    x = d2 / (d2 + d1 * F)
    return betainc_reg(d2 / 2.0, d1 / 2.0, x)


def brr_wald_test(theta0, V, R, r=None, design_df=None):
    """설계 자유도 보정 Wald F 검정. H0: R θ = r."""
    R = np.atleast_2d(R)
    q = R.shape[0]
    r = np.zeros(q) if r is None else np.asarray(r)
    diff = R @ theta0 - r
    middle = R @ V @ R.T
    W = float(diff @ np.linalg.pinv(middle) @ diff)
    d = design_df
    if d is None or d - q + 1 <= 0:
        return {"wald_chi2": W, "q": q, "F": None, "df": None, "p": None}
    F = (d - q + 1) / (d * q) * W
    return {"wald_chi2": round(W, 4), "q": q, "F": round(F, 4),
            "df": [q, d - q + 1], "p": round(f_sf(F, q, d - q + 1), 4)}


# ---------------------------------------------------------------------------
# 3. 가중 통계와 지배분석
# ---------------------------------------------------------------------------

def wmean(x, w):
    return float(np.sum(w * x) / np.sum(w))


def wcorr_matrix(X, w):
    w = w / w.sum()
    mu = w @ X
    Xc = X - mu
    cov = (Xc * w[:, None]).T @ Xc
    sd = np.sqrt(np.diag(cov))
    return cov / np.outer(sd, sd)


def r2_from_corr(Rxx, rxy, idx):
    if len(idx) == 0:
        return 0.0
    idx = list(idx)
    sub = Rxx[np.ix_(idx, idx)]
    b = np.linalg.solve(sub, rxy[idx])
    return float(rxy[idx] @ b)


def general_dominance(Rxx, rxy):
    """일반 지배 가중치 (Σ = 전체 R²)."""
    K = len(rxy)
    r2 = {}
    for s in range(K + 1):
        for comb in itertools.combinations(range(K), s):
            r2[comb] = r2_from_corr(Rxx, rxy, comb)
    gd = np.zeros(K)
    for j in range(K):
        others = [i for i in range(K) if i != j]
        by_size = []
        for s in range(K):
            incs = []
            for comb in itertools.combinations(others, s):
                with_j = tuple(sorted(comb + (j,)))
                incs.append(r2[with_j] - r2[comb])
            by_size.append(np.mean(incs))
        gd[j] = np.mean(by_size)
    return gd, r2[tuple(range(K))]


def importance_estimator(X, y, metric):
    """반환 벡터: [중요도(K), β(K), R²]."""
    K = X.shape[1]

    def f(w):
        C = wcorr_matrix(np.column_stack([X, y]), w)
        Rxx, rxy = C[:K, :K], C[:K, K]
        beta = np.linalg.solve(Rxx, rxy)
        if metric == "dominance":
            imp, r2 = general_dominance(Rxx, rxy)
        else:
            imp, r2 = np.abs(beta), float(rxy @ beta)
        return np.concatenate([imp, beta, [r2]])

    return f


# ---------------------------------------------------------------------------
# 4. 수행도: 한국 vs TALIS 평균
# ---------------------------------------------------------------------------

def country_means(df, var, cfg):
    """국가별 가중평균과 BRR 표준오차."""
    out = {}
    for c, sub in df.groupby(cfg["country_var"]):
        sub = sub.dropna(subset=[var])
        W = weight_matrix(sub, cfg)
        x = sub[var].to_numpy(float)
        est, se, _, _ = brr_run(lambda w: [wmean(x, w)], W, cfg["fay_k"])
        out[c] = (est[0], se[0])
    return out


def pooled_sd(df, var, cfg):
    """국가별 가중치 합을 같게 맞춘(senate) 통합 표준편차."""
    sub = df.dropna(subset=[var])
    w = sub[cfg["final_weight"]].to_numpy(float)
    tot = sub.groupby(cfg["country_var"])[cfg["final_weight"]].transform("sum").to_numpy(float)
    w = w / tot
    x = sub[var].to_numpy(float)
    m = np.sum(w * x) / np.sum(w)
    return float(np.sqrt(np.sum(w * (x - m) ** 2) / np.sum(w)))


def performance_scores(df, cfg):
    """레버별 표준화 수행도와 표준오차.

    P_j = d_j (μ_KOR − μ̄_TALIS) / σ_j,  μ̄_TALIS = 국가 평균들의 산술평균(한국 포함).
    SE(μ_KOR − μ̄) = sqrt((1−1/C)² SE_KOR² + (1/C²) Σ_{c≠KOR} SE_c²)  (국가 간 독립 가정)
    σ_j 는 고정값으로 취급한다.
    """
    target = cfg["target_country"]
    multi = cfg["country_var"] in df.columns and df[cfg["country_var"]].nunique() > 1
    res = {}
    for lid, lv in LEVERS.items():
        var = lv["var"]
        if multi:
            cm = country_means(df, var, cfg)
            C = len(cm)
            kor, kor_se = cm[target]
            avg = float(np.mean([m for m, _ in cm.values()]))
            se_diff = math.sqrt((1 - 1 / C) ** 2 * kor_se ** 2 +
                                sum(se ** 2 for c, (_, se) in cm.items() if c != target) / C ** 2)
            sd = pooled_sd(df, var, cfg)
            source = f"TALIS 초등 참여 {C}개 체제 평균"
        else:
            bm = EXTERNAL_BENCHMARKS.get(var)
            if bm is None:
                raise ValueError(f"{var}: 국제 자료가 없고 EXTERNAL_BENCHMARKS 값도 없습니다.")
            sub = df.dropna(subset=[var])
            W = weight_matrix(sub, cfg)
            x = sub[var].to_numpy(float)
            est, se, _, _ = brr_run(lambda w: [wmean(x, w)], W, cfg["fay_k"])
            kor, kor_se, avg, sd = est[0], se[0], bm["talis_avg"], bm["sd"]
            se_diff = kor_se
            source = "외부 기준값(보고서 표)"
        d = lv["direction"]
        res[lid] = {
            "korea_mean": round(kor, 3), "korea_mean_se": round(kor_se, 3),
            "talis_avg": round(avg, 3), "pooled_sd": round(sd, 3),
            "performance": round(d * (kor - avg) / sd, 3),
            "performance_se": round(se_diff / sd, 3),
            "benchmark_source": source,
        }
    return res


# ---------------------------------------------------------------------------
# 5. TALIS-IPA
# ---------------------------------------------------------------------------

def classify(imp, perf, ib, pb):
    if imp >= ib:
        return QUADRANT_LABELS[0] if perf < pb else QUADRANT_LABELS[1]
    return QUADRANT_LABELS[2] if perf < pb else QUADRANT_LABELS[3]


def prepare_xy(sub, outcome):
    """레버를 '유리한 방향'으로 맞춘 행렬 X와 결과 y."""
    X = np.column_stack([lv["direction"] * sub[lv["var"]].to_numpy(float) for lv in LEVERS.values()])
    y = OUTCOMES[outcome]["direction"] * sub[outcome].to_numpy(float)
    return X, y


def importance_block(sub, outcome, cfg):
    X, y = prepare_xy(sub, outcome)
    W = weight_matrix(sub, cfg)
    f = importance_estimator(X, y, cfg["importance_metric"])
    est, se, reps, V = brr_run(f, W, cfg["fay_k"])
    return est, se, reps, V


def ipa_for_outcome(kor, outcome, perf, cfg):
    K = len(LEVERS)
    cols = [lv["var"] for lv in LEVERS.values()] + [outcome]
    sub = kor.dropna(subset=cols)
    est, se, _, _ = importance_block(sub, outcome, cfg)
    imp, imp_se = est[:K], se[:K]
    beta, beta_se = est[K:2 * K], se[K:2 * K]
    r2, r2_se = est[-1], se[-1]

    ib = float(np.mean(imp))
    pvals = [perf[l]["performance"] for l in LEVERS]
    pb = 0.0 if cfg["performance_baseline"] == "zero" else float(np.mean(pvals))

    levers, quadrants = [], {q: [] for q in QUADRANT_LABELS}
    for j, (lid, lv) in enumerate(LEVERS.items()):
        p = perf[lid]
        q = classify(imp[j], p["performance"], ib, pb)
        sign_warning = beta[j] < 0
        item = {
            "id": lid, "label": lv["label"], "actor": lv["actor"], "evidence": lv["evidence"],
            "importance": round(float(imp[j]), 4), "importance_se": round(float(imp_se[j]), 4),
            "beta_std": round(float(beta[j]), 3), "beta_std_se": round(float(beta_se[j]), 3),
            **p, "quadrant": q,
            "sign_warning": bool(sign_warning),
            # 우선 과제: 집중개선 사분면 + 준인과 근거 + 부호가 기대와 일치
            "priority_flag": bool(q == QUADRANT_LABELS[0] and lv["evidence"] == "준인과"
                                  and not sign_warning),
        }
        levers.append(item)
        quadrants[q].append({k: item[k] for k in ("id", "label", "importance", "performance")})

    ranking = sorted(levers, key=lambda d: (d["quadrant"] != QUADRANT_LABELS[0],
                                            -(d["importance"] - ib) + d["performance"]))
    return {
        "label": OUTCOMES[outcome]["label"], "n": int(len(sub)),
        "importance_metric": cfg["importance_metric"],
        "r2": round(float(r2), 4), "r2_se": round(float(r2_se), 4),
        "baselines": {"importance": round(ib, 4), "performance": round(pb, 3)},
        "levers": levers, "quadrants": quadrants,
        "priority_ranking": [{"id": d["id"], "label": d["label"], "quadrant": d["quadrant"]}
                             for d in ranking],
    }


def heterogeneity_tests(kor, outcome, cfg):
    """하위집단 간 표준화 β 동일성 Wald F 검정 (같은 반복가중치 루프에서 공분산 확보)."""
    gv = cfg["group_var"]
    if gv not in kor.columns:
        return {}
    K = len(LEVERS)
    cols = [lv["var"] for lv in LEVERS.values()] + [outcome, gv]
    sub = kor.dropna(subset=cols)
    groups = sorted(sub[gv].unique())
    X, y = prepare_xy(sub, outcome)
    g = sub[gv].to_numpy()
    W = weight_matrix(sub, cfg)

    def f(w):
        out = []
        for grp in groups:
            m = g == grp
            C = wcorr_matrix(np.column_stack([X[m], y[m]]), w[m])
            out.append(np.linalg.solve(C[:K, :K], C[:K, K]))
        return np.concatenate(out)

    est, se, _, V = brr_run(f, W, cfg["fay_k"])
    d = cfg["design_df"] or (W.shape[1] - 1)
    G = len(groups)
    tests, by_group = {}, {}
    for j, lid in enumerate(LEVERS):
        idx = [gi * K + j for gi in range(G)]
        R = np.zeros((G - 1, len(est)))
        for r in range(G - 1):
            R[r, idx[0]], R[r, idx[r + 1]] = 1, -1
        tests[lid] = brr_wald_test(est, V, R, design_df=d)
        by_group[lid] = {str(grp): {"beta_std": round(float(est[idx[gi]]), 3),
                                    "se": round(float(se[idx[gi]]), 3)}
                         for gi, grp in enumerate(groups)}
    return {"group_var": gv, "groups": [str(x) for x in groups], "design_df": d,
            "beta_by_group": by_group, "wald_equal_beta": tests}


def design_effect_check(kor, var, cfg):
    """BRR 표준오차와 단순무작위 표준오차 비교 (설계효과 점검)."""
    sub = kor.dropna(subset=[var])
    W = weight_matrix(sub, cfg)
    x = sub[var].to_numpy(float)
    _, se, _, _ = brr_run(lambda w: [wmean(x, w)], W, cfg["fay_k"])
    se_srs = float(np.std(x, ddof=1) / math.sqrt(len(x)))
    return {"var": var, "se_brr": round(float(se[0]), 4), "se_srs": round(se_srs, 4),
            "deff": round(float((se[0] / se_srs) ** 2), 2)}


def run(df, cfg, synthetic=False):
    df = df.rename(columns=VARIABLE_MAP)
    kor = df[df[cfg["country_var"]] == cfg["target_country"]] if cfg["country_var"] in df else df
    perf = performance_scores(df, cfg)
    result = {
        "meta": {
            "title": "TALIS-IPA 정책 우선순위 분석",
            "synthetic_demo": synthetic,
            "warning": ("가상(합성) 자료로 생성한 데모 결과입니다. 실제 TALIS 결과가 아닙니다."
                        if synthetic else "실제 자료 분석 결과. 변수 정의와 가중치를 코드북으로 재확인할 것."),
            "generated": date.today().isoformat(),
            "target_country": cfg["target_country"],
            "n_target": int(len(kor)),
            "n_replicates": len(replicate_columns(df, cfg["replicate_prefix"])),
            "fay_k": cfg["fay_k"],
            "missing_data": "listwise (최종 분석은 MI로 교체)",
            "levers": LEVERS, "outcomes": OUTCOMES,
        },
        "design_effect": [design_effect_check(kor, o, cfg) for o in OUTCOMES],
        "outcomes": {},
    }
    for o in OUTCOMES:
        block = ipa_for_outcome(kor, o, perf, cfg)
        block["heterogeneity"] = heterogeneity_tests(kor, o, cfg)
        result["outcomes"][o] = block
    return result


# ---------------------------------------------------------------------------
# 6. 데모용 합성 자료 (BRR 반복가중치 포함)
# ---------------------------------------------------------------------------

def sylvester_hadamard(n):
    H = np.array([[1]])
    while H.shape[0] < n:
        H = np.block([[H, H], [H, -H]])
    return H


def make_synthetic(seed=2024, n_countries=10, n_schools=120, t_per_school=15, k=0.5):
    """가상 TALIS형 자료: 국가 × 학교(분산 층 짝) × 교사, Fay BRR 반복가중치 포함."""
    rng = np.random.default_rng(seed)
    n_zones = n_schools // 2
    H = sylvester_hadamard(n_zones + 1)          # 열 0(모두 1)은 쓰지 않고 열 1..Z를 분산 층에 배정
    G = H.shape[0]
    K = len(LEVERS)
    true_b = np.array([0.15, 0.10, 0.35, 0.25, 0.20, 0.05, 0.05, 0.15])  # 가상 효과
    rows = []
    countries = ["KOR"] + [f"C{i:02d}" for i in range(1, n_countries)]
    for ci, c in enumerate(countries):
        shift = rng.normal(0, 0.3, K)
        if c == "KOR":  # 데모용 가상 패턴 (실제 결과 아님)
            shift = np.array([-0.2, 0.0, 0.5, 0.4, -0.5, 0.3, -0.4, -0.3])
        for s in range(n_schools):
            zone, member = divmod(s, 2)
            school_eff = rng.normal(0, 0.45, K)
            w_school = rng.uniform(40, 160)
            for _ in range(t_per_school):
                lev = shift + school_eff + rng.normal(0, 1, K)
                fav = lev * np.array([lv["direction"] for lv in LEVERS.values()])
                u = rng.normal(0, 0.35)
                wb = fav @ true_b + u + rng.normal(0, 0.8)
                stay = 0.6 * wb + rng.normal(0, 0.9)
                w = w_school * rng.uniform(0.9, 1.1)
                sign = H[:, zone + 1]               # 모든 행 사용 → 각 층이 균형(±1 동수)
                fac = np.where(sign * (1 if member == 0 else -1) > 0, 2 - k, k)
                row = {"CNTRY": c, "IDSCHOOL": f"{c}-{s:03d}", "TCHWGT": w,
                       "exp_band": rng.choice(["0-5년", "6-10년", "11년이상"], p=[.25, .2, .55]),
                       "out_wellbeing": wb, "out_intent_stay": stay}
                for j, lv in enumerate(LEVERS.values()):
                    row[lv["var"]] = lev[j]
                for g in range(G):
                    row[f"TRWGT{g + 1}"] = w * fac[g]
                rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 7. 실행
# ---------------------------------------------------------------------------

def load(path):
    path = Path(path)
    if path.suffix.lower() == ".sav":
        try:
            import pyreadstat  # noqa: F401
        except ImportError as e:
            raise SystemExit("SPSS(.sav) 파일은 pyreadstat 이 필요합니다: pip install pyreadstat") from e
        return pd.read_spss(path)
    return pd.read_csv(path)


def main():
    ap = argparse.ArgumentParser(description="TALIS-IPA 정책 우선순위 분석")
    ap.add_argument("--data", help="교사 자료 (CSV 또는 SPSS .sav; 국제 비교 시 여러 국가 포함)")
    ap.add_argument("--demo", action="store_true", help="가상 자료로 파이프라인 검증")
    ap.add_argument("--metric", choices=["dominance", "beta"], help="중요도 지표")
    ap.add_argument("--out", default=None, help="결과 JSON 경로")
    args = ap.parse_args()

    cfg = dict(CONFIG)
    if args.metric:
        cfg["importance_metric"] = args.metric
    here = Path(__file__).resolve().parent
    if args.demo:
        df = make_synthetic()
        out = Path(args.out or here / "output" / "talis_ipa_demo_SYNTHETIC.json")
    elif args.data:
        df = load(args.data)
        out = Path(args.out or here / "output" / "talis_ipa_results.json")
    else:
        ap.error("--data 또는 --demo 중 하나를 지정하세요.")

    res = run(df, cfg, synthetic=args.demo)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[완료] {out}")
    if args.demo:
        print("※ 가상(합성) 자료 결과입니다. 실제 TALIS 결과가 아닙니다.")
    for o, b in res["outcomes"].items():
        print(f"\n■ {b['label']} (n={b['n']}, R²={b['r2']:.3f}±{b['r2_se']:.3f}, 중요도={b['importance_metric']})")
        print(f"  기준선: 중요도 {b['baselines']['importance']:.4f}, 수행도 {b['baselines']['performance']:.2f}")
        for lv in b["levers"]:
            print(f"  {lv['id']} {lv['label']:<22} I={lv['importance']:.4f}(±{lv['importance_se']:.4f}) "
                  f"P={lv['performance']:+.2f}(±{lv['performance_se']:.2f}) → {lv['quadrant']}"
                  + ("  [부호주의]" if lv["sign_warning"] else ""))
    for d in res["design_effect"]:
        print(f"\n설계효과 점검 {d['var']}: SE_BRR={d['se_brr']}, SE_SRS={d['se_srs']}, deff={d['deff']}")


if __name__ == "__main__":
    main()

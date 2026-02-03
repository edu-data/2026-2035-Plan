# -*- coding: utf-8 -*-
"""
IPA (Importance-Performance Analysis) 분석 시스템
경인교육대학교 중장기 발전계획 2026-2035

분석 대상:
- 5대 발전전략
- 21개 핵심과제
- 중요도-수행도 분석
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 데이터 경로
DATA_DIR = Path(r"d:/plan/data")

# 5대 발전전략 및 핵심과제 매핑
STRATEGIES = {
    "I": {
        "name": "AI·스마트 캠퍼스 혁신",
        "core_tasks": {
            "I-1": "AI 기반 예비교원 교육혁신",
            "I-2": "스마트 캠퍼스 조성을 통한 교육/연구 환경 혁신",
            "I-3": "AI 기반 교원 전문성 신장 및 지역 연계 체계 구축",
            "I-4": "AI 기반 교육콘텐츠 및 에듀테크 활용·개발 체계 구축"
        }
    },
    "II": {
        "name": "교육연구 선도 연구체제 선진화",
        "core_tasks": {
            "II-1": "초등교원 양성 특화 연구 강화",
            "II-2": "교육전문대학원 연구 지원 체계 고도화",
            "II-3": "지역 공동연구 및 지원 체계 강화",
            "II-4": "통합 연구지원 및 성과 확산 체계 고도화"
        }
    },
    "III": {
        "name": "포용성·공공성(사회문제해결) 고도화",
        "core_tasks": {
            "III-1": "교육 사각지대 해소를 위한 G-멘토링 플랫폼 고도화",
            "III-2": "지역사회와 함께하는 미래형 시민교육 확산",
            "III-3": "지역 현안 해결을 위한 교육 정책 싱크탱크 역할 강화",
            "III-4": "지속가능한 미래를 위한 ESG 교육 생태계 조성"
        }
    },
    "IV": {
        "name": "학생 역량·행복 증진",
        "core_tasks": {
            "IV-1": "학생 역량 개발 및 성장 지원",
            "IV-2": "학생 생활 공간 개선",
            "IV-3": "학생 적응 및 활동 지원",
            "IV-4": "학생 만족도 및 편의 증진 지원"
        }
    },
    "V": {
        "name": "글로벌 허브",
        "core_tasks": {
            "V-1": "해외파견 프로그램의 다변화 및 파트너 국가 확대",
            "V-2": "교육실습 및 해외 학점인정 체계 개선",
            "V-3": "다문화·세계시민 교육 기반 프로그램 확대",
            "V-4": "외국인 학생 및 교육자 유치 기반 강화",
            "V-5": "국제 공동연구 및 가상 교류 활성화"
        }
    }
}

# 문항-전략 매핑 (사용자 제공 정확한 순서)
# ques_1: 대학비전 (단일 문항)
# ques_2/3: 핵심가치 (중요도/수행도)
# ques_5/6: 위기요인 (중요도/수행도)
# ques_8/9: 대응방향 (중요도/수행도)
# ques_11/12: 5대 발전전략 (중요도/수행도)
# ques_14/15: I. AI·스마트 (중요도/수행도)
# ques_16/17: II. 교육연구 (중요도/수행도)
# ques_18/19: III. 포용성·공공성 (중요도/수행도)
# ques_20/21: IV. 학생역량·행복 (중요도/수행도)
# ques_22/23: V. 글로벌 허브 (중요도/수행도)

IPA_MAPPING = {
    "핵심가치": {"importance": ["ques_2(1)", "ques_2(2)", "ques_2(3)", "ques_2(4)", "ques_2(5)"],
                 "performance": ["ques_3(1)", "ques_3(2)", "ques_3(3)", "ques_3(4)", "ques_3(5)"]},
    "위기요인": {"importance": ["ques_5(1)", "ques_5(2)", "ques_5(3)", "ques_5(4)", "ques_5(5)"],
                 "performance": ["ques_6(1)", "ques_6(2)", "ques_6(3)", "ques_6(4)", "ques_6(5)"]},
    "대응방향": {"importance": ["ques_8(1)", "ques_8(2)", "ques_8(3)", "ques_8(4)", "ques_8(5)"],
                 "performance": ["ques_9(1)", "ques_9(2)", "ques_9(3)", "ques_9(4)", "ques_9(5)"]},
    "5대발전전략": {"importance": ["ques_11(1)", "ques_11(2)", "ques_11(3)", "ques_11(4)", "ques_11(5)"],
                    "performance": ["ques_12(1)", "ques_12(2)", "ques_12(3)", "ques_12(4)", "ques_12(5)"]},
    "I.AI·스마트": {"importance": ["ques_14(1)", "ques_14(2)", "ques_14(3)", "ques_14(4)"],
                    "performance": ["ques_15(1)", "ques_15(2)", "ques_15(3)", "ques_15(4)"]},
    "II.교육연구": {"importance": ["ques_16(1)", "ques_16(2)", "ques_16(3)", "ques_16(4)"],
                    "performance": ["ques_17(1)", "ques_17(2)", "ques_17(3)", "ques_17(4)"]},
    "III.포용성·공공성": {"importance": ["ques_18(1)", "ques_18(2)", "ques_18(3)", "ques_18(4)"],
                          "performance": ["ques_19(1)", "ques_19(2)", "ques_19(3)", "ques_19(4)"]},
    "IV.학생역량·행복": {"importance": ["ques_20(1)", "ques_20(2)", "ques_20(3)", "ques_20(4)"],
                         "performance": ["ques_21(1)", "ques_21(2)", "ques_21(3)", "ques_21(4)"]},
    "V.글로벌허브": {"importance": ["ques_22(1)", "ques_22(2)", "ques_22(3)", "ques_22(4)", "ques_22(5)"],
                     "performance": ["ques_23(1)", "ques_23(2)", "ques_23(3)", "ques_23(4)", "ques_23(5)"]},
}

# 세부 문항 라벨 (사용자 제공 문항 순서)
ITEM_LABELS = {
    # 핵심가치 (ques_2/3)
    "ques_2(1)": "혁신",
    "ques_2(2)": "창의",
    "ques_2(3)": "수월",
    "ques_2(4)": "배려",
    "ques_2(5)": "소통",
    # 위기요인 (ques_5/6)
    "ques_5(1)": "시대적 변화 대응 역량 교원 확보 요구",
    "ques_5(2)": "저출산 초등교원 수요 감소",
    "ques_5(3)": "교육적 배려 학생 증가 양성과정 개편",
    "ques_5(4)": "교육대학원 수요 감소",
    "ques_5(5)": "교육청과의 협력 약화",
    # 대응방향 (ques_8/9)
    "ques_8(1)": "특수목적 실현 및 고유발전 모델",
    "ques_8(2)": "교사교육기관 역할 강화",
    "ques_8(3)": "시대적 변화 대응 역량 교원 양성",
    "ques_8(4)": "교육 기회균등 및 공공성 제고",
    "ques_8(5)": "지역사회 연계 및 공헌",
    # 5대발전전략 (ques_11/12)
    "ques_11(1)": "AI·스마트 캠퍼스 혁신",
    "ques_11(2)": "교육연구 선도",
    "ques_11(3)": "포용성·공공성 고도화",
    "ques_11(4)": "학생 역량·행복 증진",
    "ques_11(5)": "글로벌 허브",
    # I. AI·스마트 (ques_14/15)
    "ques_14(1)": "AI 기반 교육혁신",
    "ques_14(2)": "스마트 캠퍼스 구축",
    "ques_14(3)": "AI 교원 전문성",
    "ques_14(4)": "에듀테크 활용",
    # II. 교육연구 (ques_16/17)
    "ques_16(1)": "초등교원 연구 강화",
    "ques_16(2)": "대학원 연구 지원",
    "ques_16(3)": "지역 공동연구",
    "ques_16(4)": "연구지원 체계",
    # III. 포용성·공공성 (ques_18/19)
    "ques_18(1)": "G-멘토링 플랫폼",
    "ques_18(2)": "미래형 시민교육",
    "ques_18(3)": "교육정책 싱크탱크",
    "ques_18(4)": "ESG 교육 생태계",
    # IV. 학생역량·행복 (ques_20/21)
    "ques_20(1)": "학생 역량 개발",
    "ques_20(2)": "학생 생활공간",
    "ques_20(3)": "학생 적응·활동",
    "ques_20(4)": "학생 만족도",
    # V. 글로벌허브 (ques_22/23)
    "ques_22(1)": "해외파견 다변화",
    "ques_22(2)": "교육실습 체계",
    "ques_22(3)": "다문화·세계시민",
    "ques_22(4)": "외국인 유치",
    "ques_22(5)": "국제 공동연구",
}


def load_data():
    """설문 데이터 로딩"""
    datasets = {}
    
    # 교직원 데이터 (주 분석 대상)
    df_staff = pd.read_excel(DATA_DIR / "교직원.xlsx")
    df_staff['group'] = '교직원'
    datasets['교직원'] = df_staff
    
    # 졸업생 데이터
    df_alumni = pd.read_excel(DATA_DIR / "졸업생.xlsx")
    df_alumni['group'] = '졸업생'
    datasets['졸업생'] = df_alumni
    
    # 학부생 데이터
    df_student = pd.read_excel(DATA_DIR / "학부생.xlsx")
    df_student['group'] = '학부생'
    datasets['학부생'] = df_student
    
    return datasets


def calculate_ipa_scores(df, mapping):
    """IPA 점수 계산"""
    results = {}
    
    for area, items in mapping.items():
        imp_cols = [c for c in items["importance"] if c in df.columns]
        perf_cols = [c for c in items["performance"] if c in df.columns]
        
        if imp_cols and perf_cols:
            # 숫자형 데이터만 추출
            imp_values = df[imp_cols].apply(pd.to_numeric, errors='coerce')
            perf_values = df[perf_cols].apply(pd.to_numeric, errors='coerce')
            
            imp_mean = float(imp_values.values.flatten()[~np.isnan(imp_values.values.flatten())].mean())
            perf_mean = float(perf_values.values.flatten()[~np.isnan(perf_values.values.flatten())].mean())
            
            results[area] = {
                "importance": round(imp_mean, 2),
                "performance": round(perf_mean, 2),
                "gap": round(imp_mean - perf_mean, 2)
            }
    
    return results


def calculate_item_ipa(df, mapping):
    """개별 문항별 IPA 점수 계산"""
    item_results = {}
    
    for area, items in mapping.items():
        imp_cols = [c for c in items["importance"] if c in df.columns]
        perf_cols = [c for c in items["performance"] if c in df.columns]
        
        # 쌍으로 매칭
        for i, (imp_col, perf_col) in enumerate(zip(imp_cols, perf_cols)):
            if imp_col in df.columns and perf_col in df.columns:
                imp_vals = pd.to_numeric(df[imp_col], errors='coerce').dropna()
                perf_vals = pd.to_numeric(df[perf_col], errors='coerce').dropna()
                
                if len(imp_vals) > 0 and len(perf_vals) > 0:
                    label = ITEM_LABELS.get(imp_col, imp_col)
                    item_results[label] = {
                        "area": area,
                        "importance": round(float(imp_vals.mean()), 2),
                        "performance": round(float(perf_vals.mean()), 2),
                        "gap": round(float(imp_vals.mean() - perf_vals.mean()), 2),
                        "imp_col": imp_col,
                        "perf_col": perf_col
                    }
    
    return item_results


def classify_quadrant(importance, performance, imp_baseline, perf_baseline):
    """IPA 4분면 분류"""
    if importance >= imp_baseline:
        if performance < perf_baseline:
            return "I. 집중개선"
        else:
            return "II. 유지강화"
    else:
        if performance < perf_baseline:
            return "III. 저우선"
        else:
            return "IV. 과잉투자"


def analyze_group_detail(df, group_name):
    """그룹별 상세 IPA 분석 (세부영역, 5대전략, 21개과제)"""
    group_result = {
        "areas": calculate_ipa_scores(df, IPA_MAPPING),
        "detail_areas": {},
        "strategies_5": {},
        "tasks_21": {}
    }
    
    # 세부영역별 IPA
    detail_area_mapping = {k: v for k, v in IPA_MAPPING.items() 
                           if k in ["핵심가치", "위기요인", "대응방향", "5대발전전략"]}
    
    for area_name, items in detail_area_mapping.items():
        area_items = {}
        imp_cols = [c for c in items["importance"] if c in df.columns]
        perf_cols = [c for c in items["performance"] if c in df.columns]
        
        for i, (imp_col, perf_col) in enumerate(zip(imp_cols, perf_cols)):
            if imp_col in df.columns and perf_col in df.columns:
                imp_vals = pd.to_numeric(df[imp_col], errors='coerce').dropna()
                perf_vals = pd.to_numeric(df[perf_col], errors='coerce').dropna()
                
                if len(imp_vals) > 0 and len(perf_vals) > 0:
                    label = ITEM_LABELS.get(imp_col, f"{area_name}_{i+1}")
                    area_items[label] = {
                        "importance": round(float(imp_vals.mean()), 2),
                        "performance": round(float(perf_vals.mean()), 2),
                        "gap": round(float(imp_vals.mean() - perf_vals.mean()), 2)
                    }
        
        if area_items:
            imp_baseline = np.mean([v["importance"] for v in area_items.values()])
            perf_baseline = np.mean([v["performance"] for v in area_items.values()])
            
            quadrants = {"I. 집중개선": [], "II. 유지강화": [], "III. 저우선": [], "IV. 과잉투자": []}
            for item_name, scores in area_items.items():
                quadrant = classify_quadrant(scores["importance"], scores["performance"], imp_baseline, perf_baseline)
                quadrants[quadrant].append({
                    "item": item_name,
                    "importance": scores["importance"],
                    "performance": scores["performance"],
                    "gap": scores["gap"]
                })
            
            group_result["detail_areas"][area_name] = {
                "items": area_items,
                "baselines": {"importance": round(imp_baseline, 2), "performance": round(perf_baseline, 2)},
                "quadrants": quadrants
            }
    
    # 5대 발전전략 IPA
    strategy_mapping = {k: v for k, v in IPA_MAPPING.items() 
                        if k.startswith(("I.", "II.", "III.", "IV.", "V."))}
    
    strategy_items = {}
    for strategy_name, items in strategy_mapping.items():
        imp_cols = [c for c in items["importance"] if c in df.columns]
        perf_cols = [c for c in items["performance"] if c in df.columns]
        
        if imp_cols and perf_cols:
            imp_values = df[imp_cols].apply(pd.to_numeric, errors='coerce')
            perf_values = df[perf_cols].apply(pd.to_numeric, errors='coerce')
            
            imp_flat = imp_values.values.flatten()
            perf_flat = perf_values.values.flatten()
            imp_mean = float(imp_flat[~np.isnan(imp_flat)].mean()) if len(imp_flat[~np.isnan(imp_flat)]) > 0 else 0
            perf_mean = float(perf_flat[~np.isnan(perf_flat)].mean()) if len(perf_flat[~np.isnan(perf_flat)]) > 0 else 0
            
            strategy_items[strategy_name] = {
                "importance": round(imp_mean, 2),
                "performance": round(perf_mean, 2),
                "gap": round(imp_mean - perf_mean, 2)
            }
    
    if strategy_items:
        imp_baseline = np.mean([v["importance"] for v in strategy_items.values()])
        perf_baseline = np.mean([v["performance"] for v in strategy_items.values()])
        
        quadrants = {"I. 집중개선": [], "II. 유지강화": [], "III. 저우선": [], "IV. 과잉투자": []}
        for item_name, scores in strategy_items.items():
            quadrant = classify_quadrant(scores["importance"], scores["performance"], imp_baseline, perf_baseline)
            quadrants[quadrant].append({
                "strategy": item_name,
                "importance": scores["importance"],
                "performance": scores["performance"],
                "gap": scores["gap"]
            })
        
        group_result["strategies_5"] = {
            "items": strategy_items,
            "baselines": {"importance": round(imp_baseline, 2), "performance": round(perf_baseline, 2)},
            "quadrants": quadrants
        }
    
    # 21개 세부과제 IPA
    all_task_items = {}
    for strategy_name, items in strategy_mapping.items():
        imp_cols = [c for c in items["importance"] if c in df.columns]
        perf_cols = [c for c in items["performance"] if c in df.columns]
        
        for i, (imp_col, perf_col) in enumerate(zip(imp_cols, perf_cols)):
            if imp_col in df.columns and perf_col in df.columns:
                imp_vals = pd.to_numeric(df[imp_col], errors='coerce').dropna()
                perf_vals = pd.to_numeric(df[perf_col], errors='coerce').dropna()
                
                if len(imp_vals) > 0 and len(perf_vals) > 0:
                    base_label = ITEM_LABELS.get(imp_col, f"과제{i+1}")
                    label = f"{strategy_name.split('.')[0]}-{i+1}. {base_label}"
                    all_task_items[label] = {
                        "strategy": strategy_name,
                        "importance": round(float(imp_vals.mean()), 2),
                        "performance": round(float(perf_vals.mean()), 2),
                        "gap": round(float(imp_vals.mean() - perf_vals.mean()), 2)
                    }
    
    if all_task_items:
        imp_baseline = np.mean([v["importance"] for v in all_task_items.values()])
        perf_baseline = np.mean([v["performance"] for v in all_task_items.values()])
        
        quadrants = {"I. 집중개선": [], "II. 유지강화": [], "III. 저우선": [], "IV. 과잉투자": []}
        for item_name, scores in all_task_items.items():
            quadrant = classify_quadrant(scores["importance"], scores["performance"], imp_baseline, perf_baseline)
            quadrants[quadrant].append({
                "task": item_name,
                "strategy": scores["strategy"],
                "importance": scores["importance"],
                "performance": scores["performance"],
                "gap": scores["gap"]
            })
        
        gap_ranking = sorted(
            [(k, v["gap"], v["importance"], v["performance"], v["strategy"]) for k, v in all_task_items.items()],
            key=lambda x: x[1], reverse=True
        )
        
        group_result["tasks_21"] = {
            "items": all_task_items,
            "baselines": {"importance": round(imp_baseline, 2), "performance": round(perf_baseline, 2)},
            "quadrants": quadrants,
            "gap_ranking": [{"task": g[0], "gap": g[1], "importance": g[2], "performance": g[3], "strategy": g[4]} for g in gap_ranking]
        }
    
    return group_result


def analyze_ipa(datasets):
    """전체 IPA 분석 실행"""
    results = {
        "summary": {},
        "by_group": {},
        "items": {},
        "quadrants": {},
        "detail_areas": {},      # 세부영역별 IPA (핵심가치, 위기요인, 대응방향, 5대전략)
        "strategies_5": {},      # 5대 발전전략 IPA
        "tasks_21": {}           # 21개 세부과제 IPA
    }
    
    # 전체 데이터 합치기
    all_df = pd.concat(datasets.values(), ignore_index=True)
    
    # 영역별 IPA 점수
    results["summary"]["areas"] = calculate_ipa_scores(all_df, IPA_MAPPING)
    
    # 집단별 상세 IPA 분석
    for group, df in datasets.items():
        results["by_group"][group] = analyze_group_detail(df, group)
    
    # 문항별 IPA 점수
    results["items"] = calculate_item_ipa(all_df, IPA_MAPPING)
    
    # === 세부영역별 IPA (핵심가치, 위기요인, 대응방향, 5대발전전략) ===
    detail_area_mapping = {k: v for k, v in IPA_MAPPING.items() 
                           if k in ["핵심가치", "위기요인", "대응방향", "5대발전전략"]}
    
    for area_name, items in detail_area_mapping.items():
        area_items = {}
        imp_cols = [c for c in items["importance"] if c in all_df.columns]
        perf_cols = [c for c in items["performance"] if c in all_df.columns]
        
        for i, (imp_col, perf_col) in enumerate(zip(imp_cols, perf_cols)):
            if imp_col in all_df.columns and perf_col in all_df.columns:
                imp_vals = pd.to_numeric(all_df[imp_col], errors='coerce').dropna()
                perf_vals = pd.to_numeric(all_df[perf_col], errors='coerce').dropna()
                
                if len(imp_vals) > 0 and len(perf_vals) > 0:
                    label = ITEM_LABELS.get(imp_col, f"{area_name}_{i+1}")
                    area_items[label] = {
                        "importance": round(float(imp_vals.mean()), 2),
                        "performance": round(float(perf_vals.mean()), 2),
                        "gap": round(float(imp_vals.mean() - perf_vals.mean()), 2)
                    }
        
        if area_items:
            # 해당 영역의 기준선 계산
            imp_baseline = np.mean([v["importance"] for v in area_items.values()])
            perf_baseline = np.mean([v["performance"] for v in area_items.values()])
            
            # 4분면 분류
            quadrants = {"I. 집중개선": [], "II. 유지강화": [], "III. 저우선": [], "IV. 과잉투자": []}
            for item_name, scores in area_items.items():
                quadrant = classify_quadrant(scores["importance"], scores["performance"], imp_baseline, perf_baseline)
                quadrants[quadrant].append({
                    "item": item_name,
                    "importance": scores["importance"],
                    "performance": scores["performance"],
                    "gap": scores["gap"]
                })
            
            results["detail_areas"][area_name] = {
                "items": area_items,
                "baselines": {"importance": round(imp_baseline, 2), "performance": round(perf_baseline, 2)},
                "quadrants": quadrants
            }
    
    # === 5대 발전전략 IPA ===
    strategy_mapping = {k: v for k, v in IPA_MAPPING.items() 
                        if k.startswith(("I.", "II.", "III.", "IV.", "V."))}
    
    strategy_items = {}
    for strategy_name, items in strategy_mapping.items():
        imp_cols = [c for c in items["importance"] if c in all_df.columns]
        perf_cols = [c for c in items["performance"] if c in all_df.columns]
        
        if imp_cols and perf_cols:
            imp_values = all_df[imp_cols].apply(pd.to_numeric, errors='coerce')
            perf_values = all_df[perf_cols].apply(pd.to_numeric, errors='coerce')
            
            imp_mean = float(imp_values.values.flatten()[~np.isnan(imp_values.values.flatten())].mean())
            perf_mean = float(perf_values.values.flatten()[~np.isnan(perf_values.values.flatten())].mean())
            
            strategy_items[strategy_name] = {
                "importance": round(imp_mean, 2),
                "performance": round(perf_mean, 2),
                "gap": round(imp_mean - perf_mean, 2)
            }
    
    if strategy_items:
        imp_baseline = np.mean([v["importance"] for v in strategy_items.values()])
        perf_baseline = np.mean([v["performance"] for v in strategy_items.values()])
        
        quadrants = {"I. 집중개선": [], "II. 유지강화": [], "III. 저우선": [], "IV. 과잉투자": []}
        for item_name, scores in strategy_items.items():
            quadrant = classify_quadrant(scores["importance"], scores["performance"], imp_baseline, perf_baseline)
            quadrants[quadrant].append({
                "strategy": item_name,
                "importance": scores["importance"],
                "performance": scores["performance"],
                "gap": scores["gap"]
            })
        
        results["strategies_5"] = {
            "items": strategy_items,
            "baselines": {"importance": round(imp_baseline, 2), "performance": round(perf_baseline, 2)},
            "quadrants": quadrants
        }
    
    # === 21개 세부과제 IPA ===
    tasks_21_mapping = {k: v for k, v in IPA_MAPPING.items() 
                        if k.startswith(("I.", "II.", "III.", "IV.", "V."))}
    
    all_task_items = {}
    for strategy_name, items in tasks_21_mapping.items():
        imp_cols = [c for c in items["importance"] if c in all_df.columns]
        perf_cols = [c for c in items["performance"] if c in all_df.columns]
        
        for i, (imp_col, perf_col) in enumerate(zip(imp_cols, perf_cols)):
            if imp_col in all_df.columns and perf_col in all_df.columns:
                imp_vals = pd.to_numeric(all_df[imp_col], errors='coerce').dropna()
                perf_vals = pd.to_numeric(all_df[perf_col], errors='coerce').dropna()
                
                if len(imp_vals) > 0 and len(perf_vals) > 0:
                    base_label = ITEM_LABELS.get(imp_col, f"과제{i+1}")
                    label = f"{strategy_name.split('.')[0]}-{i+1}. {base_label}"
                    all_task_items[label] = {
                        "strategy": strategy_name,
                        "importance": round(float(imp_vals.mean()), 2),
                        "performance": round(float(perf_vals.mean()), 2),
                        "gap": round(float(imp_vals.mean() - perf_vals.mean()), 2)
                    }
    
    if all_task_items:
        imp_baseline = np.mean([v["importance"] for v in all_task_items.values()])
        perf_baseline = np.mean([v["performance"] for v in all_task_items.values()])
        
        quadrants = {"I. 집중개선": [], "II. 유지강화": [], "III. 저우선": [], "IV. 과잉투자": []}
        for item_name, scores in all_task_items.items():
            quadrant = classify_quadrant(scores["importance"], scores["performance"], imp_baseline, perf_baseline)
            quadrants[quadrant].append({
                "task": item_name,
                "strategy": scores["strategy"],
                "importance": scores["importance"],
                "performance": scores["performance"],
                "gap": scores["gap"]
            })
        
        # 갭 순위 정렬
        gap_ranking = sorted(
            [(k, v["gap"], v["importance"], v["performance"], v["strategy"]) for k, v in all_task_items.items()],
            key=lambda x: x[1], reverse=True
        )
        
        results["tasks_21"] = {
            "items": all_task_items,
            "baselines": {"importance": round(imp_baseline, 2), "performance": round(perf_baseline, 2)},
            "quadrants": quadrants,
            "gap_ranking": [{"task": g[0], "gap": g[1], "importance": g[2], "performance": g[3], "strategy": g[4]} for g in gap_ranking]
        }
    
    # 기준선 계산 (종합)
    all_areas = results["summary"]["areas"]
    imp_values = [v["importance"] for v in all_areas.values()]
    perf_values = [v["performance"] for v in all_areas.values()]
    
    imp_baseline = np.mean(imp_values)
    perf_baseline = np.mean(perf_values)
    
    results["baselines"] = {
        "importance": round(imp_baseline, 2),
        "performance": round(perf_baseline, 2)
    }
    
    # 4분면 분류 (종합)
    quadrants = {"I. 집중개선": [], "II. 유지강화": [], "III. 저우선": [], "IV. 과잉투자": []}
    
    for area, scores in all_areas.items():
        quadrant = classify_quadrant(
            scores["importance"], 
            scores["performance"],
            imp_baseline,
            perf_baseline
        )
        quadrants[quadrant].append({
            "area": area,
            "importance": scores["importance"],
            "performance": scores["performance"],
            "gap": scores["gap"]
        })
    
    results["quadrants"] = quadrants
    
    # 갭 분석 (중요도 - 수행도 차이 큰 순)
    gap_ranking = sorted(
        [(k, v["gap"], v["importance"], v["performance"]) 
         for k, v in all_areas.items()],
        key=lambda x: x[1],
        reverse=True
    )
    results["gap_ranking"] = [
        {"area": g[0], "gap": g[1], "importance": g[2], "performance": g[3]}
        for g in gap_ranking
    ]
    
    return results


def run_ipa_analysis():
    """IPA 분석 실행 및 결과 저장"""
    print("[*] IPA Analysis Starting...")
    
    # 데이터 로딩
    print("  > Loading data...")
    datasets = load_data()
    
    # IPA 분석 실행
    print("  > Running IPA analysis...")
    results = analyze_ipa(datasets)
    
    # 결과 저장
    output_path = Path(r"d:/plan/ipa_analysis_results.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"  [OK] Analysis Complete! Results saved: {output_path}")
    
    # 결과 요약 출력
    print("\n" + "="*60)
    print("[Summary] IPA Analysis Results")
    print("="*60)
    
    print(f"\nBaselines: Importance={results['baselines']['importance']}, Performance={results['baselines']['performance']}")
    
    print("\n[Quadrant Classification]")
    for quadrant, items in results["quadrants"].items():
        print(f"\n{quadrant}:")
        for item in items:
            print(f"  * {item['area']}: I={item['importance']}, P={item['performance']}, Gap={item['gap']}")
    
    print("\n[Gap Ranking (Top 5)]:")
    for i, item in enumerate(results["gap_ranking"][:5], 1):
        print(f"  {i}. {item['area']}: Gap={item['gap']}")
    
    return results


if __name__ == "__main__":
    run_ipa_analysis()

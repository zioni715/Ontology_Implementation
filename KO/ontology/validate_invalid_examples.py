#!/usr/bin/env python3
"""Ensure intentionally invalid data triggers every essential validation family."""
from pathlib import Path
from pyshacl import validate
from rdflib import Graph, Namespace

HERE = Path(__file__).resolve().parent
SH = Namespace("http://www.w3.org/ns/shacl#")
R = Namespace("https://example.org/rcpp#")
ontology = Graph()
for name in ("schema.ttl", "classes.ttl", "properties.ttl", "code-lists.ttl"):
    ontology.parse(HERE / name, format="turtle")
data = Graph().parse(HERE / "invalid-examples.ttl", format="turtle")
shapes = Graph().parse(HERE / "shapes.ttl", format="turtle")
conforms, report_graph, report = validate(data, shacl_graph=shapes, ont_graph=ontology, inference="rdfs")
if conforms: raise SystemExit("[ERROR] invalid examples unexpectedly conform")
messages = {str(v) for v in report_graph.objects(None, SH.resultMessage)}
components = set(report_graph.objects(None, SH.sourceConstraintComponent))
expected = ("계약단가", "단위", "0 이상", "초과", "전회수량 +", "계약수량 -", "금회수량 ×", "전회금액 +", "계약금액 -", "금회수량 전달", "같은 비용항목", "집계금액", "계약수량 × 계약단가", "산출수량 전달", "출처 항목의 금회수량", "철근 강종", "호칭지름", "굵은골재 최대치수", "슬럼프", "전용횟수", "복잡도", "설치높이", "수량산정 기준", "직전 번호", "2회차 이상", "기성금액항목이 하나 이상", "집계 원천", "수량산정 기준과 이를 표현", "분류용 상위 클래스", "전회누계 원천은 최대 하나", "동일한 계약항목", "동일한 단위", "비용항목 식별코드", "비용항목명", "전회수량 또는 전회금액", "정확히 하나의 기성서류")
missing = [token for token in expected if not any(token in message for message in messages)]
if missing: raise SystemExit(f"[ERROR] undetected violation families {missing}\n{report}")
if SH.XoneConstraintComponent not in components: raise SystemExit("[ERROR] mutually exclusive cost-item subtype violation was not detected")
required_progress_paths = {R.contractQuantity, R.contractUnitPrice, R.contractAmount, R.previousQuantity, R.currentQuantity, R.cumulativeQuantity, R.remainingQuantity, R.previousAmount, R.currentAmount, R.cumulativeAmount, R.remainingAmount}
reported_paths = set(report_graph.objects(None, SH.resultPath))
if missing_paths := required_progress_paths - reported_paths:
    raise SystemExit(f"[ERROR] missing ProgressItem values were not detected: {sorted(map(str, missing_paths))}")
print(f"[OK] {len(expected)} essential SHACL violation families detected")

#!/usr/bin/env python3
"""Validate the valid four-work-category example and six competency questions."""
from pathlib import Path
from pyshacl import validate
from rdflib import Graph, Namespace

HERE = Path(__file__).resolve().parent
R = Namespace("https://example.org/rcpp#")
EX = Namespace("https://example.org/rcpp/example#")
ontology = Graph()
for name in ("schema.ttl", "classes.ttl", "properties.ttl", "code-lists.ttl"):
    ontology.parse(HERE / name, format="turtle")
data = Graph().parse(HERE / "examples.ttl", format="turtle")
shapes = Graph().parse(HERE / "shapes.ttl", format="turtle")
conforms, _, report = validate(data, shacl_graph=shapes, ont_graph=ontology, inference="rdfs")
if not conforms: raise SystemExit(report)

queries = {
"CQ01 특정 기성항목의 계약항목 대응": "ASK { ex:CT-R16 rcpp:providesContractUnitPriceToProgress ex:PR-R16 . ex:PR-R16 rcpp:representsCostItem ?c . ex:CT-R16 rcpp:representsCostItem ?c . }",
"CQ02 금회기성수량 출처와 값 전달": "ASK { ex:PQ3-R16 rcpp:providesCurrentQuantityTo ex:PR-R16 ; rcpp:currentQuantity ?q . ex:PR-R16 rcpp:currentQuantity ?q . }",
"CQ03 계약단가 출처와 값 전달": "ASK { ex:CT-R16 rcpp:providesContractUnitPriceToProgress ex:PR-R16 ; rcpp:contractUnitPrice ?price . ex:PR-R16 rcpp:contractUnitPrice ?price . }",
"CQ04 수량·금액 및 전회 이월 일관성": """ASK { ex:PR-R16 rcpp:contractQuantity ?cq; rcpp:contractAmount ?ca; rcpp:contractUnitPrice ?u; rcpp:previousQuantity ?pq; rcpp:currentQuantity ?nq; rcpp:cumulativeQuantity ?tq; rcpp:remainingQuantity ?rq; rcpp:previousAmount ?pa; rcpp:currentAmount ?na; rcpp:cumulativeAmount ?ta; rcpp:remainingAmount ?ra. ?previous rcpp:providesPreviousTotalTo ex:PR-R16; rcpp:cumulativeQuantity ?pq; rcpp:cumulativeAmount ?pa. FILTER(?pq+?nq=?tq && ?cq-?tq=?rq && ?nq*?u=?na && ?pa+?na=?ta && ?ca-?ta=?ra) }""",
"CQ05 복수 상세항목의 공종별 집계": """ASK { { SELECT ?summary (SUM(?amount) AS ?sum) WHERE { VALUES ?detail { ex:PR-R10 ex:PR-R16 } ?detail rcpp:aggregatedProgressInto ?summary ; rcpp:currentAmount ?amount . } GROUP BY ?summary } FILTER (?summary = ex:PS-R && ?sum = 15000.0) }""",
"CQ06 네 공종 전체 정보흐름": """ASK { VALUES (?q ?c ?d ?s ?pq ?p ?ps) { (ex:QB-R16 ex:CT-R16 ex:WD-R16 ex:CS-R ex:PQ3-R16 ex:PR-R16 ex:PS-R) (ex:QB-C ex:CT-C ex:WD-C ex:CS-C ex:PQ3-C ex:PR-C ex:PS-C) (ex:QB-F ex:CT-F ex:WD-F ex:CS-F ex:PQ3-F ex:PR-F ex:PS-F) (ex:QB-S ex:CT-S ex:WD-S ex:CS-S ex:PQ3-S ex:PR-S ex:PS-S) } ?q rcpp:providesCalculatedQuantityTo ?c . ?c rcpp:providesContractQuantityTo ?d; rcpp:providesContractUnitPriceTo ?d; rcpp:providesContractAmountTo ?d; rcpp:providesContractUnitPriceToProgress ?p . ?d rcpp:aggregatedContractInto ?s . ?pq rcpp:providesCurrentQuantityTo ?p . ?p rcpp:aggregatedProgressInto ?ps . }""",
"CQ07 공종별내역 세 계약값의 동일 원천": "ASK { ex:CT-R10 rcpp:providesContractQuantityTo ex:WD-R10 ; rcpp:providesContractUnitPriceTo ex:WD-R10 ; rcpp:providesContractAmountTo ex:WD-R10 . }",
"CQ08 전회누계의 정확한 직전 회차": "ASK { ex:Round2 rcpp:previousProgressRound ex:Round1 . ex:Round3 rcpp:previousProgressRound ex:Round2 . ex:PaymentDocR2 rcpp:belongsToProgressRound ex:Round2 ; rcpp:containsItem ex:PV-R10 . ex:PaymentDocR3 rcpp:belongsToProgressRound ex:Round3 ; rcpp:containsItem ex:PR-R10 . ex:PV-R10 rcpp:providesPreviousTotalTo ex:PR-R10 . }",
"CQ09 동바리 공간체적 기준과 단위 일치": "ASK { ex:Shoring rcpp:quantityBasis \"공간체적\" . ex:WD-S rcpp:representsCostItem ex:Shoring ; rcpp:usesUnit rcpp:CubicMetreSpace . }",
"CQ10 철근·콘크리트 재료와 시공 비용 분리": "ASK { ex:RebarMaterialD10 a rcpp:RebarMaterialCostItem . ex:RebarD10 a rcpp:RebarFabricationAssemblyCostItem . ex:ReadyMixedConcrete a rcpp:ReadyMixedConcreteCostItem . ex:Concrete a rcpp:ConcretePlacementCostItem . }",
"CQ11 원가근거 관계의 잠정 상태": "ASK { rcpp:providesCostBasisTo rcpp:validationStatus \"provisional\" . }",
"CQ12 재료비 두 유형의 완전한 정보흐름": """ASK { VALUES (?cost ?q ?c ?ci ?d ?cs ?pq2 ?p2 ?pq3 ?p3 ?ps) { (ex:RebarMaterialD10 ex:QB-RM10 ex:CT-RM10 ex:CI-RM10 ex:WD-RM10 ex:CS-RM ex:PQ2-RM10 ex:PV-RM10 ex:PQ3-RM10 ex:PR-RM10 ex:PS-RM) (ex:ReadyMixedConcrete ex:QB-RMC ex:CT-RMC ex:CI-RMC ex:WD-RMC ex:CS-RMC ex:PQ2-RMC ex:PV-RMC ex:PQ3-RMC ex:PR-RMC ex:PS-RMC) } ?q rcpp:representsCostItem ?cost ; rcpp:providesCalculatedQuantityTo ?c . ?ci rcpp:representsCostItem ?cost ; rcpp:providesCostBasisTo ?d . ?c rcpp:representsCostItem ?cost ; rcpp:providesContractQuantityTo ?d ; rcpp:providesContractUnitPriceTo ?d ; rcpp:providesContractAmountTo ?d ; rcpp:providesContractQuantityToProgress ?p2, ?p3 ; rcpp:providesContractUnitPriceToProgress ?p2, ?p3 ; rcpp:providesContractAmountToProgress ?p2, ?p3 . ?d rcpp:aggregatedContractInto ?cs . ?pq2 rcpp:providesCurrentQuantityTo ?p2 . ?p2 rcpp:providesPreviousTotalTo ?p3 . ?pq3 rcpp:providesCurrentQuantityTo ?p3 . ?p3 rcpp:aggregatedProgressInto ?ps . }""",
}
graph = data + ontology
for label, query in queries.items():
    if not bool(graph.query(query, initNs={"rcpp": R, "ex": EX})): raise SystemExit(f"[ERROR] {label}")
    print(f"[PASS] {label}")
print(f"[OK] SHACL conforms; {len(queries)} competency queries passed")

#!/usr/bin/env python3
"""Validate examples, domain competency questions, and technical requirements."""
from pathlib import Path
from pyshacl import validate
from rdflib import Graph, Namespace

HERE = Path(__file__).resolve().parent
R = Namespace("https://zioni715.github.io/ontology/rcpp#")
EX = Namespace("https://zioni715.github.io/ontology/rcpp/example#")
ontology = Graph()
for name in ("schema.ttl", "classes.ttl", "properties.ttl", "code-lists.ttl"):
    ontology.parse(HERE / name, format="turtle")
data = Graph().parse(HERE / "examples.ttl", format="turtle")
shapes = Graph().parse(HERE / "shapes.ttl", format="turtle")
conforms, _, report = validate(data, shacl_graph=shapes, ont_graph=ontology, inference="rdfs")
if not conforms: raise SystemExit(report)

queries = {
"CQ01 특정 기성항목의 계약항목 대응": "ASK { ex:CT-R16 rcpp:providesContractUnitPriceToProgressPaymentItem ex:PR-R16 . ex:PR-R16 rcpp:representsCostItem ?c . ex:CT-R16 rcpp:representsCostItem ?c . }",
"CQ02 특정 기성내역 행의 금회수량": "ASK { ex:PR-R16 a rcpp:ProgressPaymentItem ; rcpp:currentQuantity 10.0 . }",
"CQ03 계약단가 출처와 값 전달": "ASK { ex:CT-R16 rcpp:providesContractUnitPriceToProgressPaymentItem ex:PR-R16 ; rcpp:contractUnitPrice ?price . ex:PR-R16 rcpp:contractUnitPrice ?price . }",
"CQ04 수량·금액 및 전회 이월 일관성": """ASK { ex:PR-R16 rcpp:contractQuantity ?cq; rcpp:contractAmount ?ca; rcpp:previousCumulativeQuantity ?pq; rcpp:currentQuantity ?nq; rcpp:cumulativeQuantity ?tq; rcpp:remainingQuantity ?rq; rcpp:previousCumulativeAmount ?pa; rcpp:currentAmount ?na; rcpp:cumulativeAmount ?ta; rcpp:remainingAmount ?ra. ?previous rcpp:providesCumulativeValuesTo ex:PR-R16; rcpp:cumulativeQuantity ?pq; rcpp:cumulativeAmount ?pa. FILTER(?pq+?nq=?tq && ?cq-?tq=?rq && ?pa+?na=?ta && ?ca-?ta=?ra) }""",
"CQ05 복수 상세항목의 공종별 집계": """ASK { { SELECT ?summary (SUM(?amount) AS ?sum) WHERE { VALUES ?detail { ex:PR-R10 ex:PR-R16 } ?detail rcpp:contributesCurrentAmountTo ?summary ; rcpp:currentAmount ?amount . } GROUP BY ?summary } FILTER (?summary = ex:PS-R && ?sum = 15000.0) }""",
"CQ06 네 공종 전체 정보흐름": """ASK { VALUES (?q ?c ?d ?s ?p ?ps) { (ex:QB-R16 ex:CT-R16 ex:WD-R16 ex:CS-R ex:PR-R16 ex:PS-R) (ex:QB-C ex:CT-C ex:WD-C ex:CS-C ex:PR-C ex:PS-C) (ex:QB-F ex:CT-F ex:WD-F ex:CS-F ex:PR-F ex:PS-F) (ex:QB-S ex:CT-S ex:WD-S ex:CS-S ex:PR-S ex:PS-S) } ?q rcpp:providesCalculatedQuantityTo ?c . ?c rcpp:providesContractQuantityTo ?d; rcpp:providesContractUnitPriceTo ?d; rcpp:providesContractAmountTo ?d; rcpp:providesContractQuantityToProgressPaymentItem ?p; rcpp:providesContractUnitPriceToProgressPaymentItem ?p; rcpp:providesContractAmountToProgressPaymentItem ?p . ?d rcpp:contributesContractAmountTo ?s . ?p rcpp:currentQuantity ?currentQuantity ; rcpp:contributesCurrentAmountTo ?ps . }""",
"CQ07 비용항목의 공종·규격·단위 조회": """ASK { ex:CT-R16 rcpp:representsCostItem ex:RebarD16 ; rcpp:usesUnit rcpp:Tonne . ex:RebarD16 rcpp:belongsToWorkCategory rcpp:RebarWork ; rcpp:specification "SD400 D16 현장 가공·조립" . }""",
"CQ08 산출수량 합계와 계약수량 확인": """ASK { ex:CT-R16 rcpp:contractQuantity ?contractQuantity . { SELECT (SUM(?quantity) AS ?calculatedTotal) WHERE { ?item rcpp:providesCalculatedQuantityTo ex:CT-R16 ; rcpp:calculatedQuantity ?quantity . } } FILTER (?contractQuantity = ?calculatedTotal && ?calculatedTotal = 100.0) }""",
"CQ09 원가 구성과 산출단가 조회": """ASK { ex:CI-R16 rcpp:materialUnitCost 600.0 ; rcpp:laborUnitCost 300.0 ; rcpp:expenseUnitCost 100.0 ; rcpp:calculatedUnitPrice 1000.0 . }""",
"CQ10 전회누계의 이전 회차 출처 조회": """ASK { ex:PV-R16 rcpp:providesCumulativeValuesTo ex:PR-R16 ; rcpp:cumulativeQuantity 20.0 ; rcpp:cumulativeAmount 20000.0 . ex:PaymentDocR2 rcpp:belongsToProgressRound ex:Round2 ; rcpp:containsItem ex:PV-R16 . ex:PaymentDocR3 rcpp:belongsToProgressRound ex:Round3 ; rcpp:containsItem ex:PR-R16 . ex:Round3 rcpp:previousProgressRound ex:Round2 . }""",
"CQ11 계약·누계·잔여수량 조회": """ASK { ex:PR-R16 rcpp:contractQuantity 100.0 ; rcpp:previousCumulativeQuantity 20.0 ; rcpp:currentQuantity 10.0 ; rcpp:cumulativeQuantity 30.0 ; rcpp:remainingQuantity 70.0 . }""",
"CQ12 계약·누계·잔여금액 조회": """ASK { ex:PR-R16 rcpp:contractAmount 100000.0 ; rcpp:previousCumulativeAmount 20000.0 ; rcpp:currentAmount 10000.0 ; rcpp:cumulativeAmount 30000.0 ; rcpp:remainingAmount 70000.0 . }""",
"CQ13 문서별 포함 항목 유형 조회": """ASK { ex:QuantityDoc rcpp:containsItem [ a rcpp:CalculatedQuantityItem ] . ex:ContractDoc rcpp:containsItem [ a rcpp:ContractItem ] . ex:CostDoc rcpp:containsItem [ a rcpp:CostCalculationItem ] . ex:DetailDoc rcpp:containsItem [ a rcpp:WorkCategoryDetailItem ] . ex:ContractSummaryDoc rcpp:containsItem [ a rcpp:ContractSummaryItem ] . ex:PaymentDocR3 rcpp:containsItem [ a rcpp:ProgressPaymentItem ] . }""",
"CQ14 재료비와 시공비 유형 구분": """ASK { ex:RebarMaterialD10 a rcpp:RebarMaterialCostItem . ex:RebarD16 a rcpp:RebarFabricationAssemblyCostItem . ex:ReadyMixedConcrete a rcpp:ReadyMixedConcreteMaterialCostItem . ex:Concrete a rcpp:ConcretePlacementCostItem . }""",
"CQ15 회차·공종별 금회기성금액 합계": """ASK { { SELECT (SUM(?amount) AS ?total) WHERE { ex:PaymentDocR3 rcpp:containsItem ?item . ?item a rcpp:ProgressPaymentItem ; rcpp:representsCostItem ?cost ; rcpp:currentAmount ?amount . ?cost rcpp:belongsToWorkCategory rcpp:RebarWork . } } FILTER (?total = 16600.0) }""",
"CQ16 동바리 산정기준과 단위 조회": """ASK { ex:Shoring rcpp:quantityBasis "공간체적" . ex:PR-S rcpp:representsCostItem ex:Shoring ; rcpp:usesUnit rcpp:CubicMetreSpace . }""",
"CQ17 기성문서의 회차 조회": """ASK { ex:PaymentDocR3 a rcpp:ProgressPaymentStatement ; rcpp:belongsToProgressRound ex:Round3 . ex:Round3 rcpp:roundNumber 3 . }""",
"CQ18 항목이 속한 문서 조회": """ASK { ex:ContractDoc a rcpp:ContractStatement ; rcpp:containsItem ex:CT-R16 . ex:CT-R16 a rcpp:ContractItem . }""",
"CQ19 계약값의 공종별내역 전달 확인": """ASK { ex:CT-R16 rcpp:contractQuantity ?q ; rcpp:contractUnitPrice ?u ; rcpp:contractAmount ?a ; rcpp:providesContractQuantityTo ex:WD-R16 ; rcpp:providesContractUnitPriceTo ex:WD-R16 ; rcpp:providesContractAmountTo ex:WD-R16 . ex:WD-R16 rcpp:contractQuantity ?q ; rcpp:contractUnitPrice ?u ; rcpp:contractAmount ?a . }""",
"CQ20 공통 비용항목 기반 문서 간 추적": """ASK { ex:QB-RM10 rcpp:representsCostItem ex:RebarMaterialD10 ; rcpp:providesCalculatedQuantityTo ex:CT-RM10 . ex:CT-RM10 rcpp:representsCostItem ex:RebarMaterialD10 ; rcpp:providesContractQuantityTo ex:WD-RM10 ; rcpp:providesContractUnitPriceToProgressPaymentItem ex:PR-RM10 . ex:CI-RM10 rcpp:representsCostItem ex:RebarMaterialD10 . ex:WD-RM10 rcpp:representsCostItem ex:RebarMaterialD10 . ex:PR-RM10 rcpp:representsCostItem ex:RebarMaterialD10 . }""",
}
validation_tests = {
"VT01 공종별내역 세 계약값의 동일 원천": "ASK { ex:CT-R10 rcpp:providesContractQuantityTo ex:WD-R10 ; rcpp:providesContractUnitPriceTo ex:WD-R10 ; rcpp:providesContractAmountTo ex:WD-R10 . }",
"VT02 전회누계의 정확한 직전 회차": "ASK { ex:Round2 rcpp:previousProgressRound ex:Round1 . ex:Round3 rcpp:previousProgressRound ex:Round2 . ex:PaymentDocR2 rcpp:belongsToProgressRound ex:Round2 ; rcpp:containsItem ex:PV-R10 . ex:PaymentDocR3 rcpp:belongsToProgressRound ex:Round3 ; rcpp:containsItem ex:PR-R10 . ex:PV-R10 rcpp:providesCumulativeValuesTo ex:PR-R10 . }",
"VT03 동바리 공간체적 기준과 단위 일치": "ASK { ex:Shoring rcpp:quantityBasis \"공간체적\" . ex:WD-S rcpp:representsCostItem ex:Shoring ; rcpp:usesUnit rcpp:CubicMetreSpace . }",
"VT04 철근·콘크리트 재료와 시공 비용 분리": "ASK { ex:RebarMaterialD10 a rcpp:RebarMaterialCostItem . ex:RebarD10 a rcpp:RebarFabricationAssemblyCostItem . ex:ReadyMixedConcrete a rcpp:ReadyMixedConcreteMaterialCostItem . ex:Concrete a rcpp:ConcretePlacementCostItem . }",
"VT05 공통 비용항목 기반 문서 간 추적": """ASK { VALUES (?cost ?q ?c ?ci ?d ?cs ?p2 ?p3 ?ps) { (ex:RebarMaterialD10 ex:QB-RM10 ex:CT-RM10 ex:CI-RM10 ex:WD-RM10 ex:CS-RM ex:PV-RM10 ex:PR-RM10 ex:PS-RM) (ex:ReadyMixedConcrete ex:QB-RMC ex:CT-RMC ex:CI-RMC ex:WD-RMC ex:CS-RMC ex:PV-RMC ex:PR-RMC ex:PS-RMC) } ?q rcpp:representsCostItem ?cost ; rcpp:providesCalculatedQuantityTo ?c . ?c rcpp:representsCostItem ?cost ; rcpp:providesContractQuantityTo ?d ; rcpp:providesContractUnitPriceTo ?d ; rcpp:providesContractAmountTo ?d ; rcpp:providesContractQuantityToProgressPaymentItem ?p2, ?p3 ; rcpp:providesContractUnitPriceToProgressPaymentItem ?p2, ?p3 ; rcpp:providesContractAmountToProgressPaymentItem ?p2, ?p3 . ?ci rcpp:representsCostItem ?cost . ?d rcpp:representsCostItem ?cost ; rcpp:contributesContractAmountTo ?cs . ?p2 rcpp:representsCostItem ?cost ; rcpp:currentQuantity ?q2 ; rcpp:providesCumulativeValuesTo ?p3 . ?p3 rcpp:representsCostItem ?cost ; rcpp:currentQuantity ?q3 ; rcpp:contributesCurrentAmountTo ?ps . }""",
}
graph = data + ontology
for label, query in queries.items():
    if not bool(graph.query(query, initNs={"rcpp": R, "ex": EX})): raise SystemExit(f"[ERROR] {label}")
    print(f"[PASS] {label}")
for label, query in validation_tests.items():
    if not bool(graph.query(query, initNs={"rcpp": R, "ex": EX})): raise SystemExit(f"[ERROR] {label}")
    print(f"[PASS] {label}")
print(f"[OK] SHACL conforms; {len(queries)} core competency questions and {len(validation_tests)} validation tests passed")

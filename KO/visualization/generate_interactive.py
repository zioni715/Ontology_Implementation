"""Build a self-contained, interactive HTML explorer for the RCPP ontology."""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

from rdflib import DCTERMS, RDF, RDFS, Graph, Namespace, URIRef


ROOT = Path(__file__).resolve().parents[1]
ONTOLOGY_FILES = tuple(
    ROOT / "RDFS" / name
    for name in ("schema.ttl", "classes.ttl", "properties.ttl", "code-lists.ttl")
)
OUTPUT_FILE = Path(__file__).resolve().parent / "interactive.html"
EXAMPLES_FILE = ROOT / "RDFS" / "examples.ttl"
XSD = "http://www.w3.org/2001/XMLSchema#"
RCPP = Namespace("https://zioni715.github.io/ontology/rcpp#")
EX = Namespace("https://zioni715.github.io/ontology/rcpp/example#")


def local_name(value: object) -> str:
    text = str(value)
    return text.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def korean_text(graph: Graph, subject: URIRef, predicate: URIRef) -> str:
    values = list(graph.objects(subject, predicate))
    preferred = next((value for value in values if value.language == "ko"), None)
    return str(preferred or (values[0] if values else ""))


def load_graph() -> Graph:
    graph = Graph()
    for path in ONTOLOGY_FILES:
        if not path.is_file():
            raise FileNotFoundError(path)
        graph.parse(path, format="turtle")
    return graph


def build_data(graph: Graph) -> dict[str, object]:
    hidden_class_ids = {
        "WorkCategory",
        "RebarMaterialCostItem",
        "RebarFabricationAssemblyCostItem",
        "ReadyMixedConcreteMaterialCostItem",
        "ConcretePlacementCostItem",
    }
    all_class_uris = sorted(set(graph.subjects(RDF.type, RDFS.Class)), key=str)
    class_uris = [uri for uri in all_class_uris if local_name(uri) not in hidden_class_ids]
    class_set = set(class_uris)
    rolled_up_attribute_domains = {
        RCPP.RebarCostItem: (
            RCPP.RebarCostItem,
            RCPP.RebarMaterialCostItem,
            RCPP.RebarFabricationAssemblyCostItem,
        ),
        RCPP.ConcreteCostItem: (
            RCPP.ConcreteCostItem,
            RCPP.ReadyMixedConcreteMaterialCostItem,
            RCPP.ConcretePlacementCostItem,
        ),
    }
    nodes = []
    for uri in class_uris:
        parents = [parent for parent in graph.objects(uri, RDFS.subClassOf) if parent in class_set]
        attributes = []
        seen_attributes = set()
        for defined_on in rolled_up_attribute_domains.get(uri, (uri,)):
            for prop in graph.subjects(RDFS.domain, defined_on):
                ranges = list(graph.objects(prop, RDFS.range))
                if ranges and all(str(value).startswith(XSD) for value in ranges) and prop not in seen_attributes:
                    seen_attributes.add(prop)
                    attributes.append({
                        "id": local_name(prop),
                        "label": korean_text(graph, prop, RDFS.label) or local_name(prop),
                        "type": local_name(ranges[0]),
                        "definedOn": local_name(defined_on),
                    })
        nodes.append({
            "id": local_name(uri),
            "uri": str(uri),
            "label": korean_text(graph, uri, RDFS.label) or local_name(uri),
            "comment": korean_text(graph, uri, RDFS.comment),
            "parents": [local_name(parent) for parent in parents],
            "attributes": sorted(attributes, key=lambda item: item["label"]),
            "nodeType": "class",
        })

    category_uris = sorted(set(graph.subjects(RDF.type, RCPP.WorkCategory)), key=str)
    for uri in category_uris:
        nodes.append({
            "id": local_name(uri), "uri": str(uri),
            "label": korean_text(graph, uri, RDFS.label) or local_name(uri),
            "comment": korean_text(graph, uri, RDFS.comment),
            "parents": [], "attributes": [], "nodeType": "category",
        })

    edges = []
    for child in class_uris:
        for parent in graph.objects(child, RDFS.subClassOf):
            if parent in class_set:
                edges.append({
                    "source": local_name(child), "target": local_name(parent),
                    "label": "상위 클래스", "property": "rdfs:subClassOf", "kind": "inheritance",
                })
    for prop in sorted(set(graph.subjects(RDF.type, RDF.Property)), key=str):
        domains = [value for value in graph.objects(prop, RDFS.domain) if value in class_set]
        ranges = [value for value in graph.objects(prop, RDFS.range) if value in class_set]
        for domain in domains:
            for range_ in ranges:
                # A same-class domain/range describes relations between distinct
                # instances; drawing it on the class node creates a false self-loop.
                if domain == range_:
                    continue
                property_name = local_name(prop)
                # The concrete subproperties carry the visible semantics; do
                # not draw their summary superproperty at the same time.
                if property_name == "providesContractValueTo":
                    continue
                if property_name in {
                    "providesCalculatedQuantityTo", "providesContractQuantityTo",
                    "providesContractUnitPriceTo", "providesContractAmountTo",
                    "providesContractUnitPriceToProgressPaymentItem", "providesContractQuantityToProgressPaymentItem",
                    "providesContractAmountToProgressPaymentItem", "providesCumulativeValuesTo",
                    "contributesContractAmountTo", "contributesCurrentAmountTo",
                }:
                    kind = "flow"
                elif property_name == "containsItem":
                    kind = "containment"
                elif property_name == "representsCostItem":
                    kind = "usage"
                elif property_name == "usesUnit":
                    kind = "reference"
                else:
                    kind = "relation"
                edges.append({
                    "source": local_name(domain), "target": local_name(range_),
                    "label": ("서류항목이 비용대상으로 참조" if property_name == "representsCostItem"
                              else korean_text(graph, prop, RDFS.label) or local_name(prop)),
                    "property": property_name, "kind": kind,
                })
    for child in category_uris:
        for parent in graph.objects(child, RCPP.subWorkCategoryOf):
            if parent in category_uris:
                edges.append({
                    "source": local_name(child), "target": local_name(parent),
                    "label": "상위 공종", "property": "subWorkCategoryOf", "kind": "taxonomy",
                })

    # CostItemShape permits exactly one of the four controlled work categories.
    # Show the sh:in constraint separately from the stronger sh:hasValue rules
    # attached to each concrete cost-item family.
    for work_category in ("RebarWork", "ConcreteWork", "FormworkWork", "ShoringWork"):
        edges.append({
            "source": "CostItem", "target": work_category,
            "label": "허용 공종",
            "property": "belongsToWorkCategory · sh:in",
            "kind": "shacl",
        })

    # SHACL fixes each cost-item family to its corresponding work category.
    for cost_class, work_category in (
        ("RebarCostItem", "RebarWork"),
        ("ConcreteCostItem", "ConcreteWork"),
        ("FormworkCostItem", "FormworkWork"),
        ("ShoringCostItem", "ShoringWork"),
    ):
        edges.append({
            "source": cost_class, "target": work_category,
            "label": "공종 분류 제약",
            "property": "belongsToWorkCategory · sh:hasValue",
            "kind": "shacl",
        })

    # Document-specific item membership is defined by SHACL in this compact
    # model. Surface those constraints explicitly instead of pretending the
    # generic containsItem domain/range identifies each document's item type.
    document_item_constraints = (
        ("QuantityCalculationSheet", "CalculatedQuantityItem"),
        ("ContractStatement", "ContractItem"),
        ("CostCalculationStatement", "CostCalculationItem"),
        ("WorkCategoryDetailStatement", "WorkCategoryDetailItem"),
        ("WorkCategorySummaryStatement", "ContractSummaryItem"),
        ("ProgressPaymentStatement", "ProgressPaymentItem"),
        ("ProgressPaymentStatement", "ProgressPaymentSummaryItem"),
    )
    for document, item in document_item_constraints:
        edges.append({
            "source": document, "target": item, "label": "허용 항목",
            "property": "sh:class/containsItem", "kind": "constraint",
        })

    examples = Graph().parse(EXAMPLES_FILE, format="turtle")
    lineage_ids = (
        "QuantityDoc", "ContractDoc", "CostDoc", "DetailDoc",
        "ContractSummaryDoc", "PaymentDocR2", "PaymentDocR3",
        "QB-R10", "CT-R10", "CI-R10", "WD-R10", "CS-R",
        "PV-R10", "PR-R10", "PS-R",
    )
    lineage_uris = {EX[value] for value in lineage_ids}
    for uri in sorted(lineage_uris, key=str):
        types = sorted(examples.objects(uri, RDF.type), key=str)
        label = korean_text(examples, uri, RDFS.label)
        label = label or str(next(examples.objects(uri, RCPP.itemName), ""))
        label = label or str(next(examples.objects(uri, RCPP.documentIdentifier), ""))
        attributes = []
        for predicate, value in sorted(examples.predicate_objects(uri), key=lambda pair: (str(pair[0]), str(pair[1]))):
            if predicate == RDF.type or isinstance(value, URIRef):
                continue
            attributes.append({
                "id": local_name(predicate),
                "label": korean_text(graph, predicate, RDFS.label) or local_name(predicate),
                "type": str(value),
            })
        type_names = [korean_text(graph, value, RDFS.label) or local_name(value) for value in types]
        nodes.append({
            "id": local_name(uri), "uri": str(uri), "label": label or local_name(uri),
            "comment": f"실제 예제 계보 개체 · 유형: {', '.join(type_names)}",
            "parents": [], "attributes": attributes, "nodeType": "instance",
        })

    lineage_properties = {
        RCPP.containsItem: ("constraint", "문서 포함"),
        RCPP.providesCalculatedQuantityTo: ("flow", "산출수량 → 계약수량 · 50 t"),
        RCPP.providesContractQuantityTo: ("flow", "계약수량 → 공종별내역 계약수량 · 50 t"),
        RCPP.providesContractUnitPriceTo: ("flow", "계약단가 → 공종별내역 계약단가 · 1,000"),
        RCPP.providesContractAmountTo: ("flow", "계약금액 → 공종별내역 계약금액 · 50,000"),
        RCPP.providesContractQuantityToProgressPaymentItem: ("flow", "계약수량 → 기성내역 계약수량 · 50 t"),
        RCPP.providesContractUnitPriceToProgressPaymentItem: ("flow", "계약단가 → 기성내역 계약단가 · 1,000"),
        RCPP.providesContractAmountToProgressPaymentItem: ("flow", "계약금액 → 기성내역 계약금액 · 50,000"),
        RCPP.providesCumulativeValuesTo: ("rollover", "이전 누계 → 현재 전회값 · 10 t / 10,000"),
        RCPP.contributesContractAmountTo: ("aggregate", "계약금액 → 공종별 계약집계 · 50,000"),
        RCPP.contributesCurrentAmountTo: ("aggregate", "금회금액 → 공종별 기성집계 · 5,000"),
    }
    for prop, (kind, label) in lineage_properties.items():
        for source, target in sorted(examples.subject_objects(prop), key=lambda pair: (str(pair[0]), str(pair[1]))):
            if source in lineage_uris and target in lineage_uris:
                edges.append({
                    "source": local_name(source), "target": local_name(target),
                    "label": label, "property": local_name(prop), "kind": kind,
                })
    schema = next(graph.subjects(DCTERMS.hasVersion, None), None)
    version = str(next(graph.objects(schema, DCTERMS.hasVersion), "")) if schema else ""
    return {"nodes": nodes, "edges": edges, "version": version}


def render(data: dict[str, object]) -> str:
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    template = r'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>RCPP 온톨로지 탐색기</title>
<style>
:root{--ink:#172033;--muted:#64748b;--panel:#fff;--bg:#f3f6fb;--navy:#193a66;--blue:#3478c7;--orange:#de7c2f;--line:#cbd5e1}
*{box-sizing:border-box}body{margin:0;font-family:Inter,Pretendard,"Noto Sans KR",system-ui,sans-serif;color:var(--ink);background:var(--bg);overflow:hidden}
header{height:70px;padding:13px 22px;background:#102a4c;color:white;display:flex;align-items:center;gap:24px;box-shadow:0 2px 12px #0f172a33;position:relative;z-index:2}
.brand{min-width:250px}.brand h1{font-size:19px;margin:0 0 3px}.brand small{color:#b9cbe1}.search{flex:1;max-width:520px;position:relative}.search input{width:100%;border:1px solid #ffffff33;border-radius:10px;background:#ffffff15;color:white;padding:11px 40px 11px 14px;font-size:14px;outline:none}.search input::placeholder{color:#c6d4e5}.search span{position:absolute;right:13px;top:10px}.stats{margin-left:auto;font-size:12px;color:#cad8e8;white-space:nowrap}
.app{height:calc(100vh - 70px);display:grid;grid-template-columns:230px 1fr 300px}.sidebar,.detail{background:var(--panel);padding:19px;border-color:#dbe3ee;overflow:auto}.sidebar{border-right:1px solid #dbe3ee}.detail{border-left:1px solid #dbe3ee}.section{margin-bottom:24px}.section h2,.detail h2{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 0 12px}.check{display:flex;align-items:center;gap:9px;font-size:13px;margin:10px 0;cursor:pointer}.check input{accent-color:var(--blue)}.swatch{width:18px;height:3px;border-radius:2px}.classes{display:flex;flex-direction:column;gap:4px}.class-btn{border:0;background:transparent;text-align:left;padding:7px 9px;border-radius:7px;color:#334155;cursor:pointer}.class-btn:hover,.class-btn.active{background:#e8f1fb;color:#174f8d}.reset{width:100%;padding:9px;border:1px solid #cbd5e1;background:white;border-radius:8px;cursor:pointer;color:#334155}
.stage{position:relative;overflow:hidden;background-color:#f8fafc;background-image:radial-gradient(#b8c5d6 1px,transparent 1px);background-size:24px 24px}.hint{position:absolute;left:15px;bottom:14px;background:#ffffffdd;border:1px solid #dbe3ee;border-radius:8px;padding:8px 11px;font-size:11px;color:var(--muted);pointer-events:none}.zoom{position:absolute;right:14px;top:14px;display:flex;flex-direction:column;gap:6px}.zoom button{width:36px;height:36px;border:1px solid #d5deea;background:white;border-radius:8px;font-size:18px;cursor:pointer;box-shadow:0 2px 6px #0f172a12}svg{width:100%;height:100%;display:block}.area-title{font-size:15px;font-weight:750;fill:#64748b;letter-spacing:.06em}.area-rule{stroke:#dbe3ee;stroke-width:1}.edge{fill:none;stroke-width:1.7;opacity:.72}.edge.inheritance{stroke:var(--orange);stroke-dasharray:6 4}.edge.flow{stroke:var(--blue)}.edge.usage{stroke:#6d4bb8;stroke-width:2.7;opacity:.9}.edge.relation{stroke:#64748b}.edge.containment{stroke:#7b8794}.edge.reference{stroke:#7b8794;stroke-dasharray:3 4}.edge.shacl{stroke:#8b5e3c;stroke-dasharray:2 5}.edge.typing{stroke:#7b8794;stroke-dasharray:2 5}.edge.taxonomy{stroke:#2f855a;stroke-dasharray:7 4}.edge.dim,.node.dim{opacity:.08}.edge-label{font-size:10px;fill:#475569;paint-order:stroke;stroke:#f8fafc;stroke-width:4;stroke-linejoin:round;pointer-events:none}.node{cursor:pointer}.node.hidden{display:none}.node rect{fill:white;stroke:#9cb1c9;stroke-width:1.4;rx:10;filter:url(#shadow)}.node.category rect{fill:#edf9f2;stroke:#55a377;rx:25}.node.category .id{fill:#3b7b57}.node:hover rect,.node.selected rect{stroke:#1769aa;stroke-width:2.5;fill:#f0f7ff}.node text{font-size:12px;font-weight:700;fill:#20324a;text-anchor:middle;pointer-events:none}.node .id{font-size:9px;font-weight:400;fill:#7b8ba2}.node.match rect{fill:#fff4ce;stroke:#d89b13}.views{display:grid;gap:6px}.view-btn{padding:9px 10px;border:1px solid #d5deea;background:#fff;border-radius:8px;text-align:left;cursor:pointer;color:#405169}.view-btn:hover,.view-btn.active{border-color:#4d89c7;background:#eaf3fc;color:#174f8d;font-weight:700}.node-legend{display:flex;align-items:center;gap:8px;font-size:12px;margin:8px 0}.legend-shape{width:24px;height:16px;border:1.5px solid #9cb1c9;background:#fff;border-radius:4px}.legend-shape.category{border-color:#55a377;background:#edf9f2;border-radius:12px}
.edge.constraint{stroke:#64748b;stroke-dasharray:6 3}.edge.rollover{stroke:#c05621;stroke-width:2.2}.edge.aggregate{stroke:#805ad5;stroke-width:2}.node.instance rect{fill:#eef6ff;stroke:#3478c7;rx:6}.node.instance .id{fill:#24639f}.legend-shape.instance{border-color:#3478c7;background:#eef6ff;border-radius:2px}.empty{color:#718096;font-size:13px;line-height:1.7;margin-top:25px}.detail-title{font-size:21px;font-weight:750;margin:7px 0 3px}.detail-id{font-family:ui-monospace,monospace;font-size:11px;color:#64748b;overflow-wrap:anywhere}.comment{font-size:13px;line-height:1.65;color:#475569;margin:18px 0;padding:12px;background:#f6f8fb;border-radius:8px}.tag{display:inline-block;padding:4px 7px;background:#e7f0fa;color:#215b91;border-radius:5px;font-size:11px;margin:3px 3px 3px 0}.list{margin:8px 0 20px;padding:0;list-style:none}.list li{font-size:12px;padding:8px 0;border-bottom:1px solid #edf1f5}.list b{display:block;margin-bottom:3px}.list small{color:#718096}.uri{font-size:10px;color:#7c8a9d;overflow-wrap:anywhere;margin-top:20px}
@media(max-width:900px){.app{grid-template-columns:180px 1fr}.detail{position:absolute;right:0;top:70px;bottom:0;width:290px;box-shadow:-4px 0 20px #0f172a20}.stats{display:none}}@media(max-width:650px){.sidebar{display:none}.app{grid-template-columns:1fr}.brand{min-width:auto}.brand small{display:none}}
</style></head><body>
<header><div class="brand"><h1>RCPP 온톨로지 탐색기</h1><small>철근콘크리트공종 기성금액 산정</small></div><div class="search"><input id="search" placeholder="클래스명, 설명, 영문 ID 검색" aria-label="검색"><span>⌕</span></div><div class="stats" id="stats"></div></header>
<main class="app"><aside class="sidebar"><section class="section"><h2>탐색 관점</h2><div class="views"><button class="view-btn active" data-view="domain">Domain–Range 구조</button><button class="view-btn" data-view="classes">클래스 구조</button><button class="view-btn" data-view="works">공종 코드 구조</button><button class="view-btn" data-view="all">전체 RDF/RDFS</button></div></section><section class="section"><h2>노드 범례</h2><div class="node-legend"><i class="legend-shape"></i>RDFS 클래스</div><div class="node-legend"><i class="legend-shape category"></i>WorkCategory 개체</div></section><section class="section"><h2>관계 표시</h2><label class="check"><input id="showRelations" type="checkbox" checked><i class="swatch" style="background:#3478c7"></i>온톨로지 관계</label><label class="check"><input id="showInheritance" type="checkbox" checked><i class="swatch" style="background:#de7c2f"></i>클래스·공종 계층</label><div class="node-legend"><i class="swatch" style="background:#6d4bb8"></i>비용항목 참조</div><div class="node-legend"><i class="swatch" style="background:#3478c7"></i>속성값 전달</div><div class="node-legend"><i class="swatch" style="background:#c05621"></i>전회누계 이월</div><div class="node-legend"><i class="swatch" style="background:#805ad5"></i>금액 집계</div><div class="node-legend"><i class="swatch" style="background:#8b5e3c"></i>SHACL 공종 분류 제약</div></section><section class="section"><h2>노드 목록</h2><div class="classes" id="classList"></div></section><button class="reset" id="reset">현재 관점 초기화</button></aside>
<section class="stage" id="stage"><svg id="graph" role="img" aria-label="온톨로지 관계 그래프"><defs><filter id="shadow" x="-20%" y="-30%" width="140%" height="170%"><feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity=".13"/></filter><marker id="arrowRelation" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#3478c7"/></marker><marker id="arrowInheritance" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0,0 L8,4.5 L0,9 z" fill="#de7c2f"/></marker><marker id="arrowTyping" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0,0 L8,4.5 L0,9 z" fill="#7b8794"/></marker><marker id="arrowTaxonomy" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0,0 L8,4.5 L0,9 z" fill="#2f855a"/></marker><marker id="arrowClassification" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0,0 L8,4.5 L0,9 z" fill="#805ad5"/></marker></defs><g id="viewport"><g id="areas"><text class="area-title" x="80" y="45">서류 구조</text><line class="area-rule" x1="80" y1="58" x2="540" y2="58"/><text class="area-title" x="620" y="45">정보 흐름</text><line class="area-rule" x1="620" y1="58" x2="1010" y2="58"/><text class="area-title" x="1090" y="45">공종·비용 분류</text><line class="area-rule" x1="1090" y1="58" x2="1620" y2="58"/></g><g id="edges"></g><g id="labels"></g><g id="nodes"></g></g></svg><div class="zoom"><button id="zin" title="확대">+</button><button id="zout" title="축소">−</button><button id="fit" title="화면 맞춤">⌂</button></div><div class="hint">휠: 확대·축소 · 빈 공간 드래그: 이동 · 노드 드래그: 배치</div></section>
<aside class="detail" id="detail"><h2>선택 정보</h2><div class="empty">그래프 또는 왼쪽 목록에서 클래스를 선택하면 설명, 속성, 연결 관계를 볼 수 있습니다.</div></aside></main>
<script id="ontology-data" type="application/json">__DATA__</script><script>
const data=JSON.parse(document.getElementById('ontology-data').textContent), NS='http://www.w3.org/2000/svg';
const byId=new Map(data.nodes.map(n=>[n.id,n])); let selected=null, transform={x:0,y:0,k:1}, dragging=null, moved=false,currentView='domain';
const svg=document.getElementById('graph'), viewport=document.getElementById('viewport'), stage=document.getElementById('stage');
const W=1700,H=1000; svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
const views={
lineage:{ids:['QuantityDoc','ContractDoc','CostDoc','DetailDoc','ContractSummaryDoc','PaymentDocR2','PaymentDocR3','QB-R10','CT-R10','CI-R10','WD-R10','CS-R','PV-R10','PR-R10','PS-R'],pos:{QuantityDoc:[100,90],'QB-R10':[100,260],ContractDoc:[370,90],'CT-R10':[370,260],CostDoc:[370,650],'CI-R10':[370,500],DetailDoc:[700,90],'WD-R10':[700,260],ContractSummaryDoc:[1010,90],'CS-R':[1010,260],PaymentDocR2:[1040,500],'PV-R10':[1160,650],PaymentDocR3:[1380,500],'PR-R10':[1450,700],'PS-R':[1580,820]}},
domain:{ids:['CalculatedQuantityItem','ContractItem','CostCalculationItem','WorkCategoryDetailItem','ContractSummaryItem','ProgressPaymentItem','ProgressPaymentSummaryItem'],pos:{CalculatedQuantityItem:[140,250],ContractItem:[430,250],CostCalculationItem:[430,650],WorkCategoryDetailItem:[760,400],ContractSummaryItem:[1080,650],ProgressPaymentItem:[1120,250],ProgressPaymentSummaryItem:[1430,250]}},
documents:{ids:['QuantityCalculationSheet','CalculatedQuantityItem','ContractStatement','ContractItem','CostCalculationStatement','CostCalculationItem','WorkCategoryDetailStatement','WorkCategoryDetailItem','WorkCategorySummaryStatement','ContractSummaryItem','ProgressPaymentStatement','ProgressPaymentItem','ProgressPaymentSummaryItem'],pos:{QuantityCalculationSheet:[120,120],CalculatedQuantityItem:[120,330],ContractStatement:[390,120],ContractItem:[390,330],CostCalculationStatement:[650,120],CostCalculationItem:[650,330],WorkCategoryDetailStatement:[910,120],WorkCategoryDetailItem:[910,330],WorkCategorySummaryStatement:[1170,120],ContractSummaryItem:[1170,330],ProgressPaymentStatement:[1370,600],ProgressPaymentItem:[1370,820],ProgressPaymentSummaryItem:[1600,820]}},
classes:{ids:data.nodes.filter(n=>n.nodeType==='class').map(n=>n.id),pos:{ProgressDocument:[150,160],OutputDocument:[380,100],EvidenceDocument:[380,280],ProgressPaymentStatement:[650,100],ContractStatement:[650,200],CostCalculationStatement:[650,280],WorkCategorySummaryStatement:[650,360],WorkCategoryDetailStatement:[650,440],QuantityCalculationSheet:[650,520],DocumentItem:[850,160],DetailItem:[1080,140],SummaryItem:[1080,400],CalculatedQuantityItem:[1320,70],ContractItem:[1320,140],CostCalculationItem:[1320,210],WorkCategoryDetailItem:[1320,280],ProgressPaymentItem:[1320,420],ContractSummaryItem:[1320,520],ProgressPaymentSummaryItem:[1320,610],CostItem:[850,720],RebarCostItem:[1120,680],ConcreteCostItem:[1120,760],FormworkCostItem:[1390,680],ShoringCostItem:[1390,760],ProgressPaymentRound:[150,650],Unit:[380,760]}},
works:{ids:['ReinforcedConcreteWork','RebarWork','ConcreteWork','FormworkWork','ShoringWork'],pos:{ReinforcedConcreteWork:[700,180],RebarWork:[300,520],ConcreteWork:[570,520],FormworkWork:[840,520],ShoringWork:[1110,520]}},
all:{ids:data.nodes.filter(n=>n.nodeType!=='instance').map(n=>n.id),pos:{ProgressDocument:[100,350],OutputDocument:[300,220],EvidenceDocument:[300,500],ProgressPaymentRound:[500,100],ProgressPaymentStatement:[500,220],ContractStatement:[500,390],CostCalculationStatement:[500,470],WorkCategorySummaryStatement:[500,550],WorkCategoryDetailStatement:[500,630],QuantityCalculationSheet:[500,710],DocumentItem:[700,100],DetailItem:[700,240],CalculatedQuantityItem:[900,100],ContractItem:[900,210],CostCalculationItem:[900,320],WorkCategoryDetailItem:[900,430],ProgressPaymentItem:[900,650],SummaryItem:[700,790],ContractSummaryItem:[900,770],ProgressPaymentSummaryItem:[900,870],ReinforcedConcreteWork:[1260,100],RebarWork:[1210,250],ConcreteWork:[1210,390],FormworkWork:[1210,530],ShoringWork:[1210,670],CostItem:[1500,100],RebarCostItem:[1500,250],ConcreteCostItem:[1500,390],FormworkCostItem:[1500,530],ShoringCostItem:[1500,670],Unit:[1080,820]}}
};
data.nodes.forEach((n,i)=>{n.x=100+(i%6)*210;n.y=100+Math.floor(i/6)*150});
function el(tag,attrs={}){const e=document.createElementNS(NS,tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));return e}
const pairTotals=new Map;data.edges.forEach(e=>{const k=`${e.source}|${e.target}`;pairTotals.set(k,(pairTotals.get(k)||0)+1)});const pairSeen=new Map;
const edgeEls=data.edges.map((e,i)=>{const markers={flow:'Relation',rollover:'Inheritance',aggregate:'Classification',usage:'Classification',relation:'Typing',containment:'Typing',reference:'Typing',shacl:'Typing',typing:'Typing',inheritance:'Inheritance',taxonomy:'Taxonomy'},marker=markers[e.kind],key=`${e.source}|${e.target}`,seen=pairSeen.get(key)||0,total=pairTotals.get(key),offset=(seen-(total-1)/2)*22;pairSeen.set(key,seen+1);const line=el('path',{class:`edge ${e.kind}`,'marker-end':e.kind==='constraint'?'none':`url(#arrow${marker})`});document.getElementById('edges').append(line);const label=el('text',{class:'edge-label'});label.textContent=e.label;document.getElementById('labels').append(label);return{line,label,e,offset}});
const nodeEls=new Map(data.nodes.map(n=>{const g=el('g',{class:`node ${n.nodeType}`,tabindex:'0'}),r=el('rect',{x:-65,y:-25,width:130,height:50}),t=el('text',{y:-2}),id=el('text',{class:'id',y:15});t.textContent=n.label;id.textContent=n.id;g.append(r,t,id);g.addEventListener('pointerdown',ev=>{dragging={type:'node',n,sx:ev.clientX,sy:ev.clientY,ox:n.x,oy:n.y};moved=false;ev.stopPropagation();});g.addEventListener('click',()=>{if(!moved)select(n.id)});g.addEventListener('keydown',ev=>{if(ev.key==='Enter')select(n.id)});document.getElementById('nodes').append(g);return[n.id,g]}));
function update(){viewport.setAttribute('transform',`translate(${transform.x} ${transform.y}) scale(${transform.k})`);for(const n of data.nodes)nodeEls.get(n.id).setAttribute('transform',`translate(${n.x} ${n.y})`);edgeEls.forEach(o=>{const s=byId.get(o.e.source),t=byId.get(o.e.target);if(s.id===t.id){o.line.setAttribute('d',`M${s.x+35},${s.y-22} C${s.x+95},${s.y-90} ${s.x-95},${s.y-90} ${s.x-35},${s.y-22}`);o.label.setAttribute('x',s.x);o.label.setAttribute('y',s.y-88);return}const dx=t.x-s.x,dy=t.y-s.y,d=Math.hypot(dx,dy)||1,ox=-dy/d*o.offset,oy=dx/d*o.offset,x1=s.x+dx/d*68+ox,y1=s.y+dy/d*28+oy,x2=t.x-dx/d*68+ox,y2=t.y-dy/d*28+oy;o.line.setAttribute('d',`M${x1},${y1} L${x2},${y2}`);o.label.setAttribute('x',(x1+x2)/2);o.label.setAttribute('y',(y1+y2)/2-5);});}
function visible(){const ids=new Set(views[currentView].ids),hierarchyKinds=new Set(['inheritance','taxonomy']),relationKinds=new Set(['flow','rollover','aggregate','usage','relation','containment','reference','shacl']);edgeEls.forEach(o=>{let allowed=o.e.kind!=='typing'&&o.e.kind!=='constraint';if(currentView==='domain')allowed=o.e.kind==='flow';else if(currentView==='classes')allowed=o.e.kind==='inheritance';else if(currentView==='works')allowed=o.e.kind==='taxonomy';const toggle=hierarchyKinds.has(o.e.kind)?'showInheritance':'showRelations',on=allowed&&ids.has(o.e.source)&&ids.has(o.e.target)&&(hierarchyKinds.has(o.e.kind)||relationKinds.has(o.e.kind))&&document.getElementById(toggle).checked;o.line.style.display=o.label.style.display=on?'':'none'});}
function applyView(name){currentView=name;clear();const view=views[name],ids=new Set(view.ids);document.getElementById('areas').style.display=name==='all'?'':'none';data.nodes.forEach(n=>{nodeEls.get(n.id).classList.toggle('hidden',!ids.has(n.id));if(view.pos[n.id]){n.x=view.pos[n.id][0];n.y=view.pos[n.id][1]}});document.querySelectorAll('.class-btn').forEach(b=>b.style.display=ids.has(b.dataset.id)?'':'none');document.querySelectorAll('.view-btn').forEach(b=>b.classList.toggle('active',b.dataset.view===name));visible();fit();update()}
function select(id){selected=id;nodeEls.forEach((g,k)=>g.classList.toggle('selected',k===id));document.querySelectorAll('.class-btn').forEach(b=>b.classList.toggle('active',b.dataset.id===id));const n=byId.get(id),links=data.edges.filter(e=>e.source===id||e.target===id),outgoing=links.filter(e=>e.source===id),incoming=links.filter(e=>e.target===id);nodeEls.forEach((g,k)=>g.classList.toggle('dim',k!==id&&!links.some(e=>e.source===k||e.target===k)));edgeEls.forEach(o=>{const dim=o.e.source!==id&&o.e.target!==id;o.line.classList.toggle('dim',dim);o.label.style.opacity=dim?'.08':'1'});const relationList=(items,direction)=>items.length?`<ul class="list">${items.map(e=>`<li><b>${esc(e.label)}</b><small>${direction} ${esc(byId.get(direction==='→'?e.target:e.source).label)} · ${esc(e.property)}</small></li>`).join('')}</ul>`:'<div class="empty">해당 관계가 없습니다.</div>';document.getElementById('detail').innerHTML=`<h2>선택 정보</h2><div class="detail-title">${esc(n.label)}</div><div class="detail-id">${esc(n.id)}</div><div class="comment">${esc(n.comment||'설명이 등록되지 않았습니다.')}</div>${n.parents.length?`<h2>상위 클래스</h2>${n.parents.map(x=>`<span class="tag">${esc(byId.get(x)?.label||x)}</span>`).join('')}`:''}<h2 style="margin-top:20px">정의된 데이터 속성</h2>${n.attributes.length?`<ul class="list">${n.attributes.map(a=>`<li><b>${esc(a.label)}</b><small>${esc(a.id)} · ${esc(a.type)}${a.definedOn&&a.definedOn!==n.id?` · 정의 클래스: ${esc(a.definedOn)}`:''}</small></li>`).join('')}</ul>`:'<div class="empty">정의된 데이터 속성이 없습니다.</div>'}<h2>나가는 관계 (${outgoing.length})</h2>${relationList(outgoing,'→')}<h2>이 노드를 사용하는 들어오는 관계 (${incoming.length})</h2>${relationList(incoming,'←')}<div class="uri">${esc(n.uri)}</div>`;}
function clear(){selected=null;nodeEls.forEach(g=>g.classList.remove('selected','dim','match'));edgeEls.forEach(o=>{o.line.classList.remove('dim');o.label.style.opacity=''});document.querySelectorAll('.class-btn').forEach(b=>b.classList.remove('active'));document.getElementById('detail').innerHTML='<h2>선택 정보</h2><div class="empty">그래프 또는 왼쪽 목록에서 클래스를 선택하면 설명, 속성, 연결 관계를 볼 수 있습니다.</div>';}
function esc(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML}function fit(){transform={x:0,y:0,k:1};update()}
document.getElementById('classList').innerHTML=data.nodes.map(n=>`<button class="class-btn" data-id="${n.id}">${esc(n.label)}</button>`).join('');document.querySelectorAll('.class-btn').forEach(b=>b.onclick=()=>select(b.dataset.id));
const classCount=data.nodes.filter(n=>n.nodeType==='class').length,categoryCount=data.nodes.filter(n=>n.nodeType==='category').length;document.getElementById('stats').textContent=`v${data.version} · 노드 ${data.nodes.length} · 클래스 ${classCount} · 공종분류 ${categoryCount} · 관계 ${data.edges.length}`;
document.getElementById('search').addEventListener('input',ev=>{const q=ev.target.value.trim().toLowerCase();clear();const ids=new Set(views[currentView].ids);data.nodes.forEach(n=>{const hit=q&&ids.has(n.id)&&(n.label+n.id+n.comment).toLowerCase().includes(q);nodeEls.get(n.id).classList.toggle('match',!!hit);document.querySelector(`.class-btn[data-id="${n.id}"]`).style.display=ids.has(n.id)&&(!q||hit)?'':'none'});});
['showRelations','showInheritance'].forEach(id=>document.getElementById(id).onchange=visible);document.querySelectorAll('.view-btn').forEach(b=>b.onclick=()=>applyView(b.dataset.view));document.getElementById('reset').onclick=()=>{document.getElementById('search').value='';applyView(currentView)};document.getElementById('fit').onclick=fit;document.getElementById('zin').onclick=()=>{transform.k=Math.min(2.5,transform.k*1.2);update()};document.getElementById('zout').onclick=()=>{transform.k=Math.max(.45,transform.k/1.2);update()};
stage.addEventListener('wheel',ev=>{ev.preventDefault();transform.k=Math.max(.45,Math.min(2.5,transform.k*(ev.deltaY<0?1.1:.9)));update()},{passive:false});stage.addEventListener('pointerdown',ev=>{if(ev.target===svg||ev.target===viewport){dragging={type:'pan',sx:ev.clientX,sy:ev.clientY,ox:transform.x,oy:transform.y};moved=false}});window.addEventListener('pointermove',ev=>{if(!dragging)return;moved=moved||Math.hypot(ev.clientX-dragging.sx,ev.clientY-dragging.sy)>3;if(dragging.type==='node'){dragging.n.x=dragging.ox+(ev.clientX-dragging.sx)/transform.k;dragging.n.y=dragging.oy+(ev.clientY-dragging.sy)/transform.k}else{transform.x=dragging.ox+ev.clientX-dragging.sx;transform.y=dragging.oy+ev.clientY-dragging.sy}update()});window.addEventListener('pointerup',()=>dragging=null);applyView('domain');
</script></body></html>'''
    return template.replace("__DATA__", payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if the HTML is missing or stale")
    args = parser.parse_args()
    try:
        expected = render(build_data(load_graph()))
        if args.check:
            if not OUTPUT_FILE.is_file() or OUTPUT_FILE.read_text(encoding="utf-8") != expected:
                raise RuntimeError("interactive.html is missing or stale; regenerate it")
            print("[OK] visualization/interactive.html is current")
        else:
            OUTPUT_FILE.write_text(expected, encoding="utf-8")
            print("[OK] wrote visualization/interactive.html")
        return 0
    except (OSError, RuntimeError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

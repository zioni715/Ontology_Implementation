#!/usr/bin/env python3
"""Validate the standalone RCPP RDF dataset."""
from pathlib import Path

from pyshacl import validate
from rdflib import Graph, Namespace, RDF, RDFS

HERE = Path(__file__).resolve().parent
RDFS_DIR = HERE.parent / "RDFS"
RCPP = Namespace("https://zioni715.github.io/ontology/rcpp#")
EX = Namespace("https://zioni715.github.io/ontology/rcpp/example#")

data = Graph().parse(HERE / "rcpp-rdf.ttl", format="turtle")
ontology = Graph()
for name in ("schema.ttl", "classes.ttl", "properties.ttl"):
    ontology.parse(RDFS_DIR / name, format="turtle")
shapes = Graph().parse(RDFS_DIR / "shapes.ttl", format="turtle")

conforms, _, report = validate(
    data,
    shacl_graph=shapes,
    ont_graph=ontology,
    inference="rdfs",
)
if not conforms:
    raise SystemExit(report)

required_types = {
    "기성회차": RCPP.ProgressPaymentRound,
    "기성문서": RCPP.ProgressDocument,
    "비용항목": RCPP.CostItem,
    "문서항목": RCPP.DocumentItem,
    "공종": RCPP.WorkCategory,
    "단위": RCPP.Unit,
}
combined = data + ontology
for label, rdf_type in required_types.items():
    count = len(
        {
            instance
            for instance, declared_type in data.subject_objects(RDF.type)
            if declared_type == rdf_type
            or rdf_type
            in combined.transitiveClosure(
                lambda current, graph: graph.objects(current, RDFS.subClassOf),
                declared_type,
            )
        }
    )
    if count == 0:
        raise SystemExit(f"[ERROR] 필수 데이터 유형 누락: {label}")
    print(f"[PASS] {label}: {count}개 이상 확인")

if (EX.RCPPRDFDataset, RDF.type, None) not in data:
    raise SystemExit("[ERROR] RDF 데이터셋 메타데이터 누락")

print(f"[OK] RDF parse and SHACL validation passed: {len(data)} triples")

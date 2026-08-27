#!/usr/bin/env python3
"""Structural validation for the single compact RCPP ontology."""
from collections import defaultdict
from pathlib import Path
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS

HERE = Path(__file__).resolve().parent
R = Namespace("https://zioni715.github.io/ontology/rcpp#")
FILES = ("schema.ttl", "classes.ttl", "properties.ttl", "code-lists.ttl")

graph = Graph()
for name in FILES:
    graph.parse(HERE / name, format="turtle")
bundle = Graph().parse(HERE / "rcpp-rdfs.ttl", format="turtle")
classes = set(graph.subjects(RDF.type, RDFS.Class))
properties = set(graph.subjects(RDF.type, RDF.Property))
errors = []
if set(graph) != set(bundle):
    missing = len(set(graph) - set(bundle))
    extra = len(set(bundle) - set(graph))
    errors.append(f"submission bundle differs from source modules: missing={missing}, extra={extra}")
usage = Graph().parse(HERE / "examples.ttl", format="turtle")
usage += Graph().parse(HERE / "shapes.ttl", format="turtle")
usage += Graph().parse(HERE / "code-lists.ttl", format="turtle")
for resource in classes | properties:
    if not list(graph.objects(resource, RDFS.label)):
        errors.append(f"label missing: {resource}")
    if not list(graph.objects(resource, RDFS.comment)):
        errors.append(f"definition missing: {resource}")
for resource in classes:
    if not list(usage.triples((None, RDF.type, resource))) and not list(usage.triples((None, None, resource))) and not list(graph.triples((None, RDFS.subClassOf, resource))):
        errors.append(f"class unused by examples/SHACL: {resource}")
for resource in properties:
    if not list(usage.triples((None, resource, None))) and not list(usage.triples((None, None, resource))) and not list(graph.triples((None, resource, None))) and not list(graph.triples((None, None, resource))):
        errors.append(f"property unused by examples/SHACL: {resource}")
for predicate, label in ((RDFS.subClassOf, "class"), (RDFS.subPropertyOf, "property")):
    edges = defaultdict(set)
    for child, parent in graph.subject_objects(predicate):
        if isinstance(child, URIRef) and isinstance(parent, URIRef): edges[child].add(parent)
    for start in edges:
        stack = [(start, {start})]
        while stack:
            node, path = stack.pop()
            for parent in edges.get(node, set()):
                if parent in path: errors.append(f"{label} hierarchy cycle: {parent}")
                else: stack.append((parent, path | {parent}))
removed = (R.Project, R.belongsToProject, R.projectIdentifier, R.CostSpecification, R.hasCostSpecification, R.RebarSpecification, R.ReadyMixedConcreteSpecification, R.ConcretePlacementSpecification, R.FormworkSpecification, R.ShoringSpecification, R.usesUnitPriceFrom, R.derivedFrom, R.previousQuantityFrom, R.aggregatedInto, R.costItemCategory, R.materialCost, R.laborCost, R.expenseCost, R.totalCost, R.providesUnitPriceTo, R.QuantityItem, R.CalculationActivity, R.DocumentItemMatching, R.FieldRequirement, R.SpecificationNormalizationRule, R.DocumentUsage, R.itemOfDocument)
for resource in removed:
    if any(resource in triple for triple in graph): errors.append(f"removed concept remains: {resource}")
confirmed_flows = (R.providesCalculatedQuantityTo, R.providesContractValueTo, R.providesContractQuantityTo, R.providesContractUnitPriceTo, R.providesContractAmountTo, R.providesContractQuantityToProgressPaymentItem, R.providesContractUnitPriceToProgressPaymentItem, R.providesContractAmountToProgressPaymentItem, R.providesCumulativeValuesTo, R.contributesContractAmountTo, R.contributesCurrentAmountTo)
for resource in confirmed_flows:
    if (resource, R.validationStatus, Literal("confirmed")) not in graph: errors.append(f"confirmed status missing: {resource}")
if not (15 <= len(classes) <= 35): errors.append(f"class count out of compact range: {len(classes)}")
if not (25 <= len(properties) <= 80): errors.append(f"property count out of compact range: {len(properties)}")
if errors:
    print("\n".join(f"[ERROR] {e}" for e in errors)); raise SystemExit(1)
print(f"[OK] source modules and submission bundle match; {len(graph)} triples, {len(classes)} classes, {len(properties)} properties")

# RCPP Ontology Implementation

철근콘크리트공종 기성서류 비용산정 정보 RDF/RDFS/OWL2 구축

- ver1.0.0

## 실행 환경

WSL Ubuntu 24.04

```bash
conda create -n RC_Ontology python=3.10.14 -y
conda activate RC_Ontology
conda install -y pip
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 폴더 구조 및 파일 설명

```text
.
├── README.md                                - 프로젝트 및 제출 결과물 설명
├── SPECIFICATION.md                         - 클래스 계층 및 속성 구조 명세
├── requirements.txt                         - Python 의존성
└── KO/                                      - 한국어 온톨로지 구현
    ├── RDF/                                 - 독립 RDF 지식그래프 결과물과 검증 코드
    │   ├── rcpp-rdf.ttl                     - 기준 개체와 업무 개체를 통합한 RDF 데이터셋
    │   ├── VALIDATION_REPORT.md             - RDF 검증 범위와 결과
    │   └── validate_rdf.py                  - RDF 파싱 및 SHACL 적합성 검증
    ├── RDFS/                                - RDFS 온톨로지 결과물과 검증 코드
    │   ├── rcpp-rdfs.ttl                    - 제출용 RDFS 통합본
    │   ├── schema.ttl                       - 온톨로지 이름과 버전 등 메타데이터
    │   ├── classes.ttl                      - 기성서류, 비용항목, 공종 클래스 정의
    │   ├── properties.ttl                   - 관계와 수량·단가·금액 속성 정의
    │   ├── code-lists.ttl                   - 철근·콘크리트·거푸집·동바리 공종 코드
    │   ├── shapes.ttl                       - 데이터 유효성 검사용 SHACL 제약
    │   ├── examples.ttl                     - 검증과 질의용 정상 예제 데이터
    │   ├── invalid-examples.ttl             - 위반 검출 확인용 오류 예제 데이터
    │   ├── RDFS_VALIDATION_REPORT.md        - RDFS 검증 결과
    │   ├── ONTOLOGY_SPECIFICATION.md        - 온톨로지 명세와 CQ 추적 정보
    │   ├── validate_ontology.py             - 온톨로지 구조 검증
    │   ├── validate_examples.py             - 정상 예제의 SHACL 및 CQ 검증
    │   └── validate_invalid_examples.py     - 의도한 위반 유형 검출 여부 검증
    ├── OWL2/                                - Protégé에서 구축한 OWL 2 최종 결과물
    │   ├── rcpp-owl-final.ttl               - 제출용 OWL 2 원본
    │   ├── rcpp-owl-inferred.ttl            - HermiT 추론 결과
    │   ├── axioms.md                        - OWL 2 공리 명세
    │   ├── owl2-shapes.ttl                  - OWL 2 구조 검증 전용 SHACL
    │   ├── OWL2_VALIDATION_REPORT.md        - OWL 2·HermiT·SHACL 검토 보고서
    │   └── validate_owl2.py                 - OWL 2 SHACL 및 inferred 결과 확인
    └── visualization/                       - RDFS 구조·예제 정보흐름 시각화
        ├── generate_interactive.py          - TTL 기반 독립형 HTML 생성
        └── interactive.html                 - 브라우저용 시각화 결과물
```


## 검증

| 구분 | 파일 | 설명 |
|---|---|---|
| RDF | [`KO/RDF/rcpp-rdf.ttl`](KO/RDF/rcpp-rdf.ttl) | 공종·단위·문서·회차·비용항목 및 정보계보 인스턴스 데이터 |
| RDFS | [`KO/RDFS/rcpp-rdfs.ttl`](KO/RDFS/rcpp-rdfs.ttl) | 클래스·속성·정의역·치역·계층을 정의한 통합 스키마 |
| OWL 2 | [`KO/OWL2/rcpp-owl-final.ttl`](KO/OWL2/rcpp-owl-final.ttl) | 논리 공리와 제한조건을 포함한 최종 온톨로지 |

검증 실행:

```bash
python KO/RDF/validate_rdf.py
python KO/RDFS/validate_ontology.py
python KO/RDFS/validate_examples.py
python KO/RDFS/validate_invalid_examples.py
python KO/OWL2/validate_owl2.py
```
OWL 2 최종본은 Protégé의 HermiT reasoner로 일관성 검사를 수행하고 추론 결과를 `rcpp-owl-inferred.ttl`로 내보냄
HermiT와 OWL 2 전용 SHACL 검증 결과는 [OWL 2 검증 보고서](KO/OWL2/OWL2_VALIDATION_REPORT.md)에 기록

검증 보고서:

- [RDF 검증 보고서](KO/RDF/VALIDATION_REPORT.md)
- [RDFS 검증 보고서](KO/RDFS/RDFS_VALIDATION_REPORT.md)
- [OWL 2 검증 보고서](KO/OWL2/OWL2_VALIDATION_REPORT.md)

## 시각화

- 대상: RDFS 클래스·속성 구조 및 정상 예제의 정보흐름
- 제외: OWL 2 restriction 및 HermiT inferred 공리

```bash
python KO/visualization/generate_interactive.py
python KO/visualization/generate_interactive.py --check
```

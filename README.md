# RCPP Ontology Implementation

철근콘크리트공종 기성서류 비용산정 정보 RDFS 구축

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
KO/                                          - 한국어 온톨로지 구현
├── ontology/                                - 온톨로지 원본과 검증 코드
│   ├── schema.ttl                           - 온톨로지 이름과 버전 등 메타데이터
│   ├── classes.ttl                          - 기성서류, 비용항목, 공종 클래스 정의
│   ├── properties.ttl                       - 관계와 수량·단가·금액 속성 정의
│   ├── code-lists.ttl                       - 철근·콘크리트·거푸집·동바리 공종 코드
│   ├── shapes.ttl                           - 데이터 유효성 검사용 SHACL 제약
│   ├── examples.ttl                         - 검증과 질의용 정상 예제 데이터
│   ├── invalid-examples.ttl                 - 위반 검출 확인용 오류 예제 데이터
│   ├── ONTOLOGY_SPECIFICATION.md            - 온톨로지 명세와 CQ 추적 정보
│   ├── validate_ontology.py                 - 온톨로지 구조 검증
│   ├── validate_examples.py                 - 정상 예제의 SHACL 및 CQ 검증
│   └── validate_invalid_examples.py         - 의도한 위반 유형 검출 여부 검증
└── visualization/                           - 인터랙티브 시각화
    ├── generate_interactive.py              - TTL 기반 독립형 HTML 생성
    └── interactive.html                     - 브라우저용 시각화 결과물
```


## 검증

검증 실행:

```bash
python KO/ontology/validate_ontology.py
python KO/ontology/validate_examples.py
python KO/ontology/validate_invalid_examples.py
```



## 시각화


```bash
python KO/visualization/generate_interactive.py
python KO/visualization/generate_interactive.py --check
```

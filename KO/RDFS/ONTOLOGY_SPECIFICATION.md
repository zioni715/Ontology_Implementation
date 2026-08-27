# RCPP 온톨로지 명세

## 1. 목적 및 범위

- 목적
  - 철근콘크리트공종의 공사기성부분내역서 작성에 필요한 비용정보 표현
  - 서류별 항목, 수량, 단가 및 금액의 통합
  - 서류 간 정보전달, 산정 및 집계 관계의 추적
- 적용 서류
  - 계약내역서
  - 공사기성부분내역서
  - 원가계산서
  - 공종별집계표
  - 공종별내역서
  - 수량산출서
- 제외 범위
  - 검측·품질·안전·공정 서류
  - 계산 실행상태
  - 항목 매칭 승인업무
  - 규격 정규화 엔진
  - 원본 문서의 셀 위치
- 온톨로지 IRI
  - `https://zioni715.github.io/ontology/rcpp`
- 네임스페이스
  - `https://zioni715.github.io/ontology/rcpp#`

## 2. 설계 원칙

### 2.1 모델 구성

- 하나의 namespace와 ontology IRI 사용
- 관리 편의를 위해 스키마 파일 분리
  - `schema.ttl`: 온톨로지 식별정보
  - `classes.ttl`: 클래스 계층
  - `properties.ttl`: 속성 정의
  - `code-lists.ttl`: 공종 및 단위 기준 개체
- 제출용 통합본
  - `rcpp-rdfs.ttl`
- 의미 구조와 데이터 제약 분리
  - RDF/RDFS: 클래스, 속성, 계층, 정의역 및 치역
  - SHACL: 필수값, 카디널리티, 통제값, 산식 및 집계 검증

### 2.2 문서 및 항목

- `ProgressDocument`의 구분
  - 산출서류: `OutputDocument`
  - 근거서류: `EvidenceDocument`
- 산출서류
  - `ProgressPaymentStatement`만 해당
- 문서와 항목 연결
  - 정방향 관계 `containsItem`만 저장
  - 항목에서 문서로 이동할 때는 역방향 질의 사용
- 문서 공통 항목정보
  - 항목명: `itemName`
  - 단위: `usesUnit`
- 동일 비용대상의 문서 간 연결
  - `representsCostItem` 사용
  - 공통 대상은 `CostItem`으로 관리
- 금회기성수량
  - 별도 서류나 별도 계산 개체로 만들지 않음
  - 해당 회차 `ProgressPaymentItem`의 `currentQuantity`로 기록

### 2.3 공종 및 비용항목

- 상위 공종
  - 철근콘크리트공사
- 세부 공종
  - 철근공사
  - 콘크리트공사
  - 거푸집공사
  - 동바리공사
- 공종 표현 방식
  - `WorkCategory`의 통제 분류 개체로 표현
  - 공종 클래스와 공종 개체를 혼용하지 않음
- 비용항목 분류
  - 철근 재료비
  - 철근 가공·조립비
  - 레디믹스트콘크리트 재료비
  - 콘크리트 타설비
  - 거푸집 비용
  - 동바리 비용
- 철근 및 콘크리트 비용항목
  - 재료비와 시공비 하위 유형 중 하나로 직접 인스턴스화
- 규격 표현
  - 별도 규격 개체를 두지 않음
  - `CostItem.specification`과 공종별 상세속성 사용
- 비용정보 식별·산정 순서
  - 공종 → 규격 → 단위 → 수량 → 단가 → 금액

### 2.4 수량·단가·금액

- 수량 및 금액의 구분 기준
  - 서류명이 아닌 값의 역할을 기준으로 구분
  - 계약, 전회, 금회, 누계, 잔여
- 수치 데이터형
  - 일반 수치: `xsd:decimal`
  - 횟수 및 회차: `xsd:integer`
- 단위 표현
  - 속성명에 측정 단위 명시
  - 예: `nominalDiameterMm`, `maximumInstallationHeightM`
- 산식 검증
  - 계산 실행 개체를 만들지 않음
  - SHACL 및 검증 코드로 확인

### 2.5 집계 및 정보전달

- `SummaryItem`
  - 개별 수량이 아닌 세부 공종별 금액 합계 표현
- 계약집계
  - `WorkCategoryDetailItem.contractAmount` 합산
  - 결과: `ContractSummaryItem.contractAmount`
- 기성집계
  - `ProgressPaymentItem.currentAmount` 합산
  - 결과: `ProgressPaymentSummaryItem.currentAmount`
- 기성집계항목
  - 기관별 서식 차이를 고려한 선택 항목
  - 항목이 존재할 경우 집계 원천, 공종 및 합계 일치 필수
- 정보전달 방향
  - 수량산출항목 → 계약항목
  - 계약항목 → 공종별내역항목
  - 계약항목 → 기성내역항목
  - 이전 기성내역항목 → 현재 기성내역항목
  - 상세항목 → 집계항목
- 중복 관계 처리
  - 일반 대응관계와 역방향 출처관계를 중복 저장하지 않음
  - 수신 관계는 역방향 질의로 확인

### 2.6 적용 제한

- 동바리 수량산정 기준
  - 면적
  - 공간체적
- 제외 단위
  - `개소`
- 제외 사유
  - 현재 확인된 근거와 단위 코드 부족
- 신규 개념 채택 조건
  - 실제 서류에서 사용
  - 기성내역 작성에 필요
  - 역량질문 또는 SHACL 검증에 사용

## 3. 역량질문

| CQ | 질문 | 주요 자원 |
|---|---|---|
| CQ01 | 특정 기성항목은 어떤 계약항목에서 계약단가를 받는가? | `providesContractUnitPriceToProgressPaymentItem`, `representsCostItem` |
| CQ02 | 특정 기성내역 행의 금회수량은 얼마인가? | `ProgressPaymentItem`, `currentQuantity` |
| CQ03 | 금회기성금액의 계약단가는 어디에서 같은 값으로 전달되었는가? | `providesContractUnitPriceToProgressPaymentItem`, `contractUnitPrice` |
| CQ04 | 전회·금회·누계·잔여 수량과 금액은 일관되는가? | 수량·금액 공통 속성 및 SHACL 산식 |
| CQ05 | 상세금액은 어느 계약·기성 집계항목으로 합산되는가? | `contributesContractAmountTo`, `contributesCurrentAmountTo` |
| CQ06 | 수량산출서부터 기성내역서까지 흐름을 추적할 수 있는가? | 문서·항목·대응·출처·집계 관계 |
| CQ07 | 특정 계약항목이 나타내는 비용항목의 공종·규격·단위는 무엇인가? | `representsCostItem`, `belongsToWorkCategory`, `specification`, `usesUnit` |
| CQ08 | 계약수량은 어떤 산출항목들의 수량 합계로 구성되는가? | `providesCalculatedQuantityTo`, `calculatedQuantity`, `contractQuantity` |
| CQ09 | 특정 원가계산항목의 재료비·노무비·경비와 산출단가는 얼마인가? | `materialUnitCost`, `laborUnitCost`, `expenseUnitCost`, `calculatedUnitPrice` |
| CQ10 | 특정 기성항목의 전회누계는 어느 이전 회차 항목에서 전달되었는가? | `providesCumulativeValuesTo`, `previousProgressRound`, `containsItem` |
| CQ11 | 특정 기성항목의 계약·전회·금회·누계·잔여수량은 얼마인가? | 기성수량 상태 속성 |
| CQ12 | 특정 기성항목의 계약·전회·금회·누계·잔여금액은 얼마인가? | 기성금액 상태 속성 |
| CQ13 | 각 기성서류에는 어떤 유형의 항목이 포함되는가? | `containsItem`, 문서 및 문서항목 클래스 |
| CQ14 | 철근·콘크리트 비용항목은 재료비와 시공비 중 어느 유형인가? | 비용항목 하위 클래스 |
| CQ15 | 특정 회차·공종의 금회기성금액 합계는 얼마인가? | `belongsToProgressRound`, `belongsToWorkCategory`, `currentAmount` |
| CQ16 | 동바리 수량산정 기준과 문서항목의 측정 단위는 무엇인가? | `quantityBasis`, `usesUnit` |
| CQ17 | 특정 공사기성부분내역서는 몇 회차에 속하는가? | `belongsToProgressRound`, `roundNumber` |
| CQ18 | 특정 문서항목은 어느 기성서류에 포함되는가? | `containsItem`의 역방향 질의 |
| CQ19 | 계약수량·계약단가·계약금액이 어느 공종별내역항목으로 전달되는가? | 세 계약값 전달관계 |
| CQ20 | 동일 비용항목을 수량산출·계약·원가·공종별내역·기성 항목에서 추적할 수 있는가? | `representsCostItem` 및 값 전달관계 |

## 4. 참조자료

- 국토교통부·한국건설기술연구원, 「2026년 건설공사 표준품셈」, 국토교통부 공고 제2025-1574호
  - https://www.codil.or.kr/helpdesk/read.do?bbsId=BBSMSTR_900000000202&nttId=13261
- 국가기술표준원, 「KS F 4009 레디믹스트 콘크리트」
  - https://kats.go.kr/mobile/content.do?cid=1026&cmsid=481&mode=view&page=303&skin=%2Fmobile%2F
- 국토교통부 국가건설기준센터, 「KCS 14 20 11 철근공사」
  - https://www.kcsc.re.kr/
- 국토교통부 국가건설기준센터, 「KCS 14 20 12 거푸집 및 동바리」, 2024.12.30.
  - https://www.kcsc.re.kr/board/notdetail/6639

## 5. 검증 범위

### 5.1 정상 예제

- 대상 공종
  - 철근
  - 콘크리트
  - 거푸집
  - 동바리
- 기본 정보흐름
  - 수량산출
  - 계약 및 원가자료
  - 공종별 상세
  - 계약 공종집계
  - 기성 상세
  - 기성 공종집계
- 철근 검증 사례
  - D10 및 D16 상세항목 구성
  - 두 상세항목의 계약금액과 금회금액 합산
  - D16 계약수량과 두 산출항목 수량 합계 비교
- 회차 검증 사례
  - 2회차 및 3회차 기성항목 분리
  - 직전 회차 번호 확인
  - 전회누계 값의 이월 확인
  - 2회차 이상에서 이전 회차 1개 요구
  - 기성항목별 전회누계 원천 최대 1개 제한
- 재료비 계보 사례
  - 철근 재료비
  - 레디믹스트콘크리트 재료비
  - 수량산출부터 계약·원가·공종별내역·집계·2회차·3회차 기성까지 연결

### 5.2 오류 예제

- 필수값 누락
- 단일값 속성의 중복
- 데이터형 오류
- 음수 및 허용범위 위반
- 누계수량의 계약수량 초과
- 계약 및 기성 산식 불일치
- 산출수량 합계와 계약수량 불일치
- 계약값 전달 불일치
- 계약값 전달 원천 불일치
- 전달항목의 단위 불일치
- 이전 회차 및 전회누계 이월 불일치
- 대응 비용항목 불일치
- 공종 불일치
- 계약집계 및 기성집계 불일치
- 비용항목 코드 및 이름 누락

### 5.3 SHACL 작성 기준

- 모든 SPARQL 제약에 namespace 접두사 명시
- 산식 및 집계 검증은 OWL 공리가 아닌 SHACL에서 수행
- 정상 예제와 오류 예제를 분리하여 적합·부적합 판정 확인

### 5.4 검증 명령

```bash
python KO/RDFS/validate_ontology.py
python KO/RDFS/validate_examples.py
python KO/RDFS/validate_invalid_examples.py
```

### 5.5 판정 범위

- 포함
  - 모델 구조 검증
  - 정상 예제의 SHACL 적합성
  - 역량질문 결과 확인
  - 오류 예제의 위반 탐지
- 미포함
  - 실제 현장 문서 전체의 열·값 대조
  - 기관별 서식 차이 검증
  - 현장 전문가 검토
- 도메인 정확성 검증 완료 조건
  - 실제 현장 문서 적용
  - 원본 값 대조
  - 현장 전문가 검토

# RCPP RDFS 구조 명세

## 1. Classes

- 전체 클래스: 31개
- Level 1: 최상위 클래스 6개
- Level 2: Level 1의 직접 하위 클래스 8개
- Level 3: Level 2의 직접 하위 클래스 17개

| Level 1 | Level 2 | Level 3 |
|---|---|---|
| `ProgressDocument`<br>기성서류 | `EvidenceDocument`<br>근거서류 | `QuantityCalculationSheet`<br>수량산출서 |
| `ProgressDocument`<br>기성서류 | `EvidenceDocument`<br>근거서류 | `ContractStatement`<br>계약내역서 |
| `ProgressDocument`<br>기성서류 | `EvidenceDocument`<br>근거서류 | `CostCalculationStatement`<br>원가계산서 |
| `ProgressDocument`<br>기성서류 | `EvidenceDocument`<br>근거서류 | `WorkCategoryDetailStatement`<br>공종별내역서 |
| `ProgressDocument`<br>기성서류 | `EvidenceDocument`<br>근거서류 | `WorkCategorySummaryStatement`<br>공종별집계표 |
| `ProgressDocument`<br>기성서류 | `OutputDocument`<br>산출서류 | `ProgressPaymentStatement`<br>공사기성부분내역서 |
| `DocumentItem`<br>기성서류항목 | `DetailItem`<br>상세비용항목 | `CalculatedQuantityItem`<br>수량산출항목 |
| `DocumentItem`<br>기성서류항목 | `DetailItem`<br>상세비용항목 | `ContractItem`<br>계약항목 |
| `DocumentItem`<br>기성서류항목 | `DetailItem`<br>상세비용항목 | `CostCalculationItem`<br>원가계산항목 |
| `DocumentItem`<br>기성서류항목 | `DetailItem`<br>상세비용항목 | `WorkCategoryDetailItem`<br>공종별내역항목 |
| `DocumentItem`<br>기성서류항목 | `DetailItem`<br>상세비용항목 | `ProgressPaymentItem`<br>기성내역항목 |
| `DocumentItem`<br>기성서류항목 | `SummaryItem`<br>집계항목 | `ContractSummaryItem`<br>계약집계항목 |
| `DocumentItem`<br>기성서류항목 | `SummaryItem`<br>집계항목 | `ProgressPaymentSummaryItem`<br>기성집계항목 |
| `CostItem`<br>비용항목 | `RebarCostItem`<br>철근 비용항목 | `RebarMaterialCostItem`<br>철근 재료비항목 |
| `CostItem`<br>비용항목 | `RebarCostItem`<br>철근 비용항목 | `RebarFabricationAssemblyCostItem`<br>철근 가공·조립비항목 |
| `CostItem`<br>비용항목 | `ConcreteCostItem`<br>콘크리트 비용항목 | `ReadyMixedConcreteMaterialCostItem`<br>레디믹스트콘크리트 재료비항목 |
| `CostItem`<br>비용항목 | `ConcreteCostItem`<br>콘크리트 비용항목 | `ConcretePlacementCostItem`<br>콘크리트 타설비항목 |
| `CostItem`<br>비용항목 | `FormworkCostItem`<br>거푸집 비용항목 | — |
| `CostItem`<br>비용항목 | `ShoringCostItem`<br>동바리 비용항목 | — |
| `ProgressPaymentRound`<br>기성회차 | — | — |
| `WorkCategory`<br>공종 | — | — |
| `Unit`<br>단위 | — | — |

## 2. Object Properties

- 전체 Object Property: 18개
- Domain 또는 Range 미지정: RDFS에 명시하지 않은 항목

| Property | 의미 | Subproperty of | Domain | Range |
|---|---|---|---|---|
| `belongsToProgressRound` | 기성회차 소속 | — | `ProgressPaymentStatement` | `ProgressPaymentRound` |
| `belongsToWorkCategory` | 공종 소속 | — | 미지정 | `WorkCategory` |
| `containsItem` | 항목 포함 | — | `ProgressDocument` | `DocumentItem` |
| `contributesContractAmountTo` | 계약금액 집계 | — | `WorkCategoryDetailItem` | `ContractSummaryItem` |
| `contributesCurrentAmountTo` | 금회금액 집계 | — | `ProgressPaymentItem` | `ProgressPaymentSummaryItem` |
| `previousProgressRound` | 이전 기성회차 | — | `ProgressPaymentRound` | `ProgressPaymentRound` |
| `providesCalculatedQuantityTo` | 산출수량 전달 | — | `CalculatedQuantityItem` | `ContractItem` |
| `providesContractValueTo` | 계약값 전달 | — | `ContractItem` | `WorkCategoryDetailItem` |
| `providesContractQuantityTo` | 계약수량 전달 | `providesContractValueTo` | `ContractItem` | `WorkCategoryDetailItem` |
| `providesContractUnitPriceTo` | 계약단가 전달 | `providesContractValueTo` | `ContractItem` | `WorkCategoryDetailItem` |
| `providesContractAmountTo` | 계약금액 전달 | `providesContractValueTo` | `ContractItem` | `WorkCategoryDetailItem` |
| `providesContractQuantityToProgressPaymentItem` | 기성내역 계약수량 전달 | — | `ContractItem` | `ProgressPaymentItem` |
| `providesContractUnitPriceToProgressPaymentItem` | 기성내역 계약단가 전달 | — | `ContractItem` | `ProgressPaymentItem` |
| `providesContractAmountToProgressPaymentItem` | 기성내역 계약금액 전달 | — | `ContractItem` | `ProgressPaymentItem` |
| `providesCumulativeValuesTo` | 전회누계 전달 | — | `ProgressPaymentItem` | `ProgressPaymentItem` |
| `representsCostItem` | 비용항목 표현 | — | `DocumentItem` | `CostItem` |
| `subWorkCategoryOf` | 상위 공종 | — | `WorkCategory` | `WorkCategory` |
| `usesUnit` | 단위 사용 | — | `DetailItem` | `Unit` |

## 3. Datatype Properties

- 전체 Datatype Property: 38개
- Domain 미지정: 여러 클래스에서 공통 사용하거나 SHACL에서 적용 범위를 지정한 항목

| Property | 의미 | Domain | Range |
|---|---|---|---|
| `applicationPart` | 적용부위 | `FormworkCostItem` | `xsd:string` |
| `calculatedQuantity` | 산출수량 | 미지정 | `xsd:decimal` |
| `calculatedUnitPrice` | 산출단가 | `CostCalculationItem` | `xsd:decimal` |
| `complexityClass` | 복잡도 구분 | `FormworkCostItem` | `xsd:string` |
| `contractAmount` | 계약금액 | 미지정 | `xsd:decimal` |
| `contractQuantity` | 계약수량 | 미지정 | `xsd:decimal` |
| `contractUnitPrice` | 계약단가 | 미지정 | `xsd:decimal` |
| `cumulativeAmount` | 누계금액 | 미지정 | `xsd:decimal` |
| `cumulativeQuantity` | 누계수량 | 미지정 | `xsd:decimal` |
| `currentAmount` | 금회금액 | 미지정 | `xsd:decimal` |
| `currentQuantity` | 금회수량 | `ProgressPaymentItem` | `xsd:decimal` |
| `documentIdentifier` | 서류 식별자 | `ProgressDocument` | `xsd:string` |
| `expenseUnitCost` | 단위당 경비 | `CostCalculationItem` | `xsd:decimal` |
| `fabricationAssemblyType` | 가공·조립 유형 | `RebarFabricationAssemblyCostItem` | `xsd:string` |
| `formworkType` | 거푸집 종류 | `FormworkCostItem` | `xsd:string` |
| `itemCode` | 항목 코드 | `CostItem` | `xsd:string` |
| `itemName` | 항목명 | 미지정 | `xsd:string` |
| `laborUnitCost` | 단위당 노무비 | `CostCalculationItem` | `xsd:decimal` |
| `materialUnitCost` | 단위당 재료비 | `CostCalculationItem` | `xsd:decimal` |
| `maximumAggregateSizeMm` | 굵은골재 최대치수(mm) | `ReadyMixedConcreteMaterialCostItem` | `xsd:decimal` |
| `maximumInstallationHeightM` | 최대 설치높이(m) | `ShoringCostItem` | `xsd:decimal` |
| `nominalDiameterMm` | 호칭지름(mm) | `RebarCostItem` | `xsd:decimal` |
| `nominalStrengthMPa` | 호칭강도(MPa) | `ReadyMixedConcreteMaterialCostItem` | `xsd:decimal` |
| `placementMethod` | 타설방법 | `ConcretePlacementCostItem` | `xsd:string` |
| `previousCumulativeAmount` | 전회누계금액 | 미지정 | `xsd:decimal` |
| `previousCumulativeQuantity` | 전회누계수량 | 미지정 | `xsd:decimal` |
| `processingLocation` | 가공 장소 | `RebarFabricationAssemblyCostItem` | `xsd:string` |
| `quantityBasis` | 수량산정 기준 | `ShoringCostItem` | `xsd:string` |
| `rebarGrade` | 철근 강종 | `RebarCostItem` | `xsd:string` |
| `remainingAmount` | 잔여금액 | 미지정 | `xsd:decimal` |
| `remainingQuantity` | 잔여수량 | 미지정 | `xsd:decimal` |
| `reuseCount` | 전용횟수 | `FormworkCostItem` | `xsd:integer` |
| `roundNumber` | 회차 번호 | `ProgressPaymentRound` | `xsd:integer` |
| `shoringType` | 동바리 종류 | `ShoringCostItem` | `xsd:string` |
| `slumpMm` | 슬럼프(mm) | `ReadyMixedConcreteMaterialCostItem` | `xsd:decimal` |
| `specification` | 규격 | `CostItem` | `xsd:string` |
| `structureType` | 구조물 유형 | `ConcretePlacementCostItem` | `xsd:string` |
| `validationStatus` | 검증 상태 | 미지정 | `xsd:string` |

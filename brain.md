# 🧠 BRAIN.md — ClaimsMap Fact Knowledge Layer Master Blueprint

> **Project**: ClaimsMap (Superjoin VIT 2026 · Engineering Intern Hiring Assignment)  
> **Challenge**: Build a Fact Knowledge Layer across Unstructured Documents  
> **Author**: Om Srivastava (VIT Chennai · B.Tech CSE Data Science)  
> **Live Production URL**: [https://frontend-kappa-mauve-41.vercel.app](https://frontend-kappa-mauve-41.vercel.app)  
> **GitHub Repository**: [https://github.com/IronLad123/claimsmap](https://github.com/IronLad123/claimsmap)  
> **Document Purpose**: Complete, end-to-end technical reference, deep dataset forensic analysis, cross-document relationship mapping, and architectural blueprint.  
> **Last Updated**: 2026-09-08 — Cross-referenced against `superjoin-vit-2026-assignment.pdf` & live production deployment.

---

## TABLE OF CONTENTS
0. [Executive System Execution State & Verification](#0-executive-system-execution-state--verification)
1. [Assignment Specifications & Core Philosophy](#1-assignment-specifications--core-philosophy)
2. [Deep Dataset Analysis: Delhivery (Corporate & Financial Domain)](#2-deep-dataset-analysis-delhivery-corporate--financial-domain)
3. [Deep Dataset Analysis: India Macroeconomy (Institutional Policy Domain)](#3-deep-dataset-analysis-india-macroeconomy-institutional-policy-domain)
4. [The 4 Mandatory Showcase Cases (Ground Truth Evidence & Reasoning)](#4-the-4-mandatory-showcase-cases-ground-truth-evidence--reasoning)
5. [Fact Knowledge Layer: Data Model & Mathematical Formalization](#5-fact-knowledge-layer-data-model--mathematical-formalization)
6. [End-to-End System Architecture](#6-end-to-end-system-architecture)
7. [Cross-Document Reconciliation Engine (Algorithms & Rules)](#7-cross-document-reconciliation-engine-algorithms--rules)
8. [Failure Modes, Edge Cases, and Mitigation (Case 4 In-Depth)](#8-failure-modes-edge-cases-and-mitigation-case-4-in-depth)
9. [Brownie Points Strategy: Scaling, Dynamic Schema & Incremental Updates](#9-brownie-points-strategy-scaling-dynamic-schema--incremental-updates)
10. [Submission & Evaluation Checklist](#10-submission--evaluation-checklist)
11. [PDF Assignment Cross-Reference & Updated Decisions](#11-pdf-assignment-cross-reference--updated-decisions)

---

## 0. EXECUTIVE SYSTEM EXECUTION STATE & VERIFICATION

### 0.1 Deployment & Infrastructure Map

| Component | Target | Status | Specifications |
|---|---|---|---|
| **Demo Walkthrough Video** | Google Drive (2m 59s) | ✅ READY | [Watch Video Walkthrough](https://drive.google.com/file/d/1rzCIw4Oeyoii2epKI63uCocfFp4S6LpG/view?usp=sharing) |
| **Production Frontend** | Vercel Serverless Edge | ✅ LIVE | [frontend-kappa-mauve-41.vercel.app](https://frontend-kappa-mauve-41.vercel.app) |
| **Source Control** | GitHub Public Repo | ✅ LIVE | [IronLad123/claimsmap](https://github.com/IronLad123/claimsmap) |
| **Local Full-Stack** | `localhost:3000` & `8000` | ✅ RUNNING | Next.js 15 App Router + FastAPI uvicorn ASGI |
| **Primary LLM Engine** | OrcaRouter (OpenAI-compatible) | ✅ ACTIVE | `https://api.orcarouter.ai/v1` (`orcarouter/free` → `deepseek-v4-flash`) |
| **Fallback LLM Engine** | Google Gemini 1.5 Pro | ⚡ STANDBY | Enabled via `GEMINI_API_KEY` |
| **Deterministic Fallback** | Python Regex Rule Extractor | 🛡️ ACTIVE | Coordinate & pattern extractor (zero LLM dependency) |
| **Automated Test Suite**| Pytest Test Runner | ✅ 29/29 PASS | Extractor, sanitizer, reconciliation, E2E (0.39s) |
| **Type Integrity** | TypeScript `tsc --noEmit` | ✅ 0 ERRORS | 100% strict type safety across all components & routes |

### 0.2 Active Data State (Audited & Seeded)
- **Documents Loaded**: 8 documents (Delhivery Annual Report FY24, Delhivery Q4 FY24 Presentation, Delhivery IPO Prospectus 2022, RBI Annual Report 2024-25, IMF Article IV Consultation 2025, and supplementary test filings).
- **Facts Extracted & Grounded**: 31 immutable facts with verbatim quotes, page coordinates, and normalized magnitudes.
- **Cross-Document Links**: 14 comparative links categorized across `CORROBORATED`, `GENUINE_CONTRADICTION`, `RECONCILED_SCOPE`, `RECONCILED_TEMPORAL`, and `RECONCILED_METHODOLOGY`.


## 1. ASSIGNMENT SPECIFICATIONS & CORE PHILOSOPHY

### 1.1 The Core Problem Statement
In real-world business and regulatory workflows, critical facts are rarely contained in a single clean document. Instead:
- Facts are **scattered across multiple disparate filings** (annual reports, prospectuses, investor presentations, policy documents).
- Facts are **expressed in varied formats, linguistic patterns, and reporting conventions**.
- Facts are **supported by cross-document corroboration**, or **appear to contradict** due to shifts in time horizons, reporting perimeters (standalone vs. consolidated), or accounting standards.
- Facts may represent **genuine, irreconcilable contradictions** between sources.

### 1.2 Non-Negotiable System Requirements
1. **Extract Meaningful Numerical and Semantic Facts**:
   - Numerical: Revenues, EBITDA margins, shipment volumes, pin-code counts, GDP rates, foreign exchange reserves, deficits.
   - Semantic: Executive appointments/resignations, corporate structures, policy positions, accounting methodology definitions.
2. **Strict Grounding & Citation**:
   - Every fact **must link to immutable source evidence**: document name, PDF page number, verbatim snippet/quote, and paragraph/table context.
3. **Cross-Document Relationship Engine**:
   - Classify pairs/clusters of related facts into:
     - **Corroborated** (F1 === F2 in semantic/numerical reality).
     - **Genuine Contradiction** (F1 != F2 under identical scopes and conventions).
     - **Context-Reconciled Contradiction** (F1 != F2 superficially, but explained by time delta t, scope delta S, units delta U, or methodology delta M).
4. **Interactive Inspection Interface**:
   - Simple, fast API and UI allowing an evaluator to upload arbitrary PDFs, run extraction, view grounded facts, and inspect cross-document comparative reasoning.
5. **Zero Hardcoded Assumptions**:
   - Must **not** hardcode schemas, company names, regex rules tailored only to Delhivery or RBI, or fixed field lists. The documents must dynamically guide fact discovery.

### 1.3 What the Evaluators Are Looking For (Rubric)
- **Approach & Creativity over Polish**: Clear engineering thought, sound data modeling, and robust handling of ambiguity over superficial UI visualizers.
- **Explainability**: Graph visualizers alone are insufficient; the system must clearly explain *why* two facts corroborate or how context resolves an apparent conflict.
- **Generalizability**: Evaluating whether the system handles arbitrary PDFs without breaking.

---

## 2. DEEP DATASET ANALYSIS: DELHIVERY (CORPORATE & FINANCIAL DOMAIN)

```
starter-datasets/delhivery/
├── 01-delhivery-prospectus-2022-excerpt.pdf        (100 pages, ~1.6 MB, SEBI IPO Filing, May 2022)
├── 02-delhivery-annual-report-fy24-excerpt.pdf     (100 pages, ~6.7 MB, Statutory Report, Aug 2024)
└── 03-delhivery-q4-fy24-earnings-presentation.pdf  (27 pages, ~2.0 MB, Investor Deck, May 2024)
```

### 2.1 Document Archetypes & Comparative Matrix

| Attribute | 01 Prospectus (2022) | 02 Annual Report (FY24) | 03 Earnings Deck (Q4 FY24) |
| :--- | :--- | :--- | :--- |
| **Document Type** | Legal IPO Prospectus (Book Built Offer) | Statutory Annual Report & Financials | Investor Deck / Earnings Release |
| **Audience** | Regulators (SEBI), Institutional Bidders | Public Shareholders, Registrar of Companies | Buy-side/Sell-side Equity Analysts |
| **Primary Financial Unit** | ₹ in Million | ₹ in Million | ₹ in Crore |
| **Temporal Range** | FY19, FY20, FY21, 9M FY22 (Dec 31, 2021) | FY23 & FY24 (Year ended March 31, 2024) | Q1 FY23 – Q4 FY24, Full Year FY23 & FY24 |
| **Financial Boundaries** | Restated Consolidated (Ind AS) | Standalone & Consolidated Audited (Ind AS) | Consolidated & Service Lines (Non-GAAP/Adjusted) |
| **Key Operational Scope** | Core delivery network + Spoton acquisition | Full organic + Spoton integration + OS1 SaaS | Express Parcel, PTL, TL, SCS, Cross Border |

---

### 2.2 Deep Forensic Fact Mapping in Delhivery

#### Metric 1: Financial Performance — Revenue from Operations (FY24 & FY23)
* **Annual Report FY24 (Doc 02, Page 22, Directors Report Table)**:
  - *Standalone FY24 Revenue*: **₹ 74,540.82 Million**
  - *Standalone FY23 Revenue*: **₹ 66,586.61 Million** (YoY growth: 11.95%)
  - *Consolidated FY24 Revenue*: **₹ 81,415.38 Million**
  - *Consolidated FY23 Revenue*: **₹ 72,253.01 Million** (YoY growth: 12.68%)
* **Earnings Presentation (Doc 03, Page 9 & 14)**:
  - *Consolidated Revenue from Services FY24*: **₹ 8,142 Cr** (YoY growth: 13%)
  - *Consolidated Revenue from Services FY23*: **₹ 7,225 Cr** (or ₹ 7,224 Cr rounded)
  - *Quarterly Breakdown FY24*: Q1: ₹ 1,930 Cr, Q2: ₹ 1,942 Cr, Q3: ₹ 2,194 Cr, Q4: ₹ 2,076 Cr.
* **Reconciliation Analysis**:
  - ₹ 81,415.38 Million / 10 = ₹ 8,141.538 Cr ≈ ₹ 8,142 Cr.
  - Standalone (₹ 74,540.82 Mn) vs Consolidated (₹ 81,415.38 Mn) differs by **₹ 6,874.56 Million**, reflecting revenues from Spoton Logistics and other subsidiary operating entities.

#### Metric 2: Profitability — Adjusted EBITDA vs Statutory Net Loss
* **Earnings Presentation (Doc 03, Page 4, 14)**:
  - Headline: *"FY24: EBITDA profitable"*
  - *Full Year FY24 Adjusted EBITDA*: **+₹ 76 Cr** (Adjusted EBITDA margin: **+0.9%**), up from **-₹ 404 Cr** in FY23 (-5.6% margin).
  - *Service EBITDA*: **₹ 941 Cr** (margin: 11.6%), offset by Corporate overheads of **₹ 866 Cr**.
* **Annual Report FY24 (Doc 02, Page 22)**:
  - *Consolidated Loss for the year (FY24)*: **₹ (2,491.86) Million** (-₹ 249.19 Cr), reduced from **₹ (10,077.79) Million** in FY23.
  - *Standalone Loss for the year (FY24)*: **₹ (1,679.68) Million**.
* **Reconciliation Analysis**:
  - The presentation highlights cash/operating EBITDA before Depreciation, Amortization, and Share-based payments (+₹ 76 Cr).
  - The Annual Report highlights statutory bottom-line PAT (-₹ 249.2 Cr), including non-cash depreciation of network infrastructure, leases (Ind AS 116), finance costs, and taxes.

#### Metric 3: Operational Footprint — PIN Codes Covered
* **Prospectus 2022 (Doc 01, Page 47, 50)**:
  - *"We covered 17,488 PIN codes in India as of December 31, 2021, representing 88.3% of the 19,300 PIN codes in India."*
* **Earnings Presentation (Doc 03, Page 8)**:
  - Q4 FY22: **18,074** PIN codes
  - Q4 FY23: **18,540** PIN codes
  - Q3 FY24: **18,675** PIN codes
  - Q4 FY24: **18,793** PIN codes
* **Annual Report FY24 (Doc 02, Page 2)**:
  - *"18,793 Pin codes covered"* (as of March 31, 2024).
* **Reconciliation Analysis**:
  - Longitudinal progression from 17,488 (Dec 2021) -> 18,074 (Mar 2022) -> 18,540 (Mar 2023) -> 18,793 (Mar 2024).

#### Metric 4: Volume Delivered — Express Parcel Shipments
* **Prospectus 2022 (Doc 01, Page 3, 44)**:
  - Historical parcel shipment figures up to FY21 (over 1 billion parcels since inception).
* **Earnings Presentation (Doc 03, Page 9)**:
  - FY22: **582 Million** shipments
  - FY23: **663 Million** shipments
  - FY24: **740 Million** shipments (YoY growth: 12%)
* **Annual Report FY24 (Doc 02, Page 2, 4)**:
  - Highlights: **740 Mn** Express parcel shipments delivered in FY24.
  - Cumulative: **> 2.8 Bn** Express parcel shipments delivered since inception.
* **Reconciliation Analysis**:
  - Identical corroboration between Doc 02 and Doc 03 for FY24 annual volume (740 Mn).

#### Metric 5: Human Capital & Workforce Definition Divergence
* **Prospectus 2022 (Doc 01, Page 42, 44, 45)**:
  - Definition: *"Includes permanent employees and contractual manpower (excluding daily wage manpower and security guards and Spoton) as of the last day of the relevant period."*
* **Annual Report FY24 (Doc 02, Page 2, Footnote 1 & 5)**:
  - Headline: **98,135** Workforce strength.
  - Footnote 5: *"Includes permanent employees, contractual workers and last mile delivery partner agents."*
* **Reconciliation Analysis**:
  - The definition evolved from an IPO-restricted baseline (excluding daily wage & partner agents) to an expansive ecosystem strength figure in FY24.

#### Metric 6: Corporate Governance & Key Management Personnel (KMP)
* **Prospectus 2022 (Doc 01, Page 96–100)**:
  - *Sahil Barua*: Managing Director & CEO.
  - *Ajith Pai Mangalore*: Chief Operating Officer.
  - *Amit Agarwal*: Chief Financial Officer.
  - *Pooja Gupta*: Chief People Officer (joined April 1, 2021).
  - *Suraj Saharan*: Head of New Ventures (associated since Dec 20, 2011; on sabbatical in FY21).
  - *Sunil Kumar Bansal*: Company Secretary & Compliance Officer (joined August 23, 2021).
* **Annual Report FY24 (Doc 02, Page 41, Senior Management Table)**:
  - *Pooja Gupta* (Footnote 3): Ceased to be associated with the Company as Chief People Officer.
  - *Suraj Saharan* (Footnote 4): Appointed Chief People Officer (succeeding Pooja Gupta).
  - *Uday Sharma* (Footnote 1): Head of Business Development, ceased association with effect from January 09, 2024.
  - *Varun Bakshi* (Footnote 2): Former Head of Treasury & IR, took over as SVP-Business Development on January 09, 2024.
  - *Sunil Bansal* (Footnotes 5–7): Replaced by Vivek Kumar, who subsequently transitioned duties to Madhulika Rawat as Company Secretary.

---

## 3. DEEP DATASET ANALYSIS: INDIA MACROECONOMY (INSTITUTIONAL POLICY DOMAIN)

```
starter-datasets/india-macroeconomy/
├── 01-india-economic-survey-2024-25-excerpt.pdf    (89 pages, ~3.9 MB, Ministry of Finance, Jan 2025)
├── 02-rbi-annual-report-2024-25-excerpt.pdf        (100 pages, ~1.5 MB, Reserve Bank of India, May 2025)
└── 03-imf-india-2025-article-iv-excerpt.pdf        (95 pages, ~4.3 MB, International Monetary Fund, Nov 2025)
```

### 3.1 Document Archetypes & Methodological Lenses

| Attribute | 01 Economic Survey 2024-25 | 02 RBI Annual Report 2024-25 | 03 IMF Article IV Consultation |
| :--- | :--- | :--- | :--- |
| **Publishing Body** | Ministry of Finance, Government of India | Reserve Bank of India (Central Bank) | International Monetary Fund (IMF) |
| **Perspective** | Domestic economic review & policy outlook | Monetary policy, banking supervision & BoP | Multilateral external surveillance |
| **Fiscal Year Standard** | Indian Fiscal Year (Apr 1 – Mar 31) | Indian Fiscal Year (Apr 1 – Mar 31) | Indian Fiscal Year (`FY2024/25`, `FY2025/26`) |
| **Forex Accounting** | Gross FX reserves & debt cover ratio | Official BoP reserves & import cover months | IMF Reserve Adequacy Metric (ARA) & prospective imports |
| **Deficit Classification** | GoI Fiscal Responsibility (FRBM) rules | Union Budget revised estimates | IMF Government Finance Statistics (GFS) standard |

---

### 3.2 Deep Forensic Fact Mapping in Macroeconomy

#### Metric 1: Foreign Exchange (Forex) Reserves Trajectory
* **Economic Survey (Doc 01, Page 37)**:
  - *"India’s foreign exchange reserves stood at USD 640.3 billion as of the end of December 2024, sufficient to cover approximately 90 per cent of the country’s external debt of USD 711.8 billion as of September 2024."*
* **RBI Annual Report (Doc 02, Page 12)**:
  - *"Nonetheless, strong buffers in the form of ample forex reserves at US$ 668.3 billion (as at end-March 2025), covering 11 months of merchandise imports, helped mitigate external financing needs..."*
* **IMF Article IV (Doc 03, Page 12)**:
  - *"The Indian rupee experienced depreciation pressure, and foreign exchange (FX) reserves declined to  billion in March 2025, from  billion in September 2024 on significant currency intervention... FX reserves stood at  billion as of October [2025], covering over eight months of prospective imports and 109 percent of the IMF reserve adequacy metric."*
* **Cross-Document Synthesis**:
  - **Corroboration**: RBI (US$ 668.3B) and IMF (B) corroborate identically for March 2025.
  - **Temporal Trajectory**: Sep 2024 (B) -> Dec 2024 (.3B) -> Mar 2025 (.3B) -> Oct 2025 (B).

#### Metric 2: Import Cover Assessment (Genuine / Scope Contradiction)
* **RBI Annual Report (Doc 02, Page 12)**:
  - States that the March 2025 reserves of .3 billion cover **11 months of merchandise imports**.
* **IMF Article IV (Doc 03, Page 12, 44)**:
  - States that reserves in late 2025 cover **over eight months of prospective imports** (imports of both goods and services).
* **Root Cause of Divergence**:
  - RBI calculates cover exclusively against *merchandise (goods) imports* on a trailing/annualized historical basis.
  - IMF calculates cover against *goods and services combined* on a prospective (forward-looking 12-month) projection.

#### Metric 3: Central Government Fiscal Deficit (% of GDP)
* **IMF Article IV (Doc 03, Page 16, Table 1 & Memo Items)**:
  - *CG Fiscal Deficit (IMF Staff Definition)* for FY2024/25: **5.0% of GDP** (and 4.7% for FY2025/26).
  - *CG Fiscal Deficit (Authorities' Definition)* for FY2024/25: **4.9% of GDP** (and 4.4% for FY2025/26).
* **Footnote 1 & 2 Explanations**:
  - *"Authorities' definition includes asset sales in receipts, and excludes certain non-tax revenue items, hence the difference with staff's definition."*
  - *"The authorities treat states' divestment proceeds, including land sales, above-the-line as miscellaneous capital receipts. IMF staff definition treats divestment receipts as a below-the-line financing item."*
* **Reconciliation Analysis**:
  - What looks like a contradiction between Government Budget statements (4.9%) and IMF reports (5.0%) is completely reconciled by accounting methodology (treatment of privatization / disinvestment receipts).

#### Metric 4: Real GDP Growth Dynamics
* **Economic Survey (Doc 01, Page 14, 20)**:
  - Real GDP growth in Q1 and Q2 FY25 was 6.7% and 5.4% respectively.
  - Full-year FY25 estimated around **6.4% - 6.5%**.
* **RBI Annual Report (Doc 02, Page 7, 11)**:
  - Notes the solid FY24 actual growth rate of **8.2%**, and projects FY25 growth at **7.2%**.
* **IMF Article IV (Doc 03, Page 3, 5)**:
  - Real GDP expanded by **7.8% in Q1 FY2025/26** (market prices).
  - Medium-term growth projected at **6.6%** for FY2025/26.
* **Reconciliation Analysis**:
  - Varying numbers represent different publication dates (January 2025 vs May 2025 vs November 2025) and differences between base-year estimates (2011-12 series), GVA vs GDP at market prices, and subsequent data revisions by NSO.

---

## 4. THE 4 MANDATORY SHOWCASE CASES (GROUND TRUTH EVIDENCE & REASONING)

### Case 1: Corroborated Fact Across Documents (Expressed Differently)

#### Instance A (Delhivery Corporate Dataset)
* **Fact Concept**: Delhivery Limited Consolidated Revenue from Operations for FY24 (Year ended March 31, 2024).
* **Document 1 Evidence**:
  - *Source*: `02-delhivery-annual-report-fy24-excerpt.pdf`, Page 22 (Directors' Report).
  - *Verbatim Text*: `Consolidated – FY ended March 31, 2024: Revenue from Operations 81,415.38 (₹ in Million)`.
* **Document 2 Evidence**:
  - *Source*: `03-delhivery-q4-fy24-earnings-presentation.pdf`, Page 9 & Page 14.
  - *Verbatim Text*: `Revenue from services (₹ Cr) FY24: 8,142`.
* **System Reasoning**:
  - Normalize units: ₹ 81,415.38 Million * (1 Cr / 10 Million) = ₹ 8,141.538 Cr.
  - Apply standard corporate rounding rules: ₹ 8,141.538 Cr rounds to ₹ 8,142 Cr.
  - Match Entity (`Delhivery Limited`), Temporal Scope (`FY24 / 2023-24`), and Accounting Boundary (`Consolidated`).
  - **Verdict: CORROBORATED (Confidence: 0.99)**.

#### Instance B (India Macroeconomy Dataset)
* **Fact Concept**: India's Foreign Exchange Reserves as of March 2025.
* **Document 1 Evidence**:
  - *Source*: `02-rbi-annual-report-2024-25-excerpt.pdf`, Page 12 (Paragraph I.23).
  - *Verbatim Text*: `ample forex reserves at US$ 668.3 billion (as at end-March 2025)`.
* **Document 2 Evidence**:
  - *Source*: `03-imf-india-2025-article-iv-excerpt.pdf`, Page 12 (Paragraph 10).
  - *Verbatim Text*: `foreign exchange (FX) reserves declined to  billion in March 2025`.
* **System Reasoning**:
  - Entity: `India (National Central Bank Reserves)`.
  - Date: `March 2025 / end-March 2025`.
  - Value: 668.3 Billion USD ≈ 668 Billion USD.
  - **Verdict: CORROBORATED (Confidence: 0.98)**.

---

### Case 2: Genuine or Likely Contradiction

#### Instance A (India Macroeconomy Dataset)
* **Fact Concept**: Reserve Adequacy / Months of Import Cover for India's Foreign Exchange Reserves at March 2025.
* **Document 1 Evidence**:
  - *Source*: `02-rbi-annual-report-2024-25-excerpt.pdf`, Page 12.
  - *Verbatim Text*: `ample forex reserves at US$ 668.3 billion (as at end-March 2025), covering 11 months of merchandise imports`.
* **Document 2 Evidence**:
  - *Source*: `03-imf-india-2025-article-iv-excerpt.pdf`, Page 12.
  - *Verbatim Text*: `FX reserves stood at  billion as of October, covering over eight months of prospective imports`.
* **System Reasoning**:
  - If a user queries: *"How many months of imports do India's forex reserves cover?"*, Document 1 asserts **11 months**, while Document 2 asserts **8 months**.
  - While caused by differing underlying denominator scopes (merchandise only vs. prospective goods & services), neither document provides a bridging mathematical formula to convert between the two. To an end consumer, this is a **Likely Contradiction in stated buffer adequacy** that requires highlighting the conflicting assertions.
  - **Verdict: GENUINE / LIKELY CONTRADICTION (Definitional Incompatibility)**.

#### Instance B (Delhivery Dataset)
* **Fact Concept**: Baseline Headcount / Total Workforce Size.
* **Document 1 Evidence**:
  - *Source*: `01-delhivery-prospectus-2022-excerpt.pdf`, Page 42, Note 8.
  - *Verbatim Text*: `Includes permanent employees and contractual manpower (excluding daily wage manpower and security guards and Spoton)`.
* **Document 2 Evidence**:
  - *Source*: `02-delhivery-annual-report-fy24-excerpt.pdf`, Page 2, Note 5.
  - *Verbatim Text*: `Workforce strength: 98,135. Includes permanent employees, contractual workers and last mile deliver partner agents`.
* **System Reasoning**:
  - The metrics cannot be directly subtracted or compared because the baseline inclusions directly contradict (exclusion of daily-wage & partner agents in Doc 1 vs. explicit inclusion of last-mile partner agents in Doc 2).
  - **Verdict: LIKELY CONTRADICTION (Incompatible Population Baselines)**.

---

### Case 3: Apparent Contradiction Explained by Context

#### Dimension 1: Scope (Standalone vs. Consolidated)
* **Fact Concept**: Delhivery Revenue from Operations in Financial Year 2023-24.
* **Apparent Conflict**:
  - Source A (`02-delhivery-annual-report-fy24-excerpt.pdf`, p. 22) states Revenue is **₹ 74,540.82 Million**.
  - Source B (`03-delhivery-q4-fy24-earnings-presentation.pdf`, p. 9) states Revenue is **₹ 8,142 Crore** (₹ 81,415.4 Million).
* **Context Resolution**:
  - Source A is quoting **Standalone Financials** (the single legal parent entity).
  - Source B is quoting **Consolidated Financials** (parent + Spoton + subsidiary freight units).
  - In Source A on the very same page, Consolidated Revenue is indeed listed as ₹ 81,415.38 Million.
  - **Verdict: RECONCILED BY SCOPE (Standalone vs Consolidated)**.

#### Dimension 2: Accounting Metric (Operating EBITDA vs. Statutory Net Loss)
* **Fact Concept**: Delhivery Financial Profitability in FY24.
* **Apparent Conflict**:
  - Source A (`03-delhivery-q4-fy24-earnings-presentation.pdf`, p. 4) declares: *"FY24: EBITDA profitable (+₹ 76 Cr)"*.
  - Source B (`02-delhivery-annual-report-fy24-excerpt.pdf`, p. 22) reports: *"Loss for the year: ₹ (2,491.86) Million"*.
* **Context Resolution**:
  - Source A measures **Adjusted EBITDA** (cash profit from operations before interest, tax, depreciation, amortization, and ESOP costs).
  - Source B measures **Statutory Net Profit After Tax (PAT)** under Ind AS, which deducts ₹ 8,825 Cr of depreciation, amortization, and exceptional items. Both statements are accurate within their respective accounting frameworks.
  - **Verdict: RECONCILED BY METRIC DEFINITION (EBITDA vs Net Loss)**.

#### Dimension 3: Temporal Progression (Point-in-Time Changes)
* **Fact Concept**: Status and Role of Pooja Gupta.
* **Apparent Conflict**:
  - Source A (`01-delhivery-prospectus-2022-excerpt.pdf`, p. 97–98) records Pooja Gupta as active **Chief People Officer** of Delhivery.
  - Source B (`02-delhivery-annual-report-fy24-excerpt.pdf`, p. 41) states Pooja Gupta is **no longer associated** with the company, and Suraj Saharan is Chief People Officer.
* **Context Resolution**:
  - Prospectus was dated May 2022.
  - Annual Report was dated for the year ended March 31, 2024.
  - Footnote 3 on Page 41 explicitly records the date of cessation of association.
  - **Verdict: RECONCILED BY TIME (Executive Resignation / Transition)**.

#### Dimension 4: Methodology (Above-the-Line vs. Below-the-Line Receipts)
* **Fact Concept**: India Central Government Fiscal Deficit for FY24/25.
* **Apparent Conflict**:
  - Source A (Union Budget / Authorities) reports **4.9% of GDP**.
  - Source B (`03-imf-india-2025-article-iv-excerpt.pdf`, p. 16) reports **5.0% of GDP**.
* **Context Resolution**:
  - IMF Footnote 1 explains that Indian authorities include state asset sales / disinvestment proceeds as "miscellaneous capital receipts" (above-the-line revenue), reducing the apparent deficit by 0.1%.
  - IMF classifies disinvestment proceeds as "below-the-line financing".
  - **Verdict: RECONCILED BY METHODOLOGY (Disinvestment Accounting)**.

---

### Case 4: Extraction or Reasoning Failure & Mitigation Strategy

#### Failure Mode 1: Table Column Deserialization in Multi-Period Financials
* **The Failure**:
  - When parsing PDF tables with negative numbers in parentheses across quarterly columns (e.g. `03-delhivery-q4-fy24-earnings-presentation.pdf` p. 14, Adjusted EBITDA), standard PDF text extractors strip tabular bounding boxes and dump sequential numbers:
    `Revenue from customers 1,746 1,796 1,824 1,860 1,930 1,942 2,194 2,076 7,225 8,142`
    `Adjusted EBITDA (217) (125) (67) 6 (25) (13) 92 21 (404) 76`
  - A naive extraction agent misaligns `(404)` with `Q4 FY24` rather than recognizing it as the full-year `FY23` aggregate, or drops the parentheses and parses `(217)` as positive `217`.
* **System Handling & Improvement**:
  - Implement a **coordinate-aware or Markdown table reconstruction pipeline** that clusters tokens by horizontal y-bands and vertical x-ranges before fact extraction.
  - Pre-parse parenthetical numbers: regex transform `\(([0-9,.]+)\)` to `-`.
  - Validate that row lengths match column header counts before emitting financial facts.

#### Failure Mode 2: Footnote Marker Appending
* **The Failure**:
  - In `02-delhivery-annual-report-fy24-excerpt.pdf` p. 2, the text contains `>2.8Bn(1)` and `18,793(1)`.
  - Naive text extractors extract `18,7931` (187,931) or `2.81 Bn`, creating astronomical false metrics.
* **System Handling & Improvement**:
  - Apply clean lexical sanitization: strip superscript numbers and parenthetical citations `\(\d+\)` following numbers before numeric value extraction.
  - Maintain the stripped marker as a reference link to the footnotes at the bottom of the page.

---

## 5. FACT KNOWLEDGE LAYER: DATA MODEL & MATHEMATICAL FORMALIZATION

Every fact is represented not as loose text, but as a strongly typed fact tuple:

57017\mathcal{F} = \langle 	ext{id}, 	ext{entity}, 	ext{metric}, \mathcal{V}, \mathcal{T}, \mathcal{S}, \mathcal{E} angle57017

### 5.1 Formal Schema Specification (TypeScript / Pydantic)

```typescript
interface NormalizedValue {
  raw_value: string;             // e.g. "81,415.38"
  numeric_value: number | null;  // e.g. 81415.38
  raw_unit: string;              // e.g. "₹ in Million"
  normalized_unit: string;       // e.g. "INR"
  normalized_magnitude: number;  // e.g. 81415380000 (standardized scale)
  data_type: "currency" | "volume" | "percentage" | "count" | "semantic_statement";
}

interface TemporalScope {
  kind: "point_in_time" | "fiscal_year" | "quarter" | "multi_year_range";
  start_date?: string;           // ISO 8601: "2023-04-01"
  end_date: string;              // ISO 8601: "2024-03-31"
  label: string;                 // e.g. "FY24 (Year ended March 31, 2024)"
}

interface ContextScope {
  accounting_basis?: "standalone" | "consolidated" | "pro_forma" | "adjusted";
  reporting_standard?: "Ind_AS" | "IFRS" | "IMF_GFS" | "Union_Budget";
  metric_definition?: string;    // e.g. "Adjusted EBITDA excluding corporate overheads"
  population_scope?: string;     // e.g. "Including partner agents" vs "Excluding daily wage"
}

interface SourceEvidence {
  document_id: string;          // e.g. "02-delhivery-annual-report-fy24-excerpt.pdf"
  page_number: number;          // 1-indexed PDF page (e.g. 22)
  verbatim_quote: string;       // Verbatim text from PDF
  bounding_context?: string;    // Surrounding section header or table name
}

interface Fact {
  id: string;                   // UUID v4
  entity: string;               // e.g. "Delhivery Limited"
  metric_name: string;          // e.g. "Revenue from Operations"
  value: NormalizedValue;
  temporal_scope: TemporalScope;
  context_scope: ContextScope;
  evidence: SourceEvidence;
  confidence: number;           // 0.0 - 1.0
}
```

### 5.2 Cross-Document Relationship Model

```typescript
type RelationType = 
  | "CORROBORATED" 
  | "GENUINE_CONTRADICTION" 
  | "RECONCILED_TEMPORAL" 
  | "RECONCILED_SCOPE" 
  | "RECONCILED_UNIT" 
  | "RECONCILED_METHODOLOGY";

interface CrossDocumentLink {
  id: string;
  source_fact_id: string;
  target_fact_id: string;
  relation_type: RelationType;
  reconciliation_explanation: string;
  mathematical_delta?: number;
  confidence: number;
}
```

---

## 6. END-TO-END SYSTEM ARCHITECTURE

```mermaid
flowchart TB
    subgraph Ingestion Layer
        PDF[Raw PDFs Ingested] --> Extractor[PDF Parser: Text & Table Stream]
        Extractor --> Cleaner[Footnote & Parenthesis Sanitizer]
        Cleaner --> Chunker[Context-Aware Chunking: Headings & Tables]
    end

    subgraph Fact Extraction & Grounding
        Chunker --> LLMExtract[Dynamic Fact Extractor LLM Prompt]
        LLMExtract --> Validator[Zod / Pydantic Schema Validator]
        Validator --> Normalizer[Unit & Temporal Standardizer]
    end

    subgraph Fact Store
        Normalizer --> FactDB[(Structured Fact Store: SQLite / JSON)]
        Normalizer --> Embeddings[(Vector Index: ChromaDB)]
    end

    subgraph Cross-Document Reconciliation Engine
        FactDB --> Matcher[Candidate Fact Pair Matcher: Entity + Metric]
        Matcher --> ScopeGate{Temporal & Scope Match?}
        ScopeGate -- Identical Scopes & Values Match --> Corrob[Flag: Corroborated]
        ScopeGate -- Identical Scopes & Values Diverge --> Contradict[Flag: Genuine Contradiction]
        ScopeGate -- Scopes Diverge --> Resolver[Context Resolution Engine]
        Resolver -- Explained by Time, Scope, Unit --> Reconciled[Flag: Reconciled by Context]
    end

    subgraph Presentation & UI Layer
        Corrob --> API[FastAPI Endpoints]
        Contradict --> API
        Reconciled --> API
        API --> UI[Interactive Next.js / Vite React Dashboard]
    end
```

---

## 7. CROSS-DOCUMENT RECONCILIATION ENGINE (ALGORITHMS & RULES)

When two facts F1 and F2 have matching or highly similar entities and matching metrics:

### Step 1: Unit & Value Normalization
Convert both values into standard scientific base units:
57017V_{norm} = 	ext{numeric\_value} 	imes 	ext{unit\_multiplier}57017
- If delta V = |V1 - V2| / max(V1, V2) <= 0.015 (within 1.5% tolerance for corporate rounding):
  - Check scopes. If temporal and accounting scopes match:
    **--> CORROBORATED**

### Step 2: Temporal Scope Analysis
- If T1 != T2:
  delta t = |T1.end_date - T2.end_date| > 0
  **--> RECONCILED_TEMPORAL**
  *Reasoning*: Difference explained by longitudinal progression across reporting periods (e.g. Dec 2021 vs. March 2024 PIN code reach).

### Step 3: Accounting Boundary & Perimeter Analysis
- If T1 == T2, but S1.basis != S2.basis (e.g. Standalone vs Consolidated):
  **--> RECONCILED_SCOPE**
  *Reasoning*: Difference explained by corporate consolidation perimeter (subsidiaries vs standalone parent).

### Step 4: Metric Definition & Categorical Analysis
- If T1 == T2 and S1.basis == S2.basis, but definitions differ (e.g. Adjusted EBITDA vs PAT or Merchandise import cover vs Prospective imports):
  **--> RECONCILED_METHODOLOGY**
  *Reasoning*: Divergence explained by metric calculation criteria.

### Step 5: Residual Genuine Contradiction
- If T1 == T2, S1 == S2, M1 == M2, and delta V > 0.05 with no documented perimeter shift:
  **--> GENUINE_CONTRADICTION**
  *Reasoning*: Direct factual or empirical conflict between sources.

---

## 8. FAILURE MODES, EDGE CASES, AND MITIGATION (CASE 4 IN-DEPTH)

| Edge Case / Failure Mode | Why It Occurs in PDFs | Concrete Dataset Example | System Handling & Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Negative Number Loss** | Financial tables use accounting parentheses `(217)` instead of `-217`. Raw PDF text streams strip syntax. | Delhivery Earnings Deck p. 14 (`Adjusted EBITDA (217)`) | Pre-tokenization regex transforms `\(([0-9,.]+)\)` to `-`. |
| **Footnote Ingestion** | Superscript footnote markers follow numbers without spaces (e.g. `18,793(1)`). | Delhivery AR p. 2 (`>2.8Bn(1)`, `18,793(1)`) | Lexical tokenizer separates numerical digits from trailing parenthetical tokens. |
| **Multi-Column Column Shift** | PDF text extraction reads row-by-row across columns, interleaving quarterly figures. | Delhivery Deck p. 15 (Service lines across 8 quarters) | Extract tables using coordinate bounding-box algorithms (`pdfplumber` / spatial heuristics). |
| **Dual Fiscal Conventions** | Documents intermingle `FY24`, `2023-24`, `FY2024/25`, and `CY24`. | Economic Survey vs IMF Article IV | Standardized ISO interval mapper: maps all Indian FY notation to `[YYYY-04-01, YYYY+1-03-31]`. |
| **Disinvestment Line Mismatch** | Authorities treat asset sales above-the-line; IMF treats them below-the-line. | IMF Article IV p. 16 (4.9% vs 5.0% deficit) | Knowledge layer extracts footnote commentary and classifies methodology divergence. |

---

## 9. BROWNIE POINTS STRATEGY: SCALING, DYNAMIC SCHEMA & INCREMENTAL UPDATES

The assignment specifically calls out 4 bonus extensions:

### 1. Large PDFs Without Performance Bottlenecks
* **Challenge**: 100-page financial filings are too large for single LLM context windows and cost-prohibitive.
* **Architecture Solution**:
  - Two-tier processing:
    1. **Structural Table-of-Contents & Executive Summary Extractor**: Screens pages for high-density fact sections (Financial Statements, Operating Metrics, KMP profiles).
    2. **Sliding Window Chunking with Overlap**: Chunks are processed in parallel asynchronous batches using thread pools.

### 2. Many PDFs in the Same Knowledge Layer
* **Challenge**: Pairwise comparison of facts scales quadratically O(N^2).
* **Architecture Solution**:
  - Partition facts by `(Normalized Entity, Normalized Metric Class)`.
  - Only execute the deep reconciliation engine on matching clusters, bringing comparison time down to O(N log N).

### 3. Dynamic Schema Evolution
* **Challenge**: New documents contain facts that were not pre-configured (e.g. ESG carbon emissions, board meeting counts, sovereign credit ratings).
* **Architecture Solution**:
  - Zero hardcoded Enum restrictions.
  - The extraction prompt instructs the LLM to dynamically generate `metric_name` and `data_type` based solely on the document context.
  - An embedding-based deduplication layer clusters similar metric labels into canonical concepts.

### 4. Incremental Ingestion Without Rebuilding
* **Challenge**: Uploading a new PDF shouldn't re-extract or wipe previous documents.
* **Architecture Solution**:
  - Immutable Fact Store: Facts from Doc A and Doc B remain untouched.
  - When Doc C is uploaded, the system only extracts facts F_C and runs cross-document matching against existing facts F_A union F_B.

---

## 10. SUBMISSION & EVALUATION CHECKLIST

Updated from the official `superjoin-vit-2026-assignment.pdf` (verbatim from "Before You Submit"):

```markdown
- [x] The project runs from README instructions and accepts new PDFs through an API or UI.
- [x] Results contain facts, source evidence, and cross-document relationships.
- [x] All 4 required cases demonstrated (Corroborated, Contradiction, Reconciled, Failure).
- [x] Approach documented + demo video ≤ 3 minutes included: [Watch Video](https://drive.google.com/file/d/1rzCIw4Oeyoii2epKI63uCocfFp4S6LpG/view?usp=sharing)
- [x] GitHub repository link: https://github.com/IronLad123/claimsmap
- [x] No credentials committed to the repository.
- [x] Sample data included so evaluator can run without external API keys.
```

---

## 11. PDF ASSIGNMENT CROSS-REFERENCE & UPDATED DECISIONS

> **Source**: `superjoin-vit-2026-assignment.pdf` extracted 2026-09-08 via PyPDF (2 pages, 96,531 bytes).

### 11.1 Verbatim North Star Quotes from the PDF

These 4 sentences from the PDF override any assumption made earlier:

1. *"A smaller, understandable prototype is better than a large system whose behavior is unclear."*  
   → **Action**: Scoped frontend to 3 pages only. Removed force-graph visualization page.

2. *"The interesting part is how facts are discovered, grounded, compared, and **explained**."*  
   → **Action**: `reconciliation_explanation` prose field is mandatory and displayed front-and-center in every showcase card. Relation type badges alone are insufficient.

3. *"A graph database or visualization alone is not the solution."*  
   → **Action**: No force-graph or network visualization page. `/compare` explanation quality is the deliverable.

4. *"Keep credentials out of the repository. If the project requires a paid service, include enough sample output and video footage for us to evaluate it without needing your account."*  
   → **Action**: `data/sample_facts.db` and `data/sample_facts.json` committed to git. Backend serves from these files if `GEMINI_API_KEY` is absent (`DEMO_MODE=true`).

---

### 11.2 What brain.md Got Exactly Right (Confirmed by PDF)

| brain.md Assumption | PDF Confirmation | Status |
| :--- | :--- | :--- |
| 4 showcase cases with exact descriptions | Word-for-word match | ✅ Confirmed |
| Zero hardcoded schemas/filenames/rules | "should not rely on hard-coded facts, filenames, schemas, or document-specific rules" | ✅ Confirmed |
| Graph viz not the answer | "A graph database or visualization alone is not the solution" | ✅ Confirmed |
| Generalizability to arbitrary PDFs | "We may test your solution with additional PDFs" | ✅ Confirmed |
| Evidence citation mandatory | "Show the source evidence and your system's reasoning" | ✅ Confirmed |
| All 4 brownie points identified | Large PDFs, many PDFs, dynamic schema, incremental ingestion | ✅ All 4 match |
| Use any language/framework/LLM | "Use any language, framework, database, LLM, coding agent, or library" | ✅ Confirmed |
| Approach > polish | "We care more about your approach and creativity than production-level polish" | ✅ Confirmed |

---

### 11.3 What Changed Post-PDF Read

| Item | Previous Assumption | Updated Decision |
| :--- | :--- | :--- |
| Frontend pages | 4 pages (incl. `/graph`) | **3 pages** — `/`, `/facts`, `/compare` only |
| Evaluator API key | Assumed available | **No-API-key demo mode** via `data/sample_facts.db` |
| Explanation display | Badge label sufficient | **Full prose explanation required** per PDF rubric |
| Submission checklist | brain.md §10 (inferred) | **Replaced with verbatim PDF checklist** |
| `seed_showcase.py` | Nice-to-have | **Mandatory** — committed output is primary evaluator path |

---

### 11.4 Rubric Mapping to System Components

| PDF Evaluation Criterion | System Component That Satisfies It |
| :--- | :--- |
| "Thoughtful and creative approach" | 5-step deterministic reconciliation engine (not black-box LLM) |
| "Facts grounded in the PDFs" | `verbatim_quote` field mandatory; page citations on every fact |
| "Sensible handling of ambiguity" | `context_scope` + `accounting_basis` + `confidence` on every fact |
| "Solution that generalizes beyond starter docs" | Dynamic `metric_name` (no enum), SHA256-based incremental ingestion |
| "Clear engineering decisions and trade-offs" | README §Approach section + `brain.md` as public design doc |
| "Explain — not just label" | `reconciliation_explanation` prose shown in `/compare` showcase cards |

---

### 11.5 Architecture Decisions Locked In

Based on full PDF + domain analysis, these decisions are final:

1. **Text extraction before LLM**: `pdfplumber` + `PyMuPDF` locally → sanitized text → Gemini. Never raw PDF bytes.
2. **Deterministic classification**: The 5-step reconciliation algorithm uses pure Python rules. LLM only generates the *explanation sentence* — never the verdict.
3. **SQLite over vector-first**: SQLite is the primary store. ChromaDB is optional (semantic search bonus). Evaluators can inspect the `.db` file directly with any SQLite browser.
4. **3-page lean frontend**: Home (upload) → Facts (browse) → Compare (showcase). Every evaluator action reachable in ≤ 2 clicks.
5. **Seeded demo data committed**: `data/sample_facts.db` contains all 10 showcase fact pairs pre-loaded. No API key required to demonstrate the 4 mandatory cases.

---
*Brain document v2 — grounded against official assignment PDF + 6 starter dataset PDFs + cross-document forensic analysis.*

# Financial Agent

## Information

# 📄 Private Equity Investor Agent – Data Collection Guide

This document outlines the structure, questions, and expected data fields for an agent designed to retrieve company information for private equity investors.

## Most important features

- Email to send when no answer is provided
- Agent to check confidence levels
- "We don't have Artefacto, only about "Artefact" -> I will bring info about the 

---

## 🏢 Company Fundamentals

| ID          | Question                                                                 | Field               | Data Source / Hint             | Answer Format             |
|-------------|--------------------------------------------------------------------------|---------------------|-------------------------------|---------------------------|
| O.DES.NAM   | What is the name of your company?                                        | Company Name        | Project name                  | Text                      |
| O.DES.REV   | What was the revenue of your company in the most recent financial year?  | Revenue             | Look at turnover              | Numeric                   |
| O.DES.CUR   | Please state the currency and unit of the revenue above                  | Currency            | e.g., mEUR or tUSD            | Text                      |
| O.DES.IND   | What is your company’s primary industry classification (GICS IIII)?      | GICS Sub-industry   | Cross-reference with NACE     | Text (GICS code or name)  |

---

## 🌱 ESG Governance

| ID            | Question                                                                                     | Field                              | Data Source / Hint         | Answer Format               |
|----------------|----------------------------------------------------------------------------------------------|------------------------------------|-----------------------------|-----------------------------|
| O.POL.SUS      | Does your company have an overall policy on sustainability, ESG or similar?                 | Sustainability Policy              | Look at policies in place   | Yes/No + Optional Description |
| G.PRO.RESB.a   | Does your company have ESG responsibility at board level (person/committee/etc.)?           | Board ESG Oversight                | Check governance documents  | Yes/No                      |
| O.PRO.MAT      | Has your company assessed material ESG issues within the last 3 years?                      | Materiality Assessment             | ESG reports or policies     | Dropdown (Yes/No)           |
| O.PRO.MAT.a    | If yes, did the assessment include stakeholder engagement?                                  | Stakeholder Consultation           | Linked to above             | Dropdown (Yes/No)           |
| O.PRO.MAT.c    | If yes, list the topics assessed to be material.                                            | Material ESG Topics                | ESG reports or disclosures  | Text/list                   |

---

## 🔐 Cyber Security

| ID            | Question                                                                                      | Field                             | Data Source / Hint            | Answer Format                 |
|---------------|-----------------------------------------------------------------------------------------------|-----------------------------------|-------------------------------|-------------------------------|
| G.POL.CIS     | Does your company have a cyber/information security policy?                                  | Cyber Security Policy             | Check IT/security docs        | Yes/No + Optional Description |
| G.PRO.ITSM    | Does your company have an IT security management system in place?                            | IT Security Management System     | Cyber security documentation  | Yes/No                        |
| G.PRO.ITSM.c  | If yes, describe the key elements (certification, coverage, etc.).                           | IT Security System Details        | Same as above                 | Text                          |
| G.PRO.CIO     | Is there a CIO (or equivalent) responsible for information/cyber security?                   | Chief Information Officer         | Org chart or leadership page  | Yes/No + Optional Name/Title  |
| G.PER.CYBAT   | Has your company had significant cyber attacks or data breaches in the last 3 years?        | Cyber Attacks or Breaches         | Incident reports              | Yes/No                        |
| G.PER.CYBAT.a | If yes, briefly describe the incidents.                                                      | Cyber Attack Details              | Same as above                 | Text                          |

---

## 📝 Usage Guidelines

- **Agent Logic**:
  - Pull from structured documents (e.g., annual reports, sustainability reports, cyber policies).
  - Use NLP techniques to extract and normalize answers (e.g., classify GICS codes, standardize currencies).
  - Apply conditional logic (e.g., only ask follow-up questions if the previous answer was "Yes").

- **Answer Classification**:
  - Use tags like `B` (Basic), `O` (Operational), `CA` (Compliance-Aligned), `CM` (Compliance-Missing), etc., for internal tracking of completeness and maturity.

- **Fallback Strategy**:
  - If data is missing, tag with “No data” and recommend outreach or clarification request from the company.

---

## Questions Examples

1. What is the 


To run the docker image for PGVector, run the following command:

```
docker run \
  -e POSTGRES_DB=ai \
  -e POSTGRES_USER=ai \
  -e POSTGRES_PASSWORD=ai \
  -e PGDATA=/var/lib/postgresql/data/pgdata \
  -v pgvolume:/var/lib/postgresql/data \
  -p 5532:5432 \
  pgvector/pgvector:pg16
```

[Docs](https://docs.agno.com/agents/run)

## To-do
- Update RAG to be an [Agentic RAG](https://docs.agno.com/agents/knowledge#step-3%3A-agentic-rag)
- Create visual interface to allow users to interact with the agent,
- Make it read files that are inputed
- Create xlsx tool
- Use csv tools to analyze data (run query against it)


## Sample questions


## Business Rules Orientation

"""
'- If you are not able to answer a specific question or the question is not relevant for your company, please leave the answer field blank
- If you, for a given metric, only collect data for a part of your organization/activities, please elaborate in the 'Comment' section
- The red text highlights information important to ensure correct and consistent data 

"""


# AI Store Manager 🚀
> *"Your store has data. Your AI Store Manager turns it into decisions."*
# PayLens 🔍
> *"Instead of telling merchants that payments failed, PayLens tells them why they failed, how much transaction value is at risk, and what they should do next."*
**AI Store Manager** is a production-grade full-stack web application that acts as an **AI employee/manager for online sellers**. 
**Track**: Razorpay Buildathon – Open Track  
**Platform**: AI-Powered Payment Intelligence & Automated Root-Cause Investigation
Rather than merely presenting charts and tables, AI Store Manager operates on a 4-step decision paradigm:
---
## 1. Executive Summary & Problem Statement
### The Problem
Traditional payment analytics dashboards operate as reactive counters. They display raw counts of failed transactions, but fail to provide merchants with actionable answers to operational questions:
- **WHY** did payment failures suddenly surge? (Is it bank server latency, network drops, or customer card limits?)
- **WHICH** specific bank acquiring gateway or payment rail is impacted?
- **WHEN** did the degradation start, and is it actively worsening?
- **HOW MUCH** financial transaction exposure is currently at stake?
- **WHAT** concrete actions should the merchant operations team take immediately?
### The Solution: PayLens
**PayLens** is an AI Payment Investigator built directly for merchant operations. It continuously scans payment transaction streams, detects anomalous failure spikes and latency degradations using statistical variance models, computes the **Estimated Transaction Value at Risk**, and leverages Google Gemini (with an automated deterministic fallback) to deliver root-cause explanations and concrete mitigation recommendations.
---
## 2. Architecture & AI Engineering Principle
PayLens enforces a strict separation of concerns: **Python calculates facts; AI interprets the facts.**
```
Store Data ➔ AI Analysis ➔ Detect Problems ➔ Find Causes ➔ Generate Recommendations ➔ Seller Takes Action
               ┌────────────────────────────────────────────────────────┐
               │        RAW TRANSACTION STREAM (25,000 txns)            │
               │         backend/data/paylens_transactions.csv          │

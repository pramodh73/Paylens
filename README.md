AI Store Manager 🚀
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
               │           STRUCTURED EVIDENCE FACT SHEET               │
               │   • Window timeframe & drop percentage vs baseline     │
               │   • Affected failed transactions & ticket size metrics │
               │   • Dominant error code distribution                   │
               │   • Parallel contrast against other unaffected banks   │
               └───────────────────────────┬────────────────────────────┘
                                           │
                          ┌────────────────┴────────────────┐
                          ▼                                 ▼
             [GEMINI API KEY PRESENT]            [FALLBACK / OFFLINE]
             ┌──────────────────────┐         ┌─────────────────────────┐
             │  GOOGLE GEMINI API   │         │ DETERMINISTIC HEURISTIC │
             │  (gemini-2.5-flash)  │         │     STATISTICAL ENGINE  │
             └──────────┬───────────┘         └─────────────┬───────────┘
                        │                                   │
                        └─────────────────┬─────────────────┘
                                          ▼
               ┌────────────────────────────────────────────────────────┐
               │              AI INVESTIGATION PAYLOAD                  │
               │   1. Incident Executive Summary                        │
               │   2. Likely Root Cause Diagnosis                       │
               │   3. Observed Evidence (Facts) vs AI Interpretation    │
               │   4. Business Impact Statement                         │
               │   5. Actionable Merchant Recommendations               │
               │   6. Confidence Score                                  │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │           REACT + TAILWIND FINTECH DASHBOARD           │
               │   • Real-time KPIs & Recharts Telemetry Visualizations │
               │   • Ranked Incidents Cards with Direct Deep-Dive Modal │
               │   • Filterable & Paginated Transaction Explorer        │
               │   • Interactive Merchant AI Assistant Drawer           │
               └────────────────────────────────────────────────────────┘
```
---
Key Innovations & Features
## 3. Key Features
### 1. ☀️ Proactive Daily Store Briefing
Acts like a dedicated AI employee providing your morning briefing with 4 prioritized items:
* 🚨 **Restock Risk**: Wireless Earbuds ANC (2.2 days remaining)
* ⚠️ **Sales Investigation**: Black Running Shoes (-23% sales drop)
* ⭐ **Customer Voice**: Sizing complaints spike (+32% in 30 days)
* 📈 **Growth Opportunity**: Smart Watch Pro (+31% momentum with ready stock)
### 1. 📊 Executive Payment Health Dashboard
- **Total Transactions**: Aggregated count, volume, and latency across 25,000 transactions.
- **Platform Success Rate**: Visual health meter with success/failure distributions.
- **Estimated Transaction Value at Risk**: Transparent metric calculating total financial exposure during anomalous incidents without overclaiming actual lost revenue.
### 2. 🛡️ 360° AI Store Health Diagnostic (82/100)
Composite health score broken down into 5 critical dimensions:
* **Sales Performance**: 87/100
* **Customer Satisfaction**: 79/100
* **Inventory Health**: 91/100
* **Pricing Competitiveness**: 76/100
* **Product Performance**: 83/100
Accompanied by an explainable AI narrative diagnosis.
### 2. 🚨 Statistical Anomaly Detection Engine
- Monitors payment methods (`UPI`, `Card`, `Netbanking`, `Wallet`) and acquiring banks (`HDFC`, `ICICI`, `SBI`, `Axis`, `Kotak`, `Yes Bank`).
- Evaluates deviations against rolling baselines:
  - Sudden success-rate drop ($\Delta \ge 14\%$)
  - Failure-rate surge
  - Latency degradation ($\mu_{\text{proc}} > \text{baseline} + 1.5\sigma$)
  - Error code concentration (e.g. `GATEWAY_TIMEOUT` surges)
- Assigns severity scores: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`.
- Translates statistical evidence into natural merchant intelligence.
- **Strict Distinction**: Clearly separates **Observed Evidence** (hard numbers and baseline deltas) from **AI Interpretation** (inferences on gateway behavior).
- **Graceful Fallback**: If `GEMINI_API_KEY` is not provided or fails, automatically switches to the built-in deterministic statistical engine, signaling with `"AI unavailable — showing deterministic investigation."`
### 4. ⭐ Customer Voice & Review Intelligence
Analyzes 150+ verified customer reviews into aspect clusters:
* **Sentiment Ratio**: 76% Positive, 14% Neutral, 10% Negative
* **Emerging Issue**: ⚠️ Sizing complaints up 32% in Footwear
* **Aspect breakdown**: Comfort (94% Pos), Design (91% Pos), Battery (89% Pos), Sizing (18% Pos)
### 4. 🗂️ High-Performance Transaction Explorer
- Search by `transaction_id`, `customer_id`, or `bank`.
- Filters by Bank, Payment Method, Status (`success` / `failed`), and Error Code.
- Server-side backend pagination designed to scale smoothly with tens of thousands of rows.
### 5. 📦 Inventory Velocity & Stockout Runway Forecasting
* Calculates exact depletion runways based on daily sales velocity.
* Highlights imminent stockouts (e.g. Wireless Earbuds ANC with 2.2 days left).
* Interactive Stock Burndown Curve with 1-click Restock Purchase Order simulator.
### 5. 💬 Merchant AI Assistant Drawer
- Interactive in-dashboard panel answering merchant operational questions:
  - *"What is the biggest payment issue right now?"*
  - *"Which bank has the highest failure rate?"*
  - *"How much transaction value is currently at risk?"*
  - *"What should the merchant investigate first?"*
- Answers are strictly grounded in calculated dataset evidence.
### 6. 💰 Pricing Competitiveness & Elasticity Matrix
* Real-time price gap benchmarking against competitor averages (FleetRun, AcroFit, NovaTech).
* Safe price elasticity test recommendations with estimated conversion recovery.
---
### 7. 📢 Marketing Opportunities & AI Ad Campaign Generator
* Identifies high-margin, trending products with ready stock (Smart Watch Pro).
* Generates full marketing kits: Promotional hooks, Instagram caption with hashtags, Google/Meta ad headlines, email copy, and discount codes.
## 4. "Estimated Transaction Value at Risk" Terminology
### 8. 🤖 "Ask your AI Manager" Conversational Co-Pilot
Interactive assistant answering complex questions using live store data:
* *"Why did my sales drop this week?"*
* *"Which products should I promote?"*
* *"Which products are at risk of running out?"*
* *"What are customers complaining about?"*
* *"Should I reduce the price of my running shoes?"*
* *"Give me today's priorities."*
PayLens adheres to an explicit fintech engineering guideline: **Never confuse transaction value at risk with actual lost revenue.**
## 🏆 3-Minute Hackathon Demo Flow
## 5. Tech Stack
1. **Step 1 — Store Health**: Open dashboard to show **Store Health (82/100)** and morning briefing.
2. **Step 2 — Spot Alert**: Point to the 🚨 **"Black Running Shoes sales dropped 23%"** alert.
3. **Step 3 — Investigate Root Causes**: Click alert to reveal the multi-factor diagnostic (Competitor price ₹200 lower, sizing complaints up 18%, conversion drop from 4.2% → 3.1%).
4. **Step 4 — Take Action**: Click **"Apply Recommended Price ₹2,199"** and observe live toast feedback.
5. **Step 5 — Customer Voice**: Open **Customer Voice** tab to demonstrate the **32% sizing complaint spike**.
6. **Step 6 — Inventory Runway**: Open **Inventory** tab to view Wireless Earbuds reaching stockout in 2.2 days and trigger a restock PO.
7. **Step 7 — AI Manager Co-pilot**: Open **AI Manager Chat** and ask *"What should I focus on today?"* to get prioritized action recommendations.
8. **Step 8 — Campaign Generator**: Open **Marketing** tab and generate complete ad copy for **Smart Watch Pro**.
| Layer | Technologies |
| :--- | :--- |
| **Backend** | Python 3.12, FastAPI, Uvicorn, Pandas, NumPy, Scikit-learn, Pydantic v2, Python-dotenv |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Lucide React, Recharts |
| **AI / LLM** | Google Gemini (`google-genai` SDK / `gemini-2.5-flash`), Rule-based Fallback Engine |
| **Dataset** | 25,000 synthetic transaction records (`paylens_transactions.csv`) |
---
## 🛠️ Architecture & Tech Stack
## 6. Dataset Structure
The dataset is expected at:
```
ai-store-manager/
├── backend/                  # FastAPI Multi-Agent Backend
│   ├── agents/
│   │   ├── manager_agent.py   # Synthesizer, Health Score, Briefing, Chat Co-pilot
│   │   ├── pricing_agent.py   # Competitor gap & Elasticity engine
│   │   ├── review_agent.py    # Sentiment & Emerging issue topic clustering
│   │   ├── inventory_agent.py # Velocity & Stockout runway projection
│   │   └── marketing_agent.py # Promotion scoring & Campaign copy generator
│   ├── data_store.py          # 28 Seed Products, 150+ Reviews, 30-Day Metrics
│   ├── models.py              # Pydantic data schemas
│   ├── main.py                # REST API Gateway
│   └── tests/test_api.py      # Automated endpoint tests (pytest)
│
└── frontend/                 # React 19 + Vite + TypeScript Frontend
    ├── src/
    │   ├── components/        # Navbar, Sidebar, KPICards, Briefing, Alerts, Modals
    │   ├── pages/             # Dashboard, Products, Reviews, Inventory, Pricing, Marketing, Chat
    │   ├── services/api.ts    # REST Client
    │   └── types/index.ts     # TypeScript Interfaces
    └── tailwind.config.js     # Custom design system tokens
backend/data/paylens_transactions.csv
- `amount`: Numeric transaction amount in INR
- `payment_method`: `UPI`, `Card`, `Netbanking`, `Wallet`
- `bank`: `HDFC`, `ICICI`, `SBI`, `Axis`, `Kotak`, `Yes Bank`
- `status`: `success` or `failed`
- `error_code`: `GATEWAY_TIMEOUT`, `BANK_DECLINED`, `INSUFFICIENT_FUNDS`, `NETWORK_ERROR` (empty for successful transactions)
- `processing_time_seconds`: Transaction processing latency (float)
- `customer_id`: Unique customer identifier (e.g. `CUST15501`)
---
## 🚀 Local Setup & Quickstart
## 7. Installation & Setup
### Prerequisites
* **Node.js**: v18+ (tested on v24.19)
* **Python**: v3.10+ (tested on v3.12)
- Python 3.10+
- Node.js 18+ and npm
### 1. Start the Backend API (FastAPI)
### 1. Clone & Navigate
```bash
git clone <repository-url>
cd paylens
```
### 2. Backend Setup
```bash
# Navigate to backend
cd backend
# (Optional) Create virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
# Install dependencies
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
# Configure Environment
# Copy .env.example to .env
cp .env.example .env
```
*Backend runs on: `http://127.0.0.1:8000` (API Docs at `http://127.0.0.1:8000/docs`)*
---
## 10. Hackathon 3–5 Minute Demo Flow
1. **Dashboard Overview**:
   - Open `http://localhost:5173`.
   - Highlight the 25,000 transactions and the 92.2% overall success rate.
   - Point out the **Estimated Transaction Value at Risk** KPI card with its clear disclaimer.
2. **Review Telemetry Visualizations**:
   - Show the daily volume trend, payment-method success rates, and bank decline distributions.
3. **Spot Active Payment Incident**:
   - Review the **Active Incidents** list. Notice `CRITICAL` incident on Kotak Netbanking or SBI UPI where success rate dropped to ~64-70%.
4. **Click "Investigate"**:
   - View the deep-dive diagnostic comparison:
     - Baseline Success Rate vs Incident Success Rate.
     - Affected transaction count and processing latency spike.
5. **AI Root-Cause Diagnosis**:
   - Review **Likely Root Cause**: Shows acquiring gateway latency degradation.
   - Highlight the side-by-side distinction: **Observed Evidence (Facts)** vs **AI Interpretation (Reasoning)**.
   - Note the **Recommended Action for Merchant**: Dynamic routing shift to alternative payment rails and escalation template.
   - Click **"Re-run Investigation"** to show real-time re-analysis.
6. **Ask AI Assistant**:
   - Click **"Ask AI Assistant"** in the top navbar.
   - Click quick prompt: *"What is the biggest payment issue right now?"*
   - Verify the assistant answers strictly using the calculated incident metrics without hallucinations.
7. **Transaction Ledger**:
   - Switch to **Transactions** tab to verify fast backend pagination and filtering.
---
## 11. Security & Best Practices
- **Zero Secret Leakage**: `backend/.env` is ignored by Git. No API keys are embedded in frontend source code, client builds, or API responses.
- **Fail-Safe Fallback**: Complete application functionality (anomaly detection, analytics, and root-cause investigations) runs without requiring external LLM API availability.
- **Performance Optimized**: Data is cached in memory with Pandas, eliminating disk read overhead on every query.
---
## 12. Limitations & Future Roadmap
- **Streaming Webhook Ingestion**: In production, integrate Kafka/RabbitMQ for sub-second webhook ingestion from Razorpay.
- **Automated Routing Execution**: Directly execute smart routing adjustments via Razorpay Optimizer APIs when an acquiring partner degrades.
- **Custom Merchant Anomaly Sensitivity**: Allow merchants to configure custom alerting thresholds per payment rail.

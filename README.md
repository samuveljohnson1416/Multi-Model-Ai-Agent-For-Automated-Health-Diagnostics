# Multi-Model-Ai-Agent-For-Automated-Health-Diagnostics
An Infosys Springboard Virtual Internship project that builds an AI system to extract data from blood reports using OCR, analyze key health parameters, detect abnormalities and patterns, and generate clear, personalized health insights through a multi-model pipeline.



---

# 🚀 **Multi-Model AI Agent for Automated Health Diagnostics**

An intelligent AI system that **reads blood reports**, analyzes medical patterns, detects risks, and generates **personalized health recommendations**.
Designed to go beyond simple command execution by **inferring user intent**, even when instructions are vague.

---

# 🧠 **Project Overview**

```
   .-----------------------------.
   |  AI HEALTH DIAGNOSTICS     |
   |    MULTI–MODEL ENGINE      |
   '-----------------------------'
           |   |    |
      -----'   |    '-----
     INPUT → ANALYSIS → OUTPUT
```

This system processes medical reports in **PDF, scanned image, or JSON format**, extracts parameters through OCR, analyzes them using **three cooperating AI models**, and produces a structured medical-style summary.

---

# ✨ **Key Features**

```
 .------------------------------------------------.
 |  • Intent Inference                             |
 |  • Multi-Model Medical Analysis                 |
 |  • OCR-Based Data Extraction                    |
 |  • Pattern Detection & Risk Assessment          |
 |  • Personalized Health Recommendations          |
 '------------------------------------------------'
```

* Understands user intent, not just literal text
* Detects abnormal values (high/low/borderline)
* Identifies combinations (lipid ratios, kidney markers)
* Generates advice based on findings and user profile

---

# 🔁 **System Workflow (ASCII Diagram)**

```
   .-------------------.       .-------------------.
   |   1. INPUT        |       |  2. EXTRACTION     |
   |  (PDF / Image)    | ----> |  OCR + Cleaning    |
   '-------------------'       '-------------------'
                |
                v
   .-------------------.
   | 3. AI MODELS      |
   |-------------------|
   | Model 1: Values   |
   | Model 2: Patterns |
   | Model 3: Context  |
   '-------------------'
                |
                v
   .-------------------.
   | 4. SYNTHESIS      |
   | Full Interpretation|
   '-------------------'
                |
                v
   .-------------------.
   | 5. OUTPUT REPORT  |
   | Summary + Advice  |
   '-------------------'
```

---

# 🧬 **Three-Model AI Analysis Engine**

```
   .--------------------------------------.
   |   MULTI–MODEL ANALYSIS UNIT          |
   |--------------------------------------|
   |  [Model 1] Parameter Interpretation   |
   |      ↓ Compare with reference ranges  |
   |--------------------------------------|
   |  [Model 2] Pattern Recognition        |
   |      ↓ Ratios, correlations, risks    |
   |--------------------------------------|
   |  [Model 3] Contextual Analysis        |
   |      ↓ Age, gender, lifestyle         |
   '--------------------------------------'
```

Each model contributes a unique layer of understanding:

### ✔ Model 1 – Baseline Interpretation

* Detects high, low, or borderline values
* Uses standard medical ranges

### ✔ Model 2 – Pattern Recognition & Risks

* Lipid ratios
* Kidney/liver function indicators
* Metabolic patterns

### ✔ Model 3 – Optional Contextual Model

* Adjusts interpretation using patient profile

---

# 🧩 **Architecture (ASCII Block Diagram)**

```
 .------------------------------------------------------------.
 |                   SYSTEM ARCHITECTURE                      |
 |------------------------------------------------------------|
 | Input Parser | OCR Engine | Validator | Orchestrator       |
 |------------------------------------------------------------|
 | Model 1 | Model 2 | Model 3 | Synthesis Engine             |
 |------------------------------------------------------------|
 | Recommendation Engine | Report Generator                   |
 '------------------------------------------------------------'
```

Core components include:

* **Input Interface** – PDFs, images, JSON
* **OCR Extraction Engine** – pulls values + units
* **Validation Module** – ensures clean, standardized data
* **AI Models (1–3)** – perform multi-level medical reasoning
* **Findings Synthesizer** – merges insights
* **Recommendation Engine** – generates personalized advice
* **Report Renderer** – formats final output



---

# 📄 **End-to-End Summary (Visual Text Format)**

```
 INPUT → OCR → CLEANING → AI ANALYSIS → FINDINGS → ADVICE → REPORT
```

### What the system ultimately delivers:

* A readable health summary
* Highlighted abnormalities
* Detected medical patterns
* Personalized lifestyle/diet recommendations
* Disclaimer-based final report

---


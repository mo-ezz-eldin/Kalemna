# 🤖 AI Customer Support Orchestrator

A production-grade, modular AI-powered customer support system built with a **Clean Architecture** approach. This system leverages **LangGraph** to manage complex conversational workflows, ensuring deterministic routing, error correction, and robust data extraction.

---

# 🏗️ Architecture Overview

The project follows a **Clean Architecture** pattern to ensure separation of concerns, maintainability, and scalability.

### Project Layers

- **`application/`**
  - Orchestrates the business logic.
  - Contains LangGraph workflows.
  - Stores prompt templates.
  - Handles routing and decision-making.

- **`config/`**
  - System-wide configurations.
  - Intent metadata.
  - Action mappings.
  - Constants.

- **`domain/`**
  - Business contracts (interfaces).
  - Independent of implementation.
  - Defines abstractions such as:
    - `ITextClassifier`
    - `ITextCorrector`
    - `ISentimentAnalyzer`
    - `INERExtractor`

- **`infrastructure/`**
  - AI model implementations.
  - NLP preprocessing.
  - Spell correction.
  - External services and utilities.
  - Hugging Face models.

- **`presentation/`**
  - FastAPI endpoints.
  - Dependency Injection.
  - Request/Response schemas.

---

# 📂 Directory Structure

```text
src/
├── application/                 # Business orchestration
│   ├── graphs/                  # LangGraph nodes, edges, state & schemas
│   ├── prompts/                 # Prompt templates
│   ├── orchestrator/            # Workflow orchestrator
│   ├── decision_maker/          # Routing & decision logic
│   └── ...
│
├── config/                      # Intent metadata, mappings & constants
│
├── domain/                      # Abstract interfaces (Clean Architecture)
│
├── infrastructure/              # AI models & preprocessing implementations
│
└── presentation/                # FastAPI API layer
```

---

# 🛠️ Tech Stack

## Orchestration

- LangGraph
- LangChain

Used to build deterministic, stateful conversational workflows.

---

## Backend

- FastAPI

Provides asynchronous, high-performance REST APIs.

---

## Deep Learning & NLP

- Hugging Face Transformers
- PyTorch
- TensorFlow / Keras

Used for:

- Intent Classification
- Sentiment Analysis
- Named Entity Recognition
- Text Correction
- Language Understanding

---

## Data Validation

- Pydantic

Provides:

- Type validation
- Request parsing
- Response serialization
- Schema enforcement

---

## Preprocessing

- Regex
- NumPy

Used for:

- Text normalization
- Cleaning
- Rule-based preprocessing

---

## Architecture

- Clean Architecture
- Domain-Driven Design (DDD)

Ensures loose coupling, maintainability, and testability.

---

# 🚀 Key Features

## ✅ AI Workflow Orchestration

A complete LangGraph workflow that manages the customer support lifecycle.

Workflow:

```
User Message
      │
      ▼
Intent Prediction
      │
      ▼
Judge / Audit
      │
      ├──────────────┐
      ▼              ▼
Execute Tool     Human Escalation
      │
      ▼
NER Validation
      │
      ▼
Response Generation
      │
      ▼
Finalize
```

---

## 🎯 Intent Classification

Predicts customer intent using a custom NLP model.

Example intents:

- Order Status
- Refund Request
- Cancel Order
- Product Inquiry
- Complaint
- Technical Support

---

## 😊 Sentiment Analysis

Detects customer emotions in real time.

Examples:

- Positive
- Neutral
- Angry
- Frustrated
- Disappointed

---

## 🧠 Judge / Audit Layer

A dedicated decision node validates AI outputs before execution.

Responsibilities include:

- Confidence threshold checking
- Intent validation
- Metadata verification
- Routing decisions
- Error correction

---

## 🧾 Named Entity Recognition (NER)

Extracts required entities from customer messages.

Examples:

- Order ID
- Customer Name
- Product Name
- Email
- Phone Number
- Tracking Number

Each intent defines its own required entities.

Example:

```
Refund Request

Required:

- Order ID
- Reason
```

---

## 🛡️ Production Safety

The system includes multiple safety mechanisms.

### Human Escalation

Automatically routes conversations to a human agent when:

- Intent confidence is low
- Customer sentiment is highly negative
- Required information is missing
- AI validation fails

---

### Data Validation

Every extracted entity is validated before execution.

Invalid or missing fields trigger:

- Clarification requests
- Re-routing
- Human escalation

---

### Error Correction

Text normalization and spell correction improve model robustness before inference.

---

## 🔄 Modular AI Components

Every AI component is abstracted through interfaces.

Examples:

```
ITextClassifier

↓

BERTClassifier
RoBERTaClassifier
DistilBERTClassifier
```

Changing the implementation requires no changes to:

- API
- Graph
- Business Logic

---

# ⚙️ Workflow Overview

```
                +----------------------+
                |   User Message       |
                +----------+-----------+
                           |
                           ▼
                +----------------------+
                | Text Preprocessing   |
                +----------+-----------+
                           |
                           ▼
                +----------------------+
                | Intent Classifier    |
                +----------+-----------+
                           |
                           ▼
                +----------------------+
                | Sentiment Analyzer   |
                +----------+-----------+
                           |
                           ▼
                +----------------------+
                | Judge / Auditor      |
                +----------+-----------+
                           |
            ┌──────────────┴──────────────┐
            ▼                             ▼
+-----------------------+      +----------------------+
| Human Escalation      |      | Continue Workflow    |
+-----------------------+      +----------+-----------+
                                          |
                                          ▼
                             +-------------------------+
                             | NER Entity Extraction   |
                             +-----------+-------------+
                                         |
                                         ▼
                             +-------------------------+
                             | Entity Validation       |
                             +-----------+-------------+
                                         |
                                         ▼
                             +-------------------------+
                             | Execute Tool            |
                             +-----------+-------------+
                                         |
                                         ▼
                             +-------------------------+
                             | Generate Response       |
                             +-----------+-------------+
                                         |
                                         ▼
                             +-------------------------+
                             | Final Response          |
                             +-------------------------+
```

---

# 🎯 Design Principles

The project follows several software engineering principles:

- SOLID Principles
- Dependency Inversion
- Separation of Concerns
- Interface Segregation
- Domain-Driven Design
- Clean Architecture
- Modular Components
- Reusable AI Services

---

# 💡 Quick Start

## 1. Clone the Repository

```bash
git clone <your-repo-url>
```

---

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Run the API

```bash
python src/presentation/api/app.py
```

---

# 📌 Future Improvements

- Multi-language support
- Voice customer support
- RAG integration
- Conversation memory
- Tool calling with external APIs
- Monitoring & observability
- LLM guardrails
- Agent analytics dashboard
- Docker support
- CI/CD pipeline
- Kubernetes deployment
- Redis caching
- Authentication & Authorization
- Streaming responses
- Conversation history persistence

---

# 📄 License

This project is intended for educational and production-ready AI architecture demonstrations.

# 🧠 Supply Chain Orchestrator AI System — Project Context

## System Overview
The **Supply Chain Orchestrator AI System** is a production-ready, multi-agent platform designed to detect, analyze, and autonomously resolve supply chain disruptions. 
It uses an agentic architecture built on **LangGraph** and **LangChain**, backed by a **FastAPI** Python API, and controlled via a **React + Tailwind** frontend.

## 🤖 Agent Roles (ReAct Pattern)

1. **Inventory Agent** (`backend/agents/inventory_agent.py`)
   - Tool: `get_inventory_status` (simulated ERP)
   - Role: Checks current stock levels, thresholds, and identifies the current supplier.

2. **Risk Agent** (`backend/agents/risk_agent.py`)
   - Tool: `get_external_risk_data` (Tavily Search API)
   - Role: Fetches live global risk/disruption data, calculates a deterministic severity score, and produces a structured RiskReport.

3. **Supplier Agent** (`backend/agents/supplier_agent.py`)
   - Tool: `search_suppliers`
   - Role: Discovers alternative suppliers while strictly avoiding previously tried ones to prevent infinite loops. Validates all returns via Pydantic.

4. **Decision Agent** (`backend/agents/decision_agent.py`)
   - Details: Combines LLM reasoning with a deterministic multi-criteria scoring function (cost, ETA, risk, reliability).
   - Role: Selects the optimal supplier and generates a summary justification. Stores the decision to memory.

5. **Validation Agent** (`backend/agents/validation_agent.py`)
   - Role: Validates all upstream outputs (Inventory, Risk, Suppliers, Decision) against strict Pydantic schemas. 
   - Generates a pass/fail `ValidationResult` used by LangGraph for conditional routing and retries.

## 🕸️ LangGraph Workflow (`backend/graph/workflow.py`)

The orchestration logic is managed by an 8-node state graph:
1. `inventory` → `risk` → `supplier` → `validation`
2. **Conditional routing** from `validation`:
   - Pass ➔ `decision`
   - Fail (recoverable) ➔ loop to `supplier`
   - Fail (max_retries reached) ➔ `human_fallback`
3. **Conditional routing** from `decision`:
   - Decision exists ➔ `approval` (Interrupts execution, waits for human)
   - No decision ➔ `human_fallback`
4. **Human-in-the-loop**: Wait at `approval` node. Resume via API `/approve`.
   - Approved ➔ `execute`
   - Rejected ➔ `human_fallback`

State runs are persisted across interrupts using `MemorySaver`. A hard limit (`MAX_ITERATIONS`) prevents infinite loops.

## 🗄️ Memory Design (Vector DB)

Built using **ChromaDB** (`backend/memory/vector_store.py`).
Uses OpenAI Embeddings (fallback to SentenceTransformers).

Stores:
- **Past incidents:** Part ID, disruption type, severity.
- **Decisions:** Scores, justification, selected supplier.
- **Supplier Performance records**

*Why?* Enables future RAG patterns (e.g., "Find how we handled the Taiwan chip shortage in 2024").

## 🔌 API Contracts (`backend/api/routes.py`)

- `POST /api/v1/run-agent`
  - Body: `{"part_id": "PART-001", "disruption_type": "supplier_failure", "quantity_needed": 100}`
  - Returns: `{"run_id": "uuid-...", "status": "queued"}` (Starts background LangGraph task)

- `GET /api/v1/status/{run_id}`
  - Returns: Full `SupplyChainState`, including `status`, `current_node`, and an array of `agent_logs` (Thought/Action/Observation).

- `POST /api/v1/approve`
  - Body: `{"run_id": "uuid-...", "approved": true, "reviewer_comments": "Looks good"}`
  - Action: Resumes the interrupted LangGraph execution.

## 💻 Key Code Snippets

**ReAct Step Parsing Example (Supplier Agent)**
```python
for action, observation in result.get("intermediate_steps", []):
    log.steps.append(ReActStep(
        thought=getattr(action, "log", "").split("Action:")[0].replace("Thought:", "").strip(),
        action=f"{getattr(action, 'tool', 'unknown')}({getattr(action, 'tool_input', '')})",
        observation=str(observation)[:500],
    ))
```

**LangGraph Conditional Routing (Validation)**
```python
def route_after_validation(state: SupplyChainState) -> Literal["decision", "supplier", "human_fallback"]:
    vr = state.get("validation_result", {})
    if vr.get("valid"):
        return "decision"
    
    if state.get("retry_count", 0) < settings.max_retries:
        return "supplier"
        
    return "human_fallback"
```

## 🚀 Steps to Rebuild / Run System

1. **Configure Environment:**
   ```bash
   # In backend/.env
   OPENAI_API_KEY=sk-your-key
   TAVILY_API_KEY=tvly-your-key
   ```

2. **Start Backend (FastAPI)**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8000
   ```

3. **Start Frontend (Vite/React)**
   ```bash
   cd frontend
   npm install
   npm run dev
   # Opens at http://localhost:5173
   ```

## 🛡️ Security & Performance
- **Prompt Injection:** Filtered by `utils/security.py`.
- **Validation:** Pydantic strict schemas ensure outputs match requested formats (e.g., regex `SUP-[A-Z]+`).
- **Caching:** Tools use a `TTLCache` (`utils/cache.py`) to prevent duplicate LLM/API calls within the same run.

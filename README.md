## A2A System Demo (Agent-to-Agent Protocol)

This repository contains a minimal, in-memory Agent-to-Agent (A2A) demo that showcases collaborative agent workflows:

- User → Orchestrator routes to Research Agent
- Research Agent gathers data and, if needed, delegates to the Analysis Agent
- Analysis Agent processes results and, if needed, delegates to the Visualization Agent
- Final result is composed and returned

No external services are required for the in-memory demo; all routing happens via an async message bus inside a single Python process.

### Repository Structure

```
a2a_system/
├── core/
│   ├── __init__.py
│   ├── protocol.py         # Protocol dataclasses and enums (message/task types)
│   ├── registry.py         # Agent discovery and capability registry
│   └── message_bus.py      # Async message routing and response correlation
├── agents/
│   ├── __init__.py
│   ├── base_agent.py       # A2AAgent base class: lifecycle, message loop, delegation
│   ├── research_agent.py   # ResearchAgent: simulates research, optionally delegates analysis
│   ├── analysis_agent.py   # DataAnalysisAgent: simulates analysis, optionally delegates visualization
│   └── visualization_agent.py # VisualizationAgent: returns a simple chart spec
├── orchestrator/
│   ├── __init__.py
│   └── orchestrator.py     # Orchestrates the first hop from user to agent
├── utils/
│   ├── __init__.py
│   └── logger.py
├── main.py                 # Single-request demo using in-memory A2A
├── a2a_complete_example.py # Two-scenario demo using in-memory A2A
└── requirements.txt
```

### How It Works

1. The `AgentRegistry` records agents and indexes capabilities (e.g., `research`, `data_analysis`, `visualization`).
2. The `A2AMessageBus` routes messages to agent queues and correlates `task_request`/`task_response` pairs.
3. Each `A2AAgent` registers on start, subscribes to the message bus, and runs a message loop:
   - On `task_request`, it sends a status update, executes work, and replies with `task_response`.
   - Agents can delegate by capability using `send_task_to_agent`, which sends a new `task_request` and waits for the response.
4. The `A2AOrchestrator` infers which capability to invoke from the user text, picks a suitable agent from the registry, and sends the initial `task_request`.

Delegation chain for demo scenario:

- Research Agent → (delegates) Analysis Agent → (delegates) Visualization Agent

If a downstream agent is unavailable or times out, upstream agents still return a useful result (delegations are treated as optional in this demo).

### Requirements

- Python 3.9+

The in-memory demo uses only Python standard library modules.

### Quick Start (Windows PowerShell)

```powershell
cd C:\Users\Administrator\Downloads\a2a_system
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Option 1: single scenario
python main.py

# Option 2: two scenarios (with and without analysis delegation)
python a2a_complete_example.py
```

Expected output highlights:
- Agents register and system initializes
- Research starts and completes
- If the prompt contains words like "analyze", Research delegates to Analysis
- Analysis may delegate to Visualization
- Final `task_response` printed to console

### Scenarios

- `main.py`: Single scenario — "Research AI trends and analyze the data"
- `a2a_complete_example.py`: Two scenarios — with and without analysis keyword

You will see printed logs indicating delegations and the final composed result.

### Key Files Deep Dive

- `core/registry.py`: In-memory registry for agent capabilities. Methods: `register_agent`, `find_agents_by_capability`, `unregister_agent`.
- `core/message_bus.py`: Async routing and correlation. `send_and_wait` ensures the recipient is subscribed, otherwise raises a clear error. `complete_request` resolves pending futures.
- `agents/base_agent.py`: Common behavior for agents (start/stop, message loop, request handling, `send_task_to_agent`). Non-request messages are consumed to avoid queue buildup; responses are correlated by the bus.
- `agents/research_agent.py`: Simulates research and optionally delegates to `data_analysis`.
- `agents/analysis_agent.py`: Simulates analysis, optionally delegates `visualization`. Visualization is optional; failures do not fail the main analysis task.
- `agents/visualization_agent.py`: Produces a simple chart spec based on insights.
- `orchestrator/orchestrator.py`: Infers capability from user text using keyword matching, sends the initial `task_request`, and returns the agent’s response.

### Customization

- Make analysis/visualization mandatory: enforce delegation completion in agents before returning.
- Change timeouts: edit `A2AMessageBus.send_and_wait(timeout=...)` or the orchestrator’s call.
- Add a new agent/capability: implement a new `A2AAgent` subclass and register a unique capability; update orchestrator keywords if you want the first hop to route there.

### Troubleshooting

- "Recipient not subscribed" error: The target capability wasn’t registered yet. Ensure all agents are started before sending tasks (e.g., in `main.py` and `a2a_complete_example.py`, agents start before the orchestrator call).
- Delegation timeout: The downstream agent might be slow or not running. In this demo, upstream agents catch delegation errors and still return results.
- Nothing prints: Confirm you’re running inside the virtual environment and from the repository root.

### MCP Note (Optional)

This demo is entirely in-memory. If you need MCP-based discovery or transport across processes/machines:

- Replace the `AgentRegistry` with an MCP registry service.
- Adapt `A2AMessageBus` to send messages over MCP.
- Keep agent implementations the same to minimize refactors.

---

For questions or to extend this with HTTP transports or real tools (web search, vector DB, etc.), open an issue or request enhancements.

---------------------------------

Additional Details - 
# A2A (Agent-to-Agent) System - Complete Codebase Explanation

This is a **multi-agent orchestration system** where specialized AI agents communicate and delegate tasks to each other. Here's the complete breakdown:

---

## **Core Architecture (3 Foundation Components)**

### **1. AgentRegistry (`registry.py`)**
**Purpose**: Phone book for agents - tracks who can do what

- **Stores**: Agent ID, capabilities, endpoint, status, last heartbeat
- **Key Methods**:
  - `register_agent()`: Adds agent to registry with its capabilities
  - `find_agents_by_capability()`: Quick lookup - "who can do data analysis?"
  - **Capabilities Index**: Hash map for O(1) capability lookups
  
**Example**: When you need "visualization", registry returns `["visualization-agent-001"]`

---

### **2. A2AMessageBus (`message_bus.py`)**
**Purpose**: Post office - routes messages between agents

- **Subscribers Dictionary**: Maps agent IDs to their message queues
- **Pending Responses**: Tracks requests waiting for replies (uses Futures)

**Key Methods**:
- `publish()`: Delivers message to recipient's queue
- `send_and_wait()`: Sends message + blocks until response arrives (with timeout)
- `complete_request()`: Resolves the Future when response received

**Flow**: 
```
Agent A → send_and_wait() → publish to Agent B's queue → await Future → complete_request() → returns response
```

---

### **3. Protocol Definitions (`protocol.py`)**
**Purpose**: Standardized message formats

**Message Types**:
- `TASK_REQUEST`: "Please do this work"
- `TASK_RESPONSE`: "Here's the result"
- `STATUS_UPDATE`: "I'm working on it"
- `CAPABILITY_ANNOUNCEMENT`: "I can do X, Y, Z"

**Key Structures**:
- `Task`: Contains task_id, type, description, input_data, priority
- `A2AMessage`: Base class with protocol version, sender/recipient IDs, timestamps

---

## **Agents (3 Specialized Workers)**

### **Base Agent (`base_agent.py`)**
**Purpose**: Abstract base class all agents inherit from

**Lifecycle**:
1. `start()`: Registers with registry, subscribes to message bus, starts message loop
2. `_message_loop()`: Continuously polls queue for incoming messages
3. `_handle_message()`: Routes messages by type (task_request, task_response, status_update)
4. `stop()`: Unregisters and unsubscribes

**Key Methods**:
- `execute_task()`: **Abstract** - subclasses implement their logic here
- `send_task_to_agent()`: Delegates work to another agent by capability
- `_send_status_update()`: Notifies requester of progress
- `_send_task_response()`: Returns results + calls `complete_request()` to unblock sender

---

### **1. ResearchAgent (`research_agent.py`)**
**Capabilities**: `["web_search", "research", "summarization"]`

**What it does**:
- Simulates web research (2s delay)
- Returns mock research data with sources, summaries, relevance scores
- **Smart Delegation**: If "analyze" in description → automatically delegates to DataAnalysisAgent
- Prints progress with emojis (🔍, ✅, 🤝, 📊)

**Example Output**:
```python
{
  "query": "AI trends",
  "sources_searched": 5,
  "results": [...3 mock articles...],
  "analysis": {...delegated analysis results...}
}
```

---

### **2. DataAnalysisAgent (`analysis_agent.py`)**
**Capabilities**: `["data_analysis", "visualization", "statistics"]`

**What it does**:
- Analyzes input data (1s delay)
- Generates insights, confidence scores, trend analysis
- **Smart Delegation**: If insights exist → delegates to VisualizationAgent
- Gracefully handles visualization failures (optional enhancement)

**Flow**:
```
Receives research data → Analyzes trends → Detects insights → Delegates to viz → Returns combined result
```

---

### **3. VisualizationAgent (`visualization_agent.py`)**
**Capabilities**: `["visualization"]`

**What it does**:
- Creates chart specifications from analysis data (0.5s delay)
- Returns JSON chart config (type: bar, title, data points)

**Output Example**:
```python
{
  "artifact_type": "chart_spec",
  "chart": {
    "type": "bar",
    "title": "Insights Confidence",
    "data": [{"label": "insight1", "value": 0.92}, ...]
  }
}
```

---

## **Orchestration Layer**

### **A2AOrchestrator (`orchestrator.py`)**
**Purpose**: Entry point - translates human requests into agent tasks

**Process**:
1. **Parse Intent**: Uses keyword matching to determine capability needed
   - "research/search/find" → `research`
   - "analyze/statistics" → `data_analysis`
   - Default → `web_search`

2. **Find Agent**: Queries registry for capable agent
3. **Create Task**: Builds standardized task_request message
4. **Route & Wait**: Sends to agent via message bus, waits up to 60s for response

**Keyword Mapping**:
```python
{
  "research": ["research", "search", "find", "investigate"],
  "data_analysis": ["analyze", "analysis", "statistics", "trends"]
}
```

---

## **Execution Examples**

### **Demo 1: Full Pipeline (`a2a_complete_example.py`)**
**Request**: "Research AI trends and analyze the data for visualization"

**Execution Flow**:
```
1. Orchestrator receives request
2. Detects "research" → routes to ResearchAgent
3. ResearchAgent executes → finds "analyze" keyword
4. ResearchAgent delegates to DataAnalysisAgent
5. DataAnalysisAgent processes → detects insights
6. DataAnalysisAgent delegates to VisualizationAgent
7. VisualizationAgent creates chart spec
8. Results bubble back up: Viz → Analysis → Research → Orchestrator → User
```

**Message Count**: ~8 messages (request, status updates, responses at each level)

---

### **Demo 2: Simple Research (`a2a_complete_example.py`)**
**Request**: "Research top AI companies by market cap"

**Execution Flow**:
```
1. Orchestrator → ResearchAgent
2. ResearchAgent executes (no "analyze" keyword)
3. Returns research data directly
4. No delegation chain
```

---

## **Key Design Patterns**

### **1. Async/Await Throughout**
- All I/O operations are non-blocking
- Agents run concurrent message loops
- `asyncio.Queue` for thread-safe message passing

### **2. Request-Response with Futures**
```python
# Sender blocks here
response = await message_bus.send_and_wait(message)

# Receiver eventually calls
message_bus.complete_request(message_id, response)  # Unblocks sender
```

### **3. Capability-Based Routing**
No hardcoded agent names - always query by capability:
```python
agents = await registry.find_agents_by_capability("data_analysis")
target = agents[0]  # Pick first available
```

### **4. Graceful Degradation**
```python
try:
    viz_result = await self.send_task_to_agent("visualization", data)
except Exception:
    # Continue without visualization - not critical
    pass
```

---

## **Data Flow Example**

**User Input**: "Research AI trends and analyze the data for visualization"

```
┌─────────────┐
│ Orchestrator│ Determines capability: "research"
└──────┬──────┘
       │ task_request
       ▼
┌──────────────┐
│ResearchAgent │ Executes research → Detects "analyze"
└──────┬───────┘
       │ task_request (to data_analysis capability)
       ▼
┌──────────────┐
│AnalysisAgent │ Analyzes data → Detects insights
└──────┬───────┘
       │ task_request (to visualization capability)
       ▼
┌──────────────┐
│    VizAgent  │ Creates chart spec
└──────┬───────┘
       │ task_response
       ▼
┌──────────────┐
│AnalysisAgent │ Merges viz into analysis result
└──────┬───────┘
       │ task_response
       ▼
┌──────────────┐
│ResearchAgent │ Merges analysis into research result
└──────┬───────┘
       │ task_response
       ▼
┌─────────────┐
│ Orchestrator│ Returns final result to user
└─────────────┘
```

---

## **Critical Implementation Details**

1. **Duplicate Code**: `base_agent.py` and `orchestrator.py` have duplicate definitions (probably refactoring artifact)

2. **Status Updates**: Agents send "processing" status but orchestrator doesn't consume them (fire-and-forget)

3. **Agent Discovery**: Always picks `agents[0]` - no load balancing or health checks

4. **Error Handling**: Timeout errors return error dict, execution errors send failed task_response

5. **Simulated Work**: All delays are `asyncio.sleep()` - in production these would be real API calls

6. **No Persistence**: Everything in-memory - restart loses all state

This is a **proof-of-concept** showcasing agent orchestration patterns, capability-based routing, and async message passing in a clean, extensible architecture.



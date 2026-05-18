# AGENTS.md

## Project Goal

This project is a learning-oriented AI character engine.

The main purpose of this project is to help the user learn, as efficiently as possible, how to build:

- an agent framework
- RAG
- memory
- LLM adapters
- event/message protocols
- desktop UI integration
- later TTS / voice / character performance systems

This project should gradually benchmark and learn from the GitHub project `shinsekai`, but the priority is not blind copying. The priority is to help the user understand the architecture and rebuild a usable version step by step.

---

## Core Development Principle

Always develop the project in three possible levels:

### Level 1: Skeleton First

First focus on the project skeleton.

The goal of this stage is to make the user understand the architecture clearly.

At this level, code should emphasize:

- clear module separation
- simple but complete class structure
- readable data flow
- minimal runnable examples
- no unnecessary complex logic

Prefer building the architecture frame before implementing deep features.

Example focus:

- `main.py` as entry point
- `manager.py` as central orchestrator
- `messages.py` as event/message protocol definitions
- `llm_worker.py` as background LLM execution
- `memory.py` as memory interface
- `rag_service.py` as RAG interface
- `agent_executor.py` as agent/tool execution interface
- `desktop_window.py` as UI layer

---

### Level 2: Basic Runnable Version

After the skeleton is clear, make the project reach a basic working level.

At this level, the project should be able to run end-to-end, even if some features are simple.

The goal is:

- user can type a message
- LLM can generate a response
- response can be converted into events
- UI can consume events
- memory/RAG/agent modules can be connected through clean interfaces
- the whole program can run without major architecture gaps

Do not over-engineer this stage.

Prefer simple but complete implementations.

---

### Level 3: Shinsekai-like Restoration

After the basic version works, gradually move toward restoring more advanced behavior inspired by `shinsekai`.

At this level, compare this project with `shinsekai` in terms of:

- architecture design
- module responsibility
- event flow
- prompt management
- character behavior
- plugin/tool system
- memory system
- RAG integration
- voice/TTS pipeline
- UI interaction design

When referencing `shinsekai`, do not invent details.  
If the source code is not available in the workspace, say that the source is not available and ask the user to provide it or the relevant file.
---

## User Intent Rule

The user often wants fast progress.

If the user clearly asks for a project-level result, do not force them through every beginner step.

You may skip intermediate steps and directly write code that reaches the requested target level.

However, when skipping steps, explain briefly:

- which steps were skipped
- why they were skipped
- what level the current code is targeting
- what the user should study afterward

Example:

> I am skipping the pure skeleton stage here and directly writing a basic runnable version, because your request is project-level and you want to connect RAG/agent modules quickly.

---

## Teaching Style

This project is for learning architecture.

When explaining code, prefer:

1. overall purpose
2. module responsibility
3. data flow
4. class/function role
5. important lines
6. how it connects to the whole project

Use Chinese when explaining to the user.

Explanations should be clear, direct, and practical.

Avoid vague answers.

---

## Coding Style

Use Python as the main language unless the user says otherwise.

Code should follow these rules:

- use type hints where useful
- keep functions small and readable
- avoid unnecessary abstraction
- avoid large hidden magic
- prefer explicit data flow
- preserve the event/message architecture
- keep UI logic separate from business logic
- keep LLM adapter logic separate from manager logic
- keep RAG, memory, and agent execution as independent modules

For complex logic, add short comments.

Comments should explain why the logic exists, not repeat obvious code.

## Architecture Rules

### UI Layer

The UI layer is responsible for:

- receiving user input
- displaying messages
- displaying character state
- consuming events

The UI should not directly contain LLM, RAG, memory, or agent logic.

---

### Manager Layer

The manager layer is responsible for orchestration.

It connects:

- UI
- LLM worker
- event parser
- memory
- RAG
- agent executor

The manager should coordinate modules, but should not contain all business logic.

---

### Message/Event Layer

The message/event layer defines the communication protocol.

Examples:

- text event
- metadata event
- emotion event
- tool event
- memory event
- RAG result event

This layer should make it easy for UI, TTS, RAG, and agents to consume the same LLM output.

---

### LLM Adapter Layer

The LLM adapter layer hides model provider differences.

It may support:

- OpenAI-compatible APIs
- Ollama
- DeepSeek
- local models
- other providers

The rest of the project should not care which provider is used.

---

### Memory Layer

The memory layer stores and retrieves useful information.

Start simple.

A JSON-based or in-memory implementation is acceptable at first.

Later it can be upgraded to:

- database memory
- vector memory
- long-term user memory

---

### RAG Layer

The RAG layer is responsible for retrieval-augmented generation.

Start with a simple document search interface.

Later it can support:

- chunking
- embeddings
- vector database
- reranking
- source citation

---

### Agent Layer

The agent layer is responsible for tool usage and task execution.

Start with a simple executor.

Later it can support:

- tool registry
- function calling
- multi-step planning
- plugin-like tools
- file operations

---

## Shinsekai Benchmark Rule

For every implemented part, explain:

- which Shinsekai part it corresponds to
- what this project currently implements
- whether it is skeleton, runnable, or restoration level
- what the next upgrade step is

If Shinsekai source code is not available in the workspace, do not invent details.

Ask the user to provide the relevant Shinsekai file or explain that the comparison is based only on the current visible project structure.

---

## Output Preference

When generating code:

- say which file to create or modify
- provide complete code for small files
- provide patch-style changes for large files
- explain how to run or test it
- explain the corresponding Shinsekai part

When explaining code:

- use Chinese
- explain architecture meaning
- explain data flow
- explain why this design helps the user learn Agent / RAG / architecture
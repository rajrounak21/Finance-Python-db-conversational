# AI-Powered Financial Agent Platform

A production-grade AI system built using **Python, FastAPI, LangChain/LangGraph**, and **MongoDB** that provides real-time financial insights through intelligent LLM-based agent orchestration and multi-tool integration.

This project demonstrates real-world **AI engineering**, including tool calling, conversational memory, database-backed context, and dynamic model selection.

---

## 🚀 Key Features

- 🤖 **LLM-Based Financial Agent**
  - Multi-step reasoning using LangChain & LangGraph
  - Dynamic model routing (Groq / GPT)
  - Context-aware responses using conversation history

- 🧠 **Tool Orchestration**
  - Stock symbol resolution (Yahoo Finance)
  - Real-time stock prices (Alpha Vantage, yFinance)
  - Financial & general news search (Tavily, SerpAPI)
  - Intelligent fallback and retry logic

- 💾 **Database-Backed Memory (MongoDB)**
  - Persistent chat history
  - Session-based conversation tracking
  - User-specific context (email + session_id)
  - Aggregation pipelines for session retrieval

- ⚡ **FastAPI Backend**
  - REST APIs for chat, sessions, and history
  - Secure session handling
  - Production-style error handling

---

## 🏗️ System Architecture

```

User → FastAPI → 
AI Agent (LLM)
↓
Tool Orchestration Layer
(Stocks | News | Web Search)
↓
MongoDB (Memory)
|
response

````

---

## 🧠 AI Agent Design

The agent follows a **tool-first approach**:
1. Resolve company name → stock symbol
2. Fetch real-time stock data
3. Retrieve latest news if required
4. Combine results using LLM reasoning
5. Store conversation context in database

This avoids hallucination and ensures **accurate, real-time responses**.

---

## 🗄️ Database Design (MongoDB)

### Collection: `conversation_logs`

Each document represents one interaction:

```json
{
  "session_id": "uuid",
  "user_email": "string",
  "timestamp": "datetime",
  "user_input": "string",
  "response": "string",
  "model": "string"
}
````

### Example Queries

**Load conversation history**

```python
collection.find(
  {"session_id": session_id, "user_email": email}
).sort("timestamp", -1)
```

**Aggregation pipeline for session listing**

```python
pipeline = [
  {"$match": {"user_email": email}},
  {"$sort": {"timestamp": 1}},
  {"$group": {
      "_id": "$session_id",
      "first_message": {"$first": "$user_input"},
      "last_timestamp": {"$last": "$timestamp"}
  }},
  {"$sort": {"last_timestamp": -1}}
]
```

This database layer enables **multi-turn reasoning and personalization**, which is critical for AI systems.

---

## 🛠️ Tech Stack

* **Python**
* **FastAPI**
* **LangChain & LangGraph**
* **MongoDB**
* **yFinance**
* **Alpha Vantage API**
* **Tavily Search**
* **SerpAPI**
* **Finnhub**
* **dotenv**

---

## 📌 Why This Project

This project was built to simulate a **real-world AI application**, where:

* AI logic and database design are tightly coupled
* Agents rely on tools instead of hallucination
* Memory and context drive intelligent responses

It goes beyond simple prompt-response systems and demonstrates **AI orchestration, data engineering, and backend design**.

---

## 👨‍💻 Use Case

* Financial chatbots
* AI-powered stock analysis platforms
* Agent-based decision systems
* Real-time AI assistants

---

## 📄 License

MIT License

```


Just tell me 👍
```

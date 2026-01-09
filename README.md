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

## 👨‍💻 Use Case

* Financial chatbots
* AI-powered stock analysis platforms
* Agent-based decision systems
* Real-time AI assistants

---
## Problem statemet -1 

## 1. API Data Retrieval and Storage

The api.py file fetches book data from an external REST API in JSON format. The data includes book details such as title, author, and publication year.

The retrieved data is stored locally in a SQLite database named database.book.db, which contains a books table for persistent storage.

This setup demonstrates basic API integration, data processing, and database storage using Python.


## 2. Data Processing and Visualization

The data.py file fetches student test score data from an external API. After retrieving the data, it processes the dataset to calculate the average score for each student or subject.

The processed data is then visualized using a bar chart, making it easy to compare scores and understand overall performance.

This task demonstrates API data fetching, basic data processing, and data visualization using Python.

### 3.CSV Data Import to a Database

The csv_to_db.py script reads user data from a CSV file (user.csv) containing fields such as name and email.

The script inserts this data into a SQLite database named user.db for persistent storage. The database contains a users table to store all records from the CSV file.

This demonstrates reading CSV files, data insertion into a database, and basic Python database handling.

## 4. Most Complex Python Code: chatbot_router.py – AI chatbot with FastAPI, LLM orchestration, and real-time tools.

## 5. Most Complex Database Code: chatbot_router.py – MongoDB for session management and conversation history.



Just tell me 👍
```

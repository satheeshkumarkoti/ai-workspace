# 🔍 SPRING-RAG-ENGINE

> **Enterprise RAG System — Spring Boot 3 + Spring AI + pgvector + OpenAI**

[![Java](https://img.shields.io/badge/Java-21-orange?logo=java)](https://openjdk.org)
[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.2.5-green?logo=springboot)](https://spring.io/projects/spring-boot)
[![Spring AI](https://img.shields.io/badge/Spring%20AI-1.0.0-brightgreen)](https://spring.io/projects/spring-ai)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-black?logo=openai)](https://openai.com)
[![pgvector](https://img.shields.io/badge/pgvector-HNSW-blue?logo=postgresql)](https://github.com/pgvector/pgvector)
[![License](https://img.shields.io/badge/License-MIT-yellow)](./LICENSE)

---

> 🏗️ **Enterprise-grade RAG engine** built with Java Spring Boot 3, Spring AI 1.0.0, and pgvector — demonstrating production-ready Retrieval-Augmented Generation with multimodal AI capabilities.

---

## 📌 OVERVIEW

**Spring RAG Engine** is a comprehensive Spring Boot application showcasing enterprise AI integration patterns using **Spring AI 1.0.0**. It implements a full RAG pipeline with PDF ingestion, vector storage in pgvector, semantic search, and multimodal capabilities including audio transcription and image analysis.

---

## ✨ KEY FEATURES

| Feature | Description |
|---|---|
| 📚 **RAG Pipeline** | PDF ingestion → chunking → embedding → pgvector → semantic search |
| 🔍 **Vector Search** | pgvector with HNSW index and cosine similarity |
| 💬 **AI Chat** | GPT-4o powered conversational AI with context |
| 🎵 **Audio AI** | Audio transcription and analysis via OpenAI Whisper |
| 🖼️ **Image AI** | Image understanding and analysis via GPT-4o Vision |
| 📄 **PDF Reader** | Spring AI PDF document reader for knowledge ingestion |
| 🏃 **Player Stats** | Domain model with Achievements — RAG-powered sports analytics |
| ⚡ **Spring AI Advisors** | Vector store advisors for enhanced RAG accuracy |

---

## 🏗️ ARCHITECTURE

```
┌─────────────────────────────────────────────────────┐
│              REST API LAYER (Spring Boot)           │
│  /chat │ /audio │ /image │ /ics │ /player │ /hello  │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              SPRING AI LAYER                        │
│   ChatClient · EmbeddingModel · VectorStoreAdvisor  │
└───────┬──────────────────────────┬──────────────────┘
        │                          │
┌───────▼────────┐        ┌────────▼────────┐
│   OPENAI API   │        │   PGVECTOR DB   │
│  GPT-4o Chat   │        │  HNSW Index     │
│  Whisper Audio │        │  1536 dims      │
│  Vision Image  │        │  Cosine Sim     │
│  Ada Embedding │        │  PostgreSQL     │
└────────────────┘        └─────────────────┘
```

---

## 🤖 API ENDPOINTS

### 💬 Chat Controller
```
GET  /hello           → Basic greeting
POST /chat            → AI chat with RAG context
```

### 📄 ICS Controller (Indian Constitution Search)
```
POST /ics/load        → Load Indian Constitution PDF into vector store
POST /ics/search      → Semantic search over constitution
GET  /ics/ask?q=...   → RAG-powered Q&A on constitution
```

### 🎵 Audio Controller
```
POST /audio/transcribe   → Transcribe audio file using Whisper
POST /audio/analyse      → Analyse audio content with AI
```

### 🖼️ Image Controller
```
POST /image/analyse      → Analyse image with GPT-4o Vision
POST /image/describe     → Generate image description
```

### 🏃 Player Controller
```
GET  /player/{id}        → Get player with AI-generated insights
GET  /player/achievements → RAG-powered achievements search
```

---

## 🛠️ TECH STACK

| Layer | Technology |
|---|---|
| **Language** | Java 21 |
| **Framework** | Spring Boot 3.2.5 |
| **AI Framework** | Spring AI 1.0.0 |
| **LLM** | OpenAI GPT-4o |
| **Embeddings** | OpenAI text-embedding-3-small (1536 dims) |
| **Audio** | OpenAI Whisper |
| **Vision** | GPT-4o Vision |
| **Vector Store** | pgvector (HNSW, Cosine Similarity) |
| **Database** | PostgreSQL |
| **PDF Processing** | Spring AI PDF Document Reader |
| **Build Tool** | Maven 3.9+ |
| **Containerization** | Docker Compose |

---

## 🚀 QUICK START

### Prerequisites
- Java 21+
- Maven 3.9+
- PostgreSQL with pgvector extension
- OpenAI API Key ([Get one here](https://platform.openai.com))
- Docker (optional — for pgvector)

### Step 1 — Start pgvector with Docker

```bash
docker run -d \
  --name pgvector \
  -e POSTGRES_DB=ics \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

### Step 2 — Configure Environment

```bash
# Windows
copy .env.template .env

# Mac/Linux
cp .env.template .env
```

Edit `.env` and add your OpenAI API key:
```env
OPENAI_API_KEY=sk-your-key-here
```

### Step 3 — Build and Run

```bash
# Build
mvn clean install

# Run
mvn spring-boot:run
```

Application starts at **http://localhost:8080** 🎉

### Step 4 — Load Knowledge Base

```bash
# Load Indian Constitution PDF into vector store
curl -X POST http://localhost:8080/ics/load
```

### Step 5 — Test RAG Search

```bash
# Ask a question about the Indian Constitution
curl "http://localhost:8080/ics/ask?q=What are Fundamental Rights?"
```

---

## 📁 PROJECT STRUCTURE

```
SPRING-RAG-ENGINE/
├── src/main/java/com/sb/code/demo/
│   ├── GenAiDemoApplication.java     # Main Application
│   ├── config/
│   │   ├── PGVectorLoader.java       # pgvector Configuration + Loading
│   │   └── VectorLoader.java         # Vector Store Setup
│   ├── controller/
│   │   ├── AudioController.java      # Audio Transcription + Analysis
│   │   ├── HelloController.java      # Basic Chat Endpoint
│   │   ├── ICSController.java        # Indian Constitution RAG Search
│   │   ├── ImageController.java      # Image Analysis (GPT-4o Vision)
│   │   └── PlayerController.java     # Player + Achievements API
│   └── model/
│       ├── Player.java               # Player Domain Model
│       └── Achievements.java         # Achievements Domain Model
├── src/main/resources/
│   ├── audio/
│   │   └── sample_audio.mp3          # Sample Audio for Testing
│   ├── images/
│   │   └── elephant_lion.jpg         # Sample Image for Testing
│   ├── prompts/
│   │   └── celeb-details.st          # Prompt Templates (StringTemplate)
│   ├── static/
│   │   └── index.html                # Web UI
│   ├── Indian_Constitution.pdf       # RAG Knowledge Base
│   ├── application.yaml              # Application Configuration
│   └── schema.sql                    # pgvector Schema
├── compose.yaml                      # Docker Compose for pgvector
├── .env.template                     # Environment Variables Template
├── pom.xml                           # Maven Dependencies
└── README.MD
```

---

## 🗄️ DATABASE SCHEMA

```sql
-- pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS hstore;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Vector store table
CREATE TABLE IF NOT EXISTS vector_store (
    id        uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    content   text,
    metadata  json,
    embedding vector(1536)
);

-- HNSW index for fast similarity search
CREATE INDEX IF NOT EXISTS vector_store_embedding_idx
    ON vector_store USING HNSW (embedding vector_cosine_ops);
```

---

## 🔑 ENVIRONMENT VARIABLES

```env
# Required
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_ORG_ID=org-your-org-id-here
OPENAI_PROJECT_ID=proj-your-project-id-here

# Database
DB_URL=jdbc:postgresql://localhost:5432/ics
DB_USERNAME=postgres
DB_PASSWORD=postgres
```

---

## 📦 KEY DEPENDENCIES

```xml
<!-- Spring AI BOM -->
<spring-ai.version>1.0.0</spring-ai.version>

<!-- Core AI -->
spring-ai-starter-model-openai       <!-- GPT-4o + Whisper + Vision -->
spring-ai-starter-vector-store-pgvector  <!-- pgvector integration -->
spring-ai-pdf-document-reader        <!-- PDF ingestion -->
spring-ai-advisors-vector-store      <!-- RAG advisors -->
spring-ai-vector-store               <!-- Vector store abstraction -->
```

---

## 🗺️ ROADMAP

- [ ] Add REST API documentation (Swagger/OpenAPI)
- [ ] Add unit and integration tests
- [ ] Add Azure OpenAI support
- [ ] Add Ollama local model support
- [ ] Add streaming responses (SSE)
- [ ] Add multi-tenant vector store isolation
- [ ] Add LangGraph4j for agentic workflows
- [ ] Docker multi-stage build

---

## 👤 AUTHOR

**SATHEESH KUMAR K**
Solution Architect | Gen AI & LLM Engineer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?logo=linkedin)](https://linkedin.com/in/satheesh-kumar-k11a98823)
[![GitHub](https://img.shields.io/badge/GitHub-Portfolio-black?logo=github)](https://github.com/satheeshkumarkoti)

- 18+ Years in Enterprise IT Architecture
- 10+ Years Java Full Stack | 2+ Years Generative AI
- AWS Certified Solutions Architect | Azure AI Engineer Associate
- Expertise: Spring AI · RAG · pgvector · OpenAI · LangGraph · LangChain · MCP

---

## 📄 LICENSE

This project is licensed under the MIT License — see [LICENSE](./LICENSE) for details.

---

> *"Bringing enterprise Java and Generative AI together — production-grade RAG with Spring Boot."*

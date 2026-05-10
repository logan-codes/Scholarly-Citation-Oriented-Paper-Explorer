# SCOPE - Scholarly Citation-Oriented Paper Explorer

A powerful, full-stack application designed to explore and search scholarly research papers. Built with a modern client-server architecture, it allows you to search through millions of papers using advanced vector similarity and keyword ranking algorithms.

![Flutter](https://img.shields.io/badge/Flutter-3.10%2B-02569B)
![Python](https://img.shields.io/badge/Python-3.13%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-FF5252)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Relational_DB-336791)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)

## ✨ Key Features
-   **🔍 Advanced Hybrid Search**: Combines semantic vector search (Qdrant) with BM25 keyword search (PostgreSQL) for highly accurate results.
-   **📈 Multi-Metric Ranking**: Ranks papers based on Relevancy, PageRank, and Velocity scores to surface the most impactful research.
-   **📱 Cross-Platform UI**: Beautiful, responsive frontend built with Flutter, featuring animations, search capabilities, and detailed paper insights.
-   **⚡ High Performance**: Fast and scalable backend powered by FastAPI, SQLAlchemy, and sentence-transformers.
-   **🐳 Containerized**: Fully Dockerized backend infrastructure (API, Postgres, Qdrant) for easy and consistent deployment.

## 🛠️ Architecture
The system is split into a **FastAPI backend** and a **Flutter frontend**, ensuring a clean separation of concerns:

```mermaid
graph TD
    User([User]) <--> UI[Flutter Frontend]
    UI <--> API[FastAPI Backend]
    
    subgraph Backend
        API --> Search[Search Service]
        API --> Storage[Storage & Enrichment]
        
        Search --> Qdrant[(Qdrant Vector DB)]
        Search --> Postgres[(PostgreSQL)]
        
        Storage --> Qdrant
        Storage --> Postgres
    end
```

```text
/
├── 📁 server/              # FastAPI Backend
│   ├── main.py             # API Entry point & Application Lifecycle
│   ├── 📁 api/             # API routes (search, storage)
│   ├── 📁 services/        # Core Business Logic (Search, Storage, Enrichment)
│   ├── 📁 db/              # Postgres and Qdrant models & repositories
│   └── 📁 utils/           # Embedding & Fusion utilities
├── 📁 flutter_ui/          # Flutter Frontend
│   └── 📁 lib/             # Flutter UI code
├── docker-compose.yml      # Multi-container orchestration
└── README.md
```

### Prerequisites
-   Python 3.13 or higher (if running backend locally without Docker)
-   Flutter SDK 3.10+ (for running the frontend)
-   Docker & Docker Compose (Recommended for backend services)

### Configuration
Create a `.env` file in the `server/` directory:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/scope_db
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### Option 1: Running with Docker (Recommended for Backend)
The easiest way to get the backend infrastructure running is using Docker Compose:

```bash
docker-compose up --build
```
- **Backend API**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Qdrant**: localhost:6333

To run the frontend:
```bash
cd flutter_ui
flutter pub get
flutter run
```

### Option 2: Local Installation (Backend)
1.  **Clone the repository**
    ```bash
    git clone https://github.com/logan-codes/SCOPE.git
    cd SCOPE/server
    ```

2.  **Create and activate a virtual environment**
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    ```

3.  **Install dependencies**
    *(Using `uv` or `pip` based on `pyproject.toml`)*
    ```bash
    pip install .
    ```

4.  **Run the application**
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```

## 📚 Usage Guide
1.  **Start Services**: Ensure your backend and databases are running via Docker.
2.  **Launch App**: Open the Flutter app on your device or browser.
3.  **Explore**: Type a research query (e.g., "black holes", "neural networks") into the search bar.
4.  **Analyze**: Click on any paper to view detailed metrics like Relevancy, BM25, PageRank, and overall Trust Score.

---
*Built with ❤️ by [logan](https://github.com/logan-codes)*
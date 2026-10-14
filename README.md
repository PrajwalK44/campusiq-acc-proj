# CampusIQ: AI-Based Student Query Management System
### Docker, Kubernetes, Next.js, FastAPI, Supabase & ChromaDB

CampusIQ is an enterprise-grade, retrieval-augmented generation (RAG) full-stack application designed for higher education institutions. It enables students to query official college policies, examinations, and campus guidelines with zero hallucinations—grounded strictly in indexed PDFs with explicit source citations. When policies are not covered, queries are abstained and can be escalated directly to faculty resolution queues.

---

## 1. System Architecture

```mermaid
flowchart TD
    subgraph Client ["Client Layer"]
        Browser["Next.js Responsive UI (Port 3000)"]
    end

    subgraph Ingress ["Networking & Ingress"]
        K8sIngress["Nginx Ingress Controller (campusiq.local)"]
    end

    subgraph Application ["CampusIQ Core Services"]
        Backend["FastAPI Backend (Port 8000)"]
        Chroma["ChromaDB Vector Server (Port 8000 / 8001)"]
    end

    subgraph DataPlane ["Persistence & AI Cloud"]
        Supabase[("Supabase PostgreSQL\n(Users, Queries, Tickets, Sources)")]
        GroqCloud["Groq Cloud\n(Llama 3.3 70B Versatile)"]
        PVC_Uploads[("PersistentVolumeClaim\n(/app/data/uploads)")]
        PVC_Chroma[("PersistentVolumeClaim\n(/chroma/chroma)")]
    end

    Browser -->|HTTP/REST| K8sIngress
    K8sIngress -->|/api/v1, /health| Backend
    K8sIngress -->|/| Browser
    Backend -->|SQLAlchemy / psycopg2| Supabase
    Backend -->|Cosine Query / Embeddings| Chroma
    Backend -->|Prompt + Context| GroqCloud
    Backend --> PVC_Uploads
    Chroma --> PVC_Chroma
```

---

## 2. RAG Request & Document Ingestion Flow

```mermaid
sequenceDiagram
    autonumber
    actor Student as Student
    participant API as FastAPI Backend
    participant Embed as Sentence-Transformers
    participant Chroma as ChromaDB
    participant LLM as Groq (Llama-3.3-70b)
    participant DB as Supabase PostgreSQL

    Student->>API: POST /api/v1/queries {question, category}
    API->>Embed: Compute Query Embedding
    Embed-->>API: 384-d Dense Vector
    API->>Chroma: Query Nearest Neighbors (Top-K=5)
    Chroma-->>API: Documents, Metadatas, Cosine Distances
    alt Similarity < Threshold (0.35)
        API->>DB: Save Query with Status 'ABSTAINED'
        API-->>Student: Grounded Abstention + Ticket Option
    else Similarity >= Threshold
        API->>LLM: Synthesize Grounded Answer with Evidence Prompt
        LLM-->>API: Verified Answer with Citations
        API->>DB: Save Query, Citations, & Sources
        API-->>Student: Grounded Answer + Source Titles & Pages
    end
```

---

## 3. Directory Structure

```text
campusiq/
├── backend/                   # Python FastAPI application
│   ├── app/
│   │   ├── api/               # API routers (auth, users, queries, documents, tickets, analytics, health)
│   │   ├── core/              # Configuration & JWT security
│   │   ├── db/                # Supabase PostgreSQL session & SQL schema
│   │   ├── models/            # SQLAlchemy database entities
│   │   ├── rag/               # PDF extractor, ChromaDB vector store, Groq LLM, & pipeline
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   └── main.py            # FastAPI main entrypoint & Prometheus instrumentator
│   ├── tests/                 # Unit & RAG pipeline test suite
│   ├── requirements.txt       # Pinned backend dependencies
│   ├── .env.example           # Backend environment configuration template
│   ├── .gitignore
│   └── Dockerfile             # Multi-stage production container image
├── frontend/                  # Next.js 16 + React 19 + Tailwind CSS application
│   ├── app/                   # App router pages & layouts
│   ├── components/            # Student, Faculty, Admin, & Auth dashboard components
│   ├── context/               # Authentication context & session handling
│   ├── lib/                   # API client utilities
│   ├── types/                 # Shared TypeScript interfaces
│   ├── .env.example
│   └── Dockerfile             # Multi-stage Next.js production image
├── k8s/                       # Kubernetes deployment manifests
│   ├── namespace.yaml
│   ├── pvc.yaml
│   ├── configmap-secrets.yaml
│   ├── chromadb.yaml
│   ├── backend.yaml           # Deployment + Service + HorizontalPodAutoscaler
│   ├── frontend.yaml          # Deployment + Service
│   ├── ingress.yaml           # Ingress routing configuration
│   └── kustomization.yaml
├── monitoring/
│   ├── prometheus.yml         # Prometheus scrape configuration
│   └── grafana-dashboard.json # Grafana visual monitoring dashboard
├── docker-compose.yml         # Local multi-container development stack
├── .env.example               # Root environment reference
└── README.md
```

---

## 4. Setup & Dependency Installation

### A. Python Backend Virtual Environment (Host)
As requested, you maintain full control of your local Python virtual environment. To initialize and install the exact pinned dependencies on Windows (PowerShell):

```powershell
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate the virtual environment
.\venv\Scripts\Activate.ps1

# 4. Install all required dependencies
pip install -r requirements.txt
```

### B. Supabase PostgreSQL Initialization
1. Create a project on [Supabase](https://supabase.com).
2. Go to **SQL Editor** in the Supabase Dashboard.
3. Open `backend/app/db/schema.sql` and run its contents to create tables (`users`, `documents`, `query_history`, `query_sources`, `tickets`, `feedback`, `audit_events`) and insert the default seed credentials.
4. Copy your Connection String from **Project Settings -> Database** (Direct Connection or Session Pooler).

### C. Environment Configuration
Create `backend/.env` using `backend/.env.example`:
```env
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
JWT_SECRET_KEY=generate_a_secure_random_key_here
GROQ_API_KEY=gsk_your_groq_api_key_here
```

Create `frontend/.env.local` using `frontend/.env.example`:
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

---

## 5. Running the Application

### Option 1: Docker Compose (Recommended Local Stack)
```powershell
# Build and run all services in background
docker compose up -d --build

# View container status
docker compose ps

# Inspect logs
docker compose logs -f backend

# Stop the stack
docker compose down
```

### Option 2: Running Locally for Development
**Terminal 1 (Backend):**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 (Frontend):**
```powershell
cd frontend
npm run dev
```

Visit `http://localhost:3000` in your browser.

---

## 6. Seed Credentials for Demonstration

| Role | Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Student** | `student@campusiq.edu` | `Password123!` | Query AI Assistant, View Sources, Give Feedback, Escalate Tickets |
| **Faculty** | `faculty@campusiq.edu` | `Password123!` | View Resolution Queue, Assign Tickets, Submit Authoritative Responses |
| **Admin** | `admin@campusiq.edu` | `Password123!` | Upload & Reindex PDFs, Delete Documents, Oversee Tickets, View Analytics |

---

## 7. Kubernetes & Minikube Demonstration

```mermaid
flowchart LR
    Ingress["Minikube Ingress (campusiq.local)"] --> SvcFE["frontend-service:3000"]
    Ingress --> SvcBE["backend-service:8000"]
    SvcBE --> PodBE1["backend-deployment (Pod 1)"]
    SvcBE --> PodBE2["backend-deployment (Pod 2)"]
    PodBE1 --> SvcChroma["chromadb-service:8000"]
    PodBE2 --> SvcChroma["chromadb-service:8000"]
```

### 1. Start Minikube & Enable Addons
```powershell
minikube start --driver=docker
minikube addons enable ingress
minikube addons enable metrics-server
```

### 2. Build or Load Images into Minikube
```powershell
# Point Docker CLI to Minikube's Docker daemon
minikube -p minikube docker-env --shell powershell | Invoke-Expression

# Build images directly in Minikube's daemon
docker build -t campusiq-backend:v1 -f backend/Dockerfile .
docker build -t campusiq-frontend:v1 -f frontend/Dockerfile .
```

### 3. Deploy CampusIQ Manifests
```powershell
kubectl apply -k k8s/
```

### 4. Verify Deployments, Pods, and Services
```powershell
kubectl get pods -n campusiq -o wide
kubectl get svc -n campusiq
kubectl get ingress -n campusiq
```

### 5. Demonstrate Kubernetes Self-Healing
```powershell
# Pick a running backend pod and delete it
kubectl delete pod <backend-pod-name> -n campusiq

# Immediately verify that Kubernetes automatically provisions a replacement replica
kubectl get pods -n campusiq -w
```

### 6. Demonstrate Manual Replica Scaling & HPA
```powershell
# Scale backend replicas to 4
kubectl scale deployment backend-deployment -n campusiq --replicas=4

# Inspect active HPA status
kubectl get hpa -n campusiq
```

### 7. Demonstrate Rolling Updates & Rollback
```powershell
# Update image version
kubectl set image deployment/backend-deployment backend=campusiq-backend:v2 -n campusiq

# Observe rollout status
kubectl rollout status deployment/backend-deployment -n campusiq

# Rollback update if needed
kubectl rollout undo deployment/backend-deployment -n campusiq
```

---

## 8. Monitoring & Observability

- **Metrics Endpoint**: FastAPI automatically exposes Prometheus metrics at `/metrics`.
- **Liveness Probe**: `GET /health/live`
- **Readiness Probe**: `GET /health/ready` (validates live connectivity to Supabase and ChromaDB).
- **Grafana Visualizations**: Import `monitoring/grafana-dashboard.json` into Grafana to inspect real-time HTTP request throughput, P95 latency percentiles, error rates, and memory consumption.
"# acc-proj" 

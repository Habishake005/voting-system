# DevOps Voting System

A cloud-native voting system built with microservices, 
containerized with Docker, and orchestrated with Kubernetes.
Demonstrates auto-scaling, self-healing, CI/CD, and monitoring.

## Architecture
- **Frontend** — HTML/CSS/JS served by Nginx
- **Auth Service** — FastAPI, JWT authentication
- **Voting Service** — FastAPI, duplicate vote prevention
- **Analytics Service** — FastAPI, live vote counts
- **Database** — PostgreSQL (persistent), Redis (cache)
- **Orchestration** — Kubernetes with HPA auto-scaling
- **CI/CD** — GitHub Actions
- **Monitoring** — Prometheus + Grafana

## Features Demonstrated
- Auto-scaling: pods scale 1→5 under load (HPA)
- Self-healing: Kubernetes restarts crashed pods automatically
- CI/CD: code push triggers automatic build and deploy
- Microservices: independent deployable services

## Tech Stack
Docker · Kubernetes · Python FastAPI · PostgreSQL · 
Redis · Nginx · GitHub Actions · Prometheus · Grafana · k6

## How to Run Locally
```bash
cd docker
docker-compose up --build
# Open http://localhost:3000
```

## Kubernetes Deployment
```bash
minikube start --driver=docker --memory=1900 --cpus=2
kubectl apply -f k8s/
minikube service frontend --url
```

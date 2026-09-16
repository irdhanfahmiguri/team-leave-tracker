# Product Requirement Document (PRD) - Team Leave Tracker

## 1. Overview
A browser-based team leave management application for a single team.

## 2. Key Requirements
- **Health Check:** Served at GET /health
- **Backend API:** Served at /api/leaves
- **Port:** EXPOSE 8000
- **Features:** Leave request & approval, daily overlap quota limit (default 2), status audit trail, CSV export capability.
# MEDORA Frontend

React + Vite + TypeScript frontend for the MEDORA multi-agent healthcare backend.

## Setup

```bash
npm install
```

## Environment

Copy `.env.example` to `.env` and optionally set:

- `VITE_API_BASE_URL` – Backend API base URL. Leave empty in development to use the Vite proxy (`/api` → `http://localhost:8000`).

## Run

```bash
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). Ensure the MEDORA backend is running on port 8000 (or set `VITE_API_BASE_URL` to your backend URL).

## Build

```bash
npm run build
```

Output is in `dist/`. Serve with any static host or `npm run preview`.

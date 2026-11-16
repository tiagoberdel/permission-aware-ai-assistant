
# Andino Secure AI — Frontend

React + TypeScript frontend for Andino Secure AI, a permission-aware enterprise AI assistant.

## Tech Stack

- React
- TypeScript
- Vite
- Tailwind CSS

## Requirements

- Node.js 24+
- npm
- Andino backend running on port 8000

## Setup

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend runs at `http://localhost:5173`.

## Backend Integration

Vite proxies requests from `/api` to `http://localhost:8000`.

The frontend communicates with two endpoints:

- `POST /demo/sessions` — creates an isolated demo session for a selected user.
- `POST /agent/ask` — sends a question using that session's bearer token.

Each demo user has an independent session and conversation history.

Authorization is enforced by the backend. The frontend does not determine or enforce document permissions.

## Available Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start development server |
| `npm run lint` | Run ESLint |
| `npm run build` | Type-check and build production assets |
| `npm run preview` | Preview production build |

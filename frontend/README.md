# SHIP — Frontend

The web dashboard for **Self-Healing Infrastructure Platform (SHIP)**, a self-healing infrastructure monitoring and remediation project.

## Overview

The frontend provides a dashboard for monitoring service health, reviewing incidents, and tracking automated remediation results.

It communicates with the SHIP FastAPI backend to retrieve live operational data.

## Features

- Service health and availability overview
- Active incident counts and incident history
- Remediation success rate and attempt statistics
- Automatic dashboard refresh every 15 seconds
- Manual dashboard refresh
- API connection error handling
- Responsive dark-themed interface

## Technology Stack

- React
- TypeScript
- Vite
- Lucide React

## Prerequisites

- Node.js and npm
- The SHIP backend running locally at `http://localhost:8000`

## Getting Started

From the `frontend/` directory, install the dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Open `http://localhost:5173` in your browser.

## Available Commands

| Command | Description |
|---|---|
| `npm run dev` | Start the development server |
| `npm run build` | Type-check and build the production bundle |
| `npx tsc --noEmit` | Check TypeScript without generating output |
| `npm run preview` | Preview the production build locally |

## Backend Integration

The frontend retrieves data from the following API endpoints:

- `GET /dashboard/summary` — service, incident, and remediation metrics
- `GET /services` — monitored service status
- `GET /incidents` — incident history and remediation attempts

The current development configuration uses `http://localhost:8000` as the API base URL. The backend must be running and configured to allow requests from `http://localhost:5173`.

## Project Structure

```text
frontend/
├── public/          # Static assets
├── src/
│   ├── assets/      # Application assets
│   ├── App.tsx      # Dashboard interface
│   ├── App.css      # Dashboard styles
│   ├── api.ts       # Backend API client and TypeScript interfaces
│   ├── index.css    # Global styles
│   └── main.tsx     # Application entry point
├── index.html
├── package.json
└── vite.config.ts
```

## Production Build

Generate the production bundle with:

```bash
npm run build
```

The generated files are written to `dist/`. This directory is a build artifact and should not be committed to Git.

---

SHIP is a portfolio project focused on infrastructure monitoring, automated recovery, and operational visibility.
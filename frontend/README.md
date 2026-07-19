# Frontend — Enterprise AI Insurance Assistant

Vite + React demo UI for Phase 5: login, chat (`POST /ask`), role badge, and audit logs.

## Run

```bash
# Terminal 1 — API
cd ..
uv run uvicorn app.main:app --reload --port 8000

# Terminal 2 — UI
npm install
npm run dev
# open http://localhost:5173
```

## Config

In local dev, leave `VITE_API_BASE_URL` empty (default). Vite proxies `/ask`, `/auth`, `/logs`, etc. to `http://127.0.0.1:8000`, which avoids `localhost` / CORS fetch failures in the browser.

Only set an absolute URL if you host the built UI separately from FastAPI:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Demo users

| Username   | Password       | Role     |
|------------|----------------|----------|
| `agent`    | `agent123`     | agent    |
| `adjuster` | `adjuster123`  | adjuster |
| `manager`  | `manager123`   | manager  |

Session is stored in `localStorage` (`insurance_assistant_session`). Use **Log out** to clear it.

## Scripts

- `npm run dev` — Vite dev server
- `npm run build` — production build
- `npm run lint` — Oxlint
- `npm run preview` — preview production build

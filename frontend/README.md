# CampusFix frontend

The frontend is a React 19 single-page application built with Vite. Its `src/features` folders contain the student, staff, admin, and authentication screens. `src/context/AuthContext.jsx` manages the session, while `src/services/api.js` provides the shared authenticated API client.

## Run locally

```powershell
npm install
npm run dev
```

By default, API requests go to `http://127.0.0.1:8000/api/v1`. To use another backend, create a `.env` file in this directory:

```dotenv
VITE_API_URL=http://127.0.0.1:8000/api/v1
```

The category suggestion screen calls `/ml/predict` on the backend. The backend connects that endpoint to the top-level `ml/` package, so run the API from the repository backend setup rather than starting the semantic model as a separate service.

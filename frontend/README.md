# OTM Workbench GUI

Browser-first React shell for OTM Workbench.

The GUI consumes backend-owned contracts for navigation, active context,
preferences, jobs, artifacts, evidence, and module actions. Product modules
must use the Workbench UI Kit layer instead of importing raw third-party UI
primitives directly.

## Scripts

```bash
npm install
npm run dev
npm run build
npm run test
```

The Vite dev server proxies `/api` and `/health` to the local FastAPI backend
at `http://127.0.0.1:8000`.

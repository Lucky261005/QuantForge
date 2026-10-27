# QuantForge frontend

Next.js 14 (App Router) + TypeScript + Tailwind CSS. See the [project root README](../README.md)
for the full picture — quickstart, architecture, and links to `docs/`.

```bash
npm install
npm run dev            # http://localhost:3000
npm run type-check      # tsc --noEmit
npm run lint
npm run build
```

Set `NEXT_PUBLIC_API_URL` (in `.env.local`) to point at the backend, e.g.
`http://localhost:8000/api/v1`.

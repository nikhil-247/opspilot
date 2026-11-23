# OpsPilot Web Console

A live Next.js console backed by the OpsPilot FastAPI API. It does not render static incident samples.

## Features

- Workspace registration and sign-in through backend authentication.
- JWT kept in a server-set HttpOnly cookie, not local storage.
- Same-origin Next.js API proxy forwards requests to FastAPI.
- Incident list with API-backed status and priority filters.
- Incident details, acknowledge/resolve actions and audit timeline.
- Event explorer with a real event-ingestion form.
- Tenant-scoped service dependency registry.
- Workspace member list and role management.

## Local development

Install Node.js 22 or later, then:

\`\`\`bash
npm install
npm run dev
\`\`\`

The UI proxy defaults to http://127.0.0.1:8000. Start the API separately and set API_URL to a different API address if needed.

## Security notes

The JWT cookie is HttpOnly, SameSite=Lax and Secure in production. The API validates the token and re-checks current membership role on every request. A public deployment still needs HTTPS, CSRF protection for state-changing browser routes, rate limiting and a managed secret store.

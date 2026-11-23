# OpsPilot Web Console

The frontend is intentionally not a static mockup. It will be implemented after the first backend vertical slice is stable and will call the real `/api/v1` endpoints.

Planned stack: Next.js App Router, TypeScript, Tailwind CSS, and a typed API client.

Initial screens:

- Live incident overview backed by `GET /api/v1/incidents`.
- Incident detail and audit timeline backed by the incident detail/activity endpoints.
- Event explorer backed by `GET /api/v1/events`.
- Acknowledgement and resolution actions backed by the corresponding `POST` endpoints.
- Event simulator that submits real events to `POST /api/v1/events` for local demonstrations.

No demo cards or fake incident metrics will be presented as live data.

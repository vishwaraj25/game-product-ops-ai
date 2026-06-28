import { BackendHealth } from "@/components/backend-health";

export default function Home() {
  return (
    <main className="shell">
      <div className="workspace">
        <header className="header">
          <div>
            <p className="eyebrow">Sprint 1 Foundation</p>
            <h1>Game Product Ops AI</h1>
            <p className="subtitle">
              A development foundation for an autonomous product operations
              agent. Sprint 1 verifies the web console, API service, and
              database are ready for future investigation workflows.
            </p>
          </div>
          <span className="badge">Foundation Ready</span>
        </header>

        <section className="status-grid" aria-label="System status">
          <BackendHealth />
          <div className="panel">
            <h2>Frontend</h2>
            <p>
              <strong className="status-ok">Ready.</strong> Next.js is serving
              the product console.
            </p>
          </div>
          <div className="panel">
            <h2>Database</h2>
            <p>
              PostgreSQL is configured through Docker Compose and checked by
              the backend health endpoint.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}

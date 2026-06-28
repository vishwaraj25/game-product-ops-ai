"use client";

import { useEffect, useState } from "react";

type HealthState =
  | { status: "loading" }
  | { status: "ok"; service: string; version: string }
  | { status: "error"; message: string };

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function BackendHealth() {
  const [health, setHealth] = useState<HealthState>({ status: "loading" });

  useEffect(() => {
    let isMounted = true;

    async function loadHealth() {
      try {
        const response = await fetch(`${apiBaseUrl}/health`, {
          cache: "no-store",
        });

        if (!response.ok) {
          throw new Error(`Backend returned ${response.status}`);
        }

        const data = (await response.json()) as {
          service: string;
          version: string;
        };

        if (isMounted) {
          setHealth({
            status: "ok",
            service: data.service,
            version: data.version,
          });
        }
      } catch (error) {
        if (isMounted) {
          setHealth({
            status: "error",
            message:
              error instanceof Error
                ? error.message
                : "Unable to reach backend",
          });
        }
      }
    }

    loadHealth();

    return () => {
      isMounted = false;
    };
  }, []);

  if (health.status === "loading") {
    return (
      <div className="panel">
        <h2>Backend</h2>
        <p>
          <strong className="status-waiting">Checking.</strong> Waiting for the
          API health endpoint.
        </p>
      </div>
    );
  }

  if (health.status === "error") {
    return (
      <div className="panel">
        <h2>Backend</h2>
        <p>
          <strong className="status-waiting">Unavailable.</strong>{" "}
          {health.message}
        </p>
      </div>
    );
  }

  return (
    <div className="panel">
      <h2>Backend</h2>
      <p>
        <strong className="status-ok">Connected.</strong> {health.service}{" "}
        v{health.version}
      </p>
    </div>
  );
}

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, apiPost } from "../../lib/api-client";
import { saveSession } from "../../lib/session";

interface AuthResponse {
  token: string;
  user: {
    id: string;
    email: string;
    fullName: string;
  };
  workspace: {
    id: string;
    name: string;
  };
}

interface RegisterPayload {
  email: string;
  password: string;
  fullName: string;
  workspaceName: string;
}

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [fullName, setFullName] = useState("Carlos Silva");
  const [workspaceName, setWorkspaceName] = useState("Authority Lab");
  const [email, setEmail] = useState("founder@sa.local");
  const [password, setPassword] = useState("ChangeMe123");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <main className="min-h-screen sa-grid flex items-center justify-center px-4">
      <section className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl">
        <h1 className="text-2xl font-semibold text-ink">SA SaaS Access</h1>
        <p className="mt-2 text-sm text-slate-600">Authenticate to run social authority workflows with API-backed data.</p>

        <div className="mt-4 grid grid-cols-2 gap-2 rounded-xl bg-slate-100 p-1 text-sm">
          <button
            type="button"
            className={`rounded-lg px-3 py-2 ${mode === "login" ? "bg-white text-ink shadow-sm" : "text-slate-600"}`}
            onClick={() => setMode("login")}
          >
            Login
          </button>
          <button
            type="button"
            className={`rounded-lg px-3 py-2 ${mode === "register" ? "bg-white text-ink shadow-sm" : "text-slate-600"}`}
            onClick={() => setMode("register")}
          >
            Register
          </button>
        </div>

        <form
          className="mt-6 space-y-4"
          onSubmit={async (event) => {
            event.preventDefault();
            setIsSubmitting(true);
            setError(null);

            try {
              const path = mode === "login" ? "/api/auth/login" : "/api/auth/register";
              const payload: RegisterPayload | { email: string; password: string } =
                mode === "login"
                  ? {
                      email,
                      password
                    }
                  : {
                      email,
                      password,
                      fullName,
                      workspaceName
                    };

              const response = await apiPost<typeof payload, AuthResponse>(path, payload);
              saveSession(response);
              router.replace("/dashboard");
            } catch (caughtError) {
              if (caughtError instanceof ApiError) {
                setError(caughtError.message);
              } else if (caughtError instanceof TypeError) {
                setError("Cannot reach API. Ensure backend is running at http://localhost:4000.");
              } else {
                setError("Unexpected error while authenticating");
              }
            } finally {
              setIsSubmitting(false);
            }
          }}
        >
          {mode === "register" ? (
            <>
              <label className="block text-sm font-medium text-slate-700">
                Full name
                <input
                  className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 outline-none focus:border-signal"
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                  type="text"
                  minLength={3}
                  required
                />
              </label>
              <label className="block text-sm font-medium text-slate-700">
                Workspace
                <input
                  className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 outline-none focus:border-signal"
                  value={workspaceName}
                  onChange={(event) => setWorkspaceName(event.target.value)}
                  type="text"
                  minLength={2}
                  required
                />
              </label>
            </>
          ) : null}

          <label className="block text-sm font-medium text-slate-700">
            Email
            <input
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 outline-none focus:border-signal"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              type="email"
              required
            />
          </label>

          <label className="block text-sm font-medium text-slate-700">
            Password
            <input
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 outline-none focus:border-signal"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              required
            />
          </label>

          {error ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p> : null}

          <button
            className="w-full rounded-xl bg-ink px-4 py-2 text-white transition hover:bg-slate-900 disabled:cursor-not-allowed disabled:bg-slate-400"
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Processing..." : mode === "login" ? "Enter Control Room" : "Create Workspace"}
          </button>
        </form>
      </section>
    </main>
  );
}

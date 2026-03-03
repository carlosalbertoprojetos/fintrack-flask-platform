export interface SessionUser {
  id: string;
  email: string;
  fullName: string;
}

export interface SessionWorkspace {
  id: string;
  name: string;
}

export interface SessionData {
  token: string;
  user: SessionUser;
  workspace: SessionWorkspace;
}

const SESSION_KEY = "sa_session";

export function saveSession(session: SessionData): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function loadSession(): SessionData | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.localStorage.getItem(SESSION_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as SessionData;
  } catch {
    return null;
  }
}

export function clearSession(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(SESSION_KEY);
}

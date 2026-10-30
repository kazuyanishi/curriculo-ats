import { Job } from "./types";

const STORAGE_KEY = "resume-ai:job:v1";

function isJob(value: unknown): value is Job {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return false;
  const record = value as Record<string, unknown>;
  return ["title", "company", "location", "source_url", "description"].every(field => typeof record[field] === "string");
}

export function loadStoredJob(): Job | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const value: unknown = JSON.parse(raw);
    return isJob(value) ? value : null;
  } catch {
    return null;
  }
}

export function saveStoredJob(job: Job): void {
  if (typeof window === "undefined") return;
  try { window.localStorage.setItem(STORAGE_KEY, JSON.stringify(job)); } catch { /* optional browser storage */ }
}

export function clearStoredJob(): void {
  if (typeof window === "undefined") return;
  try { window.localStorage.removeItem(STORAGE_KEY); } catch { /* optional browser storage */ }
}

import { Candidate } from "./types";

const STORAGE_KEY = "resume-ai:candidate:v1";
type StoredCandidateV1 = { version: 1; candidate: Candidate };

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isCandidate(value: unknown): value is Candidate {
  if (!isObject(value)) return false;
  const collections = ["experiences", "education", "skills", "technologies", "tools", "languages", "certifications", "projects"];
  return isObject(value.personal_info) && isObject(value.contact_info) && collections.every(key => Array.isArray(value[key]));
}

export function loadStoredCandidate(): Candidate | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed: unknown = JSON.parse(raw);
    if (!isObject(parsed) || parsed.version !== 1 || !isCandidate(parsed.candidate)) {
      window.localStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return parsed.candidate;
  } catch { return null; }
}

export function saveStoredCandidate(candidate: Candidate): void {
  if (typeof window === "undefined") return;
  try {
    const payload: StoredCandidateV1 = { version: 1, candidate };
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  } catch { /* optional browser storage */ }
}

export function clearStoredCandidate(): void {
  if (typeof window === "undefined") return;
  try { window.localStorage.removeItem(STORAGE_KEY); } catch { /* optional browser storage */ }
}

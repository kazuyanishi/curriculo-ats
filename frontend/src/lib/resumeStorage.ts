export type StoredResumeMetadata = {
  fileName: string;
  savedAt: string;
};

const STORAGE_KEY = "resume-ai:resume-metadata:v1";

function isMetadata(value: unknown): value is StoredResumeMetadata {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return false;
  const record = value as Record<string, unknown>;
  return typeof record.fileName === "string" && typeof record.savedAt === "string";
}

export function loadStoredResumeMetadata(): StoredResumeMetadata | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const value: unknown = JSON.parse(raw);
    return isMetadata(value) ? value : null;
  } catch {
    return null;
  }
}

export function saveStoredResumeMetadata(fileName: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ fileName, savedAt: new Date().toISOString() }));
  } catch { /* optional browser storage */ }
}

export function clearStoredResumeMetadata(): void {
  if (typeof window === "undefined") return;
  try { window.localStorage.removeItem(STORAGE_KEY); } catch { /* optional browser storage */ }
}

import { CandidateImportIssue, CandidateImportIssueCode } from "./types";

const STORAGE_KEY = "resume-ai:candidate-import-review:v1";
const ISSUE_CODES: CandidateImportIssueCode[] = [
  "missing_required_field",
  "unsupported_date_format",
  "unsupported_education_status",
  "unsupported_proficiency_level",
  "unsupported_language_level",
];

export type CandidateImportReviewState = {
  issues: CandidateImportIssue[];
  review_paths: string[];
};

type StoredReviewState = CandidateImportReviewState & { version: 1 };
type RecordValue = Record<string, unknown>;

function isObject(value: unknown): value is RecordValue {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isIssue(value: unknown): value is CandidateImportIssue {
  if (!isObject(value)) return false;
  return typeof value.path === "string"
    && typeof value.code === "string"
    && ISSUE_CODES.includes(value.code as CandidateImportIssueCode)
    && (value.raw_value === null || typeof value.raw_value === "string");
}

function isReviewState(value: unknown): value is StoredReviewState {
  return isObject(value)
    && value.version === 1
    && Array.isArray(value.issues)
    && value.issues.every(isIssue)
    && Array.isArray(value.review_paths)
    && value.review_paths.every(path => typeof path === "string");
}

function removeStoredReview(): void {
  try { window.localStorage.removeItem(STORAGE_KEY); } catch { /* optional browser storage */ }
}

export function loadStoredCandidateImportReview(): CandidateImportReviewState | null {
  if (typeof window === "undefined") return null;
  let raw: string | null;
  try { raw = window.localStorage.getItem(STORAGE_KEY); } catch { return null; }
  if (!raw) return null;
  let parsed: unknown;
  try { parsed = JSON.parse(raw); } catch { removeStoredReview(); return null; }
  if (!isReviewState(parsed)) { removeStoredReview(); return null; }
  return { issues: [...parsed.issues], review_paths: [...parsed.review_paths] };
}

export function saveStoredCandidateImportReview(state: CandidateImportReviewState): void {
  if (typeof window === "undefined") return;
  if (state.issues.length === 0 && state.review_paths.length === 0) {
    removeStoredReview();
    return;
  }
  const payload: StoredReviewState = {
    version: 1,
    issues: [...state.issues],
    review_paths: [...state.review_paths],
  };
  try { window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload)); } catch { /* optional browser storage */ }
}

export function clearStoredCandidateImportReview(): void {
  if (typeof window === "undefined") return;
  removeStoredReview();
}

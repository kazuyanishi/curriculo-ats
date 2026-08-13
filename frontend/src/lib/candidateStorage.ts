import { Candidate } from "./types";

const STORAGE_KEY = "resume-ai:candidate:v1";
type StoredCandidateV1 = { version: 1; candidate: Candidate };
type RecordValue = Record<string, unknown>;

function isObject(value: unknown): value is RecordValue {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isString(value: unknown): value is string {
  return typeof value === "string";
}

function isNullableString(value: unknown): value is string | null {
  return value === null || isString(value);
}

function hasStrings(value: RecordValue, fields: string[]): boolean {
  return fields.every(field => isString(value[field]));
}

function isDescriptionList(value: unknown): boolean {
  return Array.isArray(value) && value.every(item => isObject(item) && isString(item.description));
}

function isExperience(value: unknown): boolean {
  return isObject(value) && hasStrings(value, ["company", "role", "start_date"]) && isNullableString(value.end_date) && isDescriptionList(value.activities) && isDescriptionList(value.achievements);
}

function isEducation(value: unknown): boolean {
  return isObject(value) && hasStrings(value, ["institution", "course"]) && ["", "in_progress", "completed", "interrupted"].includes(String(value.status)) && isNullableString(value.start_date) && isNullableString(value.end_date);
}

function isNamedItem(value: unknown): boolean {
  return isObject(value) && isString(value.name) && (value.level === null || ["basic", "intermediate", "advanced", "expert"].includes(String(value.level)));
}

function isLanguage(value: unknown): boolean {
  return isObject(value) && isString(value.name) && (value.level === null || ["basic", "intermediate", "advanced", "fluent", "native"].includes(String(value.level)));
}

function isCertification(value: unknown): boolean {
  return isObject(value) && hasStrings(value, ["name", "issuer"]) && isNullableString(value.issue_date) && isNullableString(value.expiration_date) && isNullableString(value.credential_id) && isNullableString(value.credential_url);
}

function isProject(value: unknown): boolean {
  return isObject(value) && hasStrings(value, ["name", "description"]) && isNullableString(value.start_date) && isNullableString(value.end_date) && Array.isArray(value.technologies) && value.technologies.every(isString) && isNullableString(value.url);
}

function isCandidate(value: unknown): value is Candidate {
  if (!isObject(value)) return false;
  const personalInfo = value.personal_info;
  const contactInfo = value.contact_info;
  const links = value.professional_links;
  return isObject(personalInfo) && hasStrings(personalInfo, ["full_name", "city", "state", "country"]) && isObject(contactInfo) && hasStrings(contactInfo, ["email", "phone"]) && isObject(links) && ["linkedin", "github", "portfolio"].every(field => isNullableString(links[field])) && Array.isArray(value.experiences) && value.experiences.every(isExperience) && Array.isArray(value.education) && value.education.every(isEducation) && Array.isArray(value.skills) && value.skills.every(isNamedItem) && Array.isArray(value.technologies) && value.technologies.every(isNamedItem) && Array.isArray(value.tools) && value.tools.every(isNamedItem) && Array.isArray(value.languages) && value.languages.every(isLanguage) && Array.isArray(value.certifications) && value.certifications.every(isCertification) && Array.isArray(value.projects) && value.projects.every(isProject);
}

function removeStoredCandidate(): void {
  try { window.localStorage.removeItem(STORAGE_KEY); } catch { /* optional browser storage */ }
}

export function loadStoredCandidate(): Candidate | null {
  if (typeof window === "undefined") return null;
  let raw: string | null;
  try { raw = window.localStorage.getItem(STORAGE_KEY); } catch { return null; }
  if (!raw) return null;
  let parsed: unknown;
  try { parsed = JSON.parse(raw); } catch { removeStoredCandidate(); return null; }
  if (!isObject(parsed) || parsed.version !== 1 || !isCandidate(parsed.candidate)) { removeStoredCandidate(); return null; }
  return parsed.candidate;
}

export function saveStoredCandidate(candidate: Candidate): void {
  if (typeof window === "undefined") return;
  try { const payload: StoredCandidateV1 = { version: 1, candidate }; window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload)); } catch { /* optional browser storage */ }
}

export function clearStoredCandidate(): void {
  if (typeof window === "undefined") return;
  removeStoredCandidate();
}

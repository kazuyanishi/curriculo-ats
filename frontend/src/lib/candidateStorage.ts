import { Candidate } from "./types";

const STORAGE_KEY = "resume-ai:candidate:v2";
const LEGACY_STORAGE_KEY = "resume-ai:candidate:v1";
type StoredCandidate = { version: 2; candidate: Candidate };
type RecordValue = Record<string, unknown>;

function isObject(value: unknown): value is RecordValue { return typeof value === "object" && value !== null && !Array.isArray(value); }
function isString(value: unknown): value is string { return typeof value === "string"; }
function isNullableString(value: unknown): value is string | null { return value === null || isString(value); }
function hasStrings(value: RecordValue, fields: string[]): boolean { return fields.every(field => isString(value[field])); }
function isMonth(value: unknown): value is string { return isString(value) && (/^\d{4}-(0[1-9]|1[0-2])$/.test(value) || value === ""); }
function isNullableMonth(value: unknown): value is string | null { return value === null || isMonth(value); }
function isDescriptionList(value: unknown): boolean { return Array.isArray(value) && value.every(item => isObject(item) && isString(item.description)); }
function isExperience(value: unknown): boolean { return isObject(value) && hasStrings(value, ["company", "role"]) && isMonth(value.start_date) && isNullableMonth(value.end_date) && isDescriptionList(value.activities) && isDescriptionList(value.achievements); }
function isEducation(value: unknown): boolean { return isObject(value) && hasStrings(value, ["institution", "course"]) && ["", "in_progress", "completed", "interrupted"].includes(String(value.status)) && isNullableMonth(value.start_date) && isNullableMonth(value.end_date); }
function isNamedItem(value: unknown): boolean { return isObject(value) && isString(value.name) && (value.level === null || ["basic", "intermediate", "advanced", "expert"].includes(String(value.level))); }
function isLanguage(value: unknown): boolean { return isObject(value) && isString(value.name) && (value.level === null || ["basic", "intermediate", "advanced", "fluent", "native"].includes(String(value.level))); }
function isCertification(value: unknown): boolean { return isObject(value) && hasStrings(value, ["name", "issuer"]) && isNullableString(value.issue_date) && isNullableString(value.expiration_date) && isNullableString(value.credential_id) && isNullableString(value.credential_url); }
function isProject(value: unknown): boolean { return isObject(value) && hasStrings(value, ["name", "description"]) && isNullableMonth(value.start_date) && isNullableMonth(value.end_date) && Array.isArray(value.technologies) && value.technologies.every(isString) && isNullableString(value.url); }
function isCandidate(value: unknown): value is Candidate {
  if (!isObject(value)) return false;
  const personalInfo = value.personal_info;
  const contactInfo = value.contact_info;
  const links = value.professional_links;
  return isObject(personalInfo) && hasStrings(personalInfo, ["full_name", "city", "state", "country"]) && isObject(contactInfo) && hasStrings(contactInfo, ["email", "phone"]) && isObject(links) && ["linkedin", "github", "portfolio"].every(field => isNullableString(links[field])) && Array.isArray(value.experiences) && value.experiences.every(isExperience) && Array.isArray(value.education) && value.education.every(isEducation) && Array.isArray(value.skills) && value.skills.every(isNamedItem) && Array.isArray(value.technologies) && value.technologies.every(isNamedItem) && Array.isArray(value.tools) && value.tools.every(isNamedItem) && Array.isArray(value.languages) && value.languages.every(isLanguage) && Array.isArray(value.certifications) && value.certifications.every(isCertification) && Array.isArray(value.projects) && value.projects.every(isProject);
}
function isLegacyCandidate(value: unknown): value is Candidate {
  if (!isObject(value)) return false;
  const collections = ["experiences", "education", "skills", "technologies", "tools", "languages", "certifications", "projects"];
  return isObject(value.personal_info) && isObject(value.contact_info) && isObject(value.professional_links)
    && collections.every(name => Array.isArray(value[name]) && value[name].every(isObject));
}
function isValidIsoDate(value: string): boolean {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) return false;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  if (year < 1 || month < 1 || month > 12 || day < 1) return false;
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const daysInMonth = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1];
  return day <= daysInMonth;
}
function toMonth(value: unknown): unknown { return isString(value) && /^\d{4}-\d{2}-\d{2}$/.test(value) && isValidIsoDate(value) ? value.slice(0, 7) : value; }
function migrateCandidate(candidate: Candidate): Candidate {
  return { ...candidate, experiences: candidate.experiences.map(item => ({ ...item, start_date: String(toMonth(item.start_date)), end_date: item.end_date === null ? null : String(toMonth(item.end_date)) })), education: candidate.education.map(item => ({ ...item, start_date: item.start_date === null ? null : String(toMonth(item.start_date)), end_date: item.end_date === null ? null : String(toMonth(item.end_date)) })), projects: candidate.projects.map(item => ({ ...item, start_date: item.start_date === null ? null : String(toMonth(item.start_date)), end_date: item.end_date === null ? null : String(toMonth(item.end_date)) })) };
}
function removeStoredCandidate(): void { try { window.localStorage.removeItem(STORAGE_KEY); window.localStorage.removeItem(LEGACY_STORAGE_KEY); } catch { /* optional browser storage */ } }
function readStored(key: string): { version: number; candidate: Candidate } | null {
  let raw: string | null;
  try { raw = window.localStorage.getItem(key); } catch { return null; }
  if (!raw) return null;
  try { const parsed: unknown = JSON.parse(raw); return isObject(parsed) && typeof parsed.version === "number" && (isCandidate(parsed.candidate) || (parsed.version === 1 && isLegacyCandidate(parsed.candidate))) ? { version: parsed.version, candidate: parsed.candidate } : null; } catch { return null; }
}
export function loadStoredCandidate(): Candidate | null {
  if (typeof window === "undefined") return null;
  const current = readStored(STORAGE_KEY);
  if (current?.version === 2) return current.candidate;
  const legacy = readStored(LEGACY_STORAGE_KEY);
  if (legacy?.version === 1) { const migrated = migrateCandidate(legacy.candidate); if (isCandidate(migrated)) { saveStoredCandidate(migrated); try { window.localStorage.removeItem(LEGACY_STORAGE_KEY); } catch { /* optional browser storage */ } return migrated; } }
  if (current || legacy) removeStoredCandidate();
  return null;
}
export function saveStoredCandidate(candidate: Candidate): void { if (typeof window === "undefined") return; try { const payload: StoredCandidate = { version: 2, candidate }; window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload)); window.localStorage.removeItem(LEGACY_STORAGE_KEY); } catch { /* optional browser storage */ } }
export function clearStoredCandidate(): void { if (typeof window === "undefined") return; removeStoredCandidate(); }

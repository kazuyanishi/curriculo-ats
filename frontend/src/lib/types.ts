export type ProficiencyLevel = "basic" | "intermediate" | "advanced" | "expert";
export type LanguageLevel = "basic" | "intermediate" | "advanced" | "fluent" | "native";
export type EducationStatus = "in_progress" | "completed" | "interrupted";

export type PersonalInfo = { full_name: string; city: string; state: string; country: string };
export type ContactInfo = { email: string; phone: string };
export type ProfessionalLinks = { linkedin: string | null; github: string | null; portfolio: string | null };
export type Activity = { description: string };
export type Achievement = { description: string };
export type Experience = {
  company: string; role: string; start_date: string; end_date: string | null;
  activities: Activity[]; achievements: Achievement[];
};
export type Education = { institution: string; course: string; status: EducationStatus; start_date: string | null; end_date: string | null };
export type NamedItem = { name: string; level: ProficiencyLevel | null };
export type Language = { name: string; level: LanguageLevel | null };
export type Certification = {
  name: string; issuer: string; issue_date: string | null; expiration_date: string | null;
  credential_id: string | null; credential_url: string | null;
};
export type Project = { name: string; description: string; start_date: string | null; end_date: string | null; technologies: string[]; url: string | null };
export type Candidate = {
  personal_info: PersonalInfo; contact_info: ContactInfo; professional_links: ProfessionalLinks;
  experiences: Experience[]; education: Education[]; skills: NamedItem[]; technologies: NamedItem[];
  tools: NamedItem[]; languages: Language[]; certifications: Certification[]; projects: Project[];
};
export type Job = { title: string; company: string; location: string; source_url: string; description: string };
export type MatchStatus = "matched" | "not_matched" | "unsupported";
export type CriterionCategory = "skill" | "technology" | "tool" | "language" | "education" | "experience" | "certification" | "other";
export type CriterionImportance = "required" | "preferred" | "unspecified";
export type JobCriterionResponse = { category: CriterionCategory; value: string; evidence: string; importance: CriterionImportance };
export type CriterionMatchResponse = { criterion: JobCriterionResponse; status: MatchStatus };
export type MatchingScoreResponse = { score: number | null; coverage: number | null };
export type GapAnalysisResponse = { gaps: CriterionMatchResponse[]; unsupported: CriterionMatchResponse[] };
export type AnalyzeResponse = { criteria: JobCriterionResponse[]; matching: CriterionMatchResponse[]; score: MatchingScoreResponse; gaps: GapAnalysisResponse; optimized_candidate: Candidate };

export type CandidateImportIssueCode =
  | "missing_required_field"
  | "unsupported_date_format"
  | "unsupported_education_status"
  | "unsupported_proficiency_level"
  | "unsupported_language_level";
export type CandidateImportIssue = { path: string; code: CandidateImportIssueCode; raw_value: string | null };
export type PersonalInfoDraft = { full_name: string | null; city: string | null; state: string | null; country: string | null };
export type ContactInfoDraft = { email: string | null; phone: string | null };
export type ProfessionalLinksDraft = { linkedin: string | null; github: string | null; portfolio: string | null };
export type ExperienceDraft = {
  company: string | null; role: string | null; start_date: string | null; end_date: string | null;
  activities: string[]; achievements: string[];
};
export type EducationDraft = {
  institution: string | null; course: string | null; status: EducationStatus | null;
  start_date: string | null; end_date: string | null;
};
export type NamedItemDraft = { name: string; level: ProficiencyLevel | null };
export type LanguageDraft = { name: string; level: LanguageLevel | null };
export type CertificationDraft = {
  name: string | null; issuer: string | null; issue_date: string | null; expiration_date: string | null;
  credential_id: string | null; credential_url: string | null;
};
export type ProjectDraft = {
  name: string | null; description: string | null; start_date: string | null; end_date: string | null;
  technologies: string[]; url: string | null;
};
export type CandidateImportDraft = {
  personal_info: PersonalInfoDraft; contact_info: ContactInfoDraft; professional_links: ProfessionalLinksDraft;
  experiences: ExperienceDraft[]; education: EducationDraft[]; skills: NamedItemDraft[];
  technologies: NamedItemDraft[]; tools: NamedItemDraft[]; languages: LanguageDraft[];
  certifications: CertificationDraft[]; projects: ProjectDraft[]; issues: CandidateImportIssue[];
};

export type NormalizedCandidate = Omit<Candidate, "personal_info" | "contact_info" | "professional_links" | "experiences" | "education" | "skills" | "technologies" | "tools" | "languages" | "certifications" | "projects"> & {
  personal_info: PersonalInfo;
  contact_info: ContactInfo;
  professional_links: ProfessionalLinks;
  experiences: Experience[];
  education: Education[];
  skills: NamedItem[];
  technologies: NamedItem[];
  tools: NamedItem[];
  languages: Language[];
  certifications: Certification[];
  projects: Project[];
};

const optional = (value: string | null | undefined): string | null => value?.trim() ? value : null;

export const normalizeCandidatePayload = (candidate: Candidate): NormalizedCandidate => ({
  ...candidate,
  professional_links: {
    linkedin: optional(candidate.professional_links.linkedin),
    github: optional(candidate.professional_links.github),
    portfolio: optional(candidate.professional_links.portfolio),
  },
  experiences: candidate.experiences.map(experience => ({
    ...experience,
    end_date: optional(experience.end_date),
    activities: experience.activities.map(item => ({ description: item.description })),
    achievements: experience.achievements.map(item => ({ description: item.description })),
  })),
  education: candidate.education.map(item => ({ ...item, start_date: optional(item.start_date), end_date: optional(item.end_date) })),
  skills: candidate.skills.map(item => ({ ...item, level: item.level || null })),
  technologies: candidate.technologies.map(item => ({ ...item, level: item.level || null })),
  tools: candidate.tools.map(item => ({ ...item, level: item.level || null })),
  languages: candidate.languages.map(item => ({ ...item, level: item.level || null })),
  certifications: candidate.certifications.map(item => ({
    ...item,
    issue_date: optional(item.issue_date),
    expiration_date: optional(item.expiration_date),
    credential_id: optional(item.credential_id),
    credential_url: optional(item.credential_url),
  })),
  projects: candidate.projects.map(item => ({
    ...item,
    start_date: optional(item.start_date),
    end_date: optional(item.end_date),
    url: optional(item.url),
  })),
});

export const normalizeJobPayload = (job: Job): Omit<Job, "title" | "company" | "location" | "source_url"> & {
  title: string | null;
  company: string | null;
  location: string | null;
  source_url: string | null;
} => ({
  ...job,
  title: optional(job.title),
  company: optional(job.company),
  location: optional(job.location),
  source_url: optional(job.source_url),
});

export const emptyCandidate = (): Candidate => ({
  personal_info: { full_name: "", city: "", state: "", country: "" },
  contact_info: { email: "", phone: "" },
  professional_links: { linkedin: null, github: null, portfolio: null },
  experiences: [], education: [], skills: [], technologies: [], tools: [], languages: [], certifications: [], projects: [],
});

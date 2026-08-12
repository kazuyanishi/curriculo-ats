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

export const emptyCandidate = (): Candidate => ({
  personal_info: { full_name: "", city: "", state: "", country: "" },
  contact_info: { email: "", phone: "" },
  professional_links: { linkedin: null, github: null, portfolio: null },
  experiences: [], education: [], skills: [], technologies: [], tools: [], languages: [], certifications: [], projects: [],
});

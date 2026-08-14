import {
  Activity,
  Achievement,
  Candidate,
  CandidateImportDraft,
  CandidateImportIssue,
  Education,
} from "./types";

export type CandidateImportEditResult = {
  candidate: Candidate;
  issues: CandidateImportIssue[];
  review_paths: string[];
};

const textOrEmpty = (value: string | null): string => value ?? "";

export function candidateFromImportDraft(
  draft: CandidateImportDraft,
): CandidateImportEditResult {
  const review_paths: string[] = [];

  const experiences = draft.experiences.map((experience, index) => {
    const end_date = experience.end_date;
    if (end_date === null && !experience.is_current) {
      review_paths.push(`experiences[${index}].end_date`);
    }
    return {
      company: textOrEmpty(experience.company),
      role: textOrEmpty(experience.role),
      start_date: textOrEmpty(experience.start_date),
      end_date: end_date ?? "",
      activities: experience.activities.map((description): Activity => ({ description })),
      achievements: experience.achievements.map((description): Achievement => ({ description })),
    };
  });

  const education: Education[] = draft.education.map(item => ({
    institution: textOrEmpty(item.institution),
    course: textOrEmpty(item.course),
    status: item.status ?? "",
    start_date: item.start_date,
    end_date: item.end_date,
  }));

  return {
    candidate: {
      personal_info: {
        full_name: textOrEmpty(draft.personal_info.full_name),
        city: textOrEmpty(draft.personal_info.city),
        state: textOrEmpty(draft.personal_info.state),
        country: textOrEmpty(draft.personal_info.country),
      },
      contact_info: {
        email: textOrEmpty(draft.contact_info.email),
        phone: textOrEmpty(draft.contact_info.phone),
      },
      professional_links: { ...draft.professional_links },
      experiences,
      education,
      skills: draft.skills.map(item => ({ ...item })),
      technologies: draft.technologies.map(item => ({ ...item })),
      tools: draft.tools.map(item => ({ ...item })),
      languages: draft.languages.map(item => ({ ...item })),
      certifications: draft.certifications.map(item => ({
        name: textOrEmpty(item.name),
        issuer: textOrEmpty(item.issuer),
        issue_date: item.issue_date,
        expiration_date: item.expiration_date,
        credential_id: item.credential_id,
        credential_url: item.credential_url,
      })),
      projects: draft.projects.map(item => ({
        name: textOrEmpty(item.name),
        description: textOrEmpty(item.description),
        start_date: item.start_date,
        end_date: item.end_date,
        technologies: [...item.technologies],
        url: item.url,
      })),
    },
    issues: [...draft.issues],
    review_paths,
  };
}

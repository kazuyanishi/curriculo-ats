import { Candidate, Job } from "./types";

export type CandidateValidationIssue = { path: string; message: string };

const isBlank = (value: string | null | undefined): boolean => !value?.trim();
const isMonth = (value: string): boolean => /^\d{4}-(0[1-9]|1[0-2])$/.test(value);
const isDate = (value: string): boolean => {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) return false;
  const year = Number(match[1]); const month = Number(match[2]); const day = Number(match[3]);
  if (year < 1 || month < 1 || month > 12 || day < 1) return false;
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  return day <= [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1];
};
const validEmail = (value: string): boolean => { const [local, domain, extra] = value.split("@"); return Boolean(local && domain && !extra); };

export function validateCandidateForAnalysis(candidate: Candidate, job: Job): CandidateValidationIssue[] {
  const issues: CandidateValidationIssue[] = [];
  const required = (path: string, label: string, value: string | null | undefined) => { if (isBlank(value)) issues.push({ path, message: `${label} — obrigatório` }); };
  const optionalMonth = (path: string, label: string, value: string | null) => { if (value && !isMonth(value)) issues.push({ path, message: `${label} — formato inválido` }); };
  required("personal_info.full_name", "Nome completo", candidate.personal_info.full_name);
  required("personal_info.city", "Cidade", candidate.personal_info.city);
  required("personal_info.state", "Estado", candidate.personal_info.state);
  required("personal_info.country", "País", candidate.personal_info.country);
  required("contact_info.email", "E-mail", candidate.contact_info.email);
  if (!isBlank(candidate.contact_info.email) && !validEmail(candidate.contact_info.email.trim())) issues.push({ path: "contact_info.email", message: "E-mail — formato inválido" });
  required("contact_info.phone", "Telefone", candidate.contact_info.phone);
  candidate.experiences.forEach((item, index) => { const prefix = `experiences[${index}]`; required(`${prefix}.company`, `Experiência ${index + 1} · Empresa`, item.company); required(`${prefix}.role`, `Experiência ${index + 1} · Cargo`, item.role); required(`${prefix}.start_date`, `Experiência ${index + 1} · Início`, item.start_date); optionalMonth(`${prefix}.start_date`, `Experiência ${index + 1} · Início`, item.start_date); optionalMonth(`${prefix}.end_date`, `Experiência ${index + 1} · Fim`, item.end_date); if (item.start_date && item.end_date && item.end_date < item.start_date) issues.push({ path: `${prefix}.end_date`, message: `Experiência ${index + 1} · Fim — não pode ser anterior ao início` }); });
  candidate.education.forEach((item, index) => { const prefix = `education[${index}]`; required(`${prefix}.institution`, `Formação ${index + 1} · Instituição`, item.institution); required(`${prefix}.course`, `Formação ${index + 1} · Curso`, item.course); required(`${prefix}.status`, `Formação ${index + 1} · Status`, item.status); optionalMonth(`${prefix}.start_date`, `Formação ${index + 1} · Início`, item.start_date); optionalMonth(`${prefix}.end_date`, `Formação ${index + 1} · Fim`, item.end_date); if (item.start_date && item.end_date && item.end_date < item.start_date) issues.push({ path: `${prefix}.end_date`, message: `Formação ${index + 1} · Fim — não pode ser anterior ao início` }); });
  const validateNamed = (items: { name: string }[], collection: string, label: string) => items.forEach((item, index) => required(`${collection}[${index}].name`, `${label} ${index + 1} · Nome`, item.name));
  validateNamed(candidate.skills, "skills", "Competência"); validateNamed(candidate.technologies, "technologies", "Tecnologia"); validateNamed(candidate.tools, "tools", "Ferramenta"); validateNamed(candidate.languages, "languages", "Idioma");
  candidate.certifications.forEach((item, index) => { const prefix = `certifications[${index}]`; required(`${prefix}.name`, `Certificação ${index + 1} · Nome`, item.name); required(`${prefix}.issuer`, `Certificação ${index + 1} · Emissor`, item.issuer); if (item.issue_date && !isDate(item.issue_date)) issues.push({ path: `${prefix}.issue_date`, message: `Certificação ${index + 1} · Emissão — formato inválido` }); if (item.expiration_date && !isDate(item.expiration_date)) issues.push({ path: `${prefix}.expiration_date`, message: `Certificação ${index + 1} · Validade — formato inválido` }); if (item.issue_date && item.expiration_date && item.expiration_date < item.issue_date) issues.push({ path: `${prefix}.expiration_date`, message: `Certificação ${index + 1} · Validade — não pode ser anterior à data de emissão` }); });
  candidate.projects.forEach((item, index) => { const prefix = `projects[${index}]`; required(`${prefix}.name`, `Projeto ${index + 1} · Nome`, item.name); required(`${prefix}.description`, `Projeto ${index + 1} · Descrição`, item.description); optionalMonth(`${prefix}.start_date`, `Projeto ${index + 1} · Início`, item.start_date); optionalMonth(`${prefix}.end_date`, `Projeto ${index + 1} · Fim`, item.end_date); if (item.start_date && item.end_date && item.end_date < item.start_date) issues.push({ path: `${prefix}.end_date`, message: `Projeto ${index + 1} · Fim — não pode ser anterior ao início` }); });
  required("description", "Descrição da vaga", job.description);
  return issues;
}

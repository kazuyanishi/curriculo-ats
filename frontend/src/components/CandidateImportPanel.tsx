"use client";

import { ChangeEvent, useRef } from "react";
import { CandidateImportIssue } from "../lib/types";
import { Card, PrimaryButton } from "./ui";

type CandidateImportPanelProps = {
  loading: boolean;
  disabled: boolean;
  success: boolean;
  errorMessage: string;
  issues: CandidateImportIssue[];
  reviewPaths: string[];
  onFileSelected: (file: File) => Promise<void>;
  onAcknowledgeReview: () => void;
};

const issueMessages: Record<CandidateImportIssue["code"], string> = {
  missing_required_field: "Campo obrigatório não encontrado no currículo.",
  unsupported_date_format: "A data não pôde ser preenchida automaticamente.",
  unsupported_education_status: "Status de formação não reconhecido automaticamente.",
  unsupported_proficiency_level: "Nível de proficiência não reconhecido automaticamente.",
  unsupported_language_level: "Nível do idioma não reconhecido automaticamente.",
};

function pathLabel(path: string): string {
  const match = path.match(/^(\w+)\[(\d+)\]\.(\w+)$/);
  if (!match) {
    return ({
      "personal_info.full_name": "Nome completo", "personal_info.city": "Cidade",
      "personal_info.state": "Estado", "personal_info.country": "País",
      "contact_info.email": "E-mail", "contact_info.phone": "Telefone",
    } as Record<string, string>)[path] ?? path;
  }
  const [, collection, index, field] = match;
  const names: Record<string, string> = { experiences: "Experiência", education: "Formação", skills: "Competência", technologies: "Tecnologia", tools: "Ferramenta", languages: "Idioma", certifications: "Certificação", projects: "Projeto" };
  const fields: Record<string, string> = { company: "Empresa", role: "Cargo", start_date: "Início", end_date: "Fim", institution: "Instituição", course: "Curso", status: "Status", level: "Nível", issuer: "Emissor", issue_date: "Data de emissão", expiration_date: "Validade", name: "Nome", description: "Descrição" };
  return `${names[collection] ?? collection} ${Number(index) + 1} · ${fields[field] ?? field}`;
}

export function CandidateImportPanel({ loading, disabled, success, errorMessage, issues, reviewPaths, onFileSelected, onAcknowledgeReview }: CandidateImportPanelProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const hasWarnings = issues.length > 0 || reviewPaths.length > 0;
  const handleChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (file) await onFileSelected(file);
  };
  return <Card><div className="mb-4"><h2 className="text-xl font-bold">Importar currículo</h2><p className="mt-1 text-sm text-slate-500">Envie um PDF ou DOCX para preencher o formulário automaticamente.</p><p className="mt-2 text-xs text-amber-700">Revise os dados importados antes de analisar a vaga. PDFs escaneados sem texto ainda não são suportados.</p></div><input ref={inputRef} type="file" accept=".pdf,.docx" aria-label="Selecionar currículo PDF ou DOCX" onChange={handleChange} disabled={loading || disabled} className="sr-only" /><PrimaryButton disabled={loading || disabled} onClick={() => inputRef.current?.click()}>{loading ? "Importando currículo..." : "Selecionar PDF ou DOCX"}</PrimaryButton>{errorMessage && <p role="alert" className="mt-3 rounded-xl border border-rose-100 bg-rose-50 px-3 py-2 text-sm text-rose-800">{errorMessage}</p>}{success && !errorMessage && <p role="status" className="mt-3 rounded-xl border border-emerald-100 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">Currículo importado. Revise os campos antes de analisar.</p>}{hasWarnings && <div className="mt-4 space-y-3 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900"><p className="font-semibold">Revise os campos indicados antes de analisar.</p><ul className="space-y-2">{issues.map((issue, index) => <li key={`${issue.path}-${index}`}><span className="font-semibold">{pathLabel(issue.path)}:</span> {issueMessages[issue.code]}{issue.raw_value ? ` Valor encontrado: "${issue.raw_value}"` : ""}</li>)}{reviewPaths.map(path => <li key={path}><span className="font-semibold">{pathLabel(path)}:</span> Confirme se esta experiência é um trabalho atual ou informe a data de término.</li>)}</ul><button type="button" onClick={onAcknowledgeReview} className="text-sm font-bold text-amber-800 underline">Marcar avisos como revisados</button></div>}</Card>;
}

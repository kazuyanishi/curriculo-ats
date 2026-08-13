import {
  AnalyzeResponse,
  Candidate,
  CandidateImportDraft,
  Job,
  normalizeCandidatePayload,
  normalizeJobPayload,
} from "./types";

type ApiErrorBody = { detail?: unknown };

export function parseApiError(status: number, body: ApiErrorBody | null): string {
  if (status === 502 && body?.detail === "Backend indisponível.") return "Não foi possível conectar ao serviço de análise.";
  if (status === 422) return typeof body?.detail === "string" ? body.detail : "Revise os campos obrigatórios ou inválidos.";
  if (status === 502 || status === 503) return "O serviço de análise está temporariamente indisponível.";
  return typeof body?.detail === "string" ? body.detail : "Não foi possível concluir a solicitação.";
}

async function responseError(response: Response): Promise<Error> {
  let body: ApiErrorBody | null = null;
  try { body = await response.json() as ApiErrorBody; } catch { /* non-JSON response */ }
  return new Error(parseApiError(response.status, body));
}

export async function analyzeCandidate(candidate: Candidate, job: Job): Promise<AnalyzeResponse> {
  const response = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ candidate: normalizeCandidatePayload(candidate), job: normalizeJobPayload(job) }),
  });
  if (!response.ok) throw await responseError(response);
  return await response.json() as AnalyzeResponse;
}

export async function downloadDocument(kind: "docx" | "pdf", candidate: Candidate): Promise<{ blob: Blob; filename: string | null }> {
  const response = await fetch(`/api/documents/${kind}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(candidate),
  });
  if (!response.ok) throw await responseError(response);
  const disposition = response.headers.get("Content-Disposition");
  const filename = disposition?.match(/filename="?([^";]+)"?/i)?.[1] ?? null;
  return { blob: await response.blob(), filename };
}

export async function importCandidateResume(file: File): Promise<CandidateImportDraft> {
  const formData = new FormData();
  formData.append("file", file, file.name);

  const response = await fetch("/api/candidate/import", {
    method: "POST",
    body: formData,
  });
  if (!response.ok) throw await responseError(response);
  return await response.json() as CandidateImportDraft;
}

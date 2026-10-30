import { Job } from "./types";

export const INDEED_CLIPBOARD_MARKER = "RESUME_AI_INDEED_JOB_V1";

export type BrowserJobImportResult = { job: Job; warnings: string[] };

function nonBlank(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function validPayload(value: unknown): value is Partial<Job> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return false;
  const record = value as Record<string, unknown>;
  return ["source_url", "title", "company", "location", "description"].every(
    field => record[field] === undefined || typeof record[field] === "string",
  );
}

function jobFromPayload(payload: Partial<Job>, fallbackUrl: string): Job {
  return {
    source_url: nonBlank(payload.source_url) || fallbackUrl,
    title: nonBlank(payload.title),
    company: nonBlank(payload.company),
    location: nonBlank(payload.location),
    description: nonBlank(payload.description),
  };
}

export async function importJobFromClipboard(currentJob: Job): Promise<BrowserJobImportResult> {
  if (typeof navigator === "undefined" || !navigator.clipboard?.readText) {
    throw new Error("O Firefox não permitiu ler a área de transferência. Clique novamente no botão e autorize o acesso.");
  }
  const raw = (await navigator.clipboard.readText()).trim();
  if (!raw) throw new Error("A área de transferência está vazia.");

  if (raw.startsWith(`${INDEED_CLIPBOARD_MARKER}\n`)) {
    try {
      const parsed: unknown = JSON.parse(raw.slice(INDEED_CLIPBOARD_MARKER.length + 1));
      if (!validPayload(parsed)) throw new Error("Formato inválido");
      const job = jobFromPayload(parsed, currentJob.source_url);
      if (!job.description) throw new Error("A descrição não foi encontrada na página do Indeed.");
      const warnings = [
        !job.title && "Título não identificado; confirme manualmente.",
        !job.company && "Empresa não identificada; confirme manualmente.",
        !job.location && "Localização não identificada; confirme manualmente.",
      ].filter((warning): warning is string => Boolean(warning));
      return { job, warnings };
    } catch {
      throw new Error("Não foi possível interpretar os dados copiados do Indeed.");
    }
  }

  const lines = raw.split(/\r?\n/).map(line => line.trim()).filter(Boolean);
  const title = lines[0]?.length <= 180 ? lines[0] : "";
  return {
    job: { ...currentJob, title: title || currentJob.title, description: raw },
    warnings: ["O texto foi importado sem metadados do Indeed. Confirme título, empresa, local e URL."],
  };
}

/** Generates a bookmarklet that reads only the rendered Indeed page. */
export function buildIndeedBookmarklet(): string {
  const marker = JSON.stringify(INDEED_CLIPBOARD_MARKER);
  const script = `(async()=>{const pick=(selectors)=>{for(const selector of selectors){const element=document.querySelector(selector);const value=element?.innerText?.trim()||element?.textContent?.trim()||element?.getAttribute("content")?.trim();if(value)return value}return""};const description=pick(["#jobDescriptionText","[data-testid=jobDescriptionText]","[data-testid=jobDescription]",".jobsearch-JobComponent-description","main article"])||document.body.innerText.trim();const payload={source_url:location.href,title:pick(["[data-testid=jobsearch-JobInfoHeader-title]","h1","meta[property='og:title']"]),company:pick(["[data-testid=inlineHeader-companyName]","[data-testid=companyName]",".jobsearch-JobInfoHeader-companyName"]),location:pick(["[data-testid=job-location]","[data-testid=inlineHeader-companyLocation]",".jobsearch-JobInfoHeader-subtitle"]),description};const value=${marker}+"\\n"+JSON.stringify(payload);try{await navigator.clipboard.writeText(value);alert("Vaga copiada. Volte ao Resume AI e clique em Importar vaga copiada.")}catch(error){const area=document.createElement("textarea");area.value=value;area.style.position="fixed";area.style.opacity="0";document.body.appendChild(area);area.focus();area.select();document.execCommand("copy");area.remove();alert("Vaga copiada. Volte ao Resume AI e clique em Importar vaga copiada.")}})()`;
  return `javascript:${encodeURIComponent(script)}`;
}

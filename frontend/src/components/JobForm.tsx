"use client";

import { Job } from "../lib/types";
import { Card, Field, PrimaryButton, TextArea } from "./ui";

export function JobForm({ job, setJob, onAnalyze, loading, disabled = false }: { job: Job; setJob: (job: Job) => void; onAnalyze: () => void; loading: boolean; disabled?: boolean }) {
  return <Card className="lg:sticky lg:top-6"><div className="mb-5"><h2 className="text-xl font-bold">Vaga desejada</h2><p className="mt-1 text-sm text-slate-500">Cole a descrição completa da vaga para uma análise mais precisa.</p></div><div className="space-y-4"><Field label="Título da vaga" placeholder="Backend Developer" value={job.title} onChange={v => setJob({ ...job, title: v })} /><Field label="Empresa" placeholder="Example Corp" value={job.company} onChange={v => setJob({ ...job, company: v })} /><Field label="Localização" placeholder="Remoto" value={job.location} onChange={v => setJob({ ...job, location: v })} /><Field label="URL" placeholder="https://empresa.com/vaga" value={job.source_url} onChange={v => setJob({ ...job, source_url: v })} /><TextArea label="Descrição da vaga" placeholder="Cole aqui os requisitos e responsabilidades..." className="min-h-[300px]" value={job.description} onChange={v => setJob({ ...job, description: v })} /><PrimaryButton disabled={loading || disabled} onClick={onAnalyze}>{loading ? "Analisando..." : <>Analisar compatibilidade <span aria-hidden>→</span></>}</PrimaryButton></div></Card>;
}

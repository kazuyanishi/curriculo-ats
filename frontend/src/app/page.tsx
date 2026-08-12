"use client";

import { useRef, useState } from "react";
import { analyzeCandidate } from "../lib/api";
import { AnalyzeResponse, Candidate, emptyCandidate, Job } from "../lib/types";
import { AnalysisResult } from "../components/AnalysisResult";
import { CandidateForm } from "../components/CandidateForm";
import { EmptyAnalysisState } from "../components/EmptyAnalysisState";
import { JobForm } from "../components/JobForm";
import { AppHeader, StepIndicator } from "../components/ui";

type AnalysisState = "idle" | "loading" | "success" | "error";

export default function Home() {
  const [candidate, setCandidate] = useState<Candidate>(emptyCandidate);
  const [job, setJob] = useState<Job>({ title: "", company: "", location: "", source_url: "", description: "" });
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [analysisState, setAnalysisState] = useState<AnalysisState>("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const resultRef = useRef<HTMLDivElement>(null);

  const submit = async () => {
    setErrorMessage("");
    if (!candidate.personal_info.full_name.trim() || !candidate.personal_info.city.trim() || !candidate.personal_info.state.trim() || !candidate.personal_info.country.trim() || !candidate.contact_info.email.trim() || !candidate.contact_info.phone.trim() || !job.description.trim()) {
      setAnalysisState("error"); setErrorMessage("Revise os campos obrigatórios ou inválidos."); return;
    }
    setAnalysisState("loading");
    try {
      const result = await analyzeCandidate(candidate, job);
      setAnalysis(result); setAnalysisState("success");
      requestAnimationFrame(() => resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }));
    } catch (error) { setAnalysisState("error"); setErrorMessage(error instanceof Error ? error.message : "Não foi possível concluir a análise."); }
  };

  return <><AppHeader /><main className="mx-auto max-w-[1400px] px-5 pb-16 pt-10 lg:px-10"><div className="mb-10 max-w-3xl"><StepIndicator step={analysisState === "success" ? 3 : 1} /><p className="mt-8 text-sm font-bold uppercase tracking-[0.18em] text-indigo-600">Seu próximo passo profissional</p><h1 className="mt-3 text-4xl font-black tracking-tight text-ink sm:text-6xl">Currículo alinhado à vaga,<br /><span className="text-indigo-600">sem inventar experiência.</span></h1><p className="mt-5 max-w-2xl text-lg leading-8 text-slate-500">Compare seu currículo com uma vaga, identifique lacunas e gere uma versão otimizada para sistemas ATS.</p></div><div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.8fr)_minmax(320px,1fr)]"><CandidateForm candidate={candidate} setCandidate={setCandidate} /><div><JobForm job={job} setJob={setJob} onAnalyze={submit} loading={analysisState === "loading"} />{analysisState === "error" && <div role="alert" className="mt-3 rounded-xl border border-rose-100 bg-rose-50 px-4 py-3 text-sm text-rose-800"><p className="font-bold">Não foi possível analisar os dados.</p><p className="mt-1">{errorMessage}</p></div>}</div></div><div ref={resultRef}>{analysis ? <AnalysisResult analysis={analysis} /> : <EmptyAnalysisState />}</div></main></>;
}

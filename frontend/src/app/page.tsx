"use client";

import { useState } from "react";
import { CandidateForm } from "../components/CandidateForm";
import { EmptyAnalysisState } from "../components/EmptyAnalysisState";
import { JobForm } from "../components/JobForm";
import { AppHeader, StepIndicator } from "../components/ui";
import { Candidate, emptyCandidate, Job } from "../lib/types";

export default function Home() {
  const [candidate, setCandidate] = useState<Candidate>(emptyCandidate);
  const [job, setJob] = useState<Job>({ title: "", company: "", location: "", source_url: "", description: "" });
  const [notice, setNotice] = useState("");

  return <><AppHeader /><main className="mx-auto max-w-[1400px] px-5 pb-16 pt-10 lg:px-10"><div className="mb-10 max-w-3xl"><StepIndicator step={1} /><p className="mt-8 text-sm font-bold uppercase tracking-[0.18em] text-indigo-600">Seu próximo passo profissional</p><h1 className="mt-3 text-4xl font-black tracking-tight text-ink sm:text-6xl">Currículo alinhado à vaga,<br /><span className="text-indigo-600">sem inventar experiência.</span></h1><p className="mt-5 max-w-2xl text-lg leading-8 text-slate-500">Compare seu currículo com uma vaga, identifique lacunas e gere uma versão otimizada para sistemas ATS.</p></div><div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.8fr)_minmax(320px,1fr)]"><CandidateForm candidate={candidate} setCandidate={setCandidate} /><div><JobForm job={job} setJob={setJob} onAnalyze={() => setNotice("A análise será conectada na próxima etapa.")} />{notice && <p role="status" className="mt-3 rounded-xl bg-indigo-50 px-4 py-3 text-center text-sm font-semibold text-indigo-700">{notice}</p>}</div></div><EmptyAnalysisState /></main></>;
}

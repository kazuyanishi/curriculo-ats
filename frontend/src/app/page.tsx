"use client";

import { useEffect, useRef, useState } from "react";
import { AnalysisResult } from "../components/AnalysisResult";
import { CandidateForm } from "../components/CandidateForm";
import { CandidateImportPanel } from "../components/CandidateImportPanel";
import { EmptyAnalysisState } from "../components/EmptyAnalysisState";
import { JobForm } from "../components/JobForm";
import { AppHeader, StepIndicator } from "../components/ui";
import { analyzeCandidate, importCandidateResume } from "../lib/api";
import { candidateFromImportDraft } from "../lib/candidateImport";
import { CandidateValidationIssue, validateCandidateForAnalysis } from "../lib/candidateValidation";
import {
  clearStoredCandidateImportReview,
  loadStoredCandidateImportReview,
  saveStoredCandidateImportReview,
} from "../lib/candidateImportReviewStorage";
import { clearStoredCandidate, loadStoredCandidate, saveStoredCandidate } from "../lib/candidateStorage";
import { AnalyzeResponse, Candidate, CandidateImportIssue, emptyCandidate, Job } from "../lib/types";

type AnalysisState = "idle" | "loading" | "success" | "error";
type ImportState = "idle" | "loading" | "success" | "error";

function candidateHasData(candidate: Candidate): boolean {
  const hasText = (value: string | null) => Boolean(value?.trim());
  const personal = Object.values(candidate.personal_info).some(hasText);
  const contact = Object.values(candidate.contact_info).some(hasText);
  const links = Object.values(candidate.professional_links).some(hasText);
  const collections = [candidate.experiences, candidate.education, candidate.skills, candidate.technologies, candidate.tools, candidate.languages, candidate.certifications, candidate.projects];
  return personal || contact || links || collections.some(items => items.length > 0);
}

function importErrorMessage(error: unknown): string {
  const message = error instanceof Error ? error.message : "Não foi possível importar o currículo.";
  const messages: Record<string, string> = {
    "Unsupported resume file type": "Envie um arquivo PDF ou DOCX.",
    "Resume file is too large": "O arquivo é grande demais para importação.",
    "Resume file is empty": "O arquivo enviado está vazio.",
    "Could not extract text from resume": "Não foi possível ler o currículo enviado.",
    "Resume contains no extractable text": "Não foi possível encontrar texto no currículo. PDFs escaneados ainda não são suportados.",
    "Resume extraction could not be validated": "Não foi possível validar com segurança os dados extraídos.",
  };
  return messages[message] ?? message;
}

export default function Home() {
  const [candidate, setCandidate] = useState<Candidate>(() => emptyCandidate());
  const [candidateHydrated, setCandidateHydrated] = useState(false);
  const [importReviewHydrated, setImportReviewHydrated] = useState(false);
  const [job, setJob] = useState<Job>({ title: "", company: "", location: "", source_url: "", description: "" });
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [analysisState, setAnalysisState] = useState<AnalysisState>("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [validationIssues, setValidationIssues] = useState<CandidateValidationIssue[]>([]);
  const [importState, setImportState] = useState<ImportState>("idle");
  const [importError, setImportError] = useState("");
  const [importIssues, setImportIssues] = useState<CandidateImportIssue[]>([]);
  const [importReviewPaths, setImportReviewPaths] = useState<string[]>([]);
  const importInFlightRef = useRef(false);
  const analysisInFlightRef = useRef(false);
  const resultRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const storedCandidate = loadStoredCandidate();
    const storedReview = loadStoredCandidateImportReview();
    if (storedCandidate) {
      setCandidate(storedCandidate);
      if (storedReview) {
        setImportIssues(storedReview.issues);
        setImportReviewPaths(storedReview.review_paths);
      }
    } else if (storedReview) {
      clearStoredCandidateImportReview();
    }
    setCandidateHydrated(true);
    setImportReviewHydrated(true);
  }, []);

  useEffect(() => {
    if (candidateHydrated) saveStoredCandidate(candidate);
  }, [candidate, candidateHydrated]);

  useEffect(() => {
    if (importReviewHydrated) {
      saveStoredCandidateImportReview({ issues: importIssues, review_paths: importReviewPaths });
    }
  }, [importIssues, importReviewPaths, importReviewHydrated]);

  const clearCandidate = () => {
    if (!window.confirm("Limpar todos os dados do currículo salvos neste navegador?")) return;
    clearStoredCandidate();
    clearStoredCandidateImportReview();
    setCandidate(emptyCandidate());
    setAnalysis(null);
    setAnalysisState("idle");
    setErrorMessage("");
    setValidationIssues([]);
    setImportState("idle");
    setImportError("");
    setImportIssues([]);
    setImportReviewPaths([]);
  };

  const submit = async () => {
    if (!candidateHydrated || !importReviewHydrated || analysisInFlightRef.current || importInFlightRef.current) return;
    if (importIssues.length > 0 || importReviewPaths.length > 0) {
      setAnalysisState("error");
      setErrorMessage("Revise os avisos da importação antes de analisar.");
      return;
    }
    setErrorMessage("");
    const issues = validateCandidateForAnalysis(candidate, job);
    if (issues.length > 0) { setValidationIssues(issues); setAnalysisState("error"); return; }
    setValidationIssues([]);
    analysisInFlightRef.current = true;
    setAnalysisState("loading");
    try {
      const result = await analyzeCandidate(candidate, job);
      setAnalysis(result); setAnalysisState("success");
      requestAnimationFrame(() => resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }));
    } catch (error) { setValidationIssues([]); setAnalysisState("error"); setErrorMessage(error instanceof Error ? error.message : "Não foi possível concluir a análise."); }
    finally { analysisInFlightRef.current = false; }
  };

  const handleImport = async (file: File) => {
    if (importInFlightRef.current || analysisInFlightRef.current || !candidateHydrated || !importReviewHydrated) return;
    if (candidateHasData(candidate) && !window.confirm("Importar este currículo substituirá os dados atuais do currículo salvos neste navegador. A vaga não será alterada. Continuar?")) return;
    importInFlightRef.current = true;
    setImportState("loading"); setImportError("");
    try {
      const draft = await importCandidateResume(file);
      const editResult = candidateFromImportDraft(draft);
      setCandidate(editResult.candidate);
      setImportIssues(editResult.issues);
      setImportReviewPaths(editResult.review_paths);
      setImportState("success");
      setAnalysis(null); setAnalysisState("idle"); setErrorMessage(""); setValidationIssues([]);
    } catch (error) {
      setImportState("error"); setImportError(importErrorMessage(error));
    } finally { importInFlightRef.current = false; }
  };

  const warningsPending = importIssues.length > 0 || importReviewPaths.length > 0;
  return <><AppHeader /><main className="mx-auto max-w-[1400px] px-5 pb-16 pt-10 lg:px-10"><div className="mb-10 max-w-3xl"><StepIndicator step={analysisState === "success" ? 3 : 1} /><p className="mt-8 text-sm font-bold uppercase tracking-[0.18em] text-indigo-600">Seu próximo passo profissional</p><h1 className="mt-3 text-4xl font-black tracking-tight text-ink sm:text-6xl">Currículo alinhado à vaga,<br /><span className="text-indigo-600">sem inventar experiência.</span></h1><p className="mt-5 max-w-2xl text-lg leading-8 text-slate-500">Compare seu currículo com uma vaga, identifique lacunas e gere uma versão otimizada para sistemas ATS.</p></div><div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.8fr)_minmax(320px,1fr)]"><div className="space-y-4"><CandidateImportPanel loading={importState === "loading"} disabled={!candidateHydrated || !importReviewHydrated || analysisState === "loading"} success={importState === "success"} errorMessage={importError} issues={importIssues} reviewPaths={importReviewPaths} onFileSelected={handleImport} onAcknowledgeReview={() => { setImportIssues([]); setImportReviewPaths([]); }} /><CandidateForm candidate={candidate} setCandidate={setCandidate} onClear={clearCandidate} /></div><div><JobForm job={job} setJob={setJob} onAnalyze={submit} loading={analysisState === "loading"} disabled={!candidateHydrated || !importReviewHydrated || importState === "loading" || warningsPending} />{analysisState === "error" && <div role="alert" className="mt-3 rounded-xl border border-rose-100 bg-rose-50 px-4 py-3 text-sm text-rose-800"><p className="font-bold">{validationIssues.length > 0 ? "Não foi possível analisar. Corrija os campos abaixo:" : "Não foi possível analisar os dados."}</p>{validationIssues.length > 0 ? <ul className="mt-2 list-disc space-y-1 pl-5">{validationIssues.map(issue => <li key={issue.path}>{issue.message}</li>)}</ul> : <p className="mt-1">{errorMessage}</p>}</div>}</div></div><div ref={resultRef}>{analysis ? <AnalysisResult analysis={analysis} /> : <EmptyAnalysisState />}</div></main></>;
}

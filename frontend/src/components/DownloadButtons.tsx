"use client";

import { useState } from "react";
import { downloadDocument } from "../lib/api";
import { Candidate } from "../lib/types";

export function DownloadButtons({ candidate }: { candidate: Candidate }) {
  const [loading, setLoading] = useState<"docx" | "pdf" | null>(null);
  const [error, setError] = useState("");
  const download = async (kind: "docx" | "pdf") => {
    setLoading(kind); setError("");
    try { const { blob, filename } = await downloadDocument(kind, candidate); const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = filename ?? `resume.${kind}`; link.click(); URL.revokeObjectURL(url); } catch { setError("Não foi possível gerar o arquivo."); } finally { setLoading(null); }
  };
  return <div><div className="flex flex-col gap-2 sm:flex-row"><button type="button" disabled={loading === "docx"} onClick={() => download("docx")} className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50">{loading === "docx" ? "Gerando DOCX..." : "Baixar DOCX"}</button><button type="button" disabled={loading === "pdf"} onClick={() => download("pdf")} className="rounded-xl border border-indigo-200 px-4 py-2.5 text-sm font-bold text-indigo-700 disabled:opacity-50">{loading === "pdf" ? "Gerando PDF..." : "Baixar PDF"}</button></div>{error && <p role="alert" className="mt-2 text-sm text-rose-600">{error}</p>}</div>;
}

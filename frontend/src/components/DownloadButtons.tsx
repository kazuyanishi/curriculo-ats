"use client";

import { useState } from "react";
import { downloadDocument } from "../lib/api";
import { Candidate } from "../lib/types";

export function DownloadButtons({ candidate }: { candidate: Candidate }) {
  const [docxLoading, setDocxLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [error, setError] = useState("");
  const download = async (kind: "docx" | "pdf") => {
    if (kind === "docx") setDocxLoading(true); else setPdfLoading(true);
    setError("");
    try {
      const { blob, filename } = await downloadDocument(kind, candidate);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename ?? `resume.${kind}`;
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      setError("Não foi possível gerar o arquivo.");
    } finally {
      if (kind === "docx") setDocxLoading(false); else setPdfLoading(false);
    }
  };
  return <div><div className="flex flex-col gap-2 sm:flex-row"><button type="button" disabled={docxLoading} onClick={() => download("docx")} className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50">{docxLoading ? "Gerando DOCX..." : "Baixar DOCX"}</button><button type="button" disabled={pdfLoading} onClick={() => download("pdf")} className="rounded-xl border border-indigo-200 px-4 py-2.5 text-sm font-bold text-indigo-700 disabled:opacity-50">{pdfLoading ? "Gerando PDF..." : "Baixar PDF"}</button></div>{error && <p role="alert" className="mt-2 text-sm text-rose-600">{error}</p>}</div>;
}

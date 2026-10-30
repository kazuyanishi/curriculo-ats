import { NextResponse } from "next/server";

const MAX_PAGE_BYTES = 2 * 1024 * 1024;
const MAX_DESCRIPTION_CHARS = 30_000;

type JobData = { title: string; company: string; location: string; source_url: string; description: string };

function decodeHtml(value: string): string {
  const entities: Record<string, string> = { amp: "&", nbsp: " ", quot: '"', apos: "'", lt: "<", gt: ">", ndash: "–", mdash: "—" };
  return value
    .replace(/&#(\d+);/g, (_, code: string) => String.fromCodePoint(Number(code)))
    .replace(/&#x([\da-f]+);/gi, (_, code: string) => String.fromCodePoint(parseInt(code, 16)))
    .replace(/&([a-z]+);/gi, (match, name: string) => entities[name.toLowerCase()] ?? match);
}

function cleanText(value: string): string {
  return decodeHtml(value
    .replace(/<!--[\s\S]*?-->/g, " ")
    .replace(/<(script|style|noscript|svg)[^>]*>[\s\S]*?<\/\1>/gi, " ")
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<\/(p|div|li|h[1-6]|section|article|main|tr|header|footer)>/gi, "\n")
    .replace(/<[^>]+>/g, " "))
    .split(/\n+/)
    .map(line => line.replace(/\s+/g, " ").trim())
    .filter(Boolean)
    .join("\n")
    .slice(0, MAX_DESCRIPTION_CHARS)
    .trim();
}

function htmlAttribute(value: string): string {
  return decodeHtml(value.replace(/<[^>]+>/g, "").trim());
}

function tagValue(html: string, tag: string): string {
  const match = html.match(new RegExp(`<${tag}[^>]*>([\\s\\S]*?)<\\/${tag}>`, "i"));
  return htmlAttribute(match?.[1] ?? "");
}

function metaValue(html: string, key: string): string {
  const escaped = key.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pattern = new RegExp(`<meta[^>]+(?:property|name)=["']${escaped}["'][^>]+content=["']([^"']*)["'][^>]*>`, "i");
  const reversePattern = new RegExp(`<meta[^>]+content=["']([^"']*)["'][^>]+(?:property|name)=["']${escaped}["'][^>]*>`, "i");
  return htmlAttribute(html.match(pattern)?.[1] ?? html.match(reversePattern)?.[1] ?? "");
}

function jsonLdJobPosting(html: string): Record<string, unknown> | null {
  const blocks = html.matchAll(/<script[^>]+type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi);
  for (const block of blocks) {
    try {
      const parsed: unknown = JSON.parse(block[1].trim());
      const candidates = Array.isArray(parsed) ? parsed : [parsed];
      const queue = [...candidates] as unknown[];
      while (queue.length) {
        const current = queue.shift();
        if (!current || typeof current !== "object") continue;
        const record = current as Record<string, unknown>;
        const type = record["@type"];
        if (type === "JobPosting" || (Array.isArray(type) && type.includes("JobPosting"))) return record;
        queue.push(...Object.values(record).filter(value => typeof value === "object"));
      }
    } catch { /* some sites publish invalid JSON-LD; visible text remains a fallback */ }
  }
  return null;
}

function stringValue(value: unknown): string { return typeof value === "string" ? cleanText(value) : ""; }

function locationValue(value: unknown): string {
  const values = Array.isArray(value) ? value : [value];
  return values.map(item => {
    if (!item || typeof item !== "object") return stringValue(item);
    const record = item as Record<string, unknown>;
    const address = record.address;
    if (address && typeof address === "object") {
      const fields = address as Record<string, unknown>;
      return [fields.streetAddress, fields.addressLocality, fields.addressRegion, fields.addressCountry].map(stringValue).filter(Boolean).join(", ");
    }
    return [record.name, record.addressLocality, record.addressRegion].map(stringValue).filter(Boolean).join(", ");
  }).filter(Boolean).join("; ");
}

function extractJob(html: string, sourceUrl: string): { job: JobData; warnings: string[] } {
  const structured = jsonLdJobPosting(html);
  const organization = structured?.hiringOrganization;
  const company = organization && typeof organization === "object" ? stringValue((organization as Record<string, unknown>).name) : "";
  const title = stringValue(structured?.title) || metaValue(html, "og:title") || metaValue(html, "twitter:title") || tagValue(html, "title");
  const description = stringValue(structured?.description) || metaValue(html, "og:description") || cleanText(html);
  const location = locationValue(structured?.jobLocation) || stringValue(structured?.jobLocationType);
  const job: JobData = { title, company, location, source_url: sourceUrl, description };
  const warnings: string[] = [];
  if (!title) warnings.push("Título não identificado; preencha manualmente.");
  if (!company) warnings.push("Empresa não identificada; preencha manualmente.");
  if (!location) warnings.push("Localização não identificada; preencha manualmente.");
  if (!description) warnings.push("Descrição não identificada; cole a descrição manualmente.");
  if (!structured) warnings.push("A página não publicou dados estruturados de vaga; os campos visíveis foram usados quando disponíveis.");
  return { job, warnings };
}

export async function POST(request: Request) {
  let input: { url?: unknown };
  try { input = await request.json() as { url?: unknown }; } catch { return NextResponse.json({ detail: "Informe uma URL válida." }, { status: 400 }); }
  if (typeof input.url !== "string" || !input.url.trim()) return NextResponse.json({ detail: "Informe uma URL válida." }, { status: 400 });
  let target: URL;
  try {
    target = new URL(input.url.trim());
    if (!/^https?:$/.test(target.protocol)) throw new Error("unsupported protocol");
  } catch { return NextResponse.json({ detail: "Use uma URL HTTP ou HTTPS válida." }, { status: 400 }); }
  try {
    const response = await fetch(target, { headers: { Accept: "text/html,application/xhtml+xml", "User-Agent": "ResumeAI/1.0 job-reader" }, signal: AbortSignal.timeout(10_000), cache: "no-store" });
    if (!response.ok) {
      const isIndeed = /(^|\.)indeed\./i.test(target.hostname);
      const detail = response.status === 403 && isIndeed
        ? "O Indeed bloqueou a leitura automática desta vaga. Abra o link no navegador, copie a descrição e cole no campo abaixo."
        : `A página respondeu com HTTP ${response.status}. Cole a descrição manualmente.`;
      return NextResponse.json({ detail }, { status: 422 });
    }
    const contentLength = Number(response.headers.get("content-length") ?? 0);
    if (contentLength > MAX_PAGE_BYTES) return NextResponse.json({ detail: "A página é grande demais para leitura automática. Cole a descrição manualmente." }, { status: 413 });
    const bytes = await response.arrayBuffer();
    if (bytes.byteLength > MAX_PAGE_BYTES) return NextResponse.json({ detail: "A página é grande demais para leitura automática. Cole a descrição manualmente." }, { status: 413 });
    const result = extractJob(new TextDecoder().decode(bytes), target.toString());
    return NextResponse.json(result);
  } catch (error) {
    const message = error instanceof Error && error.name === "TimeoutError" ? "A página demorou demais para responder. Cole a descrição manualmente." : "Não foi possível acessar essa vaga. Verifique o link ou cole a descrição manualmente.";
    return NextResponse.json({ detail: message }, { status: 502 });
  }
}

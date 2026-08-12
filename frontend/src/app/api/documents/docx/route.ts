import { NextResponse } from "next/server";

export async function POST(request: Request) {
  return proxyDocument(request, "docx");
}

async function proxyDocument(request: Request, kind: "docx") {
  try {
    const response = await fetch(`${process.env.RESUME_AI_API_URL ?? "http://127.0.0.1:8000"}/api/v1/documents/${kind}`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: await request.text(), cache: "no-store",
    });
    return new NextResponse(await response.arrayBuffer(), {
      status: response.status,
      headers: {
        "Content-Type": response.headers.get("Content-Type") ?? "application/octet-stream",
        ...(response.headers.get("Content-Disposition") ? { "Content-Disposition": response.headers.get("Content-Disposition")! } : {}),
      },
    });
  } catch { return NextResponse.json({ detail: "Backend indisponível." }, { status: 502 }); }
}

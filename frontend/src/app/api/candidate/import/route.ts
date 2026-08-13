import { NextResponse } from "next/server";

const backendUrl = () => process.env.RESUME_AI_API_URL ?? "http://127.0.0.1:8000";

export async function POST(request: Request) {
  let formData: FormData;
  try {
    formData = await request.formData();
  } catch {
    return NextResponse.json({ detail: "Invalid multipart request" }, { status: 400 });
  }

  try {
    const response = await fetch(`${backendUrl()}/api/v1/candidate/import`, {
      method: "POST",
      body: formData,
      cache: "no-store",
    });

    return new NextResponse(await response.text(), {
      status: response.status,
      headers: {
        "Content-Type": response.headers.get("Content-Type") ?? "application/json",
      },
    });
  } catch {
    return NextResponse.json({ detail: "Backend indisponível." }, { status: 502 });
  }
}

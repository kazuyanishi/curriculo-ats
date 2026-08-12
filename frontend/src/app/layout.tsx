import "./globals.css";

export const metadata = { title: "Resume AI", description: "ATS Resume Analyzer" };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="pt-BR"><body>{children}</body></html>;
}

export type Finding = {
  id: number;
  vuln_type: string;
  url: string;
  evidence: string;
  severity: string | null;
  fingerprint_hash: string | null;
  report_draft: string | null;
  status: string;
  created_at: string;
};

export type Program = {
  id: number;
  name: string;
  website_url: string | null;
  in_scope_domains: string[];
  out_of_scope_domains: string[];
  rules: string | null;
};

export type TimelineEvent = {
  event: string;
  timestamp: string;
  notes?: string;
};

export type Disclosure = {
  id: number;
  finding_id: number;
  status: string;
  program_deadline: string | null;
  cve_id: string | null;
  timeline_events: TimelineEvent[];
  created_at: string;
  updated_at: string;
};

export type Scan = {
  id: number;
  program_id: number;
  target_url: string;
  status: string;
  started_at: string;
  completed_at: string | null;
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Backend returned ${response.status} for ${path}`);
  }
  return response.json() as Promise<T>;
}

export const getFindings = () => getJson<Finding[]>("/findings");
export const getPrograms = () => getJson<Program[]>("/programs");
export const getDisclosures = () => getJson<Disclosure[]>("/disclosures");
export const getScans = () => getJson<Scan[]>("/scans");

export async function createScan(programId: number, targetUrl: string): Promise<Scan> {
  const response = await fetch(`${apiUrl}/scans`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ program_id: programId, target_url: targetUrl }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || `Server returned ${response.status}`);
  }
  return data as Scan;
}

export type CreateProgramInput = {
  name: string;
  website_url: string;
  in_scope_domains: string[];
  out_of_scope_domains?: string[];
  rules?: string | null;
};

export async function createProgram(input: CreateProgramInput): Promise<Program> {
  const response = await fetch(`${apiUrl}/programs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || `Server returned ${response.status}`);
  }
  return data as Program;
}


import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Building2, Check } from "lucide-react";
import { api } from "../../api/client";
import type { Company } from "../../types";
import { Button, ErrorState, Field, PageHeader, Panel, inputCls, cx } from "../../components/ui";
import { useSession } from "../../state/session";

const txt = (v: unknown) => (typeof v === "string" ? v : "");

export default function CompanyPage() {
  const { company, setCompany } = useSession();
  const nav = useNavigate();
  const [name, setName] = useState("");
  const [domain, setDomain] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<Error | null>(null);
  const [res, setRes] = useState<Company | null>(null);
  const [pick, setPick] = useState<string | null>(null);

  const options = res ? [{ company_id: res.company_id, name: res.name, domain: res.domain, ...res.enriched }, ...res.ambiguous_options.filter((o) => txt(o.company_id) !== res.company_id)] as Record<string, unknown>[] : [];

  async function search(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() && !domain.trim()) return;
    setBusy(true); setErr(null);
    try { const r = await api.resolveCompany({ company_name: name.trim() || undefined, domain: domain.trim() || undefined }); setRes(r); setPick(r.company_id); }
    catch (x) { setErr(x as Error); } finally { setBusy(false); }
  }

  return (
    <>
      <PageHeader title="Company" sub="Identify your company so roles are attached to it." />
      {company && <Panel className="mb-6"><div className="flex items-center gap-3"><Check className="text-positive" aria-hidden /> <span>Current company: <strong>{company.name}</strong></span></div></Panel>}
      <Panel>
        <form onSubmit={search} className="grid gap-4 sm:grid-cols-2">
          <Field label="Company name"><input className={inputCls} value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Northwind" /></Field>
          <Field label="Or domain"><input className={inputCls} value={domain} onChange={(e) => setDomain(e.target.value)} placeholder="northwind.com" /></Field>
          <div className="sm:col-span-2"><Button size="lg" disabled={busy || (!name.trim() && !domain.trim())}>{busy ? "Searching…" : "Find company"}</Button></div>
        </form>
      </Panel>
      {err && <div className="mt-4"><ErrorState error={err} /></div>}
      {res && (
        <fieldset className="mt-6 space-y-3"><legend className="mb-2 font-semibold">Select your company</legend>
          {options.map((o) => {
            const id = txt(o.company_id);
            return (
              <label key={id} className={cx("flex cursor-pointer items-center gap-4 rounded-2xl border bg-surface p-4", pick === id ? "border-brand ring-4 ring-brand-soft" : "border-line")}>
                <input type="radio" name="company" className="sr-only" checked={pick === id} onChange={() => setPick(id)} />
                <Building2 className="text-brand" aria-hidden />
                <div className="flex-1"><div className="font-semibold">{txt(o.name)}</div><div className="text-sm text-muted">{[txt(o.domain), txt(o.location), txt(o.summary)].filter(Boolean).join(" · ") || "No further details available"}</div></div>
                {pick === id && <Check className="text-brand" aria-label="Selected" />}
              </label>);
          })}
          <Button size="lg" disabled={!pick} onClick={() => { const o = options.find((x) => txt(x.company_id) === pick)!; setCompany({ id: pick!, name: txt(o.name) }); nav("/recruiter"); }}>Confirm company</Button>
        </fieldset>)}
    </>
  );
}

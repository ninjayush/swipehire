import { api, USE_MOCKS } from "../../api/client";
import { BASE_URL } from "../../api/http";
import { Button, PageHeader, Panel } from "../../components/ui";
import { useSession } from "../../state/session";

export default function Settings() {
  const { company, setCompany } = useSession();
  void api;
  return (
    <>
      <PageHeader title="Settings" />
      <Panel className="space-y-3 text-sm">
        <div><span className="text-muted">Data mode:</span> <strong>{USE_MOCKS ? "Demo (mock data)" : "Live backend"}</strong></div>
        {!USE_MOCKS && <div><span className="text-muted">Backend:</span> {BASE_URL}</div>}
        <div><span className="text-muted">Company:</span> {company?.name ?? "Not set"}</div>
        <Button variant="secondary" onClick={() => { localStorage.clear(); setCompany(null); location.href = "/"; }}>Reset demo session</Button>
      </Panel>
    </>
  );
}

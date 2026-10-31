import React, { createContext, useContext, useMemo, useState } from "react";
import { DECK, DeckCard, DEMO_CANDIDATE_ID, JOB_TITLE } from "./data";

export type Role = "recruiter" | "candidate" | null;
export interface Interest { id: string; person_id: string; job_title: string; status: "pending" | "accepted" | "rejected"; at: string }
interface Store {
  role: Role; setRole: (r: Role) => void;
  cards: DeckCard[];
  saved: string[]; shortlist: string[]; passed: string[];
  act: (card: DeckCard, a: "shortlist" | "pass" | "save") => void;
  interests: Interest[]; respond: (id: string, r: "accept" | "reject") => void;
  matches: Interest[];
}
const Ctx = createContext<Store | null>(null);
export const useStore = () => { const s = useContext(Ctx); if (!s) throw new Error("no store"); return s; };

export function StoreProvider({ children }: { children: React.ReactNode }) {
  const [role, setRole] = useState<Role>(null);
  const [saved, setSaved] = useState<string[]>([]);
  const [shortlist, setShortlist] = useState<string[]>([]);
  const [passed, setPassed] = useState<string[]>([]);
  const [interests, setInterests] = useState<Interest[]>([]);

  const value = useMemo<Store>(() => ({
    role, setRole, cards: DECK, saved, shortlist, passed,
    act: (card, a) => {
      const id = card.person.person_id;
      if (a === "pass") setPassed((l) => [...l, id]);
      if (a === "save") setSaved((l) => [...l, id]);
      if (a === "shortlist") {
        setShortlist((l) => [...l, id]);
        // Only registered members receive interest. Non-members: internal shortlist, no notification.
        if (card.person.member) setInterests((l) => l.some((i) => i.person_id === id) ? l : [...l, { id: `i-${id}`, person_id: id, job_title: JOB_TITLE, status: "pending", at: new Date().toISOString() }]);
      }
    },
    interests: interests.filter((i) => i.person_id === DEMO_CANDIDATE_ID),
    respond: (id, r) => setInterests((l) => l.map((i) => i.id === id ? { ...i, status: r === "accept" ? "accepted" : "rejected" } : i)),
    matches: interests.filter((i) => i.status === "accepted"),
  }), [role, saved, shortlist, passed, interests]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

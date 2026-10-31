// The backend has no "list saved" endpoint yet. We keep a browser-local convenience list of
// candidates saved from the deck (the save itself is still POSTed to the backend).
import type { DeckCard } from "../types";
const KEY = "sh.saved";
export interface SavedEntry { job_id: string; job_title: string; card: DeckCard; at: string }
export const getSaved = (): SavedEntry[] => { try { return JSON.parse(localStorage.getItem(KEY) ?? "[]"); } catch { return []; } };
const put = (l: SavedEntry[]) => localStorage.setItem(KEY, JSON.stringify(l));
export function addSaved(e: SavedEntry) { put([e, ...getSaved().filter((x) => !(x.job_id === e.job_id && x.card.person.person_id === e.card.person.person_id))]); }
export function removeSaved(job_id: string, person_id: string) { put(getSaved().filter((x) => !(x.job_id === job_id && x.card.person.person_id === person_id))); }

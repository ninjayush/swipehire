import React, { useEffect, useState } from "react";
import { FlatList, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useStore } from "../store";
import { c, gradient, serif } from "../theme";
import { DECK, Person } from "../data";
import { api } from "../api";
import { Busy, EmptyMsg, Retry, Title } from "./Recruiter";
import { Initials, Pill } from "../components/ProfileCard";

export function CandidateEntry() {
  const { setCandidateId } = useStore();
  const [v, setV] = useState("");
  return (
    <View style={{ flex: 1 }}>
      <Title sub="Use the candidate ID from your SwipeHire profile">Welcome back</Title>
      <View style={{ paddingHorizontal: 20, gap: 12 }}>
        <TextInput accessibilityLabel="Candidate ID" value={v} onChangeText={setV} autoCapitalize="none" autoCorrect={false} placeholder="Candidate ID" placeholderTextColor={c.muted} style={s.input} />
        <Pressable accessibilityRole="button" disabled={!v.trim()} onPress={() => setCandidateId(v.trim())} style={[s.btn, { backgroundColor: c.violet, opacity: v.trim() ? 1 : 0.5, flex: 0 }]}><Text style={[s.btnT, { color: "#fff" }]}>Continue</Text></Pressable>
        <Text style={s.fine}>Profile creation and resume upload happen on the web app for now.</Text>
      </View>
    </View>
  );
}

export function Interests() {
  const { interests, respond, candidateId, live, loading, error, reload } = useStore();
  const [busy, setBusy] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  if (live && !candidateId) return <CandidateEntry />;
  const answer = async (id: string, r: "accept" | "reject") => { setBusy(id); setErr(null); try { await respond(id, r); } catch (e) { setErr(e instanceof Error ? e.message : "Failed"); } finally { setBusy(null); } };
  return (
    <View style={{ flex: 1 }}>
      <Title sub="Recruiters who'd like to talk">Interest</Title>
      {err && <Text style={[s.fine, { color: c.red, marginBottom: 8 }]} accessibilityRole="alert">{err}</Text>}
      {error ? <Retry error={error} onRetry={reload} /> : loading && interests.length === 0 ? <Busy label="Loading…" /> : <FlatList data={interests} keyExtractor={(i) => i.id} contentContainerStyle={{ paddingHorizontal: 16, gap: 12 }}
        ListEmptyComponent={<EmptyMsg title="No interest yet" body={live ? "When a recruiter expresses interest, it shows up here." : "Demo tip: switch to the recruiter view and swipe right on Asha — her interest request shows up here."} />}
        renderItem={({ item }) => (
          <View style={s.card}>
            <Text style={s.role}>{item.job_title}</Text>
            <Text style={s.meta}>Demo recruiter · {new Date(item.at).toLocaleDateString()}</Text>
            {item.status === "pending" ? (
              <View style={s.btns}>
                <Pressable accessibilityRole="button" disabled={busy === item.id} onPress={() => answer(item.id, "reject")} style={[s.btn, { backgroundColor: c.paper }]}><Text style={[s.btnT, { color: c.ink }]}>Decline</Text></Pressable>
                <Pressable accessibilityRole="button" disabled={busy === item.id} onPress={() => answer(item.id, "accept")} style={{ flex: 1 }}><LinearGradient colors={gradient.brand} style={s.btn}><Text style={[s.btnT, { color: "#fff" }]}>Accept</Text></LinearGradient></Pressable>
              </View>) : <View style={{ marginTop: 12, flexDirection: "row" }}><Pill bg={item.status === "accepted" ? c.greenSoft : c.paper} fg={item.status === "accepted" ? c.green : c.inkSoft}>{item.status === "accepted" ? "Accepted — it's a match" : "Declined"}</Pill></View>}
          </View>)} />}
    </View>
  );
}

export function Matches() {
  const { matches, role, candidateId, live, error, reload } = useStore();
  if (live && role === "candidate" && !candidateId) return <CandidateEntry />;
  return (
    <View style={{ flex: 1 }}>
      <Title sub="Created only when a candidate accepts">Matches</Title>
      {error ? <Retry error={error} onRetry={reload} /> : <FlatList data={matches} keyExtractor={(m) => m.id} contentContainerStyle={{ paddingHorizontal: 16, gap: 12 }}
        ListEmptyComponent={<EmptyMsg title="No matches yet" body="A match happens only after a registered candidate accepts a recruiter's interest." />}
        renderItem={({ item }) => (
          <LinearGradient colors={gradient.hero} style={s.match}><Initials name={item.name || "?"} size={56} />
            <View style={{ flex: 1 }}><Text style={s.mName}>{role === "recruiter" ? item.name : item.job_title}</Text><Text style={s.mSub}>{role === "recruiter" ? item.job_title : "It's a match"}</Text></View></LinearGradient>)} />}
      <Text style={s.fine}>No messaging in this MVP — nothing leaves the app.</Text>
    </View>
  );
}

export function Profile() {
  const { live, candidateId, setCandidateId } = useStore();
  const [p, setP] = useState<Person | null>(live ? null : DECK[0].person);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => { if (live && candidateId) { setErr(null); api.candidate(candidateId).then(setP).catch((e) => setErr(e.message)); } }, [live, candidateId]);
  if (live && !candidateId) return <CandidateEntry />;
  if (err) return <Retry error={err} onRetry={() => setCandidateId(candidateId)} />;
  if (!p) return <Busy label="Loading profile…" />;
  return (
    <View style={{ flex: 1 }}>
      <Title sub={live ? "From your SwipeHire profile" : "Demo candidate profile"}>Your profile</Title>
      <View style={[s.card, { marginHorizontal: 16 }]}>
        <Text style={s.mName2}>{p.name}</Text><Text style={s.meta}>{p.headline || "No headline"}</Text>
        <Text style={[s.meta, { marginTop: 10 }]}>{p.current_title ? `${p.current_title}${p.current_company ? ` · ${p.current_company}` : ""}` : "Role not available"}</Text>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8, marginTop: 12 }}>{p.skills.map((k) => <Pill key={k}>{k}</Pill>)}</View>
        <Text style={s.fine}>Missing details show as "Unknown" to recruiters — never invented.</Text>
        {live && <Pressable accessibilityRole="button" onPress={() => setCandidateId(null)}><Text style={[s.fine, { textDecorationLine: "underline" }]}>Use a different candidate ID</Text></Pressable>}
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  input: { height: 54, borderRadius: 16, borderWidth: 1, borderColor: c.line, backgroundColor: c.card, paddingHorizontal: 16, fontSize: 16, color: c.ink },
  card: { backgroundColor: c.card, borderRadius: 24, padding: 20 },
  role: { fontFamily: serif, fontSize: 26, color: c.ink }, meta: { color: c.muted, fontSize: 14, marginTop: 4 },
  btns: { flexDirection: "row", gap: 12, marginTop: 16 }, btn: { flex: 1, height: 52, borderRadius: 26, alignItems: "center", justifyContent: "center" }, btnT: { fontWeight: "700", fontSize: 16 },
  match: { flexDirection: "row", alignItems: "center", gap: 14, padding: 18, borderRadius: 24 },
  mName: { color: "#fff", fontFamily: serif, fontSize: 24 }, mSub: { color: "rgba(255,255,255,.85)", marginTop: 2 },
  mName2: { fontFamily: serif, fontSize: 30, color: c.ink }, fine: { color: c.muted, fontSize: 12, textAlign: "center", marginTop: 14 },
});

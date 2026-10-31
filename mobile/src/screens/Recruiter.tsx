import React from "react";
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import { SwipeDeck } from "../components/SwipeDeck";
import { Pill, Initials } from "../components/ProfileCard";
import { useStore } from "../store";
import { c, serif } from "../theme";

export const Title = ({ children, sub }: { children: string; sub?: string }) => (
  <View style={{ paddingHorizontal: 20, paddingBottom: 12 }}><Text style={s.h1}>{children}</Text>{sub && <Text style={s.sub}>{sub}</Text>}</View>
);
export const EmptyMsg = ({ title, body }: { title: string; body: string }) => (
  <View style={s.empty}><Text style={s.emptyT}>{title}</Text><Text style={s.emptyB}>{body}</Text></View>
);

export const Retry = ({ error, onRetry }: { error: string; onRetry: () => void }) => (
  <View style={s.empty}><Text style={s.emptyT}>Something went wrong</Text><Text style={s.emptyB}>{error}</Text>
    <Pressable accessibilityRole="button" onPress={onRetry} style={s.retry}><Text style={{ color: "#fff", fontWeight: "700" }}>Try again</Text></Pressable></View>
);
export const Busy = ({ label }: { label: string }) => <View style={s.empty}><ActivityIndicator color={c.violet} /><Text style={[s.emptyB, { marginTop: 12 }]}>{label}</Text></View>;

function JobPicker() {
  const { jobs, selectJob, loading, error, reload } = useStore();
  return (
    <View style={{ flex: 1 }}>
      <Title sub="Pick a role to review candidates for">Your jobs</Title>
      {loading ? <Busy label="Loading jobs…" /> : error ? <Retry error={error} onRetry={reload} /> : (
        <FlatList data={jobs} keyExtractor={(j) => j.job_id} contentContainerStyle={{ paddingHorizontal: 16, gap: 10 }}
          ListEmptyComponent={<EmptyMsg title="No jobs yet" body="Create a job and confirm its requirements in the SwipeHire web dashboard, then pull to refresh here." />}
          renderItem={({ item }) => (
            <Pressable accessibilityRole="button" onPress={() => selectJob(item)} style={s.row}>
              <View style={{ flex: 1 }}><Text style={s.name}>{item.title}</Text><Text style={s.meta}>{item.must_have_skills.slice(0, 4).join(" · ") || "No must-have skills listed"}</Text></View>
              <Pill bg={item.status === "active" ? c.greenSoft : c.paper} fg={item.status === "active" ? c.green : c.inkSoft}>{item.status.replace(/_/g, " ")}</Pill>
            </Pressable>)} />)}
    </View>
  );
}

export function Discover() {
  const { cards, act, live, job, selectJob, loading, error, reload } = useStore();
  if (live && !job) return <JobPicker />;
  return (
    <View style={{ flex: 1 }}>
      <View style={{ flexDirection: "row", alignItems: "flex-end", justifyContent: "space-between", paddingRight: 20 }}>
        <View style={{ flex: 1 }}><Title sub="Direct and adjacent fits, ranked by the backend">{job?.title ?? "Candidates"}</Title></View>
        {live && <Pressable accessibilityRole="button" onPress={() => selectJob(null)}><Text style={s.link}>Change job</Text></Pressable>}
      </View>
      <View style={{ flex: 1, paddingHorizontal: 12, paddingBottom: 8 }}>
        {loading && cards.length === 0 ? <Busy label="Finding candidates… (first run can take a moment)" /> : error ? <Retry error={error} onRetry={reload} /> : cards.length === 0 && live ? <EmptyMsg title="No eligible candidates" body="Nobody met every must-have requirement for this job. Loosen the mandatory criteria on the web dashboard." /> : (
          <SwipeDeck key={job?.id} cards={cards} onAct={act} empty={<EmptyMsg title="You've seen everyone" body="Check your shortlist, or revisit the requirements." />} />)}
      </View>
    </View>
  );
}

export function Shortlist() {
  const { rows, matches, loading, error, reload } = useStore();
  return (
    <View style={{ flex: 1 }}>
      <Title sub="Shortlisted and saved candidates">Shortlist</Title>
      {error ? <Retry error={error} onRetry={reload} /> : loading && rows.length === 0 ? <Busy label="Loading…" /> : (
        <FlatList data={rows} keyExtractor={(r) => r.kind + r.id} contentContainerStyle={{ paddingHorizontal: 16, gap: 10 }}
          ListEmptyComponent={<EmptyMsg title="Nobody yet" body="Swipe right on a candidate in Discover to shortlist, or tap the flag to save." />}
          renderItem={({ item }) => {
            const status = item.kind === "save" ? "Saved for later" : !item.member ? "Internal shortlist" : matches.some((m) => m.person_id === item.id) ? "Mutual match" : "Interest sent — awaiting response";
            return (
              <View style={s.row}>
                <View style={s.avatar}><Initials name={item.name} size={48} /></View>
                <View style={{ flex: 1 }}><Text style={s.name}>{item.name}</Text>{item.title ? <Text style={s.meta}>{item.title}</Text> : null}
                  <View style={{ flexDirection: "row", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
                    <Pill bg={item.member ? c.violetSoft : c.paper} fg={item.member ? c.violet : c.inkSoft}>{item.member ? "On SwipeHire" : "Not on platform"}</Pill><Pill>{status}</Pill></View></View>
                {item.score != null && <Text style={s.score}>{Math.round(item.score)}</Text>}
              </View>);
          }} />)}
    </View>
  );
}

const s = StyleSheet.create({
  h1: { fontFamily: serif, fontSize: 32, color: c.ink }, sub: { color: c.muted, fontSize: 14, marginTop: 2 },
  empty: { padding: 32, alignItems: "center" }, emptyT: { fontFamily: serif, fontSize: 24, color: c.ink, textAlign: "center" }, emptyB: { color: c.muted, textAlign: "center", marginTop: 8, lineHeight: 21 },
  row: { flexDirection: "row", alignItems: "center", backgroundColor: c.card, borderRadius: 22, padding: 14, gap: 12 },
  avatar: { backgroundColor: c.violet, borderRadius: 24 },
  name: { fontWeight: "700", fontSize: 16, color: c.ink }, meta: { color: c.muted, fontSize: 13 },
  score: { fontFamily: serif, fontSize: 26, color: c.violet },
  link: { color: c.violet, fontWeight: "600", paddingBottom: 14 }, retry: { marginTop: 16, backgroundColor: c.violet, borderRadius: 24, paddingHorizontal: 24, paddingVertical: 12 },
});

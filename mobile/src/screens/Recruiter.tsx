import React from "react";
import { FlatList, StyleSheet, Text, View } from "react-native";
import { SwipeDeck } from "../components/SwipeDeck";
import { Pill, Initials } from "../components/ProfileCard";
import { useStore } from "../store";
import { c, serif } from "../theme";
import { JOB_TITLE } from "../data";

export const Title = ({ children, sub }: { children: string; sub?: string }) => (
  <View style={{ paddingHorizontal: 20, paddingBottom: 12 }}><Text style={s.h1}>{children}</Text>{sub && <Text style={s.sub}>{sub}</Text>}</View>
);
export const EmptyMsg = ({ title, body }: { title: string; body: string }) => (
  <View style={s.empty}><Text style={s.emptyT}>{title}</Text><Text style={s.emptyB}>{body}</Text></View>
);

export function Discover() {
  const { cards, act } = useStore();
  return (
    <View style={{ flex: 1 }}>
      <Title sub="Direct and adjacent fits, ranked by the backend">{JOB_TITLE}</Title>
      <View style={{ flex: 1, paddingHorizontal: 12, paddingBottom: 8 }}>
        <SwipeDeck cards={cards} onAct={act} empty={<EmptyMsg title="You've seen everyone" body="Check your shortlist, or revisit the requirements." />} />
      </View>
    </View>
  );
}

export function Shortlist() {
  const { cards, shortlist, saved, matches } = useStore();
  const rows = [...shortlist.map((id) => ({ id, kind: "shortlist" as const })), ...saved.map((id) => ({ id, kind: "save" as const }))];
  return (
    <View style={{ flex: 1 }}>
      <Title sub="Shortlisted and saved candidates">Shortlist</Title>
      <FlatList data={rows} keyExtractor={(r) => r.kind + r.id} contentContainerStyle={{ paddingHorizontal: 16, gap: 10 }}
        ListEmptyComponent={<EmptyMsg title="Nobody yet" body="Swipe right on a candidate in Discover to shortlist, or tap the flag to save." />}
        renderItem={({ item }) => {
          const card = cards.find((x) => x.person.person_id === item.id)!;
          const p = card.person;
          const status = item.kind === "save" ? "Saved for later" : !p.member ? "Internal shortlist" : matches.some((m) => m.person_id === p.person_id) ? "Mutual match" : "Interest sent — awaiting response";
          return (
            <View style={s.row}>
              <View style={s.avatar}><Initials name={p.name} size={48} /></View>
              <View style={{ flex: 1 }}><Text style={s.name}>{p.name}</Text><Text style={s.meta}>{p.current_title}</Text>
                <View style={{ flexDirection: "row", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
                  <Pill bg={p.member ? c.violetSoft : c.paper} fg={p.member ? c.violet : c.inkSoft}>{p.member ? "On SwipeHire" : "Not on platform"}</Pill><Pill>{status}</Pill></View></View>
              <Text style={s.score}>{Math.round(card.ev.fit_score)}</Text>
            </View>);
        }} />
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
});

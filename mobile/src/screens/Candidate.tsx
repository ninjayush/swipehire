import React from "react";
import { FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useStore } from "../store";
import { c, gradient, serif } from "../theme";
import { DECK } from "../data";
import { EmptyMsg, Title } from "./Recruiter";
import { Initials, Pill } from "../components/ProfileCard";

export function Interests() {
  const { interests, respond } = useStore();
  return (
    <View style={{ flex: 1 }}>
      <Title sub="Recruiters who'd like to talk">Interest</Title>
      <FlatList data={interests} keyExtractor={(i) => i.id} contentContainerStyle={{ paddingHorizontal: 16, gap: 12 }}
        ListEmptyComponent={<EmptyMsg title="No interest yet" body="Demo tip: switch to the recruiter view and swipe right on Asha — her interest request shows up here." />}
        renderItem={({ item }) => (
          <View style={s.card}>
            <Text style={s.role}>{item.job_title}</Text>
            <Text style={s.meta}>Demo recruiter · {new Date(item.at).toLocaleDateString()}</Text>
            {item.status === "pending" ? (
              <View style={s.btns}>
                <Pressable accessibilityRole="button" onPress={() => respond(item.id, "reject")} style={[s.btn, { backgroundColor: c.paper }]}><Text style={[s.btnT, { color: c.ink }]}>Decline</Text></Pressable>
                <Pressable accessibilityRole="button" onPress={() => respond(item.id, "accept")} style={{ flex: 1 }}><LinearGradient colors={gradient.brand} style={s.btn}><Text style={[s.btnT, { color: "#fff" }]}>Accept</Text></LinearGradient></Pressable>
              </View>) : <View style={{ marginTop: 12, flexDirection: "row" }}><Pill bg={item.status === "accepted" ? c.greenSoft : c.paper} fg={item.status === "accepted" ? c.green : c.inkSoft}>{item.status === "accepted" ? "Accepted — it's a match" : "Declined"}</Pill></View>}
          </View>)} />
    </View>
  );
}

export function Matches() {
  const { matches, role, cards } = useStore();
  return (
    <View style={{ flex: 1 }}>
      <Title sub="Created only when a candidate accepts">Matches</Title>
      <FlatList data={matches} keyExtractor={(m) => m.id} contentContainerStyle={{ paddingHorizontal: 16, gap: 12 }}
        ListEmptyComponent={<EmptyMsg title="No matches yet" body="A match happens only after a registered candidate accepts a recruiter's interest." />}
        renderItem={({ item }) => { const p = cards.find((x) => x.person.person_id === item.person_id)!.person; return (
          <LinearGradient colors={gradient.hero} style={s.match}><Initials name={p.name} size={56} />
            <View style={{ flex: 1 }}><Text style={s.mName}>{role === "recruiter" ? p.name : item.job_title}</Text><Text style={s.mSub}>{role === "recruiter" ? item.job_title : "It's a match"}</Text></View></LinearGradient>); }} />
      <Text style={s.fine}>No messaging in this MVP — nothing leaves the app.</Text>
    </View>
  );
}

export function Profile() {
  const p = DECK[0].person;
  return (
    <View style={{ flex: 1 }}>
      <Title sub="Demo candidate profile">Your profile</Title>
      <View style={[s.card, { marginHorizontal: 16 }]}>
        <Text style={s.mName2}>{p.name}</Text><Text style={s.meta}>{p.headline}</Text>
        <Text style={[s.meta, { marginTop: 10 }]}>{p.current_title} · {p.current_company}</Text>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8, marginTop: 12 }}>{p.skills.map((k) => <Pill key={k}>{k}</Pill>)}</View>
        <Text style={s.fine}>Missing details show as "Unknown" to recruiters — never invented.</Text>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  card: { backgroundColor: c.card, borderRadius: 24, padding: 20 },
  role: { fontFamily: serif, fontSize: 26, color: c.ink }, meta: { color: c.muted, fontSize: 14, marginTop: 4 },
  btns: { flexDirection: "row", gap: 12, marginTop: 16 }, btn: { flex: 1, height: 52, borderRadius: 26, alignItems: "center", justifyContent: "center" }, btnT: { fontWeight: "700", fontSize: 16 },
  match: { flexDirection: "row", alignItems: "center", gap: 14, padding: 18, borderRadius: 24 },
  mName: { color: "#fff", fontFamily: serif, fontSize: 24 }, mSub: { color: "rgba(255,255,255,.85)", marginTop: 2 },
  mName2: { fontFamily: serif, fontSize: 30, color: c.ink }, fine: { color: c.muted, fontSize: 12, textAlign: "center", marginTop: 14 },
});

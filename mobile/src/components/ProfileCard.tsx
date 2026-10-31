import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { DeckCard } from "../data";
import { c, gradient, r, serif } from "../theme";

export const Pill = ({ children, bg = c.paper, fg = c.ink }: { children: React.ReactNode; bg?: string; fg?: string }) => (
  <View style={[s.pill, { backgroundColor: bg }]}><Text style={[s.pillT, { color: fg }]}>{children}</Text></View>
);
const Unknown = ({ label }: { label: string }) => <Text style={s.unknown}>{label}: Unknown — needs confirmation</Text>;
const Block = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <View style={s.block}><Text style={s.blockTitle}>{title}</Text>{children}</View>
);

export function Initials({ name, size = 72 }: { name: string; size?: number }) {
  const t = name.split(" ").slice(0, 2).map((x) => x[0]).join("");
  return <View style={{ width: size, height: size, borderRadius: size / 2, backgroundColor: "rgba(255,255,255,.2)", alignItems: "center", justifyContent: "center" }}><Text style={{ color: "#fff", fontFamily: serif, fontSize: size * 0.4 }}>{t}</Text></View>;
}

export function ProfileBody({ card }: { card: DeckCard }) {
  const { person: p, ev } = card;
  const adj = ev.fit_type === "adjacent";
  return (
    <View>
      <LinearGradient colors={adj ? gradient.adjacent : gradient.hero} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={s.hero}>
        <View style={s.heroTop}>
          <Initials name={p.name} />
          <View style={s.score}><Text style={s.scoreN}>{Math.round(ev.fit_score)}</Text><Text style={s.scoreL}>fit</Text></View>
        </View>
        <Text style={s.name}>{p.name}</Text>
        <Text style={s.headline}>{p.headline}</Text>
        <View style={s.row}>
          <Pill bg="rgba(255,255,255,.22)" fg="#fff">{adj ? "Adjacent fit" : "Direct fit"}</Pill>
          <Pill bg="rgba(255,255,255,.22)" fg="#fff">{p.member ? "On SwipeHire" : "Not on platform"}</Pill>
        </View>
      </LinearGradient>

      <View style={s.body}>
        <View style={s.block}>
          <Text style={s.role}>{p.current_title} · {p.current_company}</Text>
          <Text style={s.meta}>{p.location ?? "Location unknown"}{" · "}{p.experience_years != null ? `${p.experience_years} yrs` : "Experience unknown"}</Text>
          <View style={[s.row, { marginTop: 12 }]}>{p.skills.slice(0, 5).map((k) => <Pill key={k}>{k}</Pill>)}</View>
        </View>

        <View style={[s.block, { backgroundColor: c.violetSoft }]}>
          <Text style={[s.blockTitle, { color: c.violet }]}>Why this candidate</Text>
          <Text style={s.prompt}>{ev.explanation}</Text>
        </View>

        {p.prompts.map((pr) => (
          <View key={pr.label} style={s.block}><Text style={s.blockTitle}>{pr.label}</Text><Text style={s.prompt}>{pr.text}</Text></View>
        ))}

        <Block title="Career timeline">
          {p.history.length === 0 ? <Unknown label="Work history" /> : p.history.map((h, i) => (
            <View key={i} style={{ marginBottom: 12 }}><Text style={s.hTitle}>{h.title} · {h.company}</Text><Text style={s.meta}>{h.years}</Text>{h.note && <Text style={s.note}>{h.note}</Text>}</View>))}
          {!p.member && <Text style={s.unknown}>From a public profile source; not independently verified.</Text>}
        </Block>

        <Block title="Education">{p.education.length === 0 ? <Unknown label="Education" /> : p.education.map((e) => <Text key={e} style={s.note}>{e}</Text>)}</Block>

        <Block title="Fit breakdown">
          {Object.entries(ev.components).map(([k, v]) => (
            <View key={k} style={{ marginBottom: 10 }}>
              <View style={s.split}><Text style={s.note}>{k}</Text><Text style={s.hTitle}>{v}</Text></View>
              <View style={s.track}><View style={[s.fill, { width: `${v}%`, backgroundColor: adj ? c.olive : c.violet }]} /></View>
            </View>))}
          <Text style={s.unknown}>Evidence coverage {Math.round(ev.coverage * 100)}% · scores come from the backend, not this app.</Text>
        </Block>
        <View style={{ height: 24 }} />
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  hero: { padding: 24, paddingTop: 28, minHeight: 300, justifyContent: "flex-end" },
  heroTop: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 56 },
  score: { alignItems: "center", backgroundColor: "rgba(255,255,255,.2)", borderRadius: 18, paddingHorizontal: 14, paddingVertical: 8 },
  scoreN: { color: "#fff", fontFamily: serif, fontSize: 28 }, scoreL: { color: "#fff", fontSize: 11, opacity: 0.85 },
  name: { color: "#fff", fontFamily: serif, fontSize: 40, lineHeight: 44 },
  headline: { color: "rgba(255,255,255,.9)", fontSize: 16, marginTop: 6, marginBottom: 14 },
  row: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  pill: { borderRadius: 999, paddingHorizontal: 12, paddingVertical: 6 }, pillT: { fontSize: 13, fontWeight: "600" },
  body: { padding: 14, gap: 12, backgroundColor: c.paper },
  block: { backgroundColor: c.card, borderRadius: r.card - 6, padding: 20 },
  blockTitle: { fontSize: 12, fontWeight: "700", letterSpacing: 0.6, textTransform: "uppercase", color: c.muted, marginBottom: 10 },
  role: { fontFamily: serif, fontSize: 22, color: c.ink }, meta: { color: c.muted, fontSize: 14, marginTop: 4 },
  prompt: { fontFamily: serif, fontSize: 24, lineHeight: 31, color: c.ink },
  hTitle: { fontWeight: "700", color: c.ink, fontSize: 15 }, note: { color: c.inkSoft, fontSize: 15, lineHeight: 21, marginTop: 2 },
  unknown: { color: c.muted, fontSize: 13, fontStyle: "italic", marginTop: 4 },
  split: { flexDirection: "row", justifyContent: "space-between" },
  track: { height: 6, borderRadius: 3, backgroundColor: c.paper, marginTop: 6 }, fill: { height: 6, borderRadius: 3 },
});

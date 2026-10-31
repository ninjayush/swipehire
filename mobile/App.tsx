import React, { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import { StoreProvider, useStore } from "./src/store";
import Welcome from "./src/screens/Welcome";
import { Discover, Shortlist } from "./src/screens/Recruiter";
import { Interests, Matches, Profile } from "./src/screens/Candidate";
import { c, serif } from "./src/theme";

const TABS = {
  recruiter: [{ k: "discover", label: "Discover", C: Discover }, { k: "shortlist", label: "Shortlist", C: Shortlist }, { k: "matches", label: "Matches", C: Matches }],
  candidate: [{ k: "interest", label: "Interest", C: Interests }, { k: "matches", label: "Matches", C: Matches }, { k: "profile", label: "Profile", C: Profile }],
} as const;

function Shell() {
  const { role, setRole } = useStore();
  const [tab, setTab] = useState(0);
  if (!role) return <Welcome />;
  const tabs = TABS[role];
  const Screen = tabs[tab].C;
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: c.paper }} edges={["top", "bottom"]}>
      <View style={s.top}><Text style={s.logo}>SwipeHire</Text>
        <Pressable accessibilityRole="button" onPress={() => { setTab(0); setRole(role === "recruiter" ? "candidate" : "recruiter"); }}><Text style={s.switch}>Switch to {role === "recruiter" ? "candidate" : "recruiter"}</Text></Pressable></View>
      <View style={{ flex: 1 }}><Screen /></View>
      <View style={s.bar} accessibilityRole="tablist">
        {tabs.map((t, i) => (
          <Pressable key={t.k} accessibilityRole="tab" accessibilityState={{ selected: i === tab }} onPress={() => setTab(i)} style={s.tab}>
            <Text style={[s.tabT, i === tab && { color: c.violet }]}>{t.label}</Text>
            {i === tab && <View style={s.dot} />}
          </Pressable>))}
      </View>
    </SafeAreaView>
  );
}

export default function App() {
  return <SafeAreaProvider><StoreProvider><StatusBar style="auto" /><Shell /></StoreProvider></SafeAreaProvider>;
}

const s = StyleSheet.create({
  top: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingHorizontal: 20, paddingVertical: 10 },
  logo: { fontFamily: serif, fontSize: 22, fontWeight: "700", color: c.ink }, switch: { color: c.muted, fontSize: 12, textDecorationLine: "underline" },
  bar: { flexDirection: "row", backgroundColor: c.card, borderTopWidth: 1, borderTopColor: c.line, paddingTop: 6 },
  tab: { flex: 1, alignItems: "center", minHeight: 48, justifyContent: "center" }, tabT: { fontSize: 13, fontWeight: "600", color: c.muted },
  dot: { width: 5, height: 5, borderRadius: 3, backgroundColor: c.violet, marginTop: 4 },
});

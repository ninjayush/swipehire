import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { SafeAreaView } from "react-native-safe-area-context";
import { c, gradient, serif } from "../theme";
import { useStore } from "../store";

export default function Welcome() {
  const { setRole } = useStore();
  return (
    <LinearGradient colors={gradient.hero} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={{ flex: 1 }}>
      <SafeAreaView style={s.safe}>
        <Text style={s.brand}>SwipeHire</Text>
        <View style={{ flex: 1, justifyContent: "center" }}>
          <Text style={s.title}>Discover talent{"\n"}beyond keywords.</Text>
          <Text style={s.sub}>An explainable, swipeable deck of people who can actually do the job — including the ones keyword search misses.</Text>
        </View>
        <Btn label="I'm hiring" onPress={() => setRole("recruiter")} primary />
        <Btn label="I'm a candidate" onPress={() => setRole("candidate")} />
        <Text style={s.fine}>Demo mode · fictional people · nothing is ever sent to anyone</Text>
      </SafeAreaView>
    </LinearGradient>
  );
}
const Btn = ({ label, onPress, primary }: { label: string; onPress: () => void; primary?: boolean }) => (
  <Pressable accessibilityRole="button" onPress={onPress} style={({ pressed }) => [s.btn, primary ? { backgroundColor: "#fff" } : { borderWidth: 1.5, borderColor: "rgba(255,255,255,.7)" }, pressed && { opacity: 0.85 }]}>
    <Text style={[s.btnT, { color: primary ? c.ink : "#fff" }]}>{label}</Text>
  </Pressable>
);
const s = StyleSheet.create({
  safe: { flex: 1, padding: 24 },
  brand: { color: "#fff", fontFamily: serif, fontSize: 26, fontWeight: "700" },
  title: { color: "#fff", fontFamily: serif, fontSize: 48, lineHeight: 52 },
  sub: { color: "rgba(255,255,255,.88)", fontSize: 17, lineHeight: 24, marginTop: 16 },
  btn: { height: 56, borderRadius: 28, alignItems: "center", justifyContent: "center", marginBottom: 12 },
  btnT: { fontSize: 17, fontWeight: "700" },
  fine: { color: "rgba(255,255,255,.7)", fontSize: 12, textAlign: "center", marginTop: 4 },
});

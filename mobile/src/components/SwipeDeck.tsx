import React, { useCallback, useMemo, useRef, useState } from "react";
import { Animated, Dimensions, PanResponder, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { Bookmark, Heart, X } from "./icons";
import { DeckCard } from "../data";
import { c, gradient, r, shadow, serif } from "../theme";
import { ProfileBody } from "./ProfileCard";

const W = Dimensions.get("window").width;
const THRESH = W * 0.3;
type Act = "shortlist" | "pass" | "save";

export function SwipeDeck({ cards, onAct, empty }: { cards: DeckCard[]; onAct: (c: DeckCard, a: Act) => void; empty: React.ReactNode }) {
  const [i, setI] = useState(0);
  const pos = useRef(new Animated.ValueXY()).current;
  const card = cards[i];
  const cardRef = useRef(card); cardRef.current = card;

  const fly = useCallback((a: Act) => {
    const target = a === "shortlist" ? { x: W * 1.3, y: 0 } : a === "pass" ? { x: -W * 1.3, y: 0 } : { x: 0, y: 800 };
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    Animated.timing(pos, { toValue: target, duration: 220, useNativeDriver: false }).start(() => {
      onAct(cardRef.current, a); pos.setValue({ x: 0, y: 0 }); setI((n) => n + 1);
    });
  }, [onAct, pos]);

  const pan = useMemo(() => PanResponder.create({
    // only claim clearly-horizontal drags so vertical scrolling of the profile still works
    onMoveShouldSetPanResponder: (_, g) => Math.abs(g.dx) > 12 && Math.abs(g.dx) > Math.abs(g.dy) * 1.6,
    onPanResponderMove: Animated.event([null, { dx: pos.x }], { useNativeDriver: false }),
    onPanResponderRelease: (_, g) => {
      if (g.dx > THRESH) fly("shortlist"); else if (g.dx < -THRESH) fly("pass");
      else Animated.spring(pos, { toValue: { x: 0, y: 0 }, useNativeDriver: false }).start();
    },
  }), [fly, pos]);

  if (!card) return <>{empty}</>;
  const rot = pos.x.interpolate({ inputRange: [-W, 0, W], outputRange: ["-8deg", "0deg", "8deg"] });
  const likeO = pos.x.interpolate({ inputRange: [0, THRESH], outputRange: [0, 1], extrapolate: "clamp" });
  const passO = pos.x.interpolate({ inputRange: [-THRESH, 0], outputRange: [1, 0], extrapolate: "clamp" });
  const member = card.person.member;

  return (
    <View style={s.wrap}>
      <Text style={s.progress} accessibilityLiveRegion="polite">{i} of {cards.length} reviewed</Text>
      <View style={s.stack}>
        {cards[i + 1] && <View style={[s.card, s.behind]} />}
        <Animated.View {...pan.panHandlers} style={[s.card, shadow, { transform: [{ translateX: pos.x }, { translateY: pos.y }, { rotate: rot }] }]}>
          <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 120 }} key={card.person.person_id}>
            <ProfileBody card={card} />
          </ScrollView>
          <Animated.View pointerEvents="none" style={[s.stamp, { left: 20, borderColor: c.green, opacity: likeO }]}><Text style={[s.stampT, { color: c.green }]}>{member ? "INTEREST" : "SHORTLIST"}</Text></Animated.View>
          <Animated.View pointerEvents="none" style={[s.stamp, { right: 20, borderColor: c.red, opacity: passO }]}><Text style={[s.stampT, { color: c.red }]}>PASS</Text></Animated.View>
        </Animated.View>

        <View style={s.dock} pointerEvents="box-none">
          <Round label="Pass" onPress={() => fly("pass")} bg="#fff" fg={c.ink}><X /></Round>
          <Round label="Save for later" onPress={() => fly("save")} bg="#fff" fg={c.ink} small><Bookmark /></Round>
          <Round label={member ? "Express interest" : "Shortlist (internal only)"} onPress={() => fly("shortlist")} gradientBg><Heart /></Round>
        </View>
      </View>
      <Text style={s.note}>{member ? "Interest sends an in-app request they can accept or decline." : "Not on platform — internal shortlist only. Nobody is contacted."}</Text>
    </View>
  );
}

function Round({ onPress, label, children, bg, fg, small, gradientBg }: { onPress: () => void; label: string; children: React.ReactNode; bg?: string; fg?: string; small?: boolean; gradientBg?: boolean }) {
  const size = small ? 52 : 68;
  const inner = <View style={{ width: size, height: size, borderRadius: size / 2, alignItems: "center", justifyContent: "center" }}>{React.isValidElement(children) ? React.cloneElement(children as React.ReactElement<{ color?: string }>, { color: gradientBg ? "#fff" : fg }) : children}</View>;
  return (
    <Pressable accessibilityRole="button" accessibilityLabel={label} onPress={onPress} style={({ pressed }) => [shadow, { borderRadius: size / 2, transform: [{ scale: pressed ? 0.94 : 1 }], backgroundColor: bg }]}>
      {gradientBg ? <LinearGradient colors={gradient.brand} style={{ borderRadius: size / 2 }}>{inner}</LinearGradient> : inner}
    </Pressable>
  );
}

const s = StyleSheet.create({
  wrap: { flex: 1 },
  progress: { textAlign: "center", color: c.muted, fontSize: 13, marginBottom: 8 },
  stack: { flex: 1 },
  card: { flex: 1, borderRadius: r.card, backgroundColor: c.paper, overflow: "hidden" },
  behind: { position: "absolute", left: 14, right: 14, top: 10, bottom: -4, backgroundColor: c.line, opacity: 0.7 },
  stamp: { position: "absolute", top: 24, borderWidth: 3, borderRadius: 12, paddingHorizontal: 12, paddingVertical: 4, backgroundColor: "#fff", transform: [{ rotate: "-6deg" }] },
  stampT: { fontFamily: serif, fontSize: 22, fontWeight: "700" },
  dock: { position: "absolute", bottom: 16, left: 0, right: 0, flexDirection: "row", justifyContent: "center", alignItems: "center", gap: 20 },
  note: { textAlign: "center", color: c.muted, fontSize: 12, marginTop: 8, paddingHorizontal: 20 },
});

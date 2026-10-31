import { Platform } from "react-native";

// Hinge-inspired mood (warm paper, near-black ink, big serif headlines, one saturated accent,
// round floating actions) using SwipeHire's own palette. No Hinge logo/assets/copy.
export const c = {
  paper: "#F6F2EB",
  card: "#FFFFFF",
  ink: "#16131F",
  inkSoft: "#4A4657",
  muted: "#8B8794",
  line: "#E6E0D6",
  violet: "#5B3FD6",
  plum: "#9B3FD6",
  violetSoft: "#ECE7FF",
  green: "#1F7A5E",
  greenSoft: "#E1F2EA",
  olive: "#A4B84A",
  oliveSoft: "#F1F4DC",
  red: "#C84E55",
  redSoft: "#FBE9E9",
};
export const gradient = { brand: [c.violet, c.plum] as const, hero: ["#2A1B6B", "#5B3FD6", "#B05AE0"] as const, adjacent: ["#6B7F1F", "#A4B84A"] as const };
export const serif = Platform.select({ ios: "Georgia", android: "serif", default: "Georgia, 'Times New Roman', serif" })!;
export const shadow = { shadowColor: "#16131F", shadowOpacity: 0.12, shadowRadius: 24, shadowOffset: { width: 0, height: 10 }, elevation: 6 };
export const r = { card: 28, btn: 16 };

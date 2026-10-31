// Tiny dependency-free glyph icons.
import React from "react";
import { Text } from "react-native";
type P = { color?: string; size?: number };
const g = (ch: string, base = 28) => ({ color = "#16131F", size = base }: P) => <Text style={{ color, fontSize: size, fontWeight: "600" }} accessible={false}>{ch}</Text>;
export const X = g("✕"); export const Heart = g("♥", 30); export const Bookmark = g("⚑", 22);

import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, radius, space, type } from '../theme';

/**
 * The product's front door.
 *
 * Vybe's thesis is that people ask questions, they do not read dashboards —
 * so the ask control sits above the data, not behind a tab. It is a Pressable
 * rather than a TextInput on purpose: tapping opens the conversation screen,
 * which keeps the home screen calm and avoids a keyboard on launch.
 */
export default function AskBar({ onPress, suggestion }) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel="Ask Vybe about your health"
      accessibilityHint="Opens a conversation where you can ask questions in your own words"
      style={({ pressed }) => [styles.wrap, pressed && styles.pressed]}
    >
      <Text style={styles.prompt}>Ask your health</Text>
      {suggestion ? <Text style={styles.suggestion}>{suggestion}</Text> : null}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  wrap: {
    backgroundColor: colors.ink,
    borderRadius: radius.card,
    paddingVertical: space(2.5),
    paddingHorizontal: space(2.5),
    gap: space(0.75),
  },
  pressed: { opacity: 0.85 },
  prompt: { ...type.title, color: colors.paper },
  suggestion: { ...type.small, color: colors.brandSoft },
});

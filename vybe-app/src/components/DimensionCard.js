import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, radius, space, type } from '../theme';

/**
 * One of the five dimensions.
 *
 * The status word is always present in text. Colour reinforces it and never
 * carries the meaning alone — a red dot with no word is unreadable to a
 * colour-blind user and meaningless to a screen reader.
 */
export default function DimensionCard({ dimension, status, detail, onPress }) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={`${dimension.label}. ${status}. ${detail}`}
      style={({ pressed }) => [styles.card, pressed && styles.pressed]}
    >
      <View style={[styles.rail, { backgroundColor: dimension.hue }]} />
      <View style={styles.body}>
        <Text style={[styles.label, { color: dimension.hue }]}>
          {dimension.label.toUpperCase()}
        </Text>
        <Text style={styles.status}>{status}</Text>
        <Text style={styles.detail}>{detail}</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: 'hidden',
  },
  pressed: { opacity: 0.9 },
  rail: { width: 5 },
  body: { flex: 1, padding: space(2), gap: space(0.5) },
  label: type.label,
  status: { ...type.title, color: colors.ink },
  detail: { ...type.small, color: colors.muted },
});

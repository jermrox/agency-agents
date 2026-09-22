import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors, space, type } from '../theme';

/**
 * One physiological reading and what it means.
 *
 * Hairline-separated rows, not a card each. A row of rounded boxes reads as
 * five separate objects; this is one list of one person's signals.
 *
 * The arrow is decoration. `reading` always states the direction in words
 * ("Down 18% on your 30-day average"), so the row survives being read aloud
 * by a screen reader or seen by someone who cannot separate the hues.
 */
const GLYPH = { up: '↑', down: '↓', flat: '→' };

export default function EvidenceRow({ item, first }) {
  const tone = item.concern ? colors.ink : colors.muted;
  return (
    <View
      style={[styles.row, !first && styles.ruled]}
      accessible
      accessibilityRole="text"
      accessibilityLabel={`${item.label}. ${item.value}. ${item.reading}.`}
    >
      <View style={styles.left}>
        <Text style={styles.label}>{item.label}</Text>
        <Text style={[styles.reading, { color: tone }]}>{item.reading}</Text>
      </View>
      <View style={styles.right}>
        <Text style={styles.value}>{item.value}</Text>
        <Text aria-hidden style={styles.glyph}>{GLYPH[item.direction]}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'flex-start', paddingVertical: space(2), gap: space(2) },
  ruled: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },
  left: { flex: 1, gap: 2 },
  right: { alignItems: 'flex-end', gap: 2 },
  label: { ...type.body, color: colors.ink, fontWeight: '600' },
  reading: { ...type.small },
  // Tabular figures keep the numbers on one optical column down the list.
  value: { ...type.title, color: colors.ink, fontVariant: ['tabular-nums'] },
  glyph: { ...type.small, color: colors.faint },
});

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors, radius, space, type } from '../theme';

/**
 * The connection between two dimensions — the thing a single-metric app
 * cannot say. This is the screen's most valuable element, so it is given
 * the brand colour and sits directly under the ask control.
 */
export default function InsightCard({ headline, body, dimensionsInvolved }) {
  return (
    <View style={styles.card} accessibilityRole="summary">
      <Text style={styles.label}>WHAT CONNECTED TODAY</Text>
      <Text style={styles.headline}>{headline}</Text>
      <Text style={styles.body}>{body}</Text>
      <View style={styles.tags}>
        {dimensionsInvolved.map((d) => (
          <View key={d.key} style={[styles.tag, { borderColor: d.hue }]}>
            <Text style={[styles.tagText, { color: d.hue }]}>{d.label}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.brand,
    borderRadius: radius.card,
    padding: space(2.5),
    gap: space(1),
  },
  label: { ...type.label, color: colors.brandSoft },
  headline: { ...type.title, color: colors.paper, lineHeight: 29 },
  body: { ...type.body, color: '#D8EBE4' },
  tags: { flexDirection: 'row', gap: space(1), marginTop: space(0.5) },
  tag: {
    borderWidth: 1.5,
    borderRadius: radius.pill,
    paddingVertical: space(0.5),
    paddingHorizontal: space(1.25),
    backgroundColor: colors.paper,
  },
  tagText: { ...type.label, fontSize: 11 },
});

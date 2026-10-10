import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, space, type } from '../theme';

/**
 * Where a hard week came from — a composition bar over a ranked list.
 *
 * The app already has two kinds of bar and neither fits this. `TrendColumns`
 * is one value per week across twenty-six weeks; `PatternWeeks` is one value
 * per week against a line. This is a single quantity broken into named parts,
 * which is a different question — not "how did it move" but "what was it made
 * of" — so it gets a single bar read left to right instead of a row of them.
 *
 * THE BAR IS THE SECOND READING, NEVER THE ONLY ONE
 * Its segments are steps of the one Connect hue, and steps of a single hue are
 * exactly what somebody with low contrast sensitivity cannot separate. So
 * every segment's name, hours and share are also printed in the list beneath
 * it, and nothing appears in the bar alone. Remove the bar and the section
 * still says everything it says.
 *
 * THE REMAINDER IS DRAWN
 * The unexplained hours get a segment with an outline and no fill, at the end
 * of the bar and at the bottom of the list. Leaving them out would make the
 * named sources sum to the whole week and quietly turn an incomplete account
 * into a complete one.
 */

// Four days is the floor for saying anything about a body response. Below it
// the list says how many days there were instead of what they did.
export const MIN_DAYS = 4;

// Steps of the single Connect hue, applied as opacity rather than as new
// colour tokens, so the palette stays in theme.js. Index by rank.
const STEPS = [1, 0.74, 0.5, 0.3];

export function namedHoursOf(sources) {
  return sources.reduce((sum, s) => sum + s.hours, 0);
}

/**
 * Clamped at zero on purpose. Hours are assigned to one source only, so the
 * named total should never exceed the measured one — but if a future data
 * source double-counts, a negative remainder would render as a backwards bar
 * and a nonsense sentence. Zero plus the overlap note is the safe failure.
 */
export function unexplainedOf(sources, strainHours) {
  return Math.max(0, strainHours - namedHoursOf(sources));
}

export function shareOf(hours, strainHours) {
  if (!strainHours) return 0;
  return Math.round((hours / strainHours) * 100);
}

/** 'matched' when there are enough comparable days to say something, else 'thin'. */
export function confidenceFor(source) {
  return source.comparedDays >= MIN_DAYS && source.response ? 'matched' : 'thin';
}

export default function LoadSources({
  sources,
  strainHours,
  hue,
  selectedId,
  onSelect,
}) {
  const unexplained = unexplainedOf(sources, strainHours);

  return (
    <View>
      {/* THE BAR. Hidden from screen readers: it carries nothing the list
          below does not say in words. */}
      <View style={styles.bar} aria-hidden accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
        {sources.map((s, i) => (
          <View
            key={s.id}
            style={[
              styles.segment,
              {
                width: `${shareOf(s.hours, strainHours)}%`,
                backgroundColor: hue,
                opacity: STEPS[i] === undefined ? 0.3 : STEPS[i],
              },
            ]}
          />
        ))}
        {unexplained > 0 ? (
          <View style={[styles.segment, styles.remainder, { width: `${shareOf(unexplained, strainHours)}%` }]} />
        ) : null}
      </View>

      {/* THE LIST. Ranked as given, which is by hours. */}
      {sources.map((s, i) => {
        const selected = s.id === selectedId;
        const share = shareOf(s.hours, strainHours);
        const matched = confidenceFor(s) === 'matched';
        return (
          <Pressable
            key={s.id}
            onPress={() => onSelect && onSelect(s.id)}
            accessibilityRole="button"
            accessibilityState={{ selected }}
            accessibilityLabel={
              `${s.label}. ${s.hours} hours, ${share} percent of the week. `
              + (matched
                ? `${s.response.metric} ${s.response.text}.`
                : `Only ${s.comparedDays} ${s.comparedDays === 1 ? 'day' : 'days'} like this, so Vybe says nothing about what it did.`)
            }
            accessibilityHint="Pins this source in the readout above the list"
            style={({ pressed }) => [
              styles.row,
              i > 0 && styles.ruled,
              selected && styles.rowSelected,
              pressed && styles.pressed,
            ]}
          >
            <View style={styles.swatchColumn}>
              <View
                aria-hidden
                style={[styles.swatch, { backgroundColor: hue, opacity: STEPS[i] === undefined ? 0.3 : STEPS[i] }]}
              />
            </View>
            <View style={styles.rowBody}>
              <Text style={styles.rowLabel}>{s.label}</Text>
              {matched ? (
                <Text style={styles.rowResponse}>
                  {s.response.metric} {s.response.text}
                </Text>
              ) : (
                <Text style={styles.rowThin}>
                  {s.comparedDays === 1
                    ? 'One day like this. Vybe will not call that a pattern.'
                    : `Only ${s.comparedDays} days like this — not enough to say what they did to you.`}
                </Text>
              )}
            </View>
            <View style={styles.rowRight}>
              <Text style={styles.rowHours}>{s.hours}h</Text>
              <Text style={styles.rowShare}>{share}%</Text>
            </View>
          </Pressable>
        );
      })}

      {/* THE REMAINDER, as a row, so it is ranked alongside the named sources
          rather than filed as a footnote. Not pressable: there is nothing to
          pin, which is the fact it exists to carry. */}
      {unexplained > 0 ? (
        <View
          style={[styles.row, styles.ruled]}
          accessible
          accessibilityRole="text"
          accessibilityLabel={
            `Not accounted for. ${unexplained} hours, `
            + `${shareOf(unexplained, strainHours)} percent of the week.`
          }
        >
          <View style={styles.swatchColumn}>
            <View aria-hidden style={[styles.swatch, styles.swatchEmpty]} />
          </View>
          <View style={styles.rowBody}>
            <Text style={styles.rowLabel}>Not accounted for</Text>
            <Text style={styles.rowThin}>No calendar entry, no travel, no weather.</Text>
          </View>
          <View style={styles.rowRight}>
            <Text style={styles.rowHours}>{unexplained}h</Text>
            <Text style={styles.rowShare}>{shareOf(unexplained, strainHours)}%</Text>
          </View>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  // Percentage widths, so there is no measurement pass and no layout library.
  bar: {
    flexDirection: 'row',
    height: 14,
    borderRadius: 3,
    overflow: 'hidden',
    backgroundColor: colors.surface,
    marginBottom: space(1),
  },
  segment: { height: '100%' },
  remainder: {
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.paper,
  },

  row: { flexDirection: 'row', alignItems: 'flex-start', paddingVertical: space(1.75), gap: space(1.5) },
  ruled: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },
  // Selection moves the left edge rather than tinting the row: a tint on a row
  // that already carries a hue swatch would read as a second meaning.
  rowSelected: { borderLeftWidth: 2, borderLeftColor: colors.ink, paddingLeft: space(1.25) },
  pressed: { opacity: 0.6 },

  // The swatch sits in a fixed column so the labels line up whether or not a
  // row is selected.
  swatchColumn: { width: 12, paddingTop: 5 },
  swatch: { width: 10, height: 10, borderRadius: 2 },
  swatchEmpty: { backgroundColor: colors.paper, borderWidth: 1, borderColor: colors.border },

  rowBody: { flex: 1, gap: 2 },
  rowLabel: { ...type.body, color: colors.ink, fontWeight: '600' },
  rowResponse: { ...type.small, color: colors.muted, lineHeight: 19 },
  rowThin: { ...type.small, color: colors.faint, lineHeight: 19 },

  rowRight: { alignItems: 'flex-end', gap: 1, minWidth: space(5) },
  rowHours: { ...type.title, color: colors.ink, fontVariant: ['tabular-nums'] },
  rowShare: { ...type.small, color: colors.faint, fontVariant: ['tabular-nums'] },
});

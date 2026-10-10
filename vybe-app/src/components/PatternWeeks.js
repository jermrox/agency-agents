import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, space, type } from '../theme';

/**
 * One row per week, showing both halves of a claimed relationship.
 *
 * WHY ROWS AND NOT COLUMNS
 * `TrendColumns` plots one series across twenty-six weeks, and at phone width
 * each column is about eight points — fine for a shape, hopeless as a touch
 * target, which is why that component needs stepper buttons beside it. This
 * plot is answering a different question: not "what did this metric do" but
 * "did these two things move together". Two values and a verdict per week do
 * not fit in an eight-point column, and twelve rows read down a phone with
 * room for a full-size target and the words on each one.
 *
 * WHY NO CHART LIBRARY
 * Same reason as TrendColumns: a bar is a View with a width. Percentage widths
 * need no measurement pass, so there is no onLayout and no native dependency.
 *
 * THE VERDICT IS A WORD
 * "Held" and "Ran the other way" are printed on every row. The bar and the
 * middle marker are a second reading of the same fact, never the only one.
 */

/** A week with too few recorded nights is not evidence, in either direction. */
export const MIN_NIGHTS = 5;

/** Round up to the next 20 so the longest bar never fills its track. */
export function ceilingFor(weeks) {
  const top = Math.max(...weeks.map((w) => w.deepMinutes));
  return Math.max(20, Math.ceil(top / 20) * 20);
}

/**
 * The middle of the weeks that actually carry data. Thin weeks are excluded so
 * a three-night week cannot drag the reference line it is then judged against.
 */
export function middleOf(weeks) {
  const values = weeks
    .filter((w) => w.nights >= MIN_NIGHTS)
    .map((w) => w.deepMinutes)
    .sort((a, b) => a - b);
  if (!values.length) return null;
  const mid = Math.floor(values.length / 2);
  return values.length % 2 ? values[mid] : Math.round((values[mid - 1] + values[mid]) / 2);
}

/**
 * The rule, in one place, applied to one week.
 *
 * 'thin'  — too few nights recorded to say anything
 * 'held'  — a late-heavy week below the middle, or a light week at or above it
 * 'broke' — the opposite of what the claim predicts
 */
export function verdictFor(week, middle, threshold) {
  if (week.nights < MIN_NIGHTS) return 'thin';
  const lateHeavy = week.lateNights >= threshold;
  const below = week.deepMinutes < middle;
  return lateHeavy === below ? 'held' : 'broke';
}

const VERDICT_WORD = {
  held: 'Held',
  broke: 'Ran the other way',
  thin: 'Too few nights',
};

export default function PatternWeeks({
  weeks,
  middle,
  threshold,
  ceiling,
  exceptions,
  selectedId,
  onSelect,
  metricUnit,
}) {
  return (
    <View>
      {weeks.map((week, i) => {
        const verdict = verdictFor(week, middle, threshold);
        const selected = week.id === selectedId;
        const why = exceptions[week.id];
        const label =
          `Week of ${week.label}. ${week.lateNights} late ${week.lateNights === 1 ? 'night' : 'nights'}. ` +
          `Deep sleep ${week.deepMinutes} ${metricUnit}, ` +
          `${week.deepMinutes < middle ? 'below' : 'at or above'} your middle of ${middle}. ` +
          `${VERDICT_WORD[verdict]}.` +
          (why ? ` ${why}` : '');

        return (
          <Pressable
            key={week.id}
            onPress={() => onSelect(week.id)}
            accessibilityRole="button"
            accessibilityState={{ selected }}
            accessibilityLabel={label}
            accessibilityHint="Pins this week to the readout above"
            style={({ pressed }) => [
              styles.row,
              i > 0 && styles.ruled,
              selected && styles.rowSelected,
              pressed && styles.pressed,
            ]}
          >
            <View style={styles.head}>
              <Text style={styles.week}>{week.label}</Text>
              <Text style={styles.verdict}>{VERDICT_WORD[verdict]}</Text>
            </View>

            <View style={styles.readings}>
              <Text style={styles.late}>
                {week.lateNights} late {week.lateNights === 1 ? 'night' : 'nights'}
              </Text>

              {/* The bar track carries one reference: the middle of the weeks
                  with data. It is named in words under the plot, because a
                  hairline on its own is a hairline. */}
              <View style={styles.track}>
                <View
                  style={[
                    styles.bar,
                    { width: `${(week.deepMinutes / ceiling) * 100}%` },
                    verdict === 'thin' && styles.barThin,
                  ]}
                />
                <View
                  aria-hidden
                  style={[styles.middleMark, { left: `${(middle / ceiling) * 100}%` }]}
                />
              </View>

              <Text style={styles.metric}>
                {week.deepMinutes} {metricUnit}
              </Text>
            </View>

            {why ? <Text style={styles.why}>{why}</Text> : null}
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { paddingVertical: space(1.75), gap: space(0.75) },
  ruled: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },
  // Selection tints the row. The readout above names the pinned week, so the
  // tint is never the only signal that it is pinned.
  rowSelected: { backgroundColor: colors.surface },
  pressed: { opacity: 0.6 },

  head: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' },
  week: { ...type.body, color: colors.ink, fontWeight: '600', fontVariant: ['tabular-nums'] },
  verdict: { ...type.small, color: colors.muted, fontWeight: '600' },

  readings: { flexDirection: 'row', alignItems: 'center', gap: space(1.5) },
  late: { ...type.small, color: colors.muted, width: 92, fontVariant: ['tabular-nums'] },

  track: {
    flex: 1,
    height: 10,
    backgroundColor: colors.border,
    borderRadius: 2,
    justifyContent: 'center',
  },
  bar: { height: 10, borderRadius: 2, backgroundColor: colors.ink, minWidth: 2 },
  // A thin week's bar is drawn hollow: the number is real, the week is not
  // evidence, and the row says "Too few nights" beside it either way.
  barThin: { backgroundColor: colors.faint, opacity: 0.4 },
  middleMark: {
    position: 'absolute',
    top: -3,
    bottom: -3,
    width: 1,
    backgroundColor: colors.paper,
  },

  metric: { ...type.small, color: colors.ink, width: 62, textAlign: 'right', fontVariant: ['tabular-nums'] },

  why: { ...type.small, color: colors.muted, lineHeight: 20, paddingTop: space(0.25) },
});

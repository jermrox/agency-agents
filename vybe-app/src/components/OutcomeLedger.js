import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, dimensions, space, type } from '../theme';

/**
 * One row per suggestion: what Vybe predicted, what happened, and the verdict.
 *
 * WHY THIS ONE IS TYPE AND NOT A PLOT
 * The app already has three plots — `TrendColumns` for one series over time,
 * `DayTimeline` for a day on a clock, `PatternWeeks` for two values and a
 * verdict per week. This row is a different shape of fact: a predicted RANGE,
 * a single actual, and whether one fell inside the other. Three numbers and a
 * word read faster set as type than drawn as geometry, and drawing a band and
 * a point here would be a picture of a sentence.
 *
 * THE VERDICT IS DERIVED, NEVER STORED
 * `verdictFor` is the only place the rule lives, and the screen prints the rule
 * next to the tally. A stored verdict can disagree with the numbers beside it;
 * a computed one cannot.
 *
 * NOT TRYING IS A THIRD STATE
 * A suggestion the person never attempted is "No test", not a failure. Scoring
 * untried advice against them would make the tally flattering to Vybe — it
 * would hide weak suggestions behind the person's week.
 */

/** 'called' | 'missed' | 'untested' — the one definition of each. */
export function verdictFor(attempt) {
  if (attempt.adherence === 'none' || attempt.actual === null) return 'untested';
  const { low, high } = attempt.predicted;
  return attempt.actual >= low && attempt.actual <= high ? 'called' : 'missed';
}

/** Rows that actually tested the advice — the denominator of the tally. */
export function testedOf(attempts) {
  return attempts.filter((a) => verdictFor(a) !== 'untested');
}

export const VERDICT_WORD = {
  called: 'Called it',
  missed: 'Missed',
  untested: 'No test',
};

const ADHERENCE_WORD = {
  full: 'Followed',
  partial: 'Followed in part',
  none: 'Not tried',
};

export default function OutcomeLedger({ attempts, selectedId, onSelect }) {
  return (
    <View>
      {attempts.map((a, i) => {
        const verdict = verdictFor(a);
        const selected = a.id === selectedId;
        const d = dimensions[a.dimension];
        const p = a.predicted;

        // One spoken sentence per row. A screen reader should get the whole
        // fact without having to assemble it from four separate labels.
        const label =
          `${a.date}. ${a.suggestion} ${ADHERENCE_WORD[a.adherence]}. ` +
          `Vybe predicted ${p.metric} between ${p.low} and ${p.high} ${p.unit} ${p.window}. ` +
          (a.actual === null
            ? 'No reading, because it was not tried.'
            : `Actual, ${a.actual} ${p.unit}.`) +
          ` ${VERDICT_WORD[verdict]}.`;

        return (
          <Pressable
            key={a.id}
            onPress={() => onSelect(a.id)}
            accessibilityRole="button"
            accessibilityState={{ selected }}
            accessibilityLabel={label}
            accessibilityHint="Pins this suggestion to the readout above"
            style={({ pressed }) => [
              styles.row,
              i > 0 && styles.ruled,
              selected && styles.rowSelected,
              pressed && styles.pressed,
            ]}
          >
            <View style={styles.head}>
              <View style={styles.headLeft}>
                <Text style={styles.date}>{a.date}</Text>
                {d ? (
                  <View style={styles.tag}>
                    <View aria-hidden style={[styles.tagDot, { backgroundColor: d.hue }]} />
                    <Text style={styles.tagLabel}>{d.label}</Text>
                  </View>
                ) : null}
              </View>
              <Text style={styles.verdict}>{VERDICT_WORD[verdict]}</Text>
            </View>

            <Text style={styles.suggestion}>{a.suggestion}</Text>

            {/* Predicted and actual on one line, in the same units, with the
                adherence word beside them. The comparison is the whole point,
                so the two numbers sit next to each other rather than in
                separate columns the eye has to join up. */}
            <Text style={styles.numbers}>
              <Text style={styles.numLabel}>{p.metric}: </Text>
              said {p.low}–{p.high} {p.unit} {p.window}
              {a.actual === null ? ' · no reading' : ` · was ${a.actual} ${p.unit}`}
            </Text>

            <Text style={styles.adherence}>{ADHERENCE_WORD[a.adherence]} · {a.note}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { paddingVertical: space(2), gap: space(0.5) },
  ruled: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },
  // Selection tints the row; the readout above names the pinned suggestion, so
  // the tint is never the only signal.
  rowSelected: { backgroundColor: colors.surface },
  pressed: { opacity: 0.6 },

  head: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline', gap: space(1) },
  headLeft: { flexDirection: 'row', alignItems: 'center', gap: space(1.5) },
  date: { ...type.small, color: colors.faint, fontVariant: ['tabular-nums'] },
  tag: { flexDirection: 'row', alignItems: 'center', gap: space(0.5) },
  tagDot: { width: 7, height: 7, borderRadius: 4 },
  tagLabel: { ...type.small, color: colors.muted },
  verdict: { ...type.small, color: colors.ink, fontWeight: '700' },

  suggestion: { ...type.body, color: colors.ink, fontWeight: '600' },
  numbers: { ...type.small, color: colors.muted, lineHeight: 20, fontVariant: ['tabular-nums'] },
  numLabel: { color: colors.ink, fontWeight: '600' },
  adherence: { ...type.small, color: colors.faint, lineHeight: 20 },
});

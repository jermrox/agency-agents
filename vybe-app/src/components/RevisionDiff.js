import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors, space, type } from '../theme';

/**
 * What a correction moved — the basis, annotated.
 *
 * Every other screen in this app shows evidence as a flat hairline list.
 * This one shows the SAME list twice over: once as Vybe's reasoning, and
 * again as what survived being argued with. So each row gains one thing, a
 * verdict, and loses nothing — a reader who has seen the Ask screen can read
 * this list without learning a new shape.
 *
 * NO LEFT-BORDER ACCENT, AND NO COLOUR ALONE
 * The verdict is a word in its own gutter column, and an overturned line is
 * also struck through. A reader who cannot separate the hues, or who is
 * hearing this read aloud, gets the same three states.
 *
 * `source` is printed on every row whether or not a correction touched it,
 * because the argument only works if the reader can see that the guess was
 * labelled a guess BEFORE anybody disagreed with it.
 */

export const VERDICT_WORD = {
  held: 'Held',
  weakened: 'Counts for less',
  overturned: 'Overturned',
};

const SOURCE_WORD = { measured: 'Measured', inferred: 'Inferred by Vybe' };

export function effectFor(correction, basisId) {
  if (!correction) return null;
  const hit = correction.effects.find((e) => e.basisId === basisId);
  return hit ? hit.verdict : 'held';
}

/** Everything the correction did not leave alone. */
export function movedOf(correction) {
  if (!correction) return [];
  return correction.effects.filter((e) => e.verdict !== 'held');
}

/**
 * Of the parts that moved, how many were the ones Vybe had already marked as
 * guesses. This is the screen's claim, so it is counted rather than written.
 */
export function inferredMovedOf(correction, basis) {
  return movedOf(correction).filter((e) => {
    const item = basis.find((b) => b.id === e.basisId);
    return item && item.source === 'inferred';
  });
}

/**
 * Which of the three things a correction did. Derived, never stored: a label
 * typed into the data could say "changes the answer" above an answer that is
 * word-for-word the one it replaced.
 */
export function kindOf(correction, original) {
  const moved = movedOf(correction);
  const answerChanged = correction.revised.answer !== original.answer;
  if (moved.length > 0 && answerChanged) return 'changes';
  if (correction.closes.length > 0 || correction.revised.confidence !== original.confidence) {
    return 'narrows';
  }
  return 'recorded';
}

export const KIND_WORD = {
  changes: 'This changed the answer',
  narrows: 'This did not change the answer. It closed a blind spot.',
  recorded: 'Recorded. This cannot change the reading.',
};

export default function RevisionDiff({ basis, correction, added }) {
  return (
    <View>
      {basis.map((item, i) => {
        const verdict = effectFor(correction, item.id);
        const gone = verdict === 'overturned';
        return (
          <View
            key={item.id}
            style={[styles.row, i > 0 && styles.ruled]}
            accessible
            accessibilityRole="text"
            accessibilityLabel={
              `${item.label}. ${SOURCE_WORD[item.source]}. `
              + `${correction ? VERDICT_WORD[verdict] : ''}. ${item.detail}`
            }
          >
            <View style={styles.gutter}>
              <Text style={[styles.verdict, gone && styles.verdictGone]}>
                {correction ? VERDICT_WORD[verdict] : SOURCE_WORD[item.source]}
              </Text>
            </View>
            <View style={styles.body}>
              <Text style={[styles.label, gone && styles.struck]}>{item.label}</Text>
              <Text style={styles.source}>{SOURCE_WORD[item.source]}</Text>
              <Text style={styles.detail}>{item.detail}</Text>
            </View>
          </View>
        );
      })}

      {/* What the correction put in. Marked as told-to-Vybe rather than
          measured, because that is exactly what it is. */}
      {(added || []).map((item) => (
        <View
          key={item.label}
          style={[styles.row, styles.ruled]}
          accessible
          accessibilityRole="text"
          accessibilityLabel={`Added. ${item.label}. ${item.detail}`}
        >
          <View style={styles.gutter}>
            <Text style={styles.verdictAdded}>Added</Text>
          </View>
          <View style={styles.body}>
            <Text style={styles.label}>{item.label}</Text>
            <Text style={styles.source}>You told Vybe</Text>
            <Text style={styles.detail}>{item.detail}</Text>
          </View>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'flex-start', paddingVertical: space(2), gap: space(2) },
  ruled: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },

  // A fixed gutter so the verdicts read down one column rather than drifting
  // with the length of each label.
  gutter: { width: space(15), paddingTop: 2 },
  verdict: { ...type.small, color: colors.muted, fontWeight: '700' },
  verdictGone: { color: colors.ink },
  verdictAdded: { ...type.small, color: colors.brand, fontWeight: '700' },

  body: { flex: 1, gap: 3 },
  label: { ...type.body, color: colors.ink, fontWeight: '600' },
  struck: { textDecorationLine: 'line-through', color: colors.muted },
  source: { ...type.small, color: colors.faint, fontWeight: '600' },
  detail: { ...type.small, color: colors.muted, lineHeight: 20 },
});

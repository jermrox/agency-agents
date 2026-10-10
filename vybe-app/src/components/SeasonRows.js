import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, space, type } from '../theme';

/**
 * Twelve calendar months, each holding whichever years Vybe has actually seen.
 *
 * The app already draws a value per week twice over — `TrendColumns` as
 * columns, `PatternWeeks` as bars against a line. This is the third question
 * and it needs a third form: not how a number moved, but whether a month came
 * out the same way the last time it happened. So the row is a PAIR, and the
 * months Vybe has seen only once are rows too, with the half that is missing
 * drawn as missing rather than left out of the list.
 *
 * DROPPING THEM WOULD BE THE WHOLE BUG. A list of only the comparable months
 * reads as a complete year and is not one, and the months that go missing are
 * exactly the winter ones a person is most worried about.
 */

export const MONTH_NAME = [
  '', 'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

export const VERDICT_WORD = {
  repeated: 'Same again',
  changed: 'Different',
  once: 'Seen once',
};

/** One entry per calendar month, carrying whichever years exist. */
export function pairsOf(readings) {
  return MONTH_NAME.slice(1).map((name, i) => {
    const month = i + 1;
    const years = readings
      .filter((r) => r.month === month)
      .sort((a, b) => a.year - b.year);
    return { month, name, years };
  }).filter((p) => p.years.length > 0);
}

/**
 * Derived, never stored. Two readings within the margin repeated; wider is a
 * change; one reading cannot be either. The margin exists so that a one-minute
 * difference cannot decide an answer.
 */
export function verdictFor(pair, sameWithin) {
  if (pair.years.length < 2) return 'once';
  const first = pair.years[0].value;
  const last = pair.years[pair.years.length - 1].value;
  return Math.abs(last - first) <= sameWithin ? 'repeated' : 'changed';
}

export function deltaFor(pair) {
  if (pair.years.length < 2) return null;
  return pair.years[pair.years.length - 1].value - pair.years[0].value;
}

/**
 * The months Vybe has seen only once, lowest value first. The screen uses this
 * to check — rather than assert — whether the thinnest evidence and the worst
 * numbers are the same months.
 */
export function seenOnceLowestFirst(readings) {
  return pairsOf(readings)
    .filter((p) => p.years.length === 1)
    .sort((a, b) => a.years[0].value - b.years[0].value);
}

export default function SeasonRows({
  readings,
  sameWithin,
  unit,
  exceptions,
  selectedMonth,
  onSelect,
}) {
  const pairs = pairsOf(readings);

  return (
    <View>
      {pairs.map((p, i) => {
        const verdict = verdictFor(p, sameWithin);
        const delta = deltaFor(p);
        const open = p.month === selectedMonth;
        const note = exceptions ? exceptions[p.month] : null;

        return (
          <Pressable
            key={p.month}
            onPress={() => onSelect && onSelect(open ? null : p.month)}
            accessibilityRole="button"
            accessibilityState={{ expanded: open }}
            accessibilityLabel={
              `${p.name}. `
              + p.years.map((y) => `${y.year}, ${y.value} ${unit}`).join('. ')
              + `. ${VERDICT_WORD[verdict]}`
              + (delta !== null
                ? `, ${delta === 0 ? 'no change' : `${delta > 0 ? 'up' : 'down'} ${Math.abs(delta)} ${unit}`}`
                : ', no second year to compare')
              + '.'
            }
            accessibilityHint={
              note
                ? open ? 'Hides what Vybe knows about this month' : 'Shows what Vybe knows about this month'
                : 'Shows this month in the readout above'
            }
            style={({ pressed }) => [styles.row, i > 0 && styles.ruled, pressed && styles.pressed]}
          >
            <View style={styles.top}>
              <Text style={styles.month}>{p.name}</Text>
              <View style={styles.years}>
                {/* Two slots, always. A month with one year shows the gap
                    rather than closing it up. */}
                {p.years.length === 1 ? (
                  <Text style={styles.missing}>—</Text>
                ) : (
                  <Text style={styles.yearValue}>
                    {p.years[0].value}
                  </Text>
                )}
                <Text style={styles.yearValue}>
                  {p.years[p.years.length - 1].value}
                </Text>
              </View>
              <Text
                style={[
                  styles.verdict,
                  verdict === 'changed' && styles.verdictChanged,
                  verdict === 'once' && styles.verdictOnce,
                ]}
              >
                {VERDICT_WORD[verdict]}
              </Text>
            </View>

            <Text style={styles.detail}>
              {p.years.length === 1
                ? `${p.years[0].year} only. Nothing to compare it with.`
                : `${p.years[0].year} to ${p.years[p.years.length - 1].year}: `
                  + (delta === 0
                    ? 'no change'
                    : `${delta > 0 ? 'up' : 'down'} ${Math.abs(delta)} ${unit}`)}
              {p.years.length === 1 ? '' : ` · ${p.years.map((y) => `${y.nights} nights`).join(', ')}`}
            </Text>

            {open && note ? <Text style={styles.note}>{note}</Text> : null}
            {open && !note && verdict === 'changed' ? (
              <Text style={styles.note}>
                Vybe does not know why this month differed. It is left here
                rather than explained away.
              </Text>
            ) : null}
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { paddingVertical: space(1.75), gap: space(0.5) },
  ruled: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },
  pressed: { opacity: 0.6 },

  top: { flexDirection: 'row', alignItems: 'baseline', gap: space(1.5) },
  month: { ...type.body, color: colors.ink, fontWeight: '600', flex: 1 },

  // Two fixed slots so the years read down two columns, and a month with only
  // one year leaves a visible hole in the first.
  years: { flexDirection: 'row', gap: space(2) },
  yearValue: {
    ...type.title,
    color: colors.ink,
    fontVariant: ['tabular-nums'],
    width: space(5),
    textAlign: 'right',
  },
  missing: {
    ...type.title,
    color: colors.faint,
    width: space(5),
    textAlign: 'right',
  },

  // The verdict is a word in its own column. Nothing here is carried by hue.
  verdict: {
    ...type.small,
    color: colors.muted,
    fontWeight: '700',
    width: space(11),
    textAlign: 'right',
  },
  verdictChanged: { color: colors.ink },
  verdictOnce: { color: colors.faint },

  detail: { ...type.small, color: colors.muted, lineHeight: 20 },
  note: { ...type.small, color: colors.ink, lineHeight: 21, paddingTop: space(0.5) },
});

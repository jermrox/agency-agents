import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, space, type } from '../theme';

/**
 * A column plot drawn with Views sized by value.
 *
 * WHY NO CHART LIBRARY
 * Every React Native charting package brings react-native-svg, and most bring
 * reanimated and gesture-handler behind it. That is three native dependencies
 * and an Expo prebuild to draw twenty-six rectangles. A View with a computed
 * height is a rectangle. The whole plot below is flexbox and arithmetic, so it
 * drops into a blank Expo app and runs.
 *
 * WHY THE COLUMNS ARE PRESSABLE RATHER THAN A STATIC IMAGE OF A TREND
 * A trend line you cannot interrogate is decoration. Tapping a week puts its
 * number and its status in the readout above, which is also the only place
 * those facts are stated — the plot itself is never the sole carrier of
 * meaning, because a shape is not readable by a screen reader and a hue is not
 * readable by everyone.
 *
 * ACCESSIBILITY, HONESTLY
 * At twenty-six weeks a column is about eight points wide, which is below any
 * sane touch target. That is inherent to a dense plot, so the columns are not
 * the only way through: the screen pairs this with full-size Earlier/Later
 * stepper buttons, and every column still carries a complete spoken label so
 * swipe navigation reaches each one.
 */

const CHART_HEIGHT = 176;

/** Round up to the next 20 so the tallest column never touches the ceiling. */
export function niceCeiling(value) {
  return Math.max(20, Math.ceil(value / 20) * 20);
}

/** The word for where a week sits relative to the person's own usual range. */
export function rangeStatus(minutes, range) {
  if (minutes > range.high) return 'Above your usual range';
  if (minutes < range.low) return 'Below your usual range';
  return 'Within your usual range';
}

export default function TrendColumns({ weeks, range, selectedStart, onSelect, unit, hue }) {
  const ceiling = niceCeiling(Math.max(...weeks.map((w) => w.minutes)));
  const pct = (value) => `${Math.min(100, (value / ceiling) * 100)}%`;

  // One spoken summary for the plot as a whole, so a screen reader user gets
  // the shape of it without stepping through twenty-six columns first.
  const first = weeks[0];
  const last = weeks[weeks.length - 1];
  const chartSummary =
    `Column chart, ${weeks.length} weeks, ${first.label} to ${last.label}. ` +
    `Ranges from ${Math.min(...weeks.map((w) => w.minutes))} to ` +
    `${Math.max(...weeks.map((w) => w.minutes))} ${unit} per week.`;

  return (
    <View>
      <View style={styles.plot} accessibilityRole="image" accessibilityLabel={chartSummary}>
        {/* The person's own usual band, drawn behind the columns. It is
            explained in words beneath the plot — on its own it is a grey
            rectangle, which tells nobody anything. */}
        <View
          style={[
            styles.band,
            { bottom: pct(range.low), height: pct(range.high - range.low) },
          ]}
        />

        <View style={styles.columns}>
          {weeks.map((week) => {
            const selected = week.start === selectedStart;
            const status = rangeStatus(week.minutes, range);
            return (
              <Pressable
                key={week.start}
                onPress={() => onSelect(week.start)}
                accessibilityRole="button"
                accessibilityState={{ selected }}
                accessibilityLabel={`Week of ${week.label}. ${week.minutes} ${unit}. ${status}.`}
                accessibilityHint="Shows this week in the readout above the chart"
                style={styles.column}
              >
                <View
                  style={[
                    styles.bar,
                    { height: pct(week.minutes), backgroundColor: hue },
                    selected && styles.barSelected,
                  ]}
                />
              </Pressable>
            );
          })}
        </View>
      </View>

      {/* Three labels, not twenty-six. A tick under every column at phone
          width is a grey smear; the readout names the selected week exactly. */}
      <View style={styles.axis}>
        <Text style={styles.axisLabel}>{first.label}</Text>
        <Text style={styles.axisLabel}>{weeks[Math.floor(weeks.length / 2)].label}</Text>
        <Text style={styles.axisLabel}>{last.label}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  plot: { height: CHART_HEIGHT, justifyContent: 'flex-end' },

  band: {
    position: 'absolute',
    left: 0,
    right: 0,
    backgroundColor: colors.border,
    opacity: 0.45,
    borderRadius: 2,
  },

  columns: { flexDirection: 'row', alignItems: 'flex-end', height: '100%', gap: 2 },

  // The column is full height so the whole strip is tappable, not just the
  // painted part — a 58-minute week is otherwise a sliver you cannot hit.
  column: { flex: 1, height: '100%', justifyContent: 'flex-end' },

  // The fill colour arrives as the `hue` prop, so this plot belongs to whichever
  // dimension renders it rather than hard-coding one. theme.js stays the only
  // place a hue is written down.
  bar: { borderRadius: 2, minHeight: 2 },
  // Selection is the one dark column. It is never the only signal: the readout
  // above the chart names the selected week and states its status in words.
  barSelected: { backgroundColor: colors.ink },

  axis: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingTop: space(0.75),
  },
  axisLabel: { ...type.small, color: colors.faint, fontVariant: ['tabular-nums'] },
});

import React, { useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { colors, dimensions, radius, space, type } from '../theme';
import { moveTrend, isSample } from '../moveTrendSampleData';
import TrendColumns, { rangeStatus } from '../components/TrendColumns';

const D = dimensions.move;

/** Ranges the selector offers, in weeks. Each one exists in the data. */
const RANGES = [6, 12, 26];

/** 201 -> "3h 21m". Hours are how people actually hold a weekly figure. */
function asDuration(minutes) {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h ? `${h}h ${m}m` : `${m}m`;
}

function mean(values) {
  return Math.round(values.reduce((a, b) => a + b, 0) / values.length);
}

/**
 * Move — how one thing changed over six months.
 *
 * Reading order, top to bottom:
 *   Verdict -> the series -> then vs now -> what happened -> what follows
 * The verdict is first for the same reason it is first on the Restore screen:
 * a chart is not an answer, and a person opening a trend screen wants to know
 * whether the line is good news before they are asked to read it.
 *
 * Deliberately NOT a stack of identical cards. Five different treatments so the
 * hierarchy reads before a word does: the verdict is oversized type on bare
 * paper, the series is a full-width plot, the comparison is two proportional
 * bars lying on their side, the events are a numbered timeline on a rule, and
 * the closing note is the one tinted panel. The plot is the only thing on the
 * screen shaped like a chart, so the eye lands there without being told to.
 */
export default function MoveTrendScreen({ onBack }) {
  const [weeksShown, setWeeksShown] = useState(12);
  const [selectedStart, setSelectedStart] = useState(
    moveTrend.weeks[moveTrend.weeks.length - 1].start,
  );

  const visible = useMemo(
    () => moveTrend.weeks.slice(-weeksShown),
    [weeksShown],
  );

  const selectedIndex = visible.findIndex((w) => w.start === selectedStart);
  // Shrinking the range can strand the selection outside the plot. Falling back
  // to the most recent visible week keeps the readout and the chart agreeing.
  const selected = selectedIndex === -1 ? visible[visible.length - 1] : visible[selectedIndex];
  const cursor = selectedIndex === -1 ? visible.length - 1 : selectedIndex;

  /**
   * The then-and-now comparison reads from the FULL series, not the visible
   * slice. "The last four weeks against the four before" is a fact about the
   * person, not about how far the chart happens to be zoomed out — and at the
   * six-week range there would not be eight weeks to compare.
   */
  const all = moveTrend.weeks;
  const recent = all.slice(-4);
  const prior = all.slice(-8, -4);
  const recentAvg = mean(recent.map((w) => w.minutes));
  const priorAvg = mean(prior.map((w) => w.minutes));
  const changePct = Math.round(((recentAvg - priorAvg) / priorAvg) * 100);
  const compareCeiling = Math.max(recentAvg, priorAvg);
  // The direction is a word first. The bar lengths agree with it; they do not
  // carry it on their own.
  const changeWord = changePct > 0 ? 'up' : changePct < 0 ? 'down' : 'level';

  const step = (delta) => {
    const next = cursor + delta;
    if (next >= 0 && next < visible.length) setSelectedStart(visible[next].start);
  };

  const selectedStatus = rangeStatus(selected.minutes, moveTrend.usualRange);

  return (
    <ScrollView
      style={styles.page}
      contentContainerStyle={styles.content}
      accessibilityLabel="Move trend over time"
    >
      {isSample ? (
        <View style={styles.sampleBar}>
          <Text style={styles.sampleText}>
            Sample data — these are not your readings.
          </Text>
        </View>
      ) : null}

      <View style={styles.header}>
        <Pressable
          onPress={onBack}
          accessibilityRole="button"
          accessibilityLabel="Back to today"
          accessibilityHint="Returns to the home screen"
          style={({ pressed }) => [styles.back, pressed && styles.pressed]}
        >
          <Text style={styles.backText}>Today</Text>
        </Pressable>
        <Text style={[styles.eyebrow, { color: D.hue }]}>MOVE · SIX MONTHS</Text>
        <Text style={styles.title}>{moveTrend.metricLabel}</Text>
      </View>

      {/* THE VERDICT — oversized type on bare paper, under a hairline. No
          container, because the thing that needs no box is the thing that
          matters most. */}
      <View style={styles.verdictBlock}>
        <Text style={styles.verdict}>{moveTrend.verdict}</Text>
        <Text style={styles.verdictCaveat}>{moveTrend.verdictCaveat}</Text>
      </View>

      {/* THE SERIES */}
      <View style={styles.section}>
        <View
          style={styles.selector}
          accessibilityRole="radiogroup"
          accessibilityLabel="Length of history shown"
        >
          {RANGES.map((n) => {
            const active = n === weeksShown;
            return (
              <Pressable
                key={n}
                onPress={() => setWeeksShown(n)}
                accessibilityRole="radio"
                accessibilityState={{ checked: active }}
                accessibilityLabel={`${n} weeks`}
                accessibilityHint={`Redraws the chart with the last ${n} weeks`}
                style={({ pressed }) => [
                  styles.selectorItem,
                  active && styles.selectorItemActive,
                  pressed && styles.pressed,
                ]}
              >
                <Text style={[styles.selectorText, active && styles.selectorTextActive]}>
                  {n} weeks
                </Text>
              </Pressable>
            );
          })}
        </View>

        {/* THE READOUT — the one place every fact about the selected week is
            stated in words. The chart never has to be seen for this to read. */}
        <View style={styles.readout}>
          <View style={styles.readoutText}>
            <Text style={styles.readoutWeek}>Week of {selected.label}</Text>
            <Text style={styles.readoutValue}>
              {selected.minutes} {moveTrend.metricUnit}
              <Text style={styles.readoutDuration}>  ·  {asDuration(selected.minutes)}</Text>
            </Text>
            <Text style={styles.readoutStatus}>{selectedStatus}</Text>
          </View>

          {/* Full-size stepper buttons. The columns themselves are eight points
              wide at the 26-week range, which no one should be asked to hit. */}
          <View style={styles.steppers}>
            <Pressable
              onPress={() => step(-1)}
              disabled={cursor === 0}
              accessibilityRole="button"
              accessibilityState={{ disabled: cursor === 0 }}
              accessibilityLabel="Earlier week"
              accessibilityHint="Moves the readout one week back"
              style={({ pressed }) => [
                styles.stepper,
                cursor === 0 && styles.stepperOff,
                pressed && styles.pressed,
              ]}
            >
              <Text style={styles.stepperText}>Earlier</Text>
            </Pressable>
            <Pressable
              onPress={() => step(1)}
              disabled={cursor === visible.length - 1}
              accessibilityRole="button"
              accessibilityState={{ disabled: cursor === visible.length - 1 }}
              accessibilityLabel="Later week"
              accessibilityHint="Moves the readout one week forward"
              style={({ pressed }) => [
                styles.stepper,
                cursor === visible.length - 1 && styles.stepperOff,
                pressed && styles.pressed,
              ]}
            >
              <Text style={styles.stepperText}>Later</Text>
            </Pressable>
          </View>
        </View>

        <TrendColumns
          weeks={visible}
          range={moveTrend.usualRange}
          selectedStart={selected.start}
          onSelect={setSelectedStart}
          unit={moveTrend.metricUnit}
          hue={D.hue}
        />

        <Text style={styles.legend}>
          The shaded band is {moveTrend.usualRange.basis} —{' '}
          {moveTrend.usualRange.low} to {moveTrend.usualRange.high}{' '}
          {moveTrend.metricUnit} a week. It is your own range, not a comparison
          with anybody else.
        </Text>
        <Text style={styles.legendFine}>{moveTrend.metricDefinition}</Text>
      </View>

      {/* THEN AND NOW — two proportional bars lying on their side, so the
          comparison does not look like the series it is drawn from. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>The last month against the one before</Text>
        <View style={styles.compare}>
          {[
            { key: 'prior', label: 'Four weeks before', value: priorAvg, tone: colors.border },
            { key: 'recent', label: 'Last four weeks', value: recentAvg, tone: D.hue },
          ].map((row) => (
            <View
              key={row.key}
              style={styles.compareRow}
              accessible
              accessibilityRole="text"
              accessibilityLabel={`${row.label}: ${row.value} ${moveTrend.metricUnit} a week on average.`}
            >
              <Text style={styles.compareLabel}>{row.label}</Text>
              <View style={styles.compareTrack}>
                <View
                  style={[
                    styles.compareFill,
                    { width: `${(row.value / compareCeiling) * 100}%`, backgroundColor: row.tone },
                  ]}
                />
              </View>
              <Text style={styles.compareValue}>{row.value}</Text>
            </View>
          ))}
        </View>
        <Text style={styles.compareSummary}>
          An average week is {changeWord} {Math.abs(changePct)} per cent —{' '}
          {Math.abs(recentAvg - priorAvg)} {moveTrend.metricUnit} more than a
          month ago.
        </Text>
      </View>

      {/* WHAT HAPPENED — a numbered timeline on a rule. These are events in
          sequence, so they are drawn as a sequence rather than as three boxes. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>What moved the line</Text>
        <View style={styles.timeline}>
          {moveTrend.annotations.map((a, i) => (
            <Pressable
              key={a.id}
              onPress={() => {
                // Jumping the readout to the annotated week is the point of the
                // timeline: it connects a sentence to a column.
                const inView = visible.some((w) => w.start === a.weekStart);
                if (!inView) setWeeksShown(26);
                setSelectedStart(a.weekStart);
              }}
              accessibilityRole="button"
              accessibilityLabel={`${a.weekLabel}. ${a.text} ${a.source}.`}
              accessibilityHint="Selects this week in the chart above"
              style={({ pressed }) => [styles.event, pressed && styles.pressed]}
            >
              <View style={styles.eventMarker}>
                <Text style={[styles.eventNumber, { color: D.hue }]}>{i + 1}</Text>
                {i < moveTrend.annotations.length - 1 ? <View style={styles.eventRule} /> : null}
              </View>
              <View style={styles.eventBody}>
                <Text style={styles.eventWeek}>{a.weekLabel}</Text>
                <Text style={styles.eventText}>{a.text}</Text>
                <Text style={styles.eventSource}>{a.source}</Text>
              </View>
            </Pressable>
          ))}
        </View>
      </View>

      {/* WHAT FOLLOWS — the one tinted panel on the screen. A trend nobody acts
          on is a screensaver. */}
      <View style={[styles.closing, { backgroundColor: D.tint }]}>
        <Text style={[styles.closingLabel, { color: D.hue }]}>WHAT THIS CHANGES</Text>
        <Text style={styles.closingText}>{moveTrend.whatThisChanges.text}</Text>
        <Text style={styles.closingWhy}>{moveTrend.whatThisChanges.why}</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: colors.paper },
  content: { padding: space(3), paddingBottom: space(8), gap: space(4) },

  sampleBar: {
    backgroundColor: colors.brandSoft,
    borderRadius: radius.pill,
    paddingVertical: space(1),
    paddingHorizontal: space(2),
    alignSelf: 'flex-start',
  },
  sampleText: { ...type.small, color: colors.deep, fontWeight: '600' },

  header: { gap: space(0.5) },
  back: { alignSelf: 'flex-start', paddingVertical: space(0.5), paddingRight: space(2) },
  backText: { ...type.small, color: colors.brand, fontWeight: '600' },
  pressed: { opacity: 0.6 },
  eyebrow: { ...type.label, marginTop: space(1) },
  title: { ...type.display, color: colors.ink },

  verdictBlock: {
    gap: space(1.5),
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
    paddingBottom: space(3),
  },
  verdict: { fontSize: 24, lineHeight: 33, color: colors.ink, fontWeight: '500' },
  verdictCaveat: { ...type.small, color: colors.muted },

  section: { gap: space(1.5) },
  sectionTitle: { ...type.title, color: colors.ink },

  selector: { flexDirection: 'row', gap: space(1) },
  selectorItem: {
    paddingVertical: space(0.75),
    paddingHorizontal: space(1.75),
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.border,
  },
  selectorItemActive: { backgroundColor: colors.ink, borderColor: colors.ink },
  selectorText: { ...type.small, color: colors.muted, fontWeight: '600' },
  selectorTextActive: { color: colors.paper },

  readout: { flexDirection: 'row', alignItems: 'flex-end', gap: space(2) },
  readoutText: { flex: 1, gap: 2 },
  readoutWeek: { ...type.label, color: colors.faint },
  readoutValue: { ...type.display, color: colors.ink, fontVariant: ['tabular-nums'] },
  readoutDuration: { ...type.small, color: colors.faint, fontWeight: '400' },
  readoutStatus: { ...type.small, color: colors.muted },

  steppers: { flexDirection: 'row', gap: space(1) },
  stepper: {
    minWidth: 44,
    minHeight: 44,
    justifyContent: 'center',
    paddingHorizontal: space(1.5),
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.border,
  },
  stepperOff: { opacity: 0.35 },
  stepperText: { ...type.small, color: colors.ink, fontWeight: '600' },

  legend: { ...type.small, color: colors.muted, marginTop: space(1) },
  legendFine: { ...type.small, color: colors.faint },

  compare: { gap: space(1.25) },
  compareRow: { flexDirection: 'row', alignItems: 'center', gap: space(1.5) },
  compareLabel: { ...type.small, color: colors.muted, width: 120 },
  compareTrack: { flex: 1, height: 14, backgroundColor: colors.surface, borderRadius: 3 },
  compareFill: { height: 14, borderRadius: 3 },
  compareValue: {
    ...type.body,
    color: colors.ink,
    fontWeight: '600',
    width: 40,
    textAlign: 'right',
    fontVariant: ['tabular-nums'],
  },
  compareSummary: { ...type.body, color: colors.ink, marginTop: space(0.5) },

  timeline: { gap: 0 },
  event: { flexDirection: 'row', gap: space(2) },
  eventMarker: { alignItems: 'center', width: 22 },
  eventNumber: { ...type.label, fontSize: 13, lineHeight: 18 },
  eventRule: { flex: 1, width: StyleSheet.hairlineWidth, backgroundColor: colors.border },
  eventBody: { flex: 1, gap: 2, paddingBottom: space(2.5) },
  eventWeek: { ...type.body, color: colors.ink, fontWeight: '600' },
  eventText: { ...type.body, color: colors.ink },
  eventSource: { ...type.small, color: colors.faint },

  closing: { borderRadius: radius.card, padding: space(3), gap: space(1) },
  closingLabel: type.label,
  closingText: { fontSize: 20, lineHeight: 28, color: colors.ink, fontWeight: '500' },
  closingWhy: { ...type.small, color: colors.muted, lineHeight: 21 },
});

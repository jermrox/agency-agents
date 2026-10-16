import React, { useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { colors, dimensions, radius, space, type } from '../theme';
import { boundary, isSample, metrics, order } from '../vitalsDriftSampleData';

const D = dimensions.vitals;

/**
 * Vitals drift — how a slow number moved over six months.
 *
 * Reading order, top to bottom:
 *   Verdict -> the bands, month by month -> then against now -> what moved
 *   them -> what a drift is not
 * The verdict is first for the same reason it is first on Move: a chart is
 * not an answer, and the person wants to know whether the line is news before
 * being asked to read it.
 *
 * WHY THIS IS NOT ANOTHER COLUMN CHART
 * The Vitals screen reads one morning against a 30-day band. The history of a
 * vital is not the history of mornings, which are noise, but of that band,
 * which drifts. So this screen draws the band itself, six times, on one shared
 * scale, so the eye can see a band slide sideways. Move's columns compare
 * weeks to a fixed range. Here the range is the thing that moves. Same tokens,
 * different form, because the claim is different.
 *
 * WHY THE SCALE IS SHARED
 * BaselineStrip normalises each vital to its own band, which is right for
 * "where is today". It would hide drift completely: every month would look the
 * same. Here all six months sit on one axis from the lowest edge to the
 * highest, so a band that moved two beats is visibly two beats to the right.
 *
 * Treatments, so the hierarchy reads before the words do: the verdict is
 * oversized type under a hairline, the metric choice is a pair of pills, the
 * bands are the one chart-like thing, the readout and the then-and-now are
 * sentences, the events are a ruled list, and the restraint is the single
 * outlined block. No tinted panel and no dark block: a history has no action,
 * and pretending otherwise is how a trend screen becomes a nag.
 */

export default function VitalsDriftScreen({ onBack, onOpenData }) {
  const [metricId, setMetricId] = useState(order[0]);
  const metric = metrics[metricId];
  const [selectedId, setSelectedId] = useState(metric.months[metric.months.length - 1].id);

  // Switching metric must not strand the selection on a month id that still
  // exists but reads differently; falling back to the latest month keeps the
  // readout and the drawing agreeing.
  const selected = metric.months.find((m) => m.id === selectedId) || metric.months[metric.months.length - 1];

  // One axis for all six months: lowest band edge to highest, with a little
  // room, so a band that moved is visibly displaced rather than re-centred.
  const axis = useMemo(() => {
    const lows = metric.months.map((m) => m.low);
    const highs = metric.months.map((m) => m.high);
    const span = Math.max(...highs) - Math.min(...lows) || 1;
    const pad = span * 0.12;
    return { min: Math.min(...lows) - pad, max: Math.max(...highs) + pad };
  }, [metric]);

  const pct = (v) => `${((v - axis.min) / (axis.max - axis.min)) * 100}%`;
  const fmt = (v) => (metric.decimals ? v.toFixed(metric.decimals) : String(Math.round(v)));

  // Then and now are derived, never typed. First month against last.
  const first = metric.months[0];
  const last = metric.months[metric.months.length - 1];
  const moved = Number((last.median - first.median).toFixed(metric.decimals));
  const movedWord = moved > 0 ? 'up' : moved < 0 ? 'down' : 'level';
  const widthFirst = first.high - first.low;
  const widthLast = last.high - last.low;
  const widthWord = widthLast > widthFirst ? 'wider' : widthLast < widthFirst ? 'narrower' : 'the same width';

  const note = metric.annotations.find((a) => a.monthId === selected.id);

  function chooseMetric(id) {
    setMetricId(id);
    setSelectedId(metrics[id].months[metrics[id].months.length - 1].id);
  }

  return (
    <ScrollView
      style={styles.page}
      contentContainerStyle={styles.content}
      accessibilityLabel="Vitals over six months"
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
          accessibilityLabel="Back to vitals"
          accessibilityHint="Returns to this morning's vitals"
          style={({ pressed }) => [styles.back, pressed && styles.pressed]}
        >
          <Text style={styles.backText}>Vitals</Text>
        </Pressable>
        <Text style={[styles.eyebrow, { color: D.hue }]}>VITALS · SIX MONTHS</Text>
        <Text style={styles.title}>{metric.label}</Text>
      </View>

      {/* THE VERDICT — oversized type on bare paper, under a hairline. */}
      <View style={styles.verdictBlock}>
        <Text style={styles.verdict}>{metric.verdict}</Text>
        <Text style={styles.verdictCaveat}>{metric.verdictCaveat}</Text>
      </View>

      {/* WHICH NUMBER — two pills. Only the two slow signals are offered,
          because a six-month view of a fast one is a six-month view of noise. */}
      <View style={styles.section}>
        <View style={styles.selector} accessibilityRole="radiogroup" accessibilityLabel="Which vital">
          {order.map((id) => {
            const active = id === metricId;
            return (
              <Pressable
                key={id}
                onPress={() => chooseMetric(id)}
                accessibilityRole="radio"
                accessibilityState={{ checked: active }}
                accessibilityLabel={metrics[id].label}
                style={({ pressed }) => [
                  styles.selectorItem,
                  active && styles.selectorItemActive,
                  pressed && styles.pressed,
                ]}
              >
                <Text style={[styles.selectorText, active && styles.selectorTextActive]}>
                  {metrics[id].label}
                </Text>
              </Pressable>
            );
          })}
        </View>

        {/* THE READOUT — every fact about the selected month, in words. The
            drawing below never has to be seen for this to read. */}
        <View style={styles.readout} accessibilityLiveRegion="polite">
          <Text style={styles.readoutMonth}>{selected.label}</Text>
          <Text style={styles.readoutValue}>
            {fmt(selected.median)}
            <Text style={styles.readoutUnit}> {metric.unit} most nights</Text>
          </Text>
          <Text style={styles.readoutBand}>
            Band {fmt(selected.low)} to {fmt(selected.high)} · {selected.nights} nights
          </Text>
          {note ? <Text style={styles.readoutNote}>{note.text}. {note.source}.</Text> : null}
        </View>

        {/* THE BANDS — six months on one shared axis. Each row is a Pressable
            carrying its whole claim in words; the drawing repeats it, never
            replaces it. */}
        <View style={styles.bands}>
          {metric.months.map((m) => {
            const isSel = m.id === selected.id;
            return (
              <Pressable
                key={m.id}
                onPress={() => setSelectedId(m.id)}
                accessibilityRole="button"
                accessibilityState={{ selected: isSel }}
                accessibilityLabel={`${m.label}. Usual ${fmt(m.median)} ${metric.unit}, band ${fmt(m.low)} to ${fmt(m.high)}, ${m.nights} nights.`}
                accessibilityHint="Shows this month in the readout above"
                style={({ pressed }) => [styles.bandRow, pressed && styles.pressed]}
              >
                <Text style={[styles.bandLabel, isSel && styles.bandLabelSel]}>{m.label.slice(0, 3)}</Text>
                <View style={styles.track}>
                  <View
                    style={[
                      styles.band,
                      { left: pct(m.low), width: `${((m.high - m.low) / (axis.max - axis.min)) * 100}%` },
                      isSel && styles.bandSel,
                    ]}
                  />
                  <View style={[styles.median, { left: pct(m.median) }, isSel && styles.medianSel]} />
                </View>
                <Text style={[styles.bandValue, isSel && styles.bandLabelSel]}>{fmt(m.median)}</Text>
              </Pressable>
            );
          })}
          {/* Three axis labels, not a ruler. */}
          <View style={styles.axis}>
            <Text style={styles.axisLabel}>{fmt(axis.min)}</Text>
            <Text style={styles.axisLabel}>{metric.unit}</Text>
            <Text style={styles.axisLabel}>{fmt(axis.max)}</Text>
          </View>
        </View>
        <Text style={styles.legend}>
          Each grey bar is the band your nights fell inside that month; the mark is the
          night most of them sat near. All six sit on one scale, so a bar that moved has
          really moved.
        </Text>
        <Text style={styles.legendFine}>{metric.definition}</Text>
      </View>

      {/* THEN AGAINST NOW — a sentence, derived. Two numbers in prose beat a
          second chart of the same data. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>{first.label} against {last.label}</Text>
        <Text style={styles.compareText}>
          Your usual night moved {movedWord}
          {moved !== 0 ? ` ${Math.abs(moved)} ${metric.unit}` : ''}, from {fmt(first.median)} to {fmt(last.median)}.
          The band is {widthWord}: {fmt(first.low)} to {fmt(first.high)} then, {fmt(last.low)} to {fmt(last.high)} now.
        </Text>
      </View>

      {/* WHAT MOVED IT — a ruled list, each line a month, a fact and its source. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>What moved the bands</Text>
        <View>
          {metric.annotations.map((a, i) => {
            const month = metric.months.find((m) => m.id === a.monthId);
            return (
              <Pressable
                key={a.id}
                onPress={() => setSelectedId(a.monthId)}
                accessibilityRole="button"
                accessibilityLabel={`${month.label}. ${a.text}. ${a.source}.`}
                accessibilityHint="Selects that month above"
                style={({ pressed }) => [styles.event, i > 0 && styles.ruled, pressed && styles.pressed]}
              >
                <Text style={[styles.eventMonth, { color: D.hue }]}>{month.label}</Text>
                <View style={styles.eventBody}>
                  <Text style={styles.eventText}>{a.text}</Text>
                  <Text style={styles.eventSource}>{a.source}</Text>
                </View>
              </Pressable>
            );
          })}
        </View>
        <Text style={styles.changes}>
          <Text style={styles.changesLead}>{metric.whatThisChanges.text} </Text>
          {metric.whatThisChanges.why}
        </Text>
      </View>

      {/* WHAT A DRIFT IS NOT — the single outlined block. */}
      <View style={styles.boundary} accessible accessibilityRole="text">
        <Text style={styles.boundaryLabel}>{boundary.label}</Text>
        <Text style={styles.boundaryText}>{boundary.text}</Text>
        <Text style={styles.boundaryDetail}>{boundary.detail}</Text>
        {onOpenData ? (
          <Pressable
            onPress={onOpenData}
            accessibilityRole="button"
            accessibilityLabel="Export these readings for a clinician"
            accessibilityHint="Opens the data screen, where the export lives"
            style={({ pressed }) => [styles.link, pressed && styles.pressed]}
          >
            <Text style={styles.linkText}>Export these readings for a clinician</Text>
          </Pressable>
        ) : null}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: colors.paper },
  content: { padding: space(3), paddingBottom: space(8), gap: space(4) },

  sampleBar: {
    backgroundColor: colors.brandSoft, borderRadius: radius.pill,
    paddingVertical: space(1), paddingHorizontal: space(2), alignSelf: 'flex-start',
  },
  sampleText: { ...type.small, color: colors.deep, fontWeight: '600' },

  header: { gap: space(0.5) },
  back: { alignSelf: 'flex-start', paddingVertical: space(0.5), paddingRight: space(2) },
  backText: { ...type.small, color: colors.brand, fontWeight: '600' },
  pressed: { opacity: 0.6 },
  eyebrow: { ...type.label, marginTop: space(1) },
  title: { ...type.display, color: colors.ink },

  verdictBlock: {
    gap: space(1.5), paddingBottom: space(3),
    borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.border,
  },
  verdict: { fontSize: 24, lineHeight: 33, color: colors.ink, fontWeight: '500' },
  verdictCaveat: { ...type.small, color: colors.muted },

  section: { gap: space(1.5) },
  sectionTitle: { ...type.title, color: colors.ink },

  selector: { flexDirection: 'row', gap: space(1), flexWrap: 'wrap' },
  selectorItem: {
    paddingVertical: space(0.75), paddingHorizontal: space(1.75),
    borderRadius: radius.pill, borderWidth: 1, borderColor: colors.border,
  },
  selectorItemActive: { backgroundColor: colors.ink, borderColor: colors.ink },
  selectorText: { ...type.small, color: colors.muted, fontWeight: '600' },
  selectorTextActive: { color: colors.paper },

  readout: { gap: 2 },
  readoutMonth: { ...type.label, color: colors.faint },
  readoutValue: { ...type.display, color: colors.ink, fontVariant: ['tabular-nums'] },
  readoutUnit: { ...type.small, color: colors.faint, fontWeight: '400' },
  readoutBand: { ...type.small, color: colors.muted, fontVariant: ['tabular-nums'] },
  readoutNote: { ...type.small, color: colors.ink, marginTop: 2 },

  // The bands. Grey for every month; the selected month is ink. Selection is
  // never the only signal: the readout names it in words.
  bands: { gap: space(1), paddingTop: space(1) },
  bandRow: { flexDirection: 'row', alignItems: 'center', gap: space(1.5), minHeight: 32 },
  bandLabel: { ...type.small, color: colors.muted, width: 32, fontWeight: '600' },
  bandLabelSel: { color: colors.ink },
  track: { flex: 1, height: 18, justifyContent: 'center' },
  band: { position: 'absolute', height: 10, borderRadius: 5, backgroundColor: colors.border },
  bandSel: { backgroundColor: colors.muted },
  median: { position: 'absolute', width: 3, height: 18, marginLeft: -1.5, borderRadius: 1.5, backgroundColor: colors.faint },
  medianSel: { backgroundColor: colors.ink },
  bandValue: { ...type.small, color: colors.muted, width: 36, textAlign: 'right', fontVariant: ['tabular-nums'], fontWeight: '600' },
  axis: { flexDirection: 'row', justifyContent: 'space-between', paddingLeft: 32 + space(1.5), paddingRight: 36 + space(1.5) },
  axisLabel: { ...type.small, color: colors.faint, fontVariant: ['tabular-nums'] },

  legend: { ...type.small, color: colors.muted, marginTop: space(1) },
  legendFine: { ...type.small, color: colors.faint },

  compareText: { ...type.body, color: colors.ink },

  event: { flexDirection: 'row', gap: space(2), paddingVertical: space(1.5) },
  ruled: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },
  eventMonth: { ...type.label, width: 84, paddingTop: 3 },
  eventBody: { flex: 1, gap: 2 },
  eventText: { ...type.body, color: colors.ink },
  eventSource: { ...type.small, color: colors.faint },
  changes: { ...type.body, color: colors.muted, marginTop: space(1) },
  changesLead: { color: colors.ink, fontWeight: '600' },

  boundary: {
    borderWidth: 1, borderColor: colors.ink, borderRadius: radius.card,
    padding: space(2.5), gap: space(0.5),
  },
  boundaryLabel: { ...type.label, color: colors.ink },
  boundaryText: { ...type.body, color: colors.ink, fontWeight: '500' },
  boundaryDetail: { ...type.small, color: colors.muted },
  link: { alignSelf: 'flex-start', paddingVertical: space(1), marginTop: space(0.5) },
  linkText: { ...type.body, color: colors.brand, fontWeight: '600' },
});

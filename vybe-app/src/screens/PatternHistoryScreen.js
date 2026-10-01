import React, { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { colors, dimensions, radius, space, type } from '../theme';
import { isSample, pattern } from '../patternHistorySampleData';
import PatternWeeks, {
  MIN_NIGHTS,
  ceilingFor,
  middleOf,
  verdictFor,
} from '../components/PatternWeeks';

// Two dimensions, because the claim crosses them. Both are named in words
// wherever their hue appears.
const RESTORE = dimensions.restore;
const NOURISH = dimensions.nourish;

/**
 * Pattern history — twelve weeks of one claim.
 *
 * `MoveTrendScreen` already does the other kind of history: one metric across
 * twenty-six weeks, and what changed. This screen answers the question that
 * actually tests the product's premise — not "what did this number do" but
 * "did the relationship Vybe claims hold up over time".
 *
 * THE DECISION THAT MAKES THIS SCREEN
 * It shows the weeks the pattern broke, at the same size as the weeks it held,
 * with Vybe's explanation beside each — and for one of them the explanation is
 * that there isn't one. Nine of eleven is a different claim from eleven of
 * eleven, and every product that reports "we found a pattern" has rounded that
 * difference away. The exceptions are not hidden behind a tap.
 *
 * NOTHING ON THIS SCREEN IS A STORED VERDICT
 * The headline count, the middle of the range, and each week's verdict are all
 * computed here from the numbers in the sample module, against a rule printed
 * on screen. A headline that is typed rather than derived can drift away from
 * the rows beneath it, and this is exactly the screen where that would matter.
 *
 * Five treatments, so the hierarchy reads before the words: the claim in
 * oversized type on bare paper, the count as one big figure, the weeks as a
 * hairline list with bars, the rule as a plain block under a rule, and the
 * closing restraint as the only dark panel.
 */
export default function PatternHistoryScreen({ onBack }) {
  const { weeks, rule, metric, driver, exceptions } = pattern;

  const middle = middleOf(weeks);
  const ceiling = ceilingFor(weeks);

  // Derived, not typed. Thin weeks leave the denominator rather than being
  // averaged in: a week the Band barely recorded is not evidence either way.
  const scored = weeks.filter((w) => w.nights >= MIN_NIGHTS);
  const held = scored.filter(
    (w) => verdictFor(w, middle, rule.driverThreshold) === 'held',
  ).length;
  const thin = weeks.length - scored.length;

  const [selectedId, setSelectedId] = useState(null);
  const selected = weeks.find((w) => w.id === selectedId) || null;
  const selectedVerdict = selected
    ? verdictFor(selected, middle, rule.driverThreshold)
    : null;

  return (
    <ScrollView
      style={styles.page}
      contentContainerStyle={styles.content}
      accessibilityLabel="Pattern history"
    >
      {isSample ? (
        <View style={styles.sampleBar}>
          <Text style={styles.sampleText}>
            Sample data — these are not your weeks.
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
        <Text style={styles.eyebrow}>TWELVE WEEKS</Text>
        <Text style={styles.window}>{pattern.window}</Text>
      </View>

      {/* THE CLAIM — a sentence, on bare paper, with the two dimensions it
          crosses named beside it. */}
      <View style={styles.claimBlock}>
        <Text style={styles.claim}>{pattern.claim}</Text>
        <View style={styles.tagRow}>
          {[NOURISH, RESTORE].map((d) => (
            <View
              key={d.key}
              style={styles.tag}
              accessible
              accessibilityRole="text"
              accessibilityLabel={`Drew on ${d.label}`}
            >
              <View aria-hidden style={[styles.tagDot, { backgroundColor: d.hue }]} />
              <Text style={styles.tagLabel}>{d.label}</Text>
            </View>
          ))}
        </View>
      </View>

      {/* THE COUNT — the figure the whole screen turns on, set large on bare
          paper and computed from the rows below rather than written down. */}
      <View style={styles.figureBlock}>
        <Text style={styles.figure}>
          {held} of {scored.length}
        </Text>
        <Text style={styles.figureLabel}>
          weeks where the pattern held
          {thin
            ? ` — ${thin} more week${thin === 1 ? '' : 's'} had too few nights to count`
            : ''}
        </Text>
      </View>

      {/* THE READOUT — what a tapped week says, in words. Empty until you pick
          one, and never the only place a fact appears. */}
      <View style={styles.readout}>
        {selected ? (
          <Text style={styles.readoutText}>
            Week of {selected.label}: {selected.lateNights} late{' '}
            {selected.lateNights === 1 ? 'night' : 'nights'}, {selected.deepMinutes}{' '}
            {metric.unit} deep sleep —{' '}
            {selected.deepMinutes < middle ? 'below' : 'at or above'} your middle of{' '}
            {middle}.{' '}
            {selectedVerdict === 'held'
              ? 'That is what the pattern predicts.'
              : selectedVerdict === 'broke'
                ? 'That is the opposite of what the pattern predicts.'
                : 'Too few nights recorded to say.'}
          </Text>
        ) : (
          <Text style={styles.readoutEmpty}>Tap a week to pin it here.</Text>
        )}
      </View>

      {/* THE WEEKS */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Week by week</Text>
        <PatternWeeks
          weeks={weeks}
          middle={middle}
          threshold={rule.driverThreshold}
          ceiling={ceiling}
          exceptions={exceptions}
          selectedId={selectedId}
          onSelect={setSelectedId}
          metricUnit={metric.unit}
        />
        <Text style={styles.plotNote}>
          Each bar is that week&rsquo;s {metric.label.toLowerCase()}. The hairline across
          the bars is {middle} {metric.unit}, the middle of the eleven weeks with
          enough nights — the line every week above is judged against.
        </Text>
        <Text style={styles.plotNote}>{metric.caveat}</Text>
      </View>

      {/* THE RULE — printed, not hidden. A pattern you cannot check is
          indistinguishable from one that was asserted. */}
      <View style={styles.ruleBlock}>
        <Text style={styles.ruleLabel}>The rule Vybe used</Text>
        <Text style={styles.ruleText}>
          A week counts as holding when {rule.driverLabel} came with{' '}
          {rule.metricLabel} — or when a quieter week came with deep sleep at or
          above it. A week with fewer than {MIN_NIGHTS} recorded nights is left out
          of the count entirely.
        </Text>
        <Text style={styles.ruleAside}>
          {driver.label} and {metric.label.toLowerCase()} both come from your own
          data. Nothing here is compared against anybody else.
        </Text>
      </View>

      {/* WHAT WOULD MAKE IT STRONGER */}
      <View style={styles.strongerBlock}>
        <Text style={styles.ruleLabel}>What would make this stronger</Text>
        <Text style={styles.ruleText}>{pattern.stronger}</Text>
      </View>

      {/* THE RESTRAINT — the only dark block, and the last word. */}
      <View style={styles.restraintPanel}>
        <Text style={styles.restraintEyebrow}>WHAT THIS IS NOT</Text>
        <Text style={styles.restraintText}>{pattern.restraint}</Text>
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
  eyebrow: { ...type.label, color: colors.brand, marginTop: space(1) },
  window: { ...type.small, color: colors.muted, fontVariant: ['tabular-nums'] },

  claimBlock: { gap: space(1.5) },
  claim: { fontSize: 26, lineHeight: 35, color: colors.ink, fontWeight: '500' },
  tagRow: { flexDirection: 'row', flexWrap: 'wrap', gap: space(2) },
  tag: { flexDirection: 'row', alignItems: 'center', gap: space(0.75) },
  tagDot: { width: 8, height: 8, borderRadius: 4 },
  tagLabel: { ...type.small, color: colors.muted, fontWeight: '600' },

  figureBlock: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
    paddingTop: space(2),
    gap: space(0.5),
  },
  // Set large on bare paper for the same reason the Nourish figure is: it is
  // the number the answer turns on, and it is arithmetic over the rows below.
  figure: { fontSize: 56, lineHeight: 62, color: colors.ink, fontWeight: '600', fontVariant: ['tabular-nums'] },
  figureLabel: { ...type.body, color: colors.muted },

  readout: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    padding: space(2),
    minHeight: 76,
    justifyContent: 'center',
  },
  readoutText: { ...type.body, color: colors.ink, lineHeight: 23 },
  readoutEmpty: { ...type.small, color: colors.faint },

  section: { gap: space(1) },
  sectionTitle: { ...type.title, color: colors.ink },
  plotNote: { ...type.small, color: colors.faint, lineHeight: 20, paddingTop: space(0.75) },

  ruleBlock: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
    paddingTop: space(2),
    gap: space(0.5),
  },
  ruleLabel: { ...type.label, color: colors.faint },
  ruleText: { ...type.body, color: colors.ink, lineHeight: 23 },
  ruleAside: { ...type.small, color: colors.muted, paddingTop: space(0.5) },

  strongerBlock: { gap: space(0.5) },

  restraintPanel: {
    backgroundColor: colors.ink,
    borderRadius: radius.card,
    padding: space(3),
    gap: space(1),
  },
  restraintEyebrow: { ...type.label, color: colors.brandSoft },
  restraintText: { fontSize: 18, lineHeight: 27, color: colors.paper },
});

import React, { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { colors, radius, space, type } from '../theme';
import {
  exceptions,
  isSample,
  metric,
  readings,
  restraint,
  rule,
  whatItCannotSay,
  whenItCanSay,
  window as windowInfo,
} from '../seasonSampleData';
import SeasonRows, {
  MONTH_NAME,
  deltaFor,
  pairsOf,
  seenOnceLowestFirst,
  verdictFor,
} from '../components/SeasonRows';

/**
 * Year on year — is this a trend, or is it just November again?
 *
 * The app has two history screens already. `MoveTrendScreen` draws one metric
 * across twenty-six weeks; `PatternHistoryScreen` tests one claim across
 * twelve. Both answer "what did this do". Neither can answer the question that
 * decides whether any of it means anything, because that question needs more
 * than a year of data.
 *
 * THE DECISION THAT MAKES THIS SCREEN
 * Every wearable shows a decline through the winter and lets the person
 * conclude they are getting worse. Usually they are not; it is winter. The
 * tempting fix is a seasonal adjustment — quietly lift the winter numbers and
 * show a flat line. That hides the only thing worth knowing. So this screen
 * does the opposite: it reports how many months it can actually compare, shows
 * the months it has seen once as rows with a visible hole where the second
 * year should be, and refuses to draw a seasonal curve through a single year.
 *
 * AND THE SECOND ONE: the five lowest months on the screen are the five it has
 * seen only once. The screen CHECKS that rather than asserting it, and says so
 * in the one place a person would otherwise read a downward slope as decline.
 *
 * NOTHING HERE IS A STORED VERDICT. The pairing, the per-month verdicts, the
 * counts and the overlap between "worst" and "thinnest" are all computed at
 * render from nineteen readings with a year and a month on each, against a
 * margin the screen prints. A pre-paired dataset could quietly disagree with
 * the readings beneath it.
 *
 * Five treatments: the count as oversized type on bare paper, the rule as a
 * plain block, twelve month rows with two value columns, what Vybe cannot say
 * as an outlined block — the treatment this app reserves for a refusal — and
 * the closing restraint as the only dark panel.
 */
export default function SeasonScreen({ onBack }) {
  const [openMonth, setOpenMonth] = useState(null);

  // Derived, never typed.
  const pairs = pairsOf(readings);
  const compared = pairs.filter((p) => p.years.length > 1);
  const once = pairs.filter((p) => p.years.length === 1);
  const repeated = compared.filter((p) => verdictFor(p, rule.sameWithin) === 'repeated');
  const changed = compared.filter((p) => verdictFor(p, rule.sameWithin) === 'changed');

  // The claim the screen makes about its own weakest evidence, checked rather
  // than asserted: are the lowest months the same ones seen only once?
  const onceLowest = seenOnceLowestFirst(readings);
  const allValues = readings.map((r) => r.value).sort((a, b) => a - b);
  const lowestN = allValues.slice(0, once.length);
  const worstAreThinnest =
    once.length > 0
    && onceLowest.every((p) => lowestN.includes(p.years[0].value));

  const selected = openMonth
    ? pairs.find((p) => p.month === openMonth) || null
    : null;

  return (
    <ScrollView
      style={styles.page}
      contentContainerStyle={styles.content}
      accessibilityLabel="Year on year"
    >
      {isSample ? (
        <View style={styles.sampleBar}>
          <Text style={styles.sampleText}>
            Sample data — these are not your months.
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
        <Text style={styles.eyebrow}>YEAR ON YEAR</Text>
        <Text style={styles.question}>
          Is this a trend, or is it just November again?
        </Text>
        <Text style={styles.window}>
          {metric.label}, {metric.perLabel} · {windowInfo.label}
        </Text>
      </View>

      {/* THE COUNT — the figure the screen turns on, and it is a limit rather
          than an achievement. */}
      <View style={styles.figureBlock}>
        <Text style={styles.figure}>
          {compared.length} of {pairs.length}
        </Text>
        <Text style={styles.figureLabel}>
          months Vybe can compare with the same month a year earlier.{' '}
          {repeated.length} of those came out the same both times and{' '}
          {changed.length}{' '}
          {changed.length === 1 ? 'did not' : 'did not'}. The other {once.length}{' '}
          it has seen once.
        </Text>
      </View>

      {/* THE READOUT */}
      <View style={styles.readout}>
        {selected ? (
          <Text style={styles.readoutText}>
            {MONTH_NAME[selected.month]}:{' '}
            {selected.years.map((y) => `${y.year} came out at ${y.value} ${metric.unit}`).join(', and ')}
            {selected.years.length > 1
              ? `. That is ${
                  deltaFor(selected) === 0
                    ? 'no change'
                    : `${Math.abs(deltaFor(selected))} ${metric.unit} ${deltaFor(selected) > 0 ? 'higher' : 'lower'}`
                }, which is ${
                  verdictFor(selected, rule.sameWithin) === 'repeated'
                    ? `inside the ${rule.sameWithin}-minute margin, so Vybe calls it the same month twice.`
                    : `outside the ${rule.sameWithin}-minute margin, so Vybe calls it a change.`
                }`
              : '. There is no second year to put beside it, so Vybe has nothing to say about whether that is normal for you.'}
          </Text>
        ) : (
          <Text style={styles.readoutEmpty}>Tap a month to pin it here.</Text>
        )}
      </View>

      {/* THE RULE — printed, not hidden. */}
      <View style={styles.ruleBlock}>
        <Text style={styles.ruleLabel}>How a month is scored</Text>
        <Text style={styles.ruleText}>{rule.text}</Text>
        <Text style={styles.ruleAside}>
          {windowInfo.note} {metric.caveat}
        </Text>
      </View>

      {/* THE MONTHS */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Every month Vybe has</Text>
        <Text style={styles.sectionLede}>
          Two columns: the earlier year, then the later one. A dash means there
          is no earlier year to compare with.
        </Text>
        <SeasonRows
          readings={readings}
          sameWithin={rule.sameWithin}
          unit={metric.unit}
          exceptions={exceptions}
          selectedMonth={openMonth}
          onSelect={setOpenMonth}
        />
      </View>

      {/* WHAT VYBE CANNOT SAY — the one outlined block, the treatment this app
          reserves for a refusal, and the label says what the outline means. */}
      <View style={styles.gapPanel}>
        <Text style={styles.gapLabel}>WHAT VYBE CANNOT SAY YET</Text>
        <Text style={styles.gapText}>{whatItCannotSay}</Text>
        {worstAreThinnest ? (
          <Text style={styles.gapAside}>
            Checked rather than claimed: the {once.length} lowest months on this
            screen are the same {once.length} months Vybe has seen only once —{' '}
            {onceLowest.map((p) => MONTH_NAME[p.month]).join(', ')}.
          </Text>
        ) : (
          <Text style={styles.gapAside}>
            The months seen only once are{' '}
            {onceLowest.map((p) => MONTH_NAME[p.month]).join(', ')}.
          </Text>
        )}
      </View>

      {/* WHEN IT CAN */}
      <View style={styles.whenBlock}>
        <Text style={styles.ruleLabel}>When this screen becomes useful</Text>
        <Text style={styles.ruleText}>{whenItCanSay}</Text>
      </View>

      {/* THE RESTRAINT — the only dark block, and the last word. */}
      <View style={styles.restraintPanel}>
        <Text style={styles.restraintEyebrow}>WHAT THIS IS NOT</Text>
        <Text style={styles.restraintText}>{restraint}</Text>
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
  question: { fontSize: 28, lineHeight: 36, color: colors.ink, fontWeight: '500' },
  window: { ...type.small, color: colors.muted, marginTop: space(0.5) },

  figureBlock: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
    paddingTop: space(2),
    gap: space(0.5),
  },
  figure: {
    fontSize: 56,
    lineHeight: 62,
    color: colors.ink,
    fontWeight: '600',
    fontVariant: ['tabular-nums'],
  },
  figureLabel: { ...type.body, color: colors.muted, lineHeight: 24 },

  readout: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    padding: space(2),
    minHeight: 76,
    justifyContent: 'center',
  },
  readoutText: { ...type.body, color: colors.ink, lineHeight: 23 },
  readoutEmpty: { ...type.small, color: colors.faint },

  ruleBlock: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
    paddingTop: space(2),
    gap: space(0.5),
  },
  ruleLabel: { ...type.label, color: colors.faint },
  ruleText: { ...type.body, color: colors.ink, lineHeight: 23 },
  ruleAside: { ...type.small, color: colors.muted, paddingTop: space(0.5), lineHeight: 20 },

  section: { gap: space(1) },
  sectionTitle: { ...type.title, color: colors.ink },
  sectionLede: { ...type.small, color: colors.muted, lineHeight: 20 },

  gapPanel: {
    borderWidth: 1,
    borderColor: colors.ink,
    borderRadius: radius.card,
    padding: space(3),
    gap: space(1.5),
  },
  gapLabel: { ...type.label, color: colors.ink },
  gapText: { ...type.body, color: colors.ink, lineHeight: 24 },
  gapAside: { ...type.small, color: colors.muted, lineHeight: 20 },

  whenBlock: { gap: space(0.5) },

  restraintPanel: {
    backgroundColor: colors.ink,
    borderRadius: radius.card,
    padding: space(3),
    gap: space(1),
  },
  restraintEyebrow: { ...type.label, color: colors.brandSoft },
  restraintText: { fontSize: 18, lineHeight: 27, color: colors.paper },
});

import React, { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { colors, dimensions, radius, space, type } from '../theme';
import { nourishDay, isSample } from '../nourishSampleData';
import EvidenceRow from '../components/EvidenceRow';
import DayTimeline, { clockLabel, formatSpan, minutesOf } from '../components/DayTimeline';

const D = dimensions.nourish;

/**
 * Nourish — the dimension detail screen.
 *
 * Same spine as Restore (answer, evidence, context, action), but the argument
 * has a different shape, so the screen does too. Restore's evidence is a set of
 * overnight readings and a list is the right form for them. This day's evidence
 * is a sequence -- five meals and a bedtime -- and the claim is about the gap
 * between two of them, which a list physically cannot show. So the middle of
 * this screen is a clock, and the figure the claim turns on is set in type big
 * enough to be the second thing you read.
 *
 * Six treatments, so the hierarchy is legible before a word is: a tinted panel
 * for the answer, oversized type on bare paper for the gap, a plot for the day,
 * a hairline list for the readings, a ruled pair for the pattern, and the one
 * dark block for the action.
 */
export default function NourishScreen({ onBack, onOpenHistory }) {
  const [selectedId, setSelectedId] = useState('dinner');

  const meals = nourishDay.meals;
  const selected = meals.find((m) => m.id === selectedId) || meals[meals.length - 1];

  // Derived here, never typed into the data: the gap is the whole argument, and
  // a hand-written "1h 35m" would survive an edit to the meal times and start
  // quietly contradicting the timeline drawn directly underneath it.
  const lastBite = minutesOf(meals[meals.length - 1].end);
  const lightsOut = minutesOf(nourishDay.sleep.lightsOut);
  const gapMinutes = lightsOut - lastBite;
  const shortBy = nourishDay.usual.gapMinutes - gapMinutes;

  const { late, early, basis, caveat, crossLink } = nourishDay.pattern;
  const deepDiff = early.deepMinutes - late.deepMinutes;
  const deepPct = Math.round((deepDiff / late.deepMinutes) * 100);

  return (
    <ScrollView
      style={styles.page}
      contentContainerStyle={styles.content}
      accessibilityLabel="Nourish detail"
    >
      {isSample ? (
        <View style={styles.sampleBar}>
          <Text style={styles.sampleText}>Sample data — these are not your readings.</Text>
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
        <Text style={[styles.eyebrow, { color: D.hue }]}>NOURISH</Text>
        <Text style={styles.date}>{nourishDay.date}</Text>
      </View>

      {/* THE ANSWER — a sentence. Not a calorie total, not a score. */}
      <View style={[styles.answerPanel, { backgroundColor: D.tint }]}>
        <Text style={styles.answer}>{nourishDay.answer}</Text>
        <Text style={[styles.confidence, { color: D.hue }]}>{nourishDay.confidence}</Text>
        <Text style={styles.confidenceWhy}>{nourishDay.confidenceWhy}</Text>
      </View>

      {/* THE FIGURE — bare paper, no panel, because it is the one number on the
          screen that the rest of the screen is about. */}
      <View style={styles.figureBlock}>
        <Text style={styles.figure} accessibilityRole="text">{formatSpan(gapMinutes)}</Text>
        <Text style={styles.figureCaption}>
          {`between your last bite at ${clockLabel(meals[meals.length - 1].end)} and lights out at `}
          {`${clockLabel(nourishDay.sleep.lightsOut)}`}
          {shortBy > 0
            ? ` — ${formatSpan(shortBy)} short of ${nourishDay.usual.gapLabel}.`
            : ` — at or past ${nourishDay.usual.gapLabel}.`}
        </Text>
      </View>

      {/* THE DAY — the sequence the claim lives in. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Your day, on the clock</Text>
        <DayTimeline
          meals={meals}
          sleep={nourishDay.sleep}
          hue={D.hue}
          selectedId={selected.id}
          onSelect={setSelectedId}
        />
        {/* Opens on the meal the answer is about, so the screen shows its own
            evidence before anybody taps anything. */}
        <View style={styles.mealDetail}>
          <Text style={styles.mealWhen}>
            {`${selected.name.toUpperCase()} · ${clockLabel(selected.start)}–${clockLabel(selected.end)} · ${formatSpan(minutesOf(selected.end) - minutesOf(selected.start))}`}
          </Text>
          <Text style={styles.mealItems}>{selected.items.join(', ')}</Text>
          <Text style={styles.mealNote}>{selected.note}</Text>
        </View>
      </View>

      {/* WHAT THE FOOD ITSELF DID — the readings that are not about timing. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>What the day added up to</Text>
        <View>
          {nourishDay.readings.map((item, i) => (
            <EvidenceRow key={item.id} item={item} first={i === 0} />
          ))}
        </View>
      </View>

      {/* THE PATTERN — two rows on one rule. Deliberately not bars: the trend
          screen owns bars, and with two values a pair of figures reads faster
          than a pair of rectangles. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Late dinners, and the nights after them</Text>
        <Text style={styles.sectionLede}>
          {`Your estimated deep sleep across ${basis}, split by when you finished eating.`}
        </Text>

        {[late, early].map((group, i) => (
          <View
            key={group.label}
            style={[styles.patternRow, i > 0 && styles.ruled]}
            accessible
            accessibilityRole="text"
            accessibilityLabel={
              `${group.label}, ${group.nights} nights. `
              + `Estimated deep sleep ${formatSpan(group.deepMinutes)}.`
            }
          >
            <View style={styles.patternLeft}>
              <Text style={styles.patternLabel}>{group.label}</Text>
              <Text style={styles.patternNights}>
                {group.nights === 1 ? '1 night' : `${group.nights} nights`}
              </Text>
            </View>
            <Text style={styles.patternValue}>{formatSpan(group.deepMinutes)}</Text>
          </View>
        ))}

        <Text style={styles.patternRead}>
          {deepDiff > 0
            ? `The earlier nights came out ${formatSpan(deepDiff)} higher — about ${deepPct}% more estimated deep sleep.`
            : `The earlier nights came out no higher, so this fortnight does not support the pattern.`}
        </Text>
        <Text style={styles.caveat}>{caveat}</Text>
        <Text style={styles.crossLink}>{crossLink}</Text>
        {/* The day screen makes the claim; the history screen shows twelve
            weeks of it, including the weeks it broke. Linking them here is the
            honest place for a reader who has just been told a pattern exists
            to go and check how often it has actually held. */}
        {onOpenHistory ? (
          <Pressable
            onPress={onOpenHistory}
            accessibilityRole="button"
            accessibilityLabel="See twelve weeks of this pattern"
            accessibilityHint="Opens the week-by-week history, including the weeks the pattern did not hold"
            style={({ pressed }) => [styles.historyLink, pressed && styles.pressed]}
          >
            <Text style={styles.historyLinkText}>See twelve weeks of this pattern</Text>
          </Pressable>
        ) : null}
      </View>

      {/* ACTION — one, and the only dark block on the screen. */}
      <View style={styles.actionPanel}>
        <Text style={styles.actionEyebrow}>TOMORROW</Text>
        <Text style={styles.actionText}>{nourishDay.action.text}</Text>
        <Text style={styles.actionWhy}>{nourishDay.action.why}</Text>
      </View>

      {/* What the screen refuses to do, which is as much of the product as what
          it does. */}
      <View style={styles.restraint}>
        <Text style={styles.restraintLabel}>What Nourish is not</Text>
        <Text style={styles.restraintText}>{nourishDay.restraint}</Text>
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
  date: { ...type.display, color: colors.ink },

  answerPanel: { borderRadius: radius.card, padding: space(3), gap: space(1.5) },
  answer: { fontSize: 22, lineHeight: 31, color: colors.ink, fontWeight: '500' },
  confidence: { ...type.label },
  confidenceWhy: { ...type.small, color: colors.muted },

  figureBlock: { gap: space(0.5) },
  figure: {
    fontSize: 56, lineHeight: 60, fontWeight: '600', color: colors.ink,
    letterSpacing: -1, fontVariant: ['tabular-nums'],
  },
  // Held to a readable measure rather than the full width: this caption is a
  // sentence, and a 44-character line is easier to read than a 70-character one.
  figureCaption: { ...type.body, color: colors.muted, maxWidth: space(40) },

  section: { gap: space(1) },
  sectionTitle: { ...type.title, color: colors.ink },
  sectionLede: { ...type.small, color: colors.muted },

  mealDetail: { marginTop: space(1), gap: 3 },
  mealWhen: { ...type.label, color: colors.faint, letterSpacing: 1.1 },
  mealItems: { ...type.body, color: colors.ink, fontWeight: '600' },
  mealNote: { ...type.small, color: colors.muted },

  patternRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: space(1.75), gap: space(2) },
  ruled: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },
  patternLeft: { flex: 1, gap: 2 },
  patternLabel: { ...type.body, color: colors.ink, fontWeight: '600' },
  patternNights: { ...type.small, color: colors.faint },
  patternValue: { fontSize: 26, fontWeight: '600', color: colors.ink, fontVariant: ['tabular-nums'] },
  patternRead: { ...type.body, color: colors.ink, marginTop: space(1) },
  caveat: { ...type.small, color: colors.faint },
  crossLink: { ...type.small, color: colors.muted, marginTop: space(1) },
  historyLink: { alignSelf: 'flex-start', paddingVertical: space(1), marginTop: space(0.5) },
  historyLinkText: { ...type.body, color: colors.brand, fontWeight: '600' },

  actionPanel: { backgroundColor: colors.ink, borderRadius: radius.card, padding: space(3), gap: space(1) },
  actionEyebrow: { ...type.label, color: colors.brandSoft },
  actionText: { fontSize: 24, lineHeight: 32, color: colors.paper, fontWeight: '600' },
  actionWhy: { ...type.small, color: '#C9D2D8', lineHeight: 21 },

  restraint: {
    borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border,
    paddingTop: space(2), gap: space(0.5),
  },
  restraintLabel: { ...type.label, color: colors.brand },
  restraintText: { ...type.small, color: colors.muted, lineHeight: 20 },
});

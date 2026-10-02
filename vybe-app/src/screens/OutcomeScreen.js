import React, { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { colors, radius, space, type } from '../theme';
import { isSample, outcomes } from '../outcomeSampleData';
import OutcomeLedger, {
  VERDICT_WORD,
  testedOf,
  verdictFor,
} from '../components/OutcomeLedger';

/**
 * Did it work — Vybe grading itself.
 *
 * This is the screen the rest of the app is pointing at. Every other screen
 * ends with one suggestion; this one comes back and says whether the suggestion
 * was any good. Almost no wellness product ships it, because the honest answer
 * is sometimes no, and a product that marks its own homework always passes.
 *
 * TWO RULES MAKE IT HONEST RATHER THAN DECORATIVE
 *
 * The criterion was written down first. Each row carries the range Vybe
 * committed to at the time — the metric, the numbers, the units and the window.
 * Deciding after the fact what counted as working is how every app in this
 * category wins every time, and it is why none of them are believed.
 *
 * Not doing it is a third outcome. Three of these ten were never attempted, so
 * the advice was never tested and Vybe learned nothing. Scoring those against
 * the person would make the tally flattering: it would hide Vybe's weak
 * suggestions behind somebody's difficult week. The screen says outright that
 * the untried ones are the clearest signal on it.
 *
 * THE TALLY IS ARITHMETIC OVER THE ROWS
 * "4 of 7" and the miss count are computed here from `adherence`, `actual` and
 * the predicted range. A typed headline can drift from the rows beneath it, and
 * on a screen whose whole claim is "we are not marking our own homework", a
 * headline that disagreed with its own ledger would be the only bug that
 * matters.
 *
 * Five treatments, so the hierarchy reads before the words: the record as a
 * fraction set large on bare paper, the reading as a sentence, the ledger as a
 * hairline list of type, what Vybe got wrong as an outlined block — the same
 * treatment the Ask screen gives a refusal, because this is the app admitting
 * something — and the closing restraint as the one dark panel.
 */
export default function OutcomeScreen({ onBack }) {
  const { attempts } = outcomes;

  const tested = testedOf(attempts);
  const called = tested.filter((a) => verdictFor(a) === 'called');
  const missed = tested.filter((a) => verdictFor(a) === 'missed');
  const untried = attempts.filter((a) => verdictFor(a) === 'untested');

  // Only the misses carry a `learned` note. Printing them together is the
  // point: a list of what the product got wrong, with what it changed.
  const lessons = missed.filter((a) => a.learned);

  const [selectedId, setSelectedId] = useState(null);
  const selected = attempts.find((a) => a.id === selectedId) || null;

  return (
    <ScrollView
      style={styles.page}
      contentContainerStyle={styles.content}
      accessibilityLabel="Outcome review"
    >
      {isSample ? (
        <View style={styles.sampleBar}>
          <Text style={styles.sampleText}>
            Sample data — these are not your suggestions or your readings.
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
        <Text style={styles.eyebrow}>DID IT WORK</Text>
        <Text style={styles.window}>{outcomes.window}</Text>
      </View>

      {/* THE RECORD — a fraction, not a percentage. Four of seven says how
          little it rests on; 57% would hide that. */}
      <View style={styles.recordBlock}>
        <Text style={styles.record}>
          {called.length} of {tested.length}
        </Text>
        <Text style={styles.recordLabel}>
          suggestions that did what Vybe said they would, out of the{' '}
          {tested.length} you actually tried
        </Text>
        <Text style={styles.reading}>{outcomes.reading}</Text>
      </View>

      {/* THE READOUT — what a tapped row says, in words. */}
      <View style={styles.readout}>
        {selected ? (
          <Text style={styles.readoutText}>
            {selected.date}: {selected.suggestion} Vybe said{' '}
            {selected.predicted.metric.toLowerCase()} would land between{' '}
            {selected.predicted.low} and {selected.predicted.high}{' '}
            {selected.predicted.unit} {selected.predicted.window}.{' '}
            {selected.actual === null
              ? 'It was never tried, so there is nothing to compare.'
              : `It came out at ${selected.actual} ${selected.predicted.unit}.`}{' '}
            {VERDICT_WORD[verdictFor(selected)]}.
          </Text>
        ) : (
          <Text style={styles.readoutEmpty}>Tap a suggestion to pin it here.</Text>
        )}
      </View>

      {/* THE RULE — printed beside the tally, not buried. */}
      <View style={styles.ruleBlock}>
        <Text style={styles.ruleLabel}>How a suggestion is scored</Text>
        <Text style={styles.ruleText}>
          Vybe writes the range down before you start. It counts as working only
          if the reading lands inside that range, in that window. A suggestion you
          did not try is not scored at all — it is marked no test, because the
          advice was never put to the question.
        </Text>
      </View>

      {/* THE LEDGER */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Every suggestion, in order</Text>
        <OutcomeLedger
          attempts={attempts}
          selectedId={selectedId}
          onSelect={setSelectedId}
        />
      </View>

      {/* NOT TRIED — stated as a signal about Vybe, not about the person. */}
      <View style={styles.untriedBlock}>
        <Text style={styles.ruleLabel}>
          {untried.length} never tried
        </Text>
        <Text style={styles.ruleText}>{outcomes.adherenceNote}</Text>
        <View style={styles.untriedList}>
          {untried.map((a) => (
            <Text key={a.id} style={styles.untriedItem}>
              {a.date} — {a.suggestion}
            </Text>
          ))}
        </View>
      </View>

      {/* WHAT VYBE GOT WRONG — the one outlined block, and the label says what
          the outline means so the treatment never carries it alone. */}
      <View style={styles.wrongPanel}>
        <Text style={styles.wrongLabel}>WHAT VYBE GOT WRONG</Text>
        <Text style={styles.wrongLede}>
          {missed.length} of the {tested.length} tested suggestions missed. Here is
          what changed because of them.
        </Text>
        {lessons.map((a) => (
          <View key={a.id} style={styles.lesson}>
            <Text style={styles.lessonHead}>
              {a.date} · {a.suggestion}
            </Text>
            <Text style={styles.lessonText}>{a.learned}</Text>
          </View>
        ))}
      </View>

      {/* THE RESTRAINT — the only dark block, and the last word. */}
      <View style={styles.restraintPanel}>
        <Text style={styles.restraintEyebrow}>WHAT THIS IS NOT</Text>
        <Text style={styles.restraintText}>{outcomes.restraint}</Text>
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

  recordBlock: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
    paddingTop: space(2),
    gap: space(1),
  },
  // A fraction rather than a percentage, set large on bare paper. "4 of 7"
  // carries its own sample size; "57%" throws it away.
  record: { fontSize: 56, lineHeight: 62, color: colors.ink, fontWeight: '600', fontVariant: ['tabular-nums'] },
  recordLabel: { ...type.body, color: colors.muted },
  reading: { ...type.body, color: colors.ink, lineHeight: 24, marginTop: space(0.5) },

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

  section: { gap: space(1) },
  sectionTitle: { ...type.title, color: colors.ink },

  untriedBlock: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
    paddingTop: space(2),
    gap: space(0.5),
  },
  untriedList: { gap: space(0.5), marginTop: space(1) },
  untriedItem: { ...type.small, color: colors.muted, lineHeight: 20 },

  wrongPanel: {
    borderWidth: 1,
    borderColor: colors.ink,
    borderRadius: radius.card,
    padding: space(3),
    gap: space(1.5),
  },
  wrongLabel: { ...type.label, color: colors.ink },
  wrongLede: { ...type.body, color: colors.ink, lineHeight: 23 },
  lesson: { gap: space(0.25) },
  lessonHead: { ...type.small, color: colors.ink, fontWeight: '700' },
  lessonText: { ...type.small, color: colors.muted, lineHeight: 21 },

  restraintPanel: {
    backgroundColor: colors.ink,
    borderRadius: radius.card,
    padding: space(3),
    gap: space(1),
  },
  restraintEyebrow: { ...type.label, color: colors.brandSoft },
  restraintText: { fontSize: 18, lineHeight: 27, color: colors.paper },
});

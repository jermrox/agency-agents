import React from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { colors, dimensions, radius, space, type } from '../theme';
import { vitalsDay, isSample } from '../vitalsSampleData';
import BaselineStrip from '../components/BaselineStrip';

const D = dimensions.vitals;

/**
 * Vitals — the dimension detail screen, and the last of the five.
 *
 * Same spine as Restore, Nourish and Connect (answer, evidence, context,
 * action, restraint), so a reader who has learned one dimension screen has
 * learned this one. The middle is different because the claim is different.
 *
 * WHY THE EVIDENCE IS A SET OF BANDS AND NOT A LIST
 * Restore's evidence is a handful of readings that explain one bad night, so
 * a hairline list works. Vitals makes a positional claim about every signal
 * at once: where does each one sit inside *this person's* range. "60 bpm" is
 * not evidence of anything; "60, at the top of a band that runs 52 to 61" is.
 * So each vital is drawn against its own 30-day band with the usual value
 * ticked and today marked. Five strips, same scale logic, read in a column.
 *
 * WHY THE REFUSAL IS ON THE SCREEN
 * Vitals is where a wearable is most tempted to sound like a clinic. This
 * screen says, in the body and not in a footer, what it will not do: it does
 * not diagnose, it does not read one reading as an alarm, and it tells the
 * person where the export is so a worrying number can go to a clinician.
 *
 * Five treatments, so the hierarchy is legible before a word is read: a
 * tinted panel for the answer, strips on bare paper for the evidence, inline
 * notes for context, the one dark block for the action, and a ruled pair for
 * the restraint and the outcome.
 */
export default function VitalsScreen({ onBack, onOpenData, onOpenOutcomes }) {
  const watching = vitalsDay.vitals.filter((v) => v.watch);

  return (
    <ScrollView
      style={styles.page}
      contentContainerStyle={styles.content}
      accessibilityLabel="Vitals detail"
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
        <Text style={[styles.eyebrow, { color: D.hue }]}>VITALS</Text>
        <Text style={styles.date}>{vitalsDay.date}</Text>
      </View>

      {/* THE ANSWER — a sentence, not four numbers and a colour. */}
      <View style={[styles.answerPanel, { backgroundColor: D.tint }]}>
        <Text style={styles.answer}>{vitalsDay.answer}</Text>
        <Text style={[styles.confidence, { color: D.hue }]}>{vitalsDay.confidence}</Text>
        <Text style={styles.confidenceWhy}>{vitalsDay.confidenceWhy}</Text>
      </View>

      {/* EVIDENCE — each vital against the wearer's own band. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Against your own baseline</Text>
        <Text style={styles.sectionLede}>
          The band is your last thirty days, the tick is your usual, the dot is this
          morning. No population averages anywhere on this screen.
        </Text>
        <View>
          {vitalsDay.vitals.map((item, i) => (
            <BaselineStrip key={item.id} item={item} first={i === 0} />
          ))}
        </View>
        {watching.length ? (
          <Text style={styles.watchNote} accessibilityRole="text">
            {watching.length === 1
              ? `One signal is marked to watch: ${watching[0].label.toLowerCase()}. One reading at the edge of a band means little; three in a row is a pattern worth a look.`
              : `${watching.length} signals are marked to watch. One reading at the edge of a band means little; three in a row is a pattern worth a look.`}
          </Text>
        ) : null}
      </View>

      {/* CONTEXT — the part no sensor can read. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>What the Band could not see</Text>
        <Text style={styles.sectionLede}>
          A vital can move for reasons a sensor cannot read. These came from you and
          your connected sources, and they are why the answer above is cautious.
        </Text>
        <View style={styles.contextList}>
          {vitalsDay.context.map((c) => (
            <View
              key={c.id}
              style={styles.contextItem}
              accessible
              accessibilityRole="text"
              accessibilityLabel={`${c.text}. ${c.source}.`}
            >
              <Text style={styles.contextText}>{c.text}</Text>
              <Text style={styles.contextSource}>{c.source}</Text>
            </View>
          ))}
        </View>
      </View>

      {/* ACTION — one, not a menu. The only dark block on the screen. */}
      <View style={styles.actionPanel}>
        <Text style={styles.actionEyebrow}>TODAY</Text>
        <Text style={styles.actionText}>{vitalsDay.action.text}</Text>
        <Text style={styles.actionWhy}>{vitalsDay.action.why}</Text>
      </View>

      {/* RESTRAINT — said in the body, because this is the screen where a
          wearable is most tempted to sound like a clinic. */}
      <View style={styles.restraint}>
        <Text style={styles.restraintLabel}>What this screen will not do</Text>
        <Text style={styles.restraintText}>{vitalsDay.notClinical}</Text>
        {onOpenData ? (
          <Pressable
            onPress={onOpenData}
            accessibilityRole="button"
            accessibilityLabel="Open the Data screen to export your readings"
            accessibilityHint="Opens data and permissions, where the export lives"
            style={({ pressed }) => [styles.link, pressed && styles.pressed]}
          >
            <Text style={styles.linkText}>Export your readings for a clinician</Text>
          </Pressable>
        ) : null}
      </View>

      {/* THE LOOP CLOSING — the part competitors do not ship. */}
      <View style={styles.outcome}>
        <Text style={styles.outcomeLabel}>Did it work last time</Text>
        <Text style={styles.outcomeText}>{vitalsDay.lastOutcome.text}</Text>
        <Text style={styles.outcomeWhen}>{vitalsDay.lastOutcome.when}</Text>
        {onOpenOutcomes ? (
          <Pressable
            onPress={onOpenOutcomes}
            accessibilityRole="button"
            accessibilityLabel="See every suggestion and whether it worked"
            accessibilityHint="Opens the outcome record, including the suggestions that missed"
            style={({ pressed }) => [styles.link, pressed && styles.pressed]}
          >
            <Text style={styles.linkText}>See every suggestion and whether it worked</Text>
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
  date: { ...type.display, color: colors.ink },

  answerPanel: { borderRadius: radius.card, padding: space(3), gap: space(1.5) },
  answer: { fontSize: 22, lineHeight: 31, color: colors.ink, fontWeight: '500' },
  confidence: { ...type.label },
  confidenceWhy: { ...type.small, color: colors.muted },

  section: { gap: space(1) },
  sectionTitle: { ...type.title, color: colors.ink },
  sectionLede: { ...type.small, color: colors.muted, marginBottom: space(1) },
  watchNote: { ...type.small, color: colors.muted, marginTop: space(1) },

  contextList: { gap: space(1.5) },
  contextItem: { gap: 2 },
  contextText: { ...type.body, color: colors.ink },
  contextSource: { ...type.small, color: colors.faint },

  actionPanel: { backgroundColor: colors.ink, borderRadius: radius.card, padding: space(3), gap: space(1) },
  actionEyebrow: { ...type.label, color: colors.brandSoft },
  actionText: { fontSize: 24, lineHeight: 32, color: colors.paper, fontWeight: '600' },
  actionWhy: { ...type.small, color: '#C9D2D8', lineHeight: 21 },

  restraint: {
    borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border,
    paddingTop: space(2), gap: space(0.5),
  },
  restraintLabel: { ...type.label, color: colors.muted },
  restraintText: { ...type.body, color: colors.ink },

  outcome: {
    borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border,
    paddingTop: space(2), gap: space(0.5),
  },
  outcomeLabel: { ...type.label, color: colors.brand },
  outcomeText: { ...type.body, color: colors.ink },
  outcomeWhen: { ...type.small, color: colors.faint },

  link: { alignSelf: 'flex-start', paddingVertical: space(1), marginTop: space(0.5) },
  linkText: { ...type.body, color: colors.brand, fontWeight: '600' },
});

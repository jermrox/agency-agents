import React, { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { colors, radius, space, type } from '../theme';
import {
  corrections,
  isSample,
  original,
  restraint,
  whatWouldMoveIt,
} from '../correctionSampleData';
import RevisionDiff, {
  KIND_WORD,
  inferredMovedOf,
  kindOf,
  movedOf,
} from '../components/RevisionDiff';

/**
 * Follow-up — what happens when you tell Vybe it is wrong.
 *
 * `AskScreen` is the front door: a question in, an answer out with its basis
 * and its blind spots. This is the half that comes after, and almost nothing
 * in this category ships it. The person usually knows something the sensor
 * does not, and the moment they say so is the moment a health assistant is
 * either useful or finished.
 *
 * THE DECISION THAT MAKES THIS SCREEN
 * Vybe does not simply accept the correction. It shows which parts of its
 * reasoning moved and which parts are still standing, and for one of the three
 * corrections here the honest outcome is that nothing moves at all. A product
 * that folds every time it is contradicted will cheerfully confirm whatever
 * the person already believed, and still sound certain doing it. That is worse
 * than ignoring them, because it is wrong in the direction they will not check.
 *
 * AND THE SECOND ONE: the part that gets overturned was labelled a guess
 * before anybody complained. Every line of the basis says whether it was
 * measured or inferred, on the first screen, unprompted — so when the
 * correction lands, the reader can see that Vybe doubted that line first.
 *
 * NOTHING HERE IS A STORED VERDICT. Which of the three things a correction did,
 * how many pieces of reasoning it moved, and how many of those were guesses are
 * all computed at render from the effects in the sample module. A label typed
 * into the data could read "this changed the answer" above an answer identical
 * to the one it replaced.
 *
 * Five treatments, so the hierarchy reads before the words: what Vybe said in a
 * quiet panel, the things you could say back as a plain chooser, the revised
 * answer as the one tinted panel, what moved as an annotated list, and the
 * closing restraint as the only dark block.
 */
export default function FollowUpScreen({ onBack }) {
  const [selectedId, setSelectedId] = useState(null);
  const correction = corrections.find((c) => c.id === selectedId) || null;

  // Derived, never typed.
  const kind = correction ? kindOf(correction, original) : null;
  const moved = movedOf(correction);
  const inferredMoved = inferredMovedOf(correction, original.basis);
  const closed = correction
    ? original.unseen.filter((u) => correction.closes.includes(u.id))
    : [];
  const stillUnseen = correction
    ? original.unseen.filter((u) => !correction.closes.includes(u.id))
    : original.unseen;

  return (
    <ScrollView
      style={styles.page}
      contentContainerStyle={styles.content}
      accessibilityLabel="Follow-up"
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
        <Text style={styles.eyebrow}>FOLLOW-UP</Text>
        <Text style={styles.question}>{original.question}</Text>
      </View>

      {/* WHAT VYBE SAID — quiet, because it is the thing about to be argued
          with rather than the answer the screen is delivering. */}
      <View style={styles.saidPanel}>
        <Text style={styles.saidLabel}>WHAT VYBE SAID</Text>
        <Text style={styles.saidText}>{original.answer}</Text>
        <Text style={styles.saidConfidence}>
          {original.confidence} — {original.confidenceWhy}
        </Text>
      </View>

      {/* THE CHOOSER — three things a person might actually say back. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Tell it what it missed</Text>
        <View>
          {corrections.map((c, i) => {
            const on = c.id === selectedId;
            return (
              <Pressable
                key={c.id}
                onPress={() => setSelectedId(on ? null : c.id)}
                accessibilityRole="button"
                accessibilityState={{ selected: on }}
                accessibilityLabel={c.text}
                accessibilityHint={
                  on
                    ? 'Clears this correction and shows the original answer again'
                    : "Applies this correction and shows what it moves in Vybe's reasoning"
                }
                style={({ pressed }) => [
                  styles.choice,
                  i > 0 && styles.ruled,
                  pressed && styles.pressed,
                ]}
              >
                <Text style={[styles.choiceMark, on && styles.choiceMarkOn]}>
                  {on ? 'Saying this' : 'Say this'}
                </Text>
                <Text style={[styles.choiceText, on && styles.choiceTextOn]}>{c.text}</Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      {/* THE REVISED ANSWER — the one tinted panel, and the kind of change is
          computed from what actually moved rather than announced. */}
      <View style={[styles.answerPanel, !correction && styles.answerPanelIdle]}>
        {correction ? (
          <>
            <Text style={styles.answerKind}>{KIND_WORD[kind]}</Text>
            <Text style={styles.answerText}>{correction.revised.answer}</Text>
            <Text style={styles.answerConfidence}>
              {correction.revised.confidence} — {correction.revised.confidenceWhy}
            </Text>
            <Text style={styles.answerNote}>{correction.note}</Text>
          </>
        ) : (
          <Text style={styles.answerIdleText}>
            Pick one above to see what it would move.
          </Text>
        )}
      </View>

      {/* WHAT MOVED — the annotated basis, and the screen's centrepiece. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>
          {correction ? 'What that moved' : 'What the answer rests on'}
        </Text>
        <Text style={styles.sectionLede}>
          {correction
            ? `${moved.length} of ${original.basis.length} parts moved`
              + (inferredMoved.length > 0
                ? `, and ${inferredMoved.length === moved.length ? 'all' : inferredMoved.length} of ${
                    moved.length === 1 ? 'it' : 'them'
                  } ${inferredMoved.length === 1 ? 'was' : 'were'} something Vybe had already marked as a guess.`
                : '. None of them was a guess — the correction landed on something measured, which is the harder case.')
            : 'Each line says whether it was measured or inferred. The inferred one is the line Vybe expects to be wrong.'}
        </Text>
        <RevisionDiff
          basis={original.basis}
          correction={correction}
          added={correction ? correction.added : []}
        />
      </View>

      {/* BLIND SPOTS — a correction can close one, and the screen keeps the
          rest on the page rather than quietly dropping the list. */}
      <View style={styles.unseenBlock}>
        <Text style={styles.ruleLabel}>
          {closed.length > 0
            ? `${closed.length} blind spot closed, ${stillUnseen.length} still open`
            : `${stillUnseen.length} things Vybe still cannot see`}
        </Text>
        {closed.map((u) => (
          <Text key={u.id} style={styles.unseenClosed}>
            {u.label} — ruled out
          </Text>
        ))}
        {stillUnseen.map((u) => (
          <Text key={u.id} style={styles.unseenItem}>
            {u.label}
          </Text>
        ))}
      </View>

      {/* WHAT WOULD ACTUALLY MOVE IT — so the honest "nothing changed" case
          still ends with something to do. */}
      <View style={styles.moveBlock}>
        <Text style={styles.ruleLabel}>What would move the reading</Text>
        <Text style={styles.ruleText}>{whatWouldMoveIt}</Text>
      </View>

      {/* THE RESTRAINT — the only dark block, and the last word. */}
      <View style={styles.restraintPanel}>
        <Text style={styles.restraintEyebrow}>WHAT VYBE WILL NOT DO</Text>
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
  question: { fontSize: 30, lineHeight: 38, color: colors.ink, fontWeight: '500' },

  // Deliberately the quietest panel on the screen: this is the claim under
  // review, not the screen's answer.
  saidPanel: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    padding: space(2.5),
    gap: space(1),
  },
  saidLabel: { ...type.label, color: colors.faint },
  saidText: { ...type.body, color: colors.muted, lineHeight: 24 },
  saidConfidence: { ...type.small, color: colors.faint, lineHeight: 19 },

  section: { gap: space(1) },
  sectionTitle: { ...type.title, color: colors.ink },
  sectionLede: { ...type.small, color: colors.muted, lineHeight: 20 },

  choice: { flexDirection: 'row', alignItems: 'flex-start', gap: space(2), paddingVertical: space(2) },
  ruled: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },
  choiceMark: { ...type.small, color: colors.faint, fontWeight: '700', width: space(13) },
  choiceMarkOn: { color: colors.brand },
  choiceText: { ...type.body, color: colors.muted, flex: 1, lineHeight: 23 },
  choiceTextOn: { color: colors.ink, fontWeight: '600' },

  answerPanel: {
    backgroundColor: colors.brandSoft,
    borderRadius: radius.card,
    padding: space(3),
    gap: space(1.5),
    minHeight: 120,
    justifyContent: 'center',
  },
  answerPanelIdle: { backgroundColor: colors.surface },
  answerKind: { ...type.label, color: colors.deep },
  answerText: { fontSize: 20, lineHeight: 29, color: colors.ink, fontWeight: '500' },
  answerConfidence: { ...type.small, color: colors.deep, lineHeight: 19 },
  answerNote: { ...type.small, color: colors.deep, lineHeight: 20, fontWeight: '600' },
  answerIdleText: { ...type.small, color: colors.faint },

  unseenBlock: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
    paddingTop: space(2),
    gap: space(0.5),
  },
  ruleLabel: { ...type.label, color: colors.faint },
  ruleText: { ...type.body, color: colors.ink, lineHeight: 23 },
  unseenClosed: {
    ...type.small,
    color: colors.muted,
    lineHeight: 21,
    textDecorationLine: 'line-through',
  },
  unseenItem: { ...type.small, color: colors.muted, lineHeight: 21 },

  moveBlock: { gap: space(0.5) },

  restraintPanel: {
    backgroundColor: colors.ink,
    borderRadius: radius.card,
    padding: space(3),
    gap: space(1),
  },
  restraintEyebrow: { ...type.label, color: colors.brandSoft },
  restraintText: { fontSize: 18, lineHeight: 27, color: colors.paper },
});

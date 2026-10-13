import React from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { colors, dimensions, radius, space, type } from '../theme';
import { isSample, receipt } from '../receiptsSampleData';

const D = dimensions.restore;

/**
 * Receipts — the working behind one Ask answer.
 *
 * Ask gives a sentence and shows its basis in four lines. This is the page
 * behind those four lines: every night the answer rests on, the baseline it
 * was compared to, the rung of the confidence ladder it sits on, and the gaps
 * it admitted. A person who wants to argue with an answer argues here.
 *
 * Reading order: the answer, restated -> the ladder -> the nights -> the
 * baseline -> what was not seen -> where it came from -> the challenge.
 *
 * Deliberately NOT a chart. Seven nights is a list you can read; a bar chart
 * of seven bars hides the two things that matter most, which are the dates
 * and the missing night. The late nights are marked with a word, "late",
 * and a tint, so the pattern survives being read aloud.
 */
export default function ReceiptsScreen({ onBack, onChallenge }) {
  const rungIndex = receipt.ladder.indexOf(receipt.rung);
  return (
    <ScrollView
      style={styles.page}
      contentContainerStyle={styles.content}
      accessibilityLabel="The receipts behind this answer"
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
          accessibilityLabel="Back to Ask"
          accessibilityHint="Returns to the conversation"
          style={({ pressed }) => [styles.back, pressed && styles.pressed]}
        >
          <Text style={styles.backText}>Ask</Text>
        </Pressable>
        <Text style={[styles.eyebrow, { color: D.hue }]}>RECEIPTS</Text>
        <Text style={styles.question}>{receipt.question}</Text>
      </View>

      {/* THE ANSWER, restated — so the receipt never floats free of its claim. */}
      <View style={[styles.answerPanel, { backgroundColor: D.tint }]}>
        <Text style={styles.answer}>{receipt.answer}</Text>
      </View>

      {/* THE LADDER — the rung is named in words; the tint only echoes it. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>How sure Vybe is</Text>
        <View
          style={styles.ladder}
          accessible
          accessibilityRole="text"
          accessibilityLabel={`Confidence ladder: ${receipt.ladder.join(', ')}. This answer is ${receipt.rung}.`}
        >
          {receipt.ladder.map((rung, i) => {
            const here = i === rungIndex;
            return (
              <View key={rung} style={[styles.rung, here && { borderColor: D.hue, backgroundColor: D.tint }]}>
                <Text style={[styles.rungText, here && styles.rungHere]}>
                  {rung}{here ? ' — this answer' : ''}
                </Text>
              </View>
            );
          })}
        </View>
        <Text style={styles.sectionLede}>{receipt.rungWhy}</Text>
      </View>

      {/* THE NIGHTS — a hairline list, one row per night, the missing one included. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Night by night</Text>
        <Text style={styles.sectionLede}>Bedtime, deep sleep and overnight HRV against your 30-night baseline.</Text>
        <View>
          {receipt.nights.map((n, i) => (
            <View
              key={n.id}
              style={[styles.night, i > 0 && styles.ruled, n.late === true && { backgroundColor: D.tint }]}
              accessible
              accessibilityRole="text"
              accessibilityLabel={`${n.date}. Bedtime ${n.bedtime}. Deep sleep ${n.deep}. HRV ${n.hrv} against baseline. ${n.note}.`}
            >
              <View style={styles.nightLeft}>
                <Text style={styles.nightDate}>{n.date}</Text>
                <Text style={[styles.nightNote, n.late === true && { color: colors.ink }]}>
                  {n.late === true ? 'late · ' : ''}{n.note}
                </Text>
              </View>
              <View style={styles.nightRight}>
                <Text style={styles.nightValue}>{n.bedtime}</Text>
                <Text style={styles.nightValue}>{n.deep}</Text>
                <Text style={styles.nightValue}>{n.hrv}</Text>
              </View>
            </View>
          ))}
        </View>
        <View style={styles.legendRow} aria-hidden>
          <Text style={styles.legend}>bedtime · deep sleep · HRV vs baseline</Text>
        </View>
      </View>

      {/* THE BASELINE — the thing every row above is measured against. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Against your baseline</Text>
        {receipt.baseline.map((b, i) => (
          <View
            key={b.id}
            style={[styles.baseRow, i > 0 && styles.ruled]}
            accessible
            accessibilityRole="text"
            accessibilityLabel={`${b.label} baseline ${b.value}, ${b.basis}.`}
          >
            <View style={styles.baseLeft}>
              <Text style={styles.baseLabel}>{b.label}</Text>
              <Text style={styles.baseBasis}>{b.basis}</Text>
            </View>
            <Text style={styles.baseValue}>{b.value}</Text>
          </View>
        ))}
      </View>

      {/* WHAT WAS NOT SEEN — the part competitors leave off the receipt. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>What the Band could not see</Text>
        <View style={styles.unseenList}>
          {receipt.unseen.map((u, i) => (
            <Text key={i} style={styles.unseenText} accessibilityRole="text">
              {u}
            </Text>
          ))}
        </View>
      </View>

      {/* SOURCES — inline notes, not cards. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Where this came from</Text>
        {receipt.sources.map((s) => (
          <View key={s.id} style={styles.source} accessible accessibilityRole="text" accessibilityLabel={`${s.name}: ${s.what}.`}>
            <Text style={styles.sourceName}>{s.name}</Text>
            <Text style={styles.sourceWhat}>{s.what}</Text>
          </View>
        ))}
      </View>

      {/* THE CHALLENGE — the one dark block, and the only action on the page. */}
      <View style={styles.challengePanel}>
        <Text style={styles.challengeEyebrow}>DISAGREE?</Text>
        <Text style={styles.challengeText}>{receipt.challenge}</Text>
        {onChallenge ? (
          <Pressable
            onPress={onChallenge}
            accessibilityRole="button"
            accessibilityLabel="Tell Vybe a night is wrong"
            accessibilityHint="Opens the follow-up, where a correction shows which parts of the answer it moves"
            style={({ pressed }) => [styles.challengeButton, pressed && styles.pressed]}
          >
            <Text style={styles.challengeButtonText}>Tell Vybe what it missed</Text>
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
  question: { ...type.title, color: colors.ink },

  answerPanel: { borderRadius: radius.card, padding: space(3) },
  answer: { fontSize: 20, lineHeight: 28, color: colors.ink, fontWeight: '500' },

  section: { gap: space(1) },
  sectionTitle: { ...type.title, color: colors.ink },
  sectionLede: { ...type.small, color: colors.muted },

  // The ladder is one row of four rungs; the current rung is outlined and
  // named, never only tinted.
  ladder: { flexDirection: 'row', flexWrap: 'wrap', gap: space(1), marginTop: space(0.5) },
  rung: { borderWidth: 1, borderColor: colors.border, borderRadius: radius.pill, paddingVertical: space(0.75), paddingHorizontal: space(1.5) },
  rungText: { ...type.small, color: colors.muted },
  rungHere: { color: colors.ink, fontWeight: '600' },

  // Nights: hairline rows. Numbers are tabular so the three columns line up.
  night: { flexDirection: 'row', alignItems: 'center', paddingVertical: space(1.5), paddingHorizontal: space(1), gap: space(2), borderRadius: 8 },
  ruled: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },
  nightLeft: { flex: 1, gap: 2 },
  nightDate: { ...type.body, color: colors.ink, fontWeight: '600' },
  nightNote: { ...type.small, color: colors.muted },
  nightRight: { flexDirection: 'row', gap: space(2) },
  nightValue: { ...type.body, color: colors.ink, fontVariant: ['tabular-nums'], minWidth: 52, textAlign: 'right' },
  legendRow: { alignItems: 'flex-end' },
  legend: { ...type.small, color: colors.faint },

  baseRow: { flexDirection: 'row', alignItems: 'flex-start', paddingVertical: space(1.5), gap: space(2) },
  baseLeft: { flex: 1, gap: 2 },
  baseLabel: { ...type.body, color: colors.ink, fontWeight: '600' },
  baseBasis: { ...type.small, color: colors.muted },
  baseValue: { ...type.title, color: colors.ink, fontVariant: ['tabular-nums'] },

  unseenList: { gap: space(1.5) },
  unseenText: { ...type.body, color: colors.ink },

  source: { gap: 2, paddingVertical: space(0.5) },
  sourceName: { ...type.body, color: colors.ink, fontWeight: '600' },
  sourceWhat: { ...type.small, color: colors.muted },

  challengePanel: { backgroundColor: colors.ink, borderRadius: radius.card, padding: space(3), gap: space(1) },
  challengeEyebrow: { ...type.label, color: colors.brandSoft },
  challengeText: { fontSize: 20, lineHeight: 28, color: colors.paper, fontWeight: '600' },
  challengeButton: { alignSelf: 'flex-start', marginTop: space(1), paddingVertical: space(1), paddingHorizontal: space(2), borderRadius: radius.pill, backgroundColor: colors.brandBright },
  challengeButtonText: { ...type.body, color: colors.deep, fontWeight: '600' },
});

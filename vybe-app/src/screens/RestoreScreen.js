import React from 'react';
import { ScrollView, StyleSheet, Text, View, Pressable } from 'react-native';
import { colors, dimensions, radius, space, type } from '../theme';
import { restoreDay, isSample } from '../restoreSampleData';
import EvidenceRow from '../components/EvidenceRow';

const D = dimensions.restore;

/**
 * Restore — the dimension detail screen.
 *
 * Reading order is the product's loop, top to bottom:
 *   Answer -> Evidence -> Context -> Action -> Outcome
 * The answer comes first because that is the whole premise: everyone else
 * opens on a score and leaves the interpreting to you.
 *
 * Deliberately NOT a stack of identical rounded cards. The answer is a tinted
 * panel, the evidence is a hairline list, the context is inline notes, and the
 * action is the one dark block on the screen — four different treatments, so
 * the hierarchy is legible before a single word is read.
 */
export default function RestoreScreen({ onBack }) {
  return (
    <ScrollView
      style={styles.page}
      contentContainerStyle={styles.content}
      accessibilityLabel="Restore detail"
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
        <Text style={[styles.eyebrow, { color: D.hue }]}>RESTORE</Text>
        <Text style={styles.date}>{restoreDay.date}</Text>
      </View>

      {/* THE ANSWER — a sentence, not a score. */}
      <View style={[styles.answerPanel, { backgroundColor: D.tint }]}>
        <Text style={styles.answer}>{restoreDay.answer}</Text>
        <View style={styles.confidenceRow}>
          <Text style={[styles.confidence, { color: D.hue }]}>{restoreDay.confidence}</Text>
        </View>
        <Text style={styles.confidenceWhy}>{restoreDay.confidenceWhy}</Text>
      </View>

      {/* EVIDENCE */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>What the Band saw</Text>
        <View>
          {restoreDay.evidence.map((item, i) => (
            <EvidenceRow key={item.id} item={item} first={i === 0} />
          ))}
        </View>
      </View>

      {/* CONTEXT — the part no sensor can read. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>What the Band could not see</Text>
        <Text style={styles.sectionLede}>
          A biomarker can change without a wearable knowing why. These came from you
          and your connected sources.
        </Text>
        <View style={styles.contextList}>
          {restoreDay.context.map((c) => (
            <View key={c.id} style={styles.contextItem} accessible accessibilityRole="text"
                  accessibilityLabel={`${c.text}. ${c.source}.`}>
              <Text style={styles.contextText}>{c.text}</Text>
              <Text style={styles.contextSource}>{c.source}</Text>
            </View>
          ))}
        </View>
      </View>

      {/* ACTION — one, not a menu. The only dark block on the screen. */}
      <View style={styles.actionPanel}>
        <Text style={styles.actionEyebrow}>TONIGHT</Text>
        <Text style={styles.actionText}>{restoreDay.action.text}</Text>
        <Text style={styles.actionWhy}>{restoreDay.action.why}</Text>
      </View>

      {/* THE LOOP CLOSING — the part competitors do not ship. */}
      <View style={styles.outcome}>
        <Text style={styles.outcomeLabel}>Did it work last time</Text>
        <Text style={styles.outcomeText}>{restoreDay.lastOutcome.text}</Text>
        <Text style={styles.outcomeWhen}>{restoreDay.lastOutcome.when}</Text>
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
  confidenceRow: { flexDirection: 'row' },
  confidence: { ...type.label },
  confidenceWhy: { ...type.small, color: colors.muted },

  section: { gap: space(1) },
  sectionTitle: { ...type.title, color: colors.ink },
  sectionLede: { ...type.small, color: colors.muted, marginBottom: space(1) },

  contextList: { gap: space(1.5) },
  contextItem: { gap: 2 },
  contextText: { ...type.body, color: colors.ink },
  contextSource: { ...type.small, color: colors.faint },

  actionPanel: { backgroundColor: colors.ink, borderRadius: radius.card, padding: space(3), gap: space(1) },
  actionEyebrow: { ...type.label, color: colors.brandSoft },
  actionText: { fontSize: 24, lineHeight: 32, color: colors.paper, fontWeight: '600' },
  actionWhy: { ...type.small, color: '#C9D2D8', lineHeight: 21 },

  outcome: {
    borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border,
    paddingTop: space(2), gap: space(0.5),
  },
  outcomeLabel: { ...type.label, color: colors.brand },
  outcomeText: { ...type.body, color: colors.ink },
  outcomeWhen: { ...type.small, color: colors.faint },
});

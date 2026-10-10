import React, { useMemo, useRef, useState } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { colors, dimensions, radius, space, type } from '../theme';
import { answers, isSample, noAnswer, opening } from '../askSampleData';

/**
 * Ask — the product's front door.
 *
 * Everyone else opens on a dashboard and leaves you to interpret it. Vybe
 * opens on a question, so this screen is the thesis: you ask in your own
 * words, and the answer arrives with its working shown.
 *
 * An answer here is never a paragraph. It is four parts, in this order:
 *   Answer -> What it rests on -> What Vybe could not see -> One action
 * The third part is the one competitors omit. A confident sentence with no
 * stated blind spots is how a wellness product starts sounding like a doctor.
 *
 * Deliberately NOT chat bubbles. Bubbles say "two people talking, both
 * equally sure". These are a question and a piece of reasoning, so they get
 * different registers: the question is a quiet label and a line of ink, the
 * answer is a tinted panel, the basis is a hairline list, the action is the
 * one dark block. Four treatments, so the hierarchy reads before the words do.
 */

/**
 * Deliberately dumb matching. A real build routes the question to a model;
 * this one recognises three worked examples and is honest about the rest,
 * because inventing a reading to fill a gap is the failure the product is
 * built against.
 */
const KEYWORDS = {
  tired: ['tired', 'exhausted', 'fatigue', 'no energy'],
  train: ['train', 'workout', 'session', 'run hard', 'lift'],
  apnea: ['apnea', 'apnoea', 'snor', 'diagnos'],
};

function findAnswer(text) {
  const q = text.trim().toLowerCase();
  if (!q) return null;
  const hit = answers.find((a) => {
    if (a.question.toLowerCase().replace(/[?.]/g, '') === q.replace(/[?.]/g, '')) return true;
    return (KEYWORDS[a.id] || []).some((k) => q.includes(k));
  });
  return hit || { ...noAnswer, id: `unknown-${q}`, question: text.trim() };
}

/** A dimension's name, with its hue as a dot beside it — never the hue alone. */
function DimensionTag({ dimensionKey }) {
  const d = dimensions[dimensionKey];
  if (!d) return null;
  return (
    <View style={styles.tag} accessible accessibilityRole="text" accessibilityLabel={`Drew on ${d.label}`}>
      <View aria-hidden style={[styles.tagDot, { backgroundColor: d.hue }]} />
      <Text style={styles.tagLabel}>{d.label}</Text>
    </View>
  );
}

/** One signal the answer rests on. A hairline row, not a card. */
function BasisRow({ item, first }) {
  return (
    <View
      style={[styles.basisRow, !first && styles.ruled]}
      accessible
      accessibilityRole="text"
      accessibilityLabel={`${item.signal}. ${item.detail}. Source: ${item.source}.`}
    >
      <Text style={styles.basisSignal}>{item.signal}</Text>
      <Text style={styles.basisDetail}>{item.detail}</Text>
      <Text style={styles.basisSource}>{item.source}</Text>
    </View>
  );
}

function Exchange({ entry }) {
  // The tint comes from the first dimension the answer drew on, which keeps
  // the conversation speaking the same colour language as the detail screens.
  const tint = entry.dimensions ? dimensions[entry.dimensions[0]].tint : colors.paper;

  return (
    <View style={styles.exchange}>
      <View style={styles.questionBlock}>
        <Text style={styles.questionLabel}>YOU ASKED</Text>
        <Text style={styles.questionText}>{entry.question}</Text>
      </View>

      {entry.kind === 'answer' ? (
        <View style={[styles.answerPanel, { backgroundColor: tint }]}>
          <Text style={styles.answerText}>{entry.answer}</Text>
          <Text style={styles.confidence}>{entry.confidence}</Text>
          <Text style={styles.confidenceWhy}>{entry.confidenceWhy}</Text>
        </View>
      ) : null}

      {entry.kind === 'boundary' ? (
        // The one outlined block on the screen. The label says what the
        // outline means, so the treatment is never carrying it alone.
        <View style={styles.boundaryPanel}>
          <Text style={styles.boundaryLabel}>OUTSIDE WHAT VYBE DOES</Text>
          <Text style={styles.answerText}>{entry.answer}</Text>
          <Text style={styles.boundaryInstead}>{entry.instead}</Text>
        </View>
      ) : null}

      {entry.kind === 'unknown' ? (
        <View style={styles.unknownBlock}>
          <Text style={styles.unknownText}>{entry.answer}</Text>
          <Text style={styles.unknownDetail}>{entry.detail}</Text>
        </View>
      ) : null}

      {entry.dimensions ? (
        <View style={styles.tagRow}>
          {entry.dimensions.map((k) => (
            <DimensionTag key={k} dimensionKey={k} />
          ))}
        </View>
      ) : null}

      {entry.basis ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>What this rests on</Text>
          <View>
            {entry.basis.map((b, i) => (
              <BasisRow key={b.id} item={b} first={i === 0} />
            ))}
          </View>
        </View>
      ) : null}

      {entry.unseen ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>What Vybe could not see</Text>
          <View style={styles.unseenList}>
            {entry.unseen.map((u) => (
              <Text key={u} style={styles.unseenItem}>
                {u}
              </Text>
            ))}
          </View>
        </View>
      ) : null}

      {entry.action ? (
        <View style={styles.actionPanel}>
          <Text style={styles.actionEyebrow}>{entry.action.when}</Text>
          <Text style={styles.actionText}>{entry.action.text}</Text>
          <Text style={styles.actionWhy}>{entry.action.why}</Text>
        </View>
      ) : null}

      {entry.handoff ? (
        <View style={styles.handoff}>
          <Text style={styles.handoffLabel}>What to do with it</Text>
          <Text style={styles.handoffText}>{entry.handoff}</Text>
        </View>
      ) : null}
    </View>
  );
}

export default function AskScreen({ onBack, onFollowUp }) {
  const [entries, setEntries] = useState([]);
  const [draft, setDraft] = useState('');
  const scroller = useRef(null);

  // Suggestions drop off the list once asked, so the screen stops offering
  // something already on the page.
  const asked = entries.map((e) => e.id);
  const remaining = useMemo(() => answers.filter((a) => !asked.includes(a.id)), [asked.join()]);

  function ask(text) {
    const found = findAnswer(text);
    if (!found) return;
    setEntries((prev) => [...prev, found]);
    setDraft('');
  }

  return (
    <View style={styles.page}>
      <View style={styles.header}>
        {isSample ? (
          <View style={styles.sampleBar}>
            <Text style={styles.sampleText}>Sample data — these are not your readings.</Text>
          </View>
        ) : null}
        <Pressable
          onPress={onBack}
          accessibilityRole="button"
          accessibilityLabel="Back to today"
          accessibilityHint="Returns to the home screen"
          style={({ pressed }) => [styles.back, pressed && styles.pressed]}
        >
          <Text style={styles.backText}>Today</Text>
        </Pressable>
        <Text style={styles.eyebrow}>ASK</Text>
      </View>

      <ScrollView
        ref={scroller}
        style={styles.scroll}
        contentContainerStyle={styles.content}
        accessibilityLabel="Conversation with Vybe"
        keyboardDismissMode="on-drag"
        onContentSizeChange={() => {
          if (entries.length) scroller.current?.scrollToEnd({ animated: true });
        }}
      >
        {entries.length === 0 ? (
          <View style={styles.openingBlock}>
            <Text style={styles.openingLede}>{opening.lede}</Text>
          </View>
        ) : null}

        {entries.map((entry, i) => (
          <Exchange key={`${entry.id}-${i}`} entry={entry} />
        ))}

        {/* The follow-up is the other half of asking, and it only has a job
            once an answer is on screen: the person who disagrees with one is
            the person who has just read it. */}
        {entries.length && onFollowUp ? (
          <Pressable
            onPress={onFollowUp}
            accessibilityRole="button"
            accessibilityLabel="Tell Vybe it got something wrong"
            accessibilityHint="Opens the follow-up, where a correction shows which parts of the answer it moves"
            style={({ pressed }) => [styles.followUp, pressed && styles.pressed]}
          >
            <Text style={styles.followUpText}>That&rsquo;s not right &mdash; tell Vybe what it missed</Text>
          </Pressable>
        ) : null}

        {remaining.length ? (
          <View style={styles.suggestions}>
            <Text style={styles.suggestionsLabel}>{opening.prompt}</Text>
            {remaining.map((a) => (
              <Pressable
                key={a.id}
                onPress={() => ask(a.question)}
                accessibilityRole="button"
                accessibilityLabel={a.question}
                accessibilityHint="Asks this question and shows the answer with its evidence"
                style={({ pressed }) => [styles.suggestion, pressed && styles.pressed]}
              >
                <Text style={styles.suggestionText}>{a.question}</Text>
              </Pressable>
            ))}
          </View>
        ) : null}
      </ScrollView>

      {/* The composer stays put rather than scrolling with the transcript:
          the question box is the screen's purpose, not its last row. */}
      <View style={styles.composer}>
        <TextInput
          value={draft}
          onChangeText={setDraft}
          onSubmitEditing={() => ask(draft)}
          placeholder="Ask about your body"
          placeholderTextColor={colors.faint}
          returnKeyType="send"
          style={styles.input}
          accessibilityLabel="Your question"
          accessibilityHint="Type a question about your health, then send it"
        />
        <Pressable
          onPress={() => ask(draft)}
          disabled={!draft.trim()}
          accessibilityRole="button"
          accessibilityLabel="Send question"
          accessibilityState={{ disabled: !draft.trim() }}
          accessibilityHint="Sends what you typed and shows Vybe's answer"
          style={({ pressed }) => [
            styles.send,
            !draft.trim() && styles.sendOff,
            pressed && styles.pressed,
          ]}
        >
          <Text style={[styles.sendText, !draft.trim() && styles.sendTextOff]}>Ask</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: colors.paper },

  header: { paddingHorizontal: space(3), paddingTop: space(2), gap: space(0.5) },
  sampleBar: {
    backgroundColor: colors.brandSoft,
    borderRadius: radius.pill,
    paddingVertical: space(1),
    paddingHorizontal: space(2),
    alignSelf: 'flex-start',
    marginBottom: space(1),
  },
  sampleText: { ...type.small, color: colors.deep, fontWeight: '600' },
  back: { alignSelf: 'flex-start', paddingVertical: space(0.5), paddingRight: space(2) },
  backText: { ...type.small, color: colors.brand, fontWeight: '600' },
  pressed: { opacity: 0.6 },
  eyebrow: { ...type.label, color: colors.brand, marginTop: space(0.5) },

  scroll: { flex: 1 },
  content: { padding: space(3), paddingBottom: space(4), gap: space(4) },

  openingBlock: { gap: space(1) },
  openingLede: { fontSize: 22, lineHeight: 31, color: colors.ink, fontWeight: '500' },

  exchange: { gap: space(2.5) },

  questionBlock: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
    paddingTop: space(2),
    gap: space(0.5),
  },
  questionLabel: { ...type.label, color: colors.faint },
  questionText: { ...type.title, color: colors.ink },

  answerPanel: { borderRadius: radius.card, padding: space(3), gap: space(1) },
  answerText: { fontSize: 22, lineHeight: 31, color: colors.ink, fontWeight: '500' },
  confidence: { ...type.label, color: colors.muted, marginTop: space(0.5) },
  confidenceWhy: { ...type.small, color: colors.muted },

  followUp: { alignSelf: 'flex-start', paddingVertical: space(1.5) },
  followUpText: { ...type.body, color: colors.brand, fontWeight: '600' },

  boundaryPanel: {
    borderWidth: 1,
    borderColor: colors.ink,
    borderRadius: radius.card,
    padding: space(3),
    gap: space(1),
  },
  boundaryLabel: { ...type.label, color: colors.ink },
  boundaryInstead: { ...type.body, color: colors.muted, marginTop: space(0.5) },

  unknownBlock: {
    borderTopWidth: 2,
    borderTopColor: colors.border,
    paddingTop: space(2),
    gap: space(0.5),
  },
  unknownText: { ...type.title, color: colors.ink },
  unknownDetail: { ...type.small, color: colors.muted },

  tagRow: { flexDirection: 'row', flexWrap: 'wrap', gap: space(1) },
  tag: { flexDirection: 'row', alignItems: 'center', gap: space(0.75) },
  tagDot: { width: 8, height: 8, borderRadius: 4 },
  tagLabel: { ...type.small, color: colors.muted, fontWeight: '600' },

  section: { gap: space(1) },
  sectionTitle: { ...type.title, color: colors.ink },

  basisRow: { paddingVertical: space(1.5), gap: 2 },
  ruled: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },
  basisSignal: { ...type.body, color: colors.ink, fontWeight: '600' },
  basisDetail: { ...type.small, color: colors.muted },
  basisSource: { ...type.small, color: colors.faint },

  unseenList: { gap: space(1.5) },
  unseenItem: { ...type.body, color: colors.muted },

  actionPanel: { backgroundColor: colors.ink, borderRadius: radius.card, padding: space(3), gap: space(1) },
  actionEyebrow: { ...type.label, color: colors.brandSoft },
  actionText: { fontSize: 24, lineHeight: 32, color: colors.paper, fontWeight: '600' },
  actionWhy: { ...type.small, color: '#C9D2D8', lineHeight: 21 },

  handoff: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
    paddingTop: space(2),
    gap: space(0.5),
  },
  handoffLabel: { ...type.label, color: colors.brand },
  handoffText: { ...type.body, color: colors.ink },

  suggestions: { gap: space(1) },
  suggestionsLabel: { ...type.small, color: colors.faint, marginBottom: space(0.5) },
  suggestion: {
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    borderRadius: radius.pill,
    paddingVertical: space(1.5),
    paddingHorizontal: space(2.5),
    alignSelf: 'flex-start',
  },
  suggestionText: { ...type.body, color: colors.ink },

  composer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space(1.5),
    paddingHorizontal: space(3),
    paddingVertical: space(2),
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
    backgroundColor: colors.surface,
  },
  input: {
    flex: 1,
    ...type.body,
    color: colors.ink,
    backgroundColor: colors.paper,
    borderRadius: radius.pill,
    paddingVertical: space(1.5),
    paddingHorizontal: space(2.5),
  },
  send: {
    backgroundColor: colors.ink,
    borderRadius: radius.pill,
    paddingVertical: space(1.5),
    paddingHorizontal: space(2.5),
  },
  // Disabled is a lighter fill AND the label stays legible — the state is
  // also announced through accessibilityState, not left to the colour.
  sendOff: { backgroundColor: colors.border },
  sendText: { ...type.body, color: colors.paper, fontWeight: '600' },
  sendTextOff: { color: colors.muted },
});

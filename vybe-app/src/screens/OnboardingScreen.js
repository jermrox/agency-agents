import React, { useEffect, useRef, useState } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  View,
} from 'react-native';
import { colors, radius, space, type } from '../theme';
import {
  band,
  boundary,
  isSample,
  promises,
  readiness,
  sources as sampleSources,
  steps,
} from '../onboardingSampleData';

/**
 * First run — pairing, sources, consent.
 *
 * Four steps, in the only order that makes consent mean anything:
 *   Pair the Band -> choose sources -> see what you agreed to -> see what Vybe
 *   actually knows.
 *
 * Two decisions carry this screen.
 *
 * The first is that every source is described by the QUESTION it unlocks, not
 * by a data category. "Calendar" tells a person nothing; "was it the week, or
 * was it me?" tells them exactly what they are buying with the permission. The
 * Data screen already does disclosure — what each source hands over — so this
 * screen deliberately does the other axis. Nothing is pre-enabled: a ticked box
 * a person did not tick is not consent.
 *
 * The second is the last step. Every first-run flow ends on "you're all set",
 * which on day one is a lie — a band that has watched you for zero nights knows
 * nothing about you. So the final step says "Today: nothing yet" and lays out
 * what arrives at three nights, two weeks and six weeks. It is the only
 * expectation that survives contact with the product.
 *
 * Treatments, so the hierarchy reads before the words do: the pairing state is
 * oversized type on bare paper, the sources are a hairline list with switches,
 * the promises are plain statements under a rule, the claim boundary is the one
 * outlined block (the same treatment the Ask screen gives a refusal), and the
 * only dark block on the screen is the button that ends the flow.
 */

/**
 * Pairing is a state machine, not a spinner. Each state is named in words on
 * screen, because "a circle is moving" is not a status and a screen reader
 * cannot read a spinner.
 */
const SEARCH_MS = 1600;
const PAIR_MS = 1200;

const PAIR_STATUS = {
  idle: 'Not looking yet',
  searching: 'Looking for your Band…',
  found: 'Found it',
  pairing: 'Pairing…',
  paired: 'Paired',
};

export default function OnboardingScreen({ onFinish, onSkip, onImport }) {
  const [step, setStep] = useState(0);
  const [pair, setPair] = useState('idle');
  const [sources, setSources] = useState(sampleSources);
  const timers = useRef([]);

  // Timers outlive a screen that unmounts mid-search unless they are cleared,
  // and a setState after unmount is a warning at best and a leak at worst.
  useEffect(() => () => timers.current.forEach(clearTimeout), []);

  function later(fn, ms) {
    timers.current.push(setTimeout(fn, ms));
  }

  const toggle = (id) =>
    setSources((prev) => prev.map((s) => (s.id === id ? { ...s, on: !s.on } : s)));

  const chosen = sources.filter((s) => s.on);
  const last = step === steps.length - 1;

  return (
    <View style={styles.page}>
      <View style={styles.header}>
        {isSample ? (
          <View style={styles.sampleBar}>
            <Text style={styles.sampleText}>
              Sample data — no Band is really being paired.
            </Text>
          </View>
        ) : null}

        {/* Progress in words first. The segmented rule repeats it; on its own a
            row of bars is decoration, and the current step has to be readable
            by someone who cannot separate the tones. */}
        <Text style={styles.progress}>
          Step {step + 1} of {steps.length} · {steps[step].label}
        </Text>
        <View style={styles.track} aria-hidden>
          {steps.map((s, i) => (
            <View
              key={s.id}
              style={[styles.segment, i <= step ? styles.segmentDone : null]}
            />
          ))}
        </View>
      </View>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        accessibilityLabel={`Setting up Vybe. ${steps[step].label}.`}
      >
        {/* STEP 1 — PAIR */}
        {step === 0 ? (
          <View style={styles.section}>
            <Text style={styles.title}>Let’s find your Band.</Text>

            <View style={styles.statusBlock}>
              <Text
                style={styles.statusText}
                accessibilityLiveRegion="polite"
                accessible
                accessibilityRole="text"
                accessibilityLabel={`Pairing status: ${PAIR_STATUS[pair]}`}
              >
                {PAIR_STATUS[pair]}
              </Text>
              {pair === 'found' || pair === 'pairing' || pair === 'paired' ? (
                <Text style={styles.statusSub}>
                  {band.name} · {band.serial}
                </Text>
              ) : null}
            </View>

            {pair === 'idle' ? (
              <Pressable
                onPress={() => {
                  setPair('searching');
                  later(() => setPair('found'), SEARCH_MS);
                }}
                accessibilityRole="button"
                accessibilityLabel="Look for my Band"
                accessibilityHint="Searches over Bluetooth for a Band nearby"
                style={({ pressed }) => [styles.primary, pressed && styles.pressed]}
              >
                <Text style={styles.primaryText}>Look for my Band</Text>
              </Pressable>
            ) : null}

            {pair === 'found' ? (
              <Pressable
                onPress={() => {
                  setPair('pairing');
                  later(() => setPair('paired'), PAIR_MS);
                }}
                accessibilityRole="button"
                accessibilityLabel={`Pair with ${band.name}`}
                accessibilityHint="Connects this Band to your phone"
                style={({ pressed }) => [styles.primary, pressed && styles.pressed]}
              >
                <Text style={styles.primaryText}>Pair this Band</Text>
              </Pressable>
            ) : null}

            {/* The three physical things that decide whether a search works,
                shown BEFORE the failure rather than behind a "trouble
                connecting?" link that appears after it. */}
            {pair === 'idle' || pair === 'searching' ? (
              <View style={styles.helpBlock}>
                <Text style={styles.helpLabel}>What it needs</Text>
                {band.requirements.map((r) => (
                  <Text key={r} style={styles.helpItem}>
                    {r}
                  </Text>
                ))}
              </View>
            ) : null}

            <Text style={styles.aside}>{band.privacyLine}</Text>
          </View>
        ) : null}

        {/* STEP 2 — SOURCES */}
        {step === 1 ? (
          <View style={styles.section}>
            <Text style={styles.title}>What should Vybe be allowed to read?</Text>
            <Text style={styles.lede}>
              Everything here is off. Each one buys you an answer Vybe cannot give
              without it, and each says what it will never be used for.
            </Text>

            <View>
              {sources.map((s, i) => (
                <View key={s.id} style={[styles.sourceRow, i > 0 && styles.ruled]}>
                  <View style={styles.sourceMain}>
                    <Text style={styles.sourceName}>{s.name}</Text>
                    <Text style={styles.sourceUnlocks}>{s.unlocks}</Text>
                    <Text style={styles.sourceDetail}>{s.detail}</Text>
                    <Text style={styles.sourceNever}>{s.never}</Text>
                  </View>
                  <View style={styles.sourceControl}>
                    {/* The word is the state. The switch's position is a second
                        signal, never the only one. */}
                    <Text style={styles.sourceState}>{s.on ? 'On' : 'Off'}</Text>
                    <Switch
                      value={s.on}
                      onValueChange={() => toggle(s.id)}
                      accessibilityRole="switch"
                      accessibilityLabel={s.name}
                      accessibilityHint={`Lets Vybe answer: ${s.unlocks}`}
                      accessibilityState={{ checked: s.on }}
                      trackColor={{ false: colors.border, true: colors.brandSoft }}
                      thumbColor={s.on ? colors.brand : colors.surface}
                    />
                  </View>
                </View>
              ))}
            </View>

            <Text style={styles.aside}>
              None of these are required, and every one can be turned off later on
              the Data screen without losing the history you already have.
            </Text>

            {/* A source with years already in it is a different conversation
                from a source that starts empty, and it is the one that decides
                what Vybe can say on day one. */}
            {onImport ? (
              <Pressable
                onPress={onImport}
                accessibilityRole="button"
                accessibilityLabel="See what Vybe will do with your existing history"
                accessibilityHint="Shows which imported records Vybe will compute with, which it will only display, and which it will not take"
                style={({ pressed }) => [styles.importLink, pressed && styles.pressed]}
              >
                <Text style={styles.importLinkText}>
                  Already have years of data? See what Vybe will do with it
                </Text>
              </Pressable>
            ) : null}
          </View>
        ) : null}

        {/* STEP 3 — CONSENT, as a summary of choices already made */}
        {step === 2 ? (
          <View style={styles.section}>
            <Text style={styles.title}>Here is what you just agreed to.</Text>

            <View style={styles.summary}>
              <Text style={styles.summaryLabel}>Reading from</Text>
              <Text style={styles.summaryText}>
                {pair === 'paired' ? 'Your Vybe Band' : 'No Band yet'}
                {chosen.length
                  ? `, and ${chosen.map((s) => s.name.toLowerCase()).join(', ')}`
                  : ', and nothing else'}
                .
              </Text>
            </View>

            {promises.map((p) => (
              <View key={p.id} style={styles.promise}>
                <Text style={styles.promiseText}>{p.text}</Text>
                <Text style={styles.promiseDetail}>{p.detail}</Text>
              </View>
            ))}

            {/* The one outlined block. The label says what the outline means, so
                the treatment never carries it alone. */}
            <View style={styles.boundaryPanel}>
              <Text style={styles.boundaryLabel}>{boundary.label}</Text>
              <Text style={styles.boundaryText}>{boundary.text}</Text>
              <Text style={styles.boundaryDetail}>{boundary.detail}</Text>
            </View>
          </View>
        ) : null}

        {/* STEP 4 — WHAT VYBE ACTUALLY KNOWS */}
        {step === 3 ? (
          <View style={styles.section}>
            <Text style={styles.title}>What Vybe can tell you, and when.</Text>
            <Text style={styles.lede}>
              It has been watching you for no nights at all. That is worth saying
              out loud, because the alternative is an answer that is really about
              people in general.
            </Text>

            <View>
              {readiness.map((r, i) => (
                <View
                  key={r.id}
                  style={[styles.readyRow, i > 0 && styles.ruled]}
                  accessible
                  accessibilityRole="text"
                  accessibilityLabel={`${r.when}. ${r.what} ${r.detail}`}
                >
                  <Text style={styles.readyWhen}>{r.when}</Text>
                  <Text style={styles.readyWhat}>{r.what}</Text>
                  <Text style={styles.readyDetail}>{r.detail}</Text>
                </View>
              ))}
            </View>

            <View style={styles.finishPanel}>
              <Text style={styles.finishEyebrow}>WEAR IT TONIGHT</Text>
              <Text style={styles.finishText}>
                One night is enough for Vybe to start.
              </Text>
              <Text style={styles.finishWhy}>
                Put it on before bed. Tomorrow it will have something to say, and
                it will tell you how sure it is.
              </Text>
            </View>
          </View>
        ) : null}
      </ScrollView>

      {/* Navigation. "Set up later" is a real exit rather than a dark pattern:
          the Band step can be skipped, and the consequence is stated instead of
          hidden. */}
      <View style={styles.nav}>
        {step > 0 ? (
          <Pressable
            onPress={() => setStep((s) => s - 1)}
            accessibilityRole="button"
            accessibilityLabel="Back a step"
            accessibilityHint={`Returns to ${steps[Math.max(0, step - 1)].label}`}
            style={({ pressed }) => [styles.navBack, pressed && styles.pressed]}
          >
            <Text style={styles.navBackText}>Back</Text>
          </Pressable>
        ) : (
          <Pressable
            onPress={onSkip}
            accessibilityRole="button"
            accessibilityLabel="Set up later"
            accessibilityHint={band.skipLine}
            style={({ pressed }) => [styles.navBack, pressed && styles.pressed]}
          >
            <Text style={styles.navBackText}>Set up later</Text>
          </Pressable>
        )}

        <Pressable
          onPress={() => (last ? onFinish() : setStep((s) => s + 1))}
          accessibilityRole="button"
          accessibilityLabel={last ? 'Finish setting up' : 'Continue'}
          accessibilityHint={
            last
              ? 'Opens today’s screen'
              : `Goes on to ${steps[Math.min(steps.length - 1, step + 1)].label}`
          }
          style={({ pressed }) => [styles.navNext, pressed && styles.pressed]}
        >
          <Text style={styles.navNextText}>{last ? 'Start' : 'Continue'}</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: colors.paper },

  header: { paddingHorizontal: space(3), paddingTop: space(2), gap: space(1) },
  sampleBar: {
    backgroundColor: colors.brandSoft,
    borderRadius: radius.pill,
    paddingVertical: space(1),
    paddingHorizontal: space(2),
    alignSelf: 'flex-start',
  },
  sampleText: { ...type.small, color: colors.deep, fontWeight: '600' },
  progress: { ...type.label, color: colors.brand },
  track: { flexDirection: 'row', gap: space(0.75) },
  segment: { flex: 1, height: 3, backgroundColor: colors.border, borderRadius: 2 },
  segmentDone: { backgroundColor: colors.ink },

  scroll: { flex: 1 },
  content: { padding: space(3), paddingBottom: space(4) },
  section: { gap: space(3) },

  title: { ...type.display, color: colors.ink },
  lede: { ...type.body, color: colors.muted, maxWidth: 420 },
  importLink: { alignSelf: 'flex-start', paddingVertical: space(1.5) },
  importLinkText: { ...type.body, color: colors.brand, fontWeight: '600' },

  aside: { ...type.small, color: colors.faint, lineHeight: 20 },

  // Pairing: oversized type on bare paper, no container. The status is the
  // largest thing on the step because it is the only thing the person is
  // waiting on.
  statusBlock: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
    paddingTop: space(2),
    gap: space(0.5),
  },
  statusText: { fontSize: 34, lineHeight: 42, color: colors.ink, fontWeight: '500' },
  statusSub: { ...type.small, color: colors.muted, fontVariant: ['tabular-nums'] },

  primary: {
    backgroundColor: colors.ink,
    borderRadius: radius.pill,
    paddingVertical: space(2),
    paddingHorizontal: space(3),
    alignSelf: 'flex-start',
  },
  primaryText: { ...type.body, color: colors.paper, fontWeight: '600' },

  helpBlock: { gap: space(0.75) },
  helpLabel: { ...type.label, color: colors.faint },
  helpItem: { ...type.body, color: colors.ink },

  sourceRow: { flexDirection: 'row', gap: space(2), paddingVertical: space(2) },
  ruled: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },
  sourceMain: { flex: 1, gap: space(0.5) },
  sourceName: { ...type.body, color: colors.ink, fontWeight: '600' },
  sourceUnlocks: { ...type.body, color: colors.ink },
  sourceDetail: { ...type.small, color: colors.muted },
  sourceNever: { ...type.small, color: colors.faint },
  sourceControl: { alignItems: 'flex-end', gap: space(0.5) },
  sourceState: { ...type.small, color: colors.muted, fontWeight: '600' },

  summary: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
    paddingTop: space(2),
    gap: space(0.5),
  },
  summaryLabel: { ...type.label, color: colors.faint },
  summaryText: { ...type.title, color: colors.ink },

  promise: { gap: space(0.5) },
  promiseText: { fontSize: 24, lineHeight: 32, color: colors.ink, fontWeight: '500' },
  promiseDetail: { ...type.small, color: colors.muted, lineHeight: 21 },

  boundaryPanel: {
    borderWidth: 1,
    borderColor: colors.ink,
    borderRadius: radius.card,
    padding: space(3),
    gap: space(1),
  },
  boundaryLabel: { ...type.label, color: colors.ink },
  boundaryText: { fontSize: 22, lineHeight: 31, color: colors.ink, fontWeight: '500' },
  boundaryDetail: { ...type.small, color: colors.muted, lineHeight: 21 },

  readyRow: { paddingVertical: space(2), gap: space(0.5) },
  readyWhen: { ...type.label, color: colors.brand },
  readyWhat: { ...type.title, color: colors.ink },
  readyDetail: { ...type.small, color: colors.muted, lineHeight: 21 },

  finishPanel: {
    backgroundColor: colors.ink,
    borderRadius: radius.card,
    padding: space(3),
    gap: space(1),
  },
  finishEyebrow: { ...type.label, color: colors.brandSoft },
  finishText: { fontSize: 24, lineHeight: 32, color: colors.paper, fontWeight: '600' },
  finishWhy: { ...type.small, color: '#C9D2D8', lineHeight: 21 },

  nav: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: space(2),
    paddingHorizontal: space(3),
    paddingVertical: space(2),
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
    backgroundColor: colors.surface,
  },
  navBack: { paddingVertical: space(1), paddingRight: space(2) },
  navBackText: { ...type.small, color: colors.brand, fontWeight: '600' },
  navNext: {
    backgroundColor: colors.ink,
    borderRadius: radius.pill,
    paddingVertical: space(1.75),
    paddingHorizontal: space(3),
  },
  navNextText: { ...type.body, color: colors.paper, fontWeight: '600' },
  pressed: { opacity: 0.6 },
});

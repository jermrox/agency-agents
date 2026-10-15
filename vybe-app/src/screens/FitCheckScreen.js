import React, { useEffect, useRef, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { colors, dimensions, radius, space, type } from '../theme';
import {
  STATUS,
  checks,
  honestLine,
  intro,
  isSample,
  passes,
  recordLine,
  skipLine,
  wristNote,
  wrists,
} from '../fitSampleData';

/**
 * Fit check — first run, between pairing the Band and the first night.
 *
 * Onboarding already pairs the Band and takes consent. What no first-run flow
 * in this category does is tell the person, before the first night, whether
 * the thing on their wrist can actually read them. They find out weeks later
 * as a "low quality" badge on a night that is already gone. This screen moves
 * that conversation to the only moment it is useful.
 *
 * Two decisions carry it.
 *
 * The first is that the result is words, never a number. A "signal quality
 * 73%" reads like a health figure and invites the person to chase it. "The
 * Band is not sliding when you move" tells them what is true and what to do.
 * Each check carries its own fix, so a fault and its remedy are one line
 * apart rather than a help article apart.
 *
 * The second is that the check says what it keeps: nothing. A fit check
 * listens to the sensor, and a person who has just been asked for consent is
 * entitled to know those seconds are discarded. That line is the one outlined
 * block on the screen, the same treatment Onboarding gives its claim boundary.
 *
 * Treatments, so the hierarchy reads before the words do: the state is
 * oversized type on bare paper, the wrist choice is a two-way switch, the
 * three checks are a hairline list with a word and a glyph per row, the
 * record line is the single outlined block, and the one dark block is the
 * button that runs the check or ends the step. No two sections share a shape.
 */

const READ_MS = 1400;
const GOOD = dimensions.nourish.hue;
const FIX = dimensions.move.hue;

export default function FitCheckScreen({ onBack, onDone, onSkip }) {
  const [wrist, setWrist] = useState(wrists[0].id);
  // `pass` counts completed reads; `phase` is the state the screen is in.
  const [phase, setPhase] = useState('idle');
  const [pass, setPass] = useState(0);
  const timers = useRef([]);

  // A timer outliving the screen would set state on an unmounted component.
  useEffect(() => () => timers.current.forEach(clearTimeout), []);

  function later(fn, ms) {
    timers.current.push(setTimeout(fn, ms));
  }

  // The sample is scripted: the pass index picks the outcome, and the last
  // pass repeats if someone keeps checking, so the screen never runs out.
  const result = pass > 0 ? passes[Math.min(pass, passes.length) - 1] : null;
  const faults = result ? checks.filter((c) => !result[c.id]) : [];

  function runCheck() {
    setPhase('reading');
    later(() => {
      const next = pass + 1;
      const outcome = passes[Math.min(next, passes.length) - 1];
      setPass(next);
      setPhase(checks.every((c) => outcome[c.id]) ? 'clean' : 'adjust');
    }, READ_MS);
  }

  const reading = phase === 'reading';
  const clean = phase === 'clean';

  return (
    <ScrollView
      style={styles.page}
      contentContainerStyle={styles.content}
      accessibilityLabel="Fit check"
    >
      {isSample ? (
        <View style={styles.sampleBar}>
          <Text style={styles.sampleText}>
            Sample data — no sensor is really being read.
          </Text>
        </View>
      ) : null}

      <View style={styles.header}>
        <Pressable
          onPress={onBack}
          accessibilityRole="button"
          accessibilityLabel="Back to setting up"
          accessibilityHint="Returns to pairing"
          style={({ pressed }) => [styles.back, pressed && styles.pressed]}
        >
          <Text style={styles.backText}>Setting up</Text>
        </Pressable>
        <Text style={styles.eyebrow}>FIT CHECK</Text>
        <Text style={styles.title}>{intro.title}</Text>
        <Text style={styles.lede}>{intro.lede}</Text>
      </View>

      {/* THE STATE — oversized words on bare paper. A spinner is not a
          status, and a screen reader cannot read one. */}
      <View style={styles.statusBlock}>
        <Text
          style={styles.statusText}
          accessible
          accessibilityRole="text"
          accessibilityLiveRegion="polite"
          accessibilityLabel={`Fit status: ${STATUS[phase]}`}
        >
          {STATUS[phase]}
        </Text>
        <Text style={styles.statusSub}>
          {phase === 'idle'
            ? 'Put the Band on the way you would wear it to bed.'
            : phase === 'reading'
              ? 'Hold still for a moment.'
              : clean
                ? 'All three checks passed. Tonight’s read will be about you, not the strap.'
                : `${faults.length === 1 ? 'One check' : `${faults.length} checks`} need a change. The fix is next to each.`}
        </Text>
      </View>

      {/* WHICH WRIST — a two-way switch, not a dropdown. Both answers are
          right, so it is a preference with a reason, not a gate. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Which wrist?</Text>
        <View style={styles.segmented} accessibilityRole="radiogroup">
          {wrists.map((w) => {
            const on = w.id === wrist;
            return (
              <Pressable
                key={w.id}
                onPress={() => setWrist(w.id)}
                accessibilityRole="radio"
                accessibilityState={{ checked: on }}
                accessibilityLabel={w.label}
                style={({ pressed }) => [
                  styles.segment,
                  on && styles.segmentOn,
                  pressed && styles.pressed,
                ]}
              >
                <Text style={[styles.segmentText, on && styles.segmentTextOn]}>
                  {w.label}
                </Text>
              </Pressable>
            );
          })}
        </View>
        <Text style={styles.aside}>{wristNote}</Text>
      </View>

      {/* THE THREE CHECKS — a hairline list. Each row says in words what is
          true and, when something is wrong, what to do. The glyph and the
          colour repeat the word; they never replace it. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>What the sensor can see</Text>
        {checks.map((c, i) => {
          const known = result !== null && !reading;
          const ok = known && result[c.id];
          const bad = known && !result[c.id];
          const line = !known ? 'Not checked yet' : ok ? c.good : c.fix;
          return (
            <View
              key={c.id}
              style={[styles.checkRow, i > 0 && styles.ruled]}
              accessible
              accessibilityRole="text"
              accessibilityLabel={`${c.label}: ${ok ? 'good. ' : bad ? 'needs a change. ' : ''}${line}`}
            >
              <View style={styles.checkHead}>
                <Text style={styles.checkLabel}>{c.label}</Text>
                <Text
                  style={[
                    styles.checkWord,
                    ok && { color: GOOD },
                    bad && { color: FIX },
                  ]}
                >
                  {!known ? '—' : ok ? '✓ Good' : '↻ Change'}
                </Text>
              </View>
              <Text style={[styles.checkLine, bad && styles.checkFix]}>{line}</Text>
              {/* The reason is shown while nothing is known and again when
                  something is wrong; a passing row does not need a lecture. */}
              {!known || bad ? <Text style={styles.checkWhy}>{c.why}</Text> : null}
            </View>
          );
        })}
      </View>

      {/* WHAT THIS CHECK KEEPS — the one outlined block. */}
      <View style={styles.boundary} accessible accessibilityRole="text">
        <Text style={styles.boundaryLabel}>{recordLine.label}</Text>
        <Text style={styles.boundaryText}>{recordLine.text}</Text>
        <Text style={styles.boundaryDetail}>{recordLine.detail}</Text>
      </View>

      <Text style={styles.honest}>{honestLine}</Text>

      {/* THE ACTION — the only dark block. It runs the check, runs it again,
          or ends the step; never two buttons competing. */}
      <Pressable
        onPress={clean ? onDone : runCheck}
        disabled={reading}
        accessibilityRole="button"
        accessibilityState={{ disabled: reading, busy: reading }}
        accessibilityLabel={
          clean ? 'Done, wear it tonight' : pass > 0 ? 'Check the fit again' : 'Check the fit'
        }
        accessibilityHint={
          clean
            ? 'Returns to setting up with the fit confirmed'
            : 'Reads the sensor for a few seconds and reports in words'
        }
        style={({ pressed }) => [
          styles.primary,
          reading && styles.primaryBusy,
          pressed && !reading && styles.pressed,
        ]}
      >
        <Text style={styles.primaryText}>
          {reading
            ? 'Reading…'
            : clean
              ? 'Done — wear it tonight'
              : pass > 0
                ? 'I’ve adjusted it. Check again'
                : 'Check the fit'}
        </Text>
      </Pressable>

      {!clean ? (
        <View style={styles.skipBlock}>
          <Pressable
            onPress={onSkip}
            accessibilityRole="button"
            accessibilityLabel="Skip the fit check"
            accessibilityHint="Returns to setting up without checking the fit"
            style={({ pressed }) => [styles.skip, pressed && styles.pressed]}
          >
            <Text style={styles.skipText}>Skip for now</Text>
          </Pressable>
          <Text style={styles.aside}>{skipLine}</Text>
        </View>
      ) : null}
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
  eyebrow: { ...type.label, color: colors.brand, marginTop: space(1) },
  title: { ...type.display, color: colors.ink },
  lede: { ...type.body, color: colors.muted, marginTop: space(1) },

  // Oversized type on bare paper: the state is the loudest thing here.
  statusBlock: { gap: space(1) },
  statusText: { fontSize: 28, lineHeight: 34, fontWeight: '600', color: colors.ink },
  statusSub: { ...type.body, color: colors.muted },

  section: { gap: space(1.5) },
  sectionTitle: { ...type.title, color: colors.ink },
  aside: { ...type.small, color: colors.faint, lineHeight: 20 },

  // Two-way switch. The chosen side is ink on paper reversed, and the label
  // still says which is chosen for anyone who cannot see the fill.
  segmented: {
    flexDirection: 'row', borderWidth: 1, borderColor: colors.border,
    borderRadius: radius.pill, padding: 3, alignSelf: 'flex-start',
  },
  segment: { paddingVertical: space(1), paddingHorizontal: space(2.5), borderRadius: radius.pill },
  segmentOn: { backgroundColor: colors.ink },
  segmentText: { ...type.body, color: colors.ink, fontWeight: '500' },
  segmentTextOn: { color: colors.paper },

  // Hairline list. No card, no border accent; the rule does the separating.
  checkRow: { paddingVertical: space(1.5), gap: 4 },
  ruled: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },
  checkHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' },
  checkLabel: { ...type.body, color: colors.ink, fontWeight: '600' },
  checkWord: { ...type.label, color: colors.faint },
  checkLine: { ...type.body, color: colors.ink },
  checkFix: { fontWeight: '500' },
  checkWhy: { ...type.small, color: colors.faint },

  // The single outlined block.
  boundary: {
    borderWidth: 1, borderColor: colors.ink, borderRadius: radius.card,
    padding: space(2.5), gap: space(0.5),
  },
  boundaryLabel: { ...type.label, color: colors.ink },
  boundaryText: { ...type.body, color: colors.ink, fontWeight: '500' },
  boundaryDetail: { ...type.small, color: colors.muted },

  honest: { ...type.body, color: colors.muted, fontStyle: 'italic' },

  // The one dark block.
  primary: { backgroundColor: colors.ink, borderRadius: radius.card, padding: space(2.5), alignItems: 'center' },
  primaryBusy: { backgroundColor: colors.muted },
  primaryText: { ...type.body, color: colors.paper, fontWeight: '600' },

  skipBlock: { gap: space(1) },
  skip: { alignSelf: 'flex-start', paddingVertical: space(1) },
  skipText: { ...type.body, color: colors.brand, fontWeight: '600' },
});

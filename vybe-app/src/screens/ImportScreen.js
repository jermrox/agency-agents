import React, { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { colors, radius, space, type } from '../theme';
import {
  capabilities,
  isSample,
  records,
  restraint,
  source,
  whatHappensNext,
} from '../importSampleData';
import ImportBuckets, { statusFor, usableDaysOf } from '../components/ImportBuckets';

/**
 * Connecting a source that already has years in it.
 *
 * `OnboardingScreen` asks which sources you will connect. This is the screen
 * immediately after, and the one nobody builds: the phone health store opens
 * and three years of somebody else's readings come out.
 *
 * THE DECISION THAT MAKES THIS SCREEN
 * The convenient thing is to import all of it, draw one seamless chart back to
 * 2023, and compute a baseline from the lot. That is wrong in a way the person
 * cannot possibly see. Another product's sleep stages and HRV come from a
 * different sensor, sampled at different moments, through an algorithm nobody
 * has published. Build a baseline on those and every later sentence that says
 * "below your baseline" is quietly measuring Vybe against a competitor's guess.
 *
 * So the history is sorted into three groups with the rule stated above each,
 * and the groups are consequential rather than cosmetic: a capability whose
 * input landed in "show only" reports itself blocked, with the record that
 * blocked it named. Three years of sleep stages sits right there on screen,
 * drawn and unusable, which is the most honest thing this app says to a new
 * user.
 *
 * NOTHING HERE IS A STORED VERDICT. Every capability's state is computed from
 * the buckets and the day counts against its own stated requirement, so the
 * list cannot announce a capability as ready while the record it needs is in
 * the group Vybe refuses to compute with.
 *
 * Five treatments, so the hierarchy reads before the words: the source and its
 * span in a quiet header block, the usable figure oversized on bare paper, what
 * it unlocks as a ruled list of states, the history itself as three titled
 * groups, and the closing restraint as the only dark panel.
 */
export default function ImportScreen({ onBack, onContinue }) {
  const [openId, setOpenId] = useState(null);

  // Derived, never typed.
  const usableDays = usableDaysOf(records);
  const states = capabilities.map((c) => ({ c, s: statusFor(c, records) }));
  const ready = states.filter((x) => x.s.kind === 'ready');
  const blocked = states.filter((x) => x.s.kind === 'blocked');
  const waiting = states.filter((x) => x.s.kind === 'waiting');

  return (
    <ScrollView
      style={styles.page}
      contentContainerStyle={styles.content}
      accessibilityLabel="Imported history"
    >
      {isSample ? (
        <View style={styles.sampleBar}>
          <Text style={styles.sampleText}>
            Sample data — these are record counts, not anybody&rsquo;s readings.
          </Text>
        </View>
      ) : null}

      <View style={styles.header}>
        <Pressable
          onPress={onBack}
          accessibilityRole="button"
          accessibilityLabel="Back"
          accessibilityHint="Returns to the previous step without importing"
          style={({ pressed }) => [styles.back, pressed && styles.pressed]}
        >
          <Text style={styles.backText}>Back</Text>
        </Pressable>
        <Text style={styles.eyebrow}>{source.name.toUpperCase()} IS CONNECTED</Text>
        <Text style={styles.title}>You brought history with you.</Text>
        <Text style={styles.sub}>
          {source.spanLabel} of it, from {source.firstDate} to {source.lastDate}.{' '}
          {source.deviceNote}
        </Text>
      </View>

      {/* THE FIGURE — bare paper. The number that decides what today looks
          like, and it is the length of the usable history rather than the
          length of the file. */}
      <View style={styles.figureBlock}>
        <Text style={styles.figure}>{usableDays.toLocaleString()}</Text>
        <Text style={styles.figureCaption}>
          days of it Vybe can actually compute with. The rest is kept, drawn, or
          left behind — and the screen says which, for every record.
        </Text>
      </View>

      {/* WHAT IT UNLOCKS — one ruled list, three states, each derived. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>What this history gives you</Text>
        <Text style={styles.sectionLede}>
          {`${ready.length} ready today · ${blocked.length} that imported data cannot do · `}
          {`${waiting.length} waiting on more`}
        </Text>
        <View>
          {states.map(({ c, s }, i) => (
            <View
              key={c.id}
              style={[styles.capRow, i > 0 && styles.ruled]}
              accessible
              accessibilityRole="text"
              accessibilityLabel={
                `${c.label}. `
                + (s.kind === 'ready'
                  ? `Ready, on ${s.days} days of history.`
                  : s.kind === 'blocked'
                    ? `Not available from imported data, because ${s.blocker.label} is history only.`
                    : `Waiting. ${s.days} days so far, ${s.short} more needed.`)
              }
            >
              <View style={styles.capGutter}>
                <Text
                  style={[
                    styles.capState,
                    s.kind === 'ready' && styles.capReady,
                    s.kind === 'blocked' && styles.capBlocked,
                  ]}
                >
                  {s.kind === 'ready' ? 'Ready' : s.kind === 'blocked' ? 'Not from this' : 'Waiting'}
                </Text>
              </View>
              <View style={styles.capBody}>
                <Text style={styles.capLabel}>{c.label}</Text>
                <Text style={styles.capWhy}>
                  {s.kind === 'ready'
                    ? `${s.days.toLocaleString()} days of history, and it needs ${c.needsDays}.`
                    : s.kind === 'blocked'
                      ? `${s.blocker.label} came from another product, so Vybe will show it and will not compute with it. This starts working once Vybe has recorded ${c.needsDays} days itself.`
                      : `${s.input.label}: ${s.days} ${s.days === 1 ? 'day' : 'days'} so far, ${s.short} short of the ${c.needsDays} this needs.`}
                </Text>
              </View>
            </View>
          ))}
        </View>
        <Text style={styles.nextNote}>{whatHappensNext}</Text>
      </View>

      {/* THE HISTORY ITSELF — three titled groups, each with its rule. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Every record, and where it went</Text>
        <Text style={styles.sectionLede}>
          Tap any row for the reason. Nothing here is hidden behind a setting.
        </Text>
        <ImportBuckets records={records} selectedId={openId} onSelect={setOpenId} />
      </View>

      {/* THE RESTRAINT — the only dark block, and the last word. */}
      <View style={styles.restraintPanel}>
        <Text style={styles.restraintEyebrow}>WHY VYBE IS NOT TAKING ALL OF IT</Text>
        <Text style={styles.restraintText}>{restraint}</Text>
      </View>

      {onContinue ? (
        <Pressable
          onPress={onContinue}
          accessibilityRole="button"
          accessibilityLabel="Continue with this import"
          accessibilityHint="Keeps the records listed above and moves on"
          style={({ pressed }) => [styles.cta, pressed && styles.pressed]}
        >
          <Text style={styles.ctaText}>Continue</Text>
        </Pressable>
      ) : null}
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
  title: { ...type.display, color: colors.ink },
  sub: { ...type.body, color: colors.muted, lineHeight: 24, marginTop: space(0.5) },

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
  figureCaption: { ...type.body, color: colors.muted, maxWidth: space(40) },

  section: { gap: space(1) },
  sectionTitle: { ...type.title, color: colors.ink },
  sectionLede: { ...type.small, color: colors.muted, lineHeight: 20 },

  capRow: { flexDirection: 'row', alignItems: 'flex-start', gap: space(2), paddingVertical: space(1.75) },
  ruled: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },
  // The state is a word in its own fixed column, never a colour on its own.
  capGutter: { width: space(12), paddingTop: 2 },
  capState: { ...type.small, color: colors.muted, fontWeight: '700' },
  capReady: { color: colors.brand },
  capBlocked: { color: colors.ink },
  capBody: { flex: 1, gap: 3 },
  capLabel: { ...type.body, color: colors.ink, fontWeight: '600' },
  capWhy: { ...type.small, color: colors.muted, lineHeight: 20 },

  nextNote: { ...type.small, color: colors.faint, lineHeight: 20, paddingTop: space(1) },

  restraintPanel: {
    backgroundColor: colors.ink,
    borderRadius: radius.card,
    padding: space(3),
    gap: space(1),
  },
  restraintEyebrow: { ...type.label, color: colors.brandSoft },
  restraintText: { fontSize: 18, lineHeight: 27, color: colors.paper },

  cta: {
    backgroundColor: colors.brand,
    borderRadius: radius.card,
    paddingVertical: space(2.25),
    alignItems: 'center',
  },
  ctaText: { ...type.body, color: colors.paper, fontWeight: '700' },
});

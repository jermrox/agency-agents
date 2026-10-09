import React, { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { colors, radius, space, type } from '../theme';
import {
  deletePromise,
  exportInfo,
  formats,
  groups,
  isSample,
  restraint,
  retention,
} from '../exportSampleData';
import ExportManifest, {
  PORTABLE_WORD,
  groupsForFormat,
  recordsOfKind,
  totalRecords,
} from '../components/ExportManifest';

/**
 * Taking everything with you — the import screen, backwards.
 *
 * `DataSettingsScreen` offers "Export everything" and "Delete everything" and
 * promises CSV for the readings, JSON for the rest, and a delete that finishes
 * within seven days. This is the screen behind that tap, and its job is to
 * keep that promise in detail rather than quietly improve on it.
 *
 * THE DECISION THAT MAKES THIS SCREEN
 * On Wednesday's import screen Vybe refused to compute with another product's
 * sleep stages and HRV, because they are somebody else's estimate from a
 * different sensor through an unpublished algorithm. That position only holds
 * if it points both ways. So Vybe's own answers, pattern verdicts and outcome
 * records are listed here under a heading that says what they are — Vybe's
 * conclusions, not measurements — and the manifest tells the next product to
 * treat them exactly as Vybe treated the last one's.
 *
 * AND THE SECOND ONE: the derived records are a rounding error by count and
 * most of the value, and the screen says so as arithmetic rather than as a
 * boast. Four hundred and fifty-eight conclusions against 1.19 million
 * readings is 0.04% of the file.
 *
 * NOTHING HERE IS A STORED TOTAL. The record count, the derived share, the
 * portable share and which groups each format can carry are computed from the
 * manifest, so a format cannot claim to carry something the group does not
 * list.
 *
 * Five treatments: the size and span in a quiet header, the manifest as three
 * titled groups with a portability word per group, the formats as a plain list
 * of what each is and is not good for, what Vybe keeps after a delete as the
 * one outlined block, and the closing restraint as the only dark panel.
 */
export default function ExportScreen({ onBack }) {
  const [openId, setOpenId] = useState(null);
  const [format, setFormat] = useState('json');

  // Derived, never typed.
  const total = totalRecords(groups);
  const derived = recordsOfKind(groups, 'derived');
  const portable = groups
    .filter((g) => g.kind !== 'derived')
    .reduce((sum, g) => sum + g.records, 0);
  // Guards the claim below: every record is either portable or derived.
  const accountsFor = portable + derived === total;
  // Both figures to the same precision, and the portable share is computed as
  // the complement rather than rounded on its own: at 0.04% derived, an
  // independently rounded portable share reads "100%" and then the caption
  // says "the remaining 0.04%", which looks like the screen contradicting
  // itself. 99.96% is also the more honest headline — it says virtually all,
  // without claiming all.
  const derivedPct = ((derived / total) * 100).toFixed(2);
  const portablePct = (100 - Number(derivedPct)).toFixed(2);
  const carried = groupsForFormat(groups, format);
  const missed = groups.filter((g) => !g.formats.includes(format));
  const chosen = formats.find((f) => f.id === format);

  return (
    <ScrollView
      style={styles.page}
      contentContainerStyle={styles.content}
      accessibilityLabel="Export everything"
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
          accessibilityLabel="Back to your data"
          accessibilityHint="Returns to the data and permissions screen"
          style={({ pressed }) => [styles.back, pressed && styles.pressed]}
        >
          <Text style={styles.backText}>Your data</Text>
        </Pressable>
        <Text style={styles.eyebrow}>EXPORT EVERYTHING</Text>
        <Text style={styles.title}>Everything, and what it is worth to anyone else.</Text>
        <Text style={styles.sub}>
          {exportInfo.spanLabel} · {exportInfo.sizeLabel} · {exportInfo.preparedLabel}.{' '}
          {exportInfo.waitNote}
        </Text>
      </View>

      {/* THE FIGURE — the share another product can actually use, which is the
          only number that decides whether an export is real. */}
      <View style={styles.figureBlock}>
        <Text style={styles.figure}>{portablePct}%</Text>
        <Text style={styles.figureCaption}>
          of these records are measurements any other product can read on the
          first day. The remaining {derivedPct}% are Vybe&rsquo;s own
          conclusions — {derived} of them — which travel with you and should
          not be treated as evidence by whatever comes next.
          {accountsFor ? '' : ' Some records fall into neither group; the manifest below is the complete list.'}
        </Text>
      </View>

      {/* THE MANIFEST */}
      <View style={styles.section}>
        <Text style={styles.sectionHeading}>What is in the file</Text>
        <Text style={styles.sectionLede}>
          Tap any line for what is in it and why. Nothing here is behind a
          setting or a support request.
        </Text>
        <ExportManifest groups={groups} openId={openId} onToggle={setOpenId} />
      </View>

      {/* THE FORMAT — a real choice with real consequences, and the screen
          computes what each one leaves behind rather than claiming parity. */}
      <View style={styles.section}>
        <Text style={styles.sectionHeading}>Pick a format</Text>
        <View style={styles.formatRow}>
          {formats.map((f) => {
            const on = f.id === format;
            return (
              <Pressable
                key={f.id}
                onPress={() => setFormat(f.id)}
                accessibilityRole="radio"
                accessibilityState={{ selected: on }}
                accessibilityLabel={f.label}
                accessibilityHint={`Shows what ${f.label} carries and what it leaves out`}
                style={({ pressed }) => [
                  styles.formatChip,
                  on && styles.formatChipOn,
                  pressed && styles.pressed,
                ]}
              >
                <Text style={[styles.formatChipText, on && styles.formatChipTextOn]}>
                  {f.label}
                </Text>
              </Pressable>
            );
          })}
        </View>
        <View style={styles.formatDetail}>
          <Text style={styles.formatGood}>{chosen.good}</Text>
          <Text style={styles.formatBad}>{chosen.bad}</Text>
          <Text style={styles.formatCoverage}>
            {chosen.label} carries {carried.length} of the {groups.length} groups
            above
            {missed.length > 0
              ? `. It leaves out ${missed.map((g) => g.label.toLowerCase()).join(', ')}.`
              : ' — all of them.'}
          </Text>
        </View>
      </View>

      {/* WHAT VYBE KEEPS — the one outlined block, and the label says what the
          outline means. This belongs on the screen, not in a policy page. */}
      <View style={styles.keepPanel}>
        <Text style={styles.keepLabel}>WHAT VYBE KEEPS AFTER YOU DELETE</Text>
        <Text style={styles.keepText}>{deletePromise}</Text>
        <View style={styles.keepList}>
          {retention.map((r, i) => (
            <View
              key={r.id}
              style={[styles.keepRow, i > 0 && styles.ruledLight]}
              accessible
              accessibilityRole="text"
              accessibilityLabel={`${r.label}. ${
                r.days >= 365
                  ? `${Math.round(r.days / 365)} years`
                  : `${r.days} days`
              }. ${r.why}`}
            >
              <View style={styles.keepBody}>
                <Text style={styles.keepItem}>{r.label}</Text>
                <Text style={styles.keepWhy}>{r.why}</Text>
              </View>
              <Text style={styles.keepDays}>
                {r.days >= 365
                  ? `${Math.round(r.days / 365)} yr`
                  : `${r.days} days`}
              </Text>
            </View>
          ))}
        </View>
      </View>

      {/* THE RESTRAINT — the only dark block, and the last word. */}
      <View style={styles.restraintPanel}>
        <Text style={styles.restraintEyebrow}>WHY IT IS THIS EASY</Text>
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
  title: { fontSize: 30, lineHeight: 38, color: colors.ink, fontWeight: '600' },
  sub: { ...type.small, color: colors.muted, lineHeight: 21, marginTop: space(0.5) },

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
  figureCaption: { ...type.body, color: colors.muted, lineHeight: 24 },

  section: { gap: space(1) },
  sectionHeading: { ...type.title, color: colors.ink },
  sectionLede: { ...type.small, color: colors.muted, lineHeight: 20 },

  formatRow: { flexDirection: 'row', gap: space(1), marginTop: space(0.5) },
  // A chip, not a segmented control: the state is the word plus a fill, and
  // the label is always legible either way.
  formatChip: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.pill,
    paddingVertical: space(1),
    paddingHorizontal: space(2.5),
  },
  formatChipOn: { backgroundColor: colors.ink, borderColor: colors.ink },
  formatChipText: { ...type.small, color: colors.muted, fontWeight: '700' },
  formatChipTextOn: { color: colors.paper },

  formatDetail: { gap: space(0.5), marginTop: space(1) },
  formatGood: { ...type.body, color: colors.ink, lineHeight: 23 },
  formatBad: { ...type.small, color: colors.muted, lineHeight: 21 },
  formatCoverage: { ...type.small, color: colors.faint, lineHeight: 20, paddingTop: space(0.5) },

  keepPanel: {
    borderWidth: 1,
    borderColor: colors.ink,
    borderRadius: radius.card,
    padding: space(3),
    gap: space(1.5),
  },
  keepLabel: { ...type.label, color: colors.ink },
  keepText: { ...type.body, color: colors.ink, lineHeight: 24 },
  keepList: { marginTop: space(0.5) },
  keepRow: { flexDirection: 'row', alignItems: 'flex-start', gap: space(2), paddingVertical: space(1.5) },
  ruledLight: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },
  keepBody: { flex: 1, gap: 2 },
  keepItem: { ...type.body, color: colors.ink, fontWeight: '600' },
  keepWhy: { ...type.small, color: colors.muted, lineHeight: 20 },
  keepDays: {
    ...type.small,
    color: colors.ink,
    fontWeight: '700',
    fontVariant: ['tabular-nums'],
    textAlign: 'right',
    width: space(9),
  },

  restraintPanel: {
    backgroundColor: colors.ink,
    borderRadius: radius.card,
    padding: space(3),
    gap: space(1),
  },
  restraintEyebrow: { ...type.label, color: colors.brandSoft },
  restraintText: { fontSize: 18, lineHeight: 27, color: colors.paper },
});

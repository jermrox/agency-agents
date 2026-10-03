import React, { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Switch, Text, View } from 'react-native';
import { colors, dimensions, radius, space, type } from '../theme';
import { dataSettings, isSample } from '../dataSettingsSampleData';

/** Vitals red marks the one destructive control, and only that control. */
const DANGER = dimensions.vitals.hue;

/**
 * Data and permissions.
 *
 * Most settings screens are a list of switches whose labels are category names
 * — "Health data", "Analytics" — which is how consent forms end up unreadable
 * while still being technically complete. This screen is built the other way
 * round: every row says what the source actually hands over, and the storage
 * split is drawn rather than asserted, because "almost all of it stays on your
 * phone" is either visible in the proportions or it is not true.
 *
 * Reading order: the position -> what you have connected -> where it sits ->
 * what we never do -> the two controls that prove it. The controls are last on
 * purpose: export and delete are the only lines on the screen that can be
 * checked, so they close the argument rather than opening it.
 *
 * Five treatments, so the hierarchy reads before a word does: oversized type on
 * bare paper, a hairline list with switches, one proportional bar, the single
 * dark block, and two buttons that look like what they do.
 */
export default function DataSettingsScreen({ onBack }) {
  const [sources, setSources] = useState(dataSettings.sources);
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  const toggle = (id) =>
    setSources((prev) => prev.map((s) => (s.id === id ? { ...s, on: !s.on } : s)));

  // The bar only tells the truth if the shares are a whole. Catching this here
  // beats drawing a bar that quietly does not add up.
  const total = dataSettings.residency.reduce((sum, r) => sum + r.share, 0);
  const residencySummary = dataSettings.residency
    .map((r) => `${r.place}, ${r.share} per cent`)
    .join('. ');

  return (
    <ScrollView
      style={styles.page}
      contentContainerStyle={styles.content}
      accessibilityLabel="Data and permissions"
    >
      {isSample ? (
        <View style={styles.sampleBar}>
          <Text style={styles.sampleText}>
            Sample data — these are not your sources or your readings.
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
        <Text style={styles.eyebrow}>DATA AND PERMISSIONS</Text>
        <Text style={styles.title}>Your data</Text>
      </View>

      {/* THE POSITION — oversized type, no container, under a hairline. */}
      <View style={styles.positionBlock}>
        <Text style={styles.position}>{dataSettings.position}</Text>
        <Text style={styles.positionDetail}>{dataSettings.positionDetail}</Text>
      </View>

      {/* CONNECTED SOURCES — a hairline list, not a stack of cards. Each row
          says what the source actually sends, and its state in words. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>What is connected</Text>
        <Text style={styles.sectionLede}>
          Each row says what that source hands over. Turn any of them off and
          Vybe keeps working with less to go on — it will say so rather than
          guess.
        </Text>

        <View>
          {sources.map((s, i) => (
            <View key={s.id} style={[styles.sourceRow, i > 0 && styles.ruled]}>
              <View style={styles.sourceText}>
                <Text style={styles.sourceName}>{s.name}</Text>
                <Text style={styles.sourceSends}>{s.sends}</Text>
                <Text style={styles.sourceDetail}>{s.detail}</Text>
                <Text style={styles.sourceMeta}>
                  {/* The state is a word first. The switch agrees with it; it
                      does not carry the meaning by itself. */}
                  {s.on ? 'On' : 'Off'} · {s.lastSync}
                </Text>
              </View>
              <Switch
                value={s.on}
                onValueChange={() => toggle(s.id)}
                accessibilityRole="switch"
                accessibilityState={{ checked: s.on }}
                accessibilityLabel={`${s.name}. ${s.on ? 'On' : 'Off'}. Sends ${s.sends}.`}
                accessibilityHint={
                  s.on
                    ? `Turns off ${s.name} and stops it sending anything`
                    : `Turns on ${s.name} so it can send ${s.sends}`
                }
                trackColor={{ true: colors.brand, false: colors.border }}
                thumbColor={colors.surface}
              />
            </View>
          ))}
        </View>
      </View>

      {/* WHERE IT SITS — one proportional bar. A claim about residency should
          be shown at its real proportions or not made. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Where it sits</Text>

        {total === 100 ? (
          <View
            style={styles.bar}
            accessibilityRole="image"
            accessibilityLabel={`Where your data sits. ${residencySummary}.`}
          >
            {dataSettings.residency.map((r, i) => (
              <View
                key={r.id}
                style={[
                  styles.barPart,
                  {
                    flex: r.share,
                    backgroundColor:
                      r.id === 'phone' ? colors.brand
                        : r.id === 'servers' ? colors.brandSoft
                          : colors.border,
                  },
                  i > 0 && styles.barGap,
                ]}
              />
            ))}
          </View>
        ) : null}

        {/* The legend does the explaining. The bar without it is three
            rectangles, which tell a screen reader nothing at all. */}
        <View style={styles.legend}>
          {dataSettings.residency.map((r) => (
            <View
              key={r.id}
              style={styles.legendRow}
              accessible
              accessibilityRole="text"
              accessibilityLabel={`${r.place}, ${r.share} per cent. ${r.what}`}
            >
              <Text style={styles.legendShare}>{r.share}%</Text>
              <View style={styles.legendText}>
                <Text style={styles.legendPlace}>{r.place}</Text>
                <Text style={styles.legendWhat}>{r.what}</Text>
              </View>
            </View>
          ))}
        </View>
      </View>

      {/* NEVER — the one dark block on the screen. Flat negatives, no hedges. */}
      <View style={styles.neverPanel}>
        <Text style={styles.neverLabel}>WHAT IS NEVER DONE WITH IT</Text>
        {dataSettings.never.map((line) => (
          <Text key={line} style={styles.neverLine}>
            {line}
          </Text>
        ))}
      </View>

      {/* THE CONTROLS — the two things that make the rest checkable. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Your controls</Text>

        <Pressable
          onPress={() => {
            // TODO: hand off to the export job once the data layer exists.
          }}
          accessibilityRole="button"
          accessibilityLabel={dataSettings.controls.exportLabel}
          accessibilityHint={dataSettings.controls.exportDetail}
          style={({ pressed }) => [styles.exportButton, pressed && styles.pressed]}
        >
          <Text style={styles.exportText}>{dataSettings.controls.exportLabel}</Text>
        </Pressable>
        <Text style={styles.controlDetail}>{dataSettings.controls.exportDetail}</Text>

        {/* Delete asks twice. The second press is the one that means it, and
            the button says which state it is in rather than relying on colour. */}
        <Pressable
          onPress={() => setConfirmingDelete((c) => !c)}
          accessibilityRole="button"
          accessibilityLabel={
            confirmingDelete
              ? 'Confirm deleting everything. Permanent.'
              : dataSettings.controls.deleteLabel
          }
          accessibilityHint={
            confirmingDelete
              ? 'Press again to start the deletion, or press Keep my data to stop'
              : 'Asks you to confirm before anything is deleted'
          }
          style={({ pressed }) => [styles.deleteButton, pressed && styles.pressed]}
        >
          <Text style={styles.deleteText}>
            {confirmingDelete
              ? 'Press again to delete permanently'
              : dataSettings.controls.deleteLabel}
          </Text>
        </Pressable>
        <Text style={styles.controlDetail}>{dataSettings.controls.deleteDetail}</Text>

        {confirmingDelete ? (
          <Pressable
            onPress={() => setConfirmingDelete(false)}
            accessibilityRole="button"
            accessibilityLabel="Keep my data"
            accessibilityHint="Cancels the deletion"
            style={({ pressed }) => [styles.cancel, pressed && styles.pressed]}
          >
            <Text style={styles.cancelText}>Keep my data</Text>
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
  eyebrow: { ...type.label, color: colors.faint, marginTop: space(1) },
  title: { ...type.display, color: colors.ink },

  positionBlock: {
    gap: space(1.5),
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
    paddingBottom: space(3),
  },
  position: { fontSize: 26, lineHeight: 34, color: colors.ink, fontWeight: '500' },
  positionDetail: { ...type.small, color: colors.muted, lineHeight: 21 },

  section: { gap: space(1.5) },
  sectionTitle: { ...type.title, color: colors.ink },
  sectionLede: { ...type.small, color: colors.muted },

  sourceRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: space(2),
    paddingVertical: space(2),
  },
  ruled: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },
  sourceText: { flex: 1, gap: 3 },
  sourceName: { ...type.body, color: colors.ink, fontWeight: '600' },
  sourceSends: { ...type.body, color: colors.ink },
  sourceDetail: { ...type.small, color: colors.muted, lineHeight: 19 },
  sourceMeta: { ...type.small, color: colors.faint, marginTop: 2 },

  bar: { flexDirection: 'row', height: 18, borderRadius: 3, overflow: 'hidden' },
  barPart: { height: '100%' },
  barGap: { marginLeft: 2 },

  legend: { gap: space(1.5), marginTop: space(0.5) },
  legendRow: { flexDirection: 'row', gap: space(1.5), alignItems: 'flex-start' },
  legendShare: {
    ...type.body,
    color: colors.ink,
    fontWeight: '600',
    width: 44,
    fontVariant: ['tabular-nums'],
  },
  legendText: { flex: 1, gap: 2 },
  legendPlace: { ...type.body, color: colors.ink },
  legendWhat: { ...type.small, color: colors.muted, lineHeight: 19 },

  neverPanel: {
    backgroundColor: colors.ink,
    borderRadius: radius.card,
    padding: space(3),
    gap: space(1.25),
  },
  neverLabel: { ...type.label, color: colors.brandSoft, marginBottom: space(0.5) },
  neverLine: { ...type.body, color: colors.paper, lineHeight: 23 },

  exportButton: {
    backgroundColor: colors.ink,
    borderRadius: radius.card,
    paddingVertical: space(2),
    alignItems: 'center',
  },
  exportText: { ...type.body, color: colors.paper, fontWeight: '600' },

  deleteButton: {
    borderWidth: 1,
    borderColor: DANGER,
    borderRadius: radius.card,
    paddingVertical: space(2),
    alignItems: 'center',
    marginTop: space(1.5),
  },
  deleteText: { ...type.body, color: DANGER, fontWeight: '600' },

  controlDetail: { ...type.small, color: colors.muted, lineHeight: 19 },

  cancel: { alignSelf: 'center', paddingVertical: space(1), paddingHorizontal: space(2) },
  cancelText: { ...type.body, color: colors.brand, fontWeight: '600' },
});

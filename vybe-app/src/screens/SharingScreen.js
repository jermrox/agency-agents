import React, { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Switch, Text, View } from 'react-native';
import { colors, dimensions, order, radius, space, type } from '../theme';
import { sharing, isSample } from '../sharingSampleData';

/** Vitals red marks the one ending control, and only that control. */
const DANGER = dimensions.vitals.hue;

/**
 * Showing someone else — scoped, read-only, and it runs out.
 *
 * `DataSettingsScreen` settles what Vybe itself holds. This is the question
 * that comes straight after it in real life: "can my coach see this?" Most
 * products answer with a share link that shows everything, forever, to whoever
 * holds it. That is a convenience for the product and a liability for the
 * person.
 *
 * THREE DECISIONS MAKE THE SCREEN
 *
 * 1. Scope is written as what they will see AND what they will not. A switch
 *    labelled "Restore" asks the person to guess; a line that says "sleep
 *    timing and overnight HRV, not the notes you wrote" lets them decide.
 *    The "will not" half matters more, so it is never hidden behind a tap.
 * 2. Every share has an end date, and the longest is ninety days. There is no
 *    "always" option to forget about.
 * 3. Each active share shows its time left as a drawn bar AND in words, and
 *    says whether it has been opened. A share you cannot see being used is a
 *    share you cannot judge.
 *
 * Reading order: the position -> who, and what they see -> for how long ->
 * the line that confirms it -> shares already running -> what is never done.
 */
export default function SharingScreen({ onBack }) {
  const [on, setOn] = useState(sharing.draft.on);
  const [durationId, setDurationId] = useState(sharing.draft.durationId);
  const [active, setActive] = useState(sharing.active);
  const [created, setCreated] = useState(false);
  const [ending, setEnding] = useState(null);

  const toggle = (key) => {
    setCreated(false);
    setOn((prev) => (prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]));
  };

  const duration = sharing.durations.find((d) => d.id === durationId);
  // Keep the confirmation line in dimension order, not tap order, so the
  // sentence reads the same way as the list above it.
  const chosen = order.filter((k) => on.includes(k)).map((k) => dimensions[k].label);
  const summary = chosen.length
    ? `${sharing.draft.name} sees ${chosen.join(', ')} for ${duration.label}, read-only.`
    : 'Choose at least one area to share.';

  const endShare = (id) => {
    setActive((prev) => prev.filter((a) => a.id !== id));
    setEnding(null);
  };

  return (
    <ScrollView
      style={styles.page}
      contentContainerStyle={styles.content}
      accessibilityLabel="Sharing with someone else"
    >
      {isSample ? (
        <View style={styles.sampleBar}>
          <Text style={styles.sampleText}>
            Sample data — these people, dates and shares are invented.
          </Text>
        </View>
      ) : null}

      <View style={styles.header}>
        <Pressable
          onPress={onBack}
          accessibilityRole="button"
          accessibilityLabel="Back to your data"
          accessibilityHint="Returns to data and permissions"
          style={({ pressed }) => [styles.back, pressed && styles.pressed]}
        >
          <Text style={styles.backText}>Your data</Text>
        </Pressable>
        <Text style={styles.eyebrow}>SHARING</Text>
        <Text style={styles.title}>Show someone</Text>
      </View>

      {/* THE POSITION — oversized type, no container. */}
      <View style={styles.positionBlock}>
        <Text style={styles.position}>{sharing.position}</Text>
        <Text style={styles.positionDetail}>{sharing.positionDetail}</Text>
      </View>

      {/* WHO AND WHAT — a two-column hairline list. The right column ("they
          will not see") is the same weight as the left on purpose. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>
          For {sharing.draft.name}
          <Text style={styles.role}>  {sharing.draft.role}</Text>
        </Text>
        <Text style={styles.sectionLede}>
          Pick the areas. Each row says what they get and what stays with you.
        </Text>

        {sharing.scope.map((s, i) => {
          const d = dimensions[s.key];
          const isOn = on.includes(s.key);
          return (
            <View key={s.key} style={[styles.scopeRow, i > 0 && styles.ruled]}>
              <View style={styles.scopeHead}>
                {/* The hue sits beside the name, never instead of it. */}
                <View style={[styles.dot, { backgroundColor: d.hue }]} />
                <Text style={styles.scopeName}>{d.label}</Text>
                <Text style={styles.scopeState}>{isOn ? 'Shared' : 'Not shared'}</Text>
                <Switch
                  value={isOn}
                  onValueChange={() => toggle(s.key)}
                  accessibilityRole="switch"
                  accessibilityState={{ checked: isOn }}
                  accessibilityLabel={`${d.label}. ${isOn ? 'Shared' : 'Not shared'}.`}
                  accessibilityHint={`They would see ${s.shows}. They would not see ${s.hides}.`}
                  trackColor={{ true: colors.brand, false: colors.border }}
                  thumbColor={colors.surface}
                />
              </View>
              <View style={[styles.columns, !isOn && styles.dimmed]}>
                <View style={styles.col}>
                  <Text style={styles.colLabel}>THEY SEE</Text>
                  <Text style={styles.colText}>{s.shows}</Text>
                </View>
                <View style={styles.col}>
                  <Text style={styles.colLabel}>THEY DO NOT SEE</Text>
                  <Text style={styles.colText}>{s.hides}</Text>
                </View>
              </View>
            </View>
          );
        })}
      </View>

      {/* HOW LONG — a three-way segmented choice, labelled in days. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>For how long</Text>
        <View style={styles.segment} accessibilityRole="radiogroup">
          {sharing.durations.map((d) => {
            const selected = d.id === durationId;
            return (
              <Pressable
                key={d.id}
                onPress={() => {
                  setCreated(false);
                  setDurationId(d.id);
                }}
                accessibilityRole="radio"
                accessibilityState={{ selected }}
                accessibilityLabel={`${d.label}${selected ? ', selected' : ''}`}
                style={({ pressed }) => [
                  styles.segmentItem,
                  selected && styles.segmentOn,
                  pressed && styles.pressed,
                ]}
              >
                <Text style={[styles.segmentText, selected && styles.segmentTextOn]}>
                  {d.label}
                </Text>
              </Pressable>
            );
          })}
        </View>
        <Text style={styles.sectionLede}>
          Ninety days is the longest. When it runs out, the link stops working.
        </Text>
      </View>

      {/* THE CONFIRMATION — one sentence that restates the whole decision, so
          the tap that creates the share is the tap on a sentence they read. */}
      <View style={styles.section}>
        <Text style={styles.summary} accessibilityLiveRegion="polite">
          {created ? `Done. ${summary}` : summary}
        </Text>
        <Pressable
          onPress={() => setCreated(true)}
          disabled={!chosen.length || created}
          accessibilityRole="button"
          accessibilityState={{ disabled: !chosen.length || created }}
          accessibilityLabel={created ? 'Share created' : 'Create this share'}
          accessibilityHint="Makes a read-only link for this person only"
          style={({ pressed }) => [
            styles.primary,
            (!chosen.length || created) && styles.primaryOff,
            pressed && styles.pressed,
          ]}
        >
          <Text style={styles.primaryText}>
            {created ? 'Share created' : 'Create this share'}
          </Text>
        </Pressable>
      </View>

      {/* RUNNING NOW — each share with its time left drawn and said, and
          whether it has been opened. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Running now</Text>
        {active.length === 0 ? (
          <Text style={styles.sectionLede}>Nobody can see anything right now.</Text>
        ) : null}
        {active.map((a, i) => {
          const left = a.daysLeft <= 0 ? 'Ends today' : `${a.daysLeft} days left`;
          const used = Math.max(0, a.totalDays - a.daysLeft);
          const dims = a.dims.map((k) => dimensions[k].label).join(', ');
          return (
            <View key={a.id} style={[styles.activeRow, i > 0 && styles.ruled]}>
              <Text style={styles.activeName}>
                {a.name}
                <Text style={styles.role}>  {a.role}</Text>
              </Text>
              <Text style={styles.activeDims}>Sees {dims}</Text>
              <View
                style={styles.timeBar}
                accessible
                accessibilityRole="image"
                accessibilityLabel={`${left}. Started ${a.started}, ends ${a.ends}.`}
              >
                <View style={[styles.timeUsed, { flex: used || 0.001 }]} />
                <View style={[styles.timeLeft, { flex: a.daysLeft || 0.001 }]} />
              </View>
              <Text style={styles.activeMeta}>
                {left} · {a.started} to {a.ends}
              </Text>
              <Text style={styles.activeMeta}>{a.opened}</Text>

              {/* Ending asks once more, and the button names the person so
                  the wrong share is not ended by a stray tap. */}
              {ending === a.id ? (
                <View style={styles.endRow}>
                  <Pressable
                    onPress={() => endShare(a.id)}
                    accessibilityRole="button"
                    accessibilityLabel={`Confirm ending the share with ${a.name}`}
                    accessibilityHint="Their link stops working straight away"
                    style={({ pressed }) => [styles.endButton, pressed && styles.pressed]}
                  >
                    <Text style={styles.endText}>End it now</Text>
                  </Pressable>
                  <Pressable
                    onPress={() => setEnding(null)}
                    accessibilityRole="button"
                    accessibilityLabel="Keep this share"
                    style={({ pressed }) => [styles.keep, pressed && styles.pressed]}
                  >
                    <Text style={styles.keepText}>Keep it</Text>
                  </Pressable>
                </View>
              ) : (
                <Pressable
                  onPress={() => setEnding(a.id)}
                  accessibilityRole="button"
                  accessibilityLabel={`End the share with ${a.name}`}
                  accessibilityHint="Asks you to confirm first"
                  style={({ pressed }) => [styles.endLink, pressed && styles.pressed]}
                >
                  <Text style={styles.endLinkText}>End early</Text>
                </Pressable>
              )}
            </View>
          );
        })}
      </View>

      {/* NEVER — the one dark block. Flat negatives, no hedges. */}
      <View style={styles.neverPanel}>
        <Text style={styles.neverLabel}>WHAT A SHARE NEVER DOES</Text>
        {sharing.never.map((line) => (
          <Text key={line} style={styles.neverLine}>
            {line}
          </Text>
        ))}
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
  role: { ...type.small, color: colors.faint, fontWeight: '400' },

  scopeRow: { paddingVertical: space(2), gap: space(1.25) },
  ruled: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },
  scopeHead: { flexDirection: 'row', alignItems: 'center', gap: space(1) },
  dot: { width: 10, height: 10, borderRadius: 5 },
  scopeName: { ...type.body, color: colors.ink, fontWeight: '600', flex: 1 },
  scopeState: { ...type.small, color: colors.muted },
  columns: { flexDirection: 'row', gap: space(2) },
  dimmed: { opacity: 0.45 },
  col: { flex: 1, gap: 4 },
  colLabel: { ...type.label, fontSize: 10, color: colors.faint },
  colText: { ...type.small, color: colors.ink, lineHeight: 19 },

  segment: {
    flexDirection: 'row',
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.pill,
    padding: 3,
  },
  segmentItem: {
    flex: 1,
    paddingVertical: space(1.25),
    borderRadius: radius.pill,
    alignItems: 'center',
  },
  segmentOn: { backgroundColor: colors.ink },
  segmentText: { ...type.body, color: colors.ink },
  segmentTextOn: { color: colors.paper, fontWeight: '600' },

  summary: { fontSize: 20, lineHeight: 28, color: colors.ink, fontWeight: '500' },
  primary: {
    backgroundColor: colors.brand,
    borderRadius: radius.card,
    paddingVertical: space(2),
    alignItems: 'center',
  },
  primaryOff: { backgroundColor: colors.faint },
  primaryText: { ...type.body, color: colors.surface, fontWeight: '600' },

  activeRow: { paddingVertical: space(2), gap: space(0.75) },
  activeName: { ...type.body, color: colors.ink, fontWeight: '600' },
  activeDims: { ...type.body, color: colors.ink },
  timeBar: {
    flexDirection: 'row',
    height: 8,
    borderRadius: 4,
    overflow: 'hidden',
    marginTop: space(0.5),
    backgroundColor: colors.border,
  },
  timeUsed: { backgroundColor: colors.border },
  timeLeft: { backgroundColor: colors.brand },
  activeMeta: { ...type.small, color: colors.muted },

  endLink: { alignSelf: 'flex-start', paddingVertical: space(0.5) },
  endLinkText: { ...type.small, color: DANGER, fontWeight: '600' },
  endRow: { flexDirection: 'row', alignItems: 'center', gap: space(2), marginTop: space(0.5) },
  endButton: {
    borderWidth: 1,
    borderColor: DANGER,
    borderRadius: radius.card,
    paddingVertical: space(1),
    paddingHorizontal: space(2),
  },
  endText: { ...type.small, color: DANGER, fontWeight: '600' },
  keep: { paddingVertical: space(1) },
  keepText: { ...type.small, color: colors.brand, fontWeight: '600' },

  neverPanel: {
    backgroundColor: colors.ink,
    borderRadius: radius.card,
    padding: space(3),
    gap: space(1.25),
  },
  neverLabel: { ...type.label, color: colors.brandSoft, marginBottom: space(0.5) },
  neverLine: { ...type.body, color: colors.paper, lineHeight: 23 },
});

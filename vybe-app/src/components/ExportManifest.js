import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, space, type } from '../theme';

/**
 * What is actually in the file, grouped by what another product can do with it.
 *
 * The import screen sorted somebody else's history into three groups and said
 * the rule above each. This is the same list from the other side, so it uses
 * the same shape on purpose: a reader who has seen one should not have to
 * learn a second grammar to read the mirror of it.
 *
 * THE PORTABILITY WORD IS THE POINT, AND IT IS A WORD.
 * "Any product can read this" versus "Vybe's own conclusion" is the whole
 * argument of the screen, so it is set as text in its own column rather than
 * signalled by a tint. Read the list aloud and nothing is lost.
 */

export const KIND_ORDER = ['measured', 'derived', 'account'];

export const KIND_TITLE = {
  measured: 'Measured — any product can use these',
  derived: 'Vybe’s own conclusions — yours, but not evidence',
  account: 'What you agreed to',
};

export const KIND_RULE = {
  measured: 'A timestamp and a value. Nothing in these depends on Vybe being right.',
  derived:
    'Take them with you. The next product should treat them the way Vybe '
    + 'treats an imported score from somebody else: read, not computed with.',
  account: 'The record of what you turned on, so you can check it against what happened.',
};

export const PORTABLE_WORD = {
  measured: 'Portable',
  derived: 'Vybe only',
  account: 'Portable',
};

export function groupsByKind(groups) {
  return KIND_ORDER
    .map((kind) => ({ kind, items: groups.filter((g) => g.kind === kind) }))
    .filter((g) => g.items.length > 0);
}

export function totalRecords(groups) {
  return groups.reduce((sum, g) => sum + g.records, 0);
}

export function recordsOfKind(groups, kind) {
  return groups.filter((g) => g.kind === kind).reduce((sum, g) => sum + g.records, 0);
}

/** Which groups a given format can carry. Derived from each group's own list. */
export function groupsForFormat(groups, formatId) {
  return groups.filter((g) => g.formats.includes(formatId));
}

function countLabel(n) {
  if (n >= 1000000) return `${(n / 1000000).toFixed(2)}M records`;
  if (n >= 1000) return `${Math.round(n / 1000)}k records`;
  return `${n} ${n === 1 ? 'record' : 'records'}`;
}

export default function ExportManifest({ groups, openId, onToggle }) {
  return (
    <View style={styles.wrap}>
      {groupsByKind(groups).map((section) => (
        <View key={section.kind} style={styles.section}>
          <Text style={styles.sectionTitle}>{KIND_TITLE[section.kind]}</Text>
          <Text style={styles.sectionRule}>{KIND_RULE[section.kind]}</Text>
          <View style={styles.list}>
            {section.items.map((g, i) => {
              const open = g.id === openId;
              return (
                <Pressable
                  key={g.id}
                  onPress={() => onToggle && onToggle(open ? null : g.id)}
                  accessibilityRole="button"
                  accessibilityState={{ expanded: open }}
                  accessibilityLabel={
                    `${g.label}. ${countLabel(g.records)}. `
                    + `${PORTABLE_WORD[g.kind]}. `
                    + `Available as ${g.formats.map((f) => f.toUpperCase()).join(' and ')}.`
                  }
                  accessibilityHint={open ? 'Hides the detail' : 'Shows what is in this and why'}
                  style={({ pressed }) => [
                    styles.row,
                    i > 0 && styles.ruled,
                    pressed && styles.pressed,
                  ]}
                >
                  <View style={styles.top}>
                    <View style={styles.body}>
                      <Text style={styles.label}>{g.label}</Text>
                      <Text style={styles.formats}>
                        {g.formats.map((f) => f.toUpperCase()).join(' · ')}
                      </Text>
                    </View>
                    <Text style={styles.count}>{countLabel(g.records)}</Text>
                  </View>
                  {open ? (
                    <View style={styles.detailBlock}>
                      <Text style={styles.detail}>{g.detail}</Text>
                      <Text style={styles.note}>{g.note}</Text>
                    </View>
                  ) : null}
                </Pressable>
              );
            })}
          </View>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: space(4) },
  section: { gap: space(0.5) },
  sectionTitle: { ...type.title, color: colors.ink },
  sectionRule: { ...type.small, color: colors.muted, lineHeight: 20 },
  list: { marginTop: space(1) },

  row: { paddingVertical: space(1.75), gap: space(1) },
  ruled: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },
  pressed: { opacity: 0.6 },

  top: { flexDirection: 'row', alignItems: 'flex-start', gap: space(2) },
  body: { flex: 1, gap: 2 },
  label: { ...type.body, color: colors.ink, fontWeight: '600' },
  formats: { ...type.small, color: colors.faint, fontWeight: '600', letterSpacing: 0.6 },
  // Tabular figures in a fixed column, so a million and eighty-eight are
  // comparable without reading them twice.
  count: {
    ...type.small,
    color: colors.muted,
    fontWeight: '600',
    fontVariant: ['tabular-nums'],
    textAlign: 'right',
    width: space(14),
  },

  detailBlock: { gap: space(0.5) },
  detail: { ...type.small, color: colors.ink, lineHeight: 21 },
  note: { ...type.small, color: colors.muted, lineHeight: 21 },
});

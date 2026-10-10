import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, space, type } from '../theme';

/**
 * Imported history, sorted into what Vybe will compute with, what it will only
 * draw, and what it will not take at all.
 *
 * THE GROUPING IS THE ARGUMENT, SO THE GROUPS ARE HEADINGS, NOT COLOURS.
 * Each group gets a stated heading and a one-line rule, and every row inside it
 * carries its own reason. Strip the styling out and the screen still says the
 * same thing — which is the test a health product should pass, because the
 * person who most needs to understand this screen may be hearing it read aloud.
 *
 * Day counts use tabular figures and sit in a fixed right column so the sizes
 * of three years and eighteen days are comparable at a glance.
 */

export const BUCKET_ORDER = ['used', 'shown', 'ignored'];

export const BUCKET_TITLE = {
  used: 'Vybe will compute with these',
  shown: 'Vybe will show these and never compute with them',
  ignored: 'Vybe is not importing these',
};

export const BUCKET_RULE = {
  used: 'A clock reading or a direct measurement, comparable between devices.',
  shown: 'Another product’s estimate. Worth seeing, not worth building on.',
  ignored: 'Nothing here can be checked, so none of it is kept.',
};

export function bucketsOf(records) {
  return BUCKET_ORDER.map((key) => ({
    key,
    items: records.filter((r) => r.bucket === key),
  })).filter((g) => g.items.length > 0);
}

/** The longest run of history Vybe can actually compute with. */
export function usableDaysOf(records) {
  const used = records.filter((r) => r.bucket === 'used');
  return used.reduce((most, r) => Math.max(most, r.days), 0);
}

/**
 * What a capability can do with this import. Derived from the buckets and the
 * day counts, never stored — the whole point of the three groups is that a
 * capability cannot call itself ready while its input sits in `shown`.
 *
 * Returns one of:
 *   ready    — every input is usable and long enough
 *   waiting  — inputs are usable, but one is too short (carries the shortfall)
 *   blocked  — an input is in `shown` or `ignored` (carries which, and why)
 */
export function statusFor(capability, records) {
  const inputs = capability.needs.map((id) => records.find((r) => r.id === id));

  const blocker = inputs.find((r) => !r || r.bucket !== 'used');
  if (blocker) {
    return { kind: 'blocked', blocker };
  }

  const shortest = inputs.reduce(
    (min, r) => (min === null || r.days < min.days ? r : min),
    null,
  );
  if (shortest.days >= capability.needsDays) {
    return { kind: 'ready', days: shortest.days };
  }
  return {
    kind: 'waiting',
    days: shortest.days,
    short: capability.needsDays - shortest.days,
    input: shortest,
  };
}

function daysLabel(days) {
  if (days === 0) return 'none yet';
  if (days === 1) return '1 day';
  if (days < 400) return `${days} days`;
  const years = Math.floor(days / 365);
  return `${days} days · about ${years} ${years === 1 ? 'year' : 'years'}`;
}

export default function ImportBuckets({ records, selectedId, onSelect }) {
  return (
    <View style={styles.wrap}>
      {bucketsOf(records).map((group) => (
        <View key={group.key} style={styles.group}>
          <Text style={styles.groupTitle}>{BUCKET_TITLE[group.key]}</Text>
          <Text style={styles.groupRule}>{BUCKET_RULE[group.key]}</Text>
          <View style={styles.list}>
            {group.items.map((r, i) => {
              const open = r.id === selectedId;
              return (
                <Pressable
                  key={r.id}
                  onPress={() => onSelect && onSelect(open ? null : r.id)}
                  accessibilityRole="button"
                  accessibilityState={{ expanded: open }}
                  accessibilityLabel={`${r.label}. ${daysLabel(r.days)}. From ${r.from}.`}
                  accessibilityHint={
                    open ? 'Hides why this is here' : 'Shows why Vybe put this here'
                  }
                  style={({ pressed }) => [
                    styles.row,
                    i > 0 && styles.ruled,
                    pressed && styles.pressed,
                  ]}
                >
                  <View style={styles.rowTop}>
                    <View style={styles.rowBody}>
                      <Text style={styles.rowLabel}>{r.label}</Text>
                      <Text style={styles.rowFrom}>{r.from}</Text>
                    </View>
                    <Text style={styles.rowDays}>{daysLabel(r.days)}</Text>
                  </View>
                  {open ? <Text style={styles.rowWhy}>{r.why}</Text> : null}
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
  group: { gap: space(0.5) },
  groupTitle: { ...type.title, color: colors.ink },
  groupRule: { ...type.small, color: colors.muted, lineHeight: 20 },
  list: { marginTop: space(1) },

  row: { paddingVertical: space(2), gap: space(1) },
  ruled: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },
  pressed: { opacity: 0.6 },

  rowTop: { flexDirection: 'row', alignItems: 'flex-start', gap: space(2) },
  rowBody: { flex: 1, gap: 2 },
  rowLabel: { ...type.body, color: colors.ink, fontWeight: '600' },
  rowFrom: { ...type.small, color: colors.faint },
  // Fixed column and tabular figures, so three years and eighteen days are
  // comparable without reading the numbers twice.
  rowDays: {
    ...type.small,
    color: colors.muted,
    fontWeight: '600',
    fontVariant: ['tabular-nums'],
    textAlign: 'right',
    width: space(17),
  },
  rowWhy: { ...type.small, color: colors.muted, lineHeight: 21 },
});

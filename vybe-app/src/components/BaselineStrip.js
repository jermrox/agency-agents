import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors, space, type } from '../theme';

/**
 * One vital, drawn against the wearer's own 30-day band.
 *
 * WHY A STRIP AND NOT A NUMBER
 * Every other product shows "60 bpm" and a colour. The number is meaningless
 * on its own: 60 is high for one person and low for the next. The claim Vybe
 * makes is positional — where today sits inside *your* range — so the form
 * has to show a range with a mark on it. A strip does that with no chart
 * library: three Views whose widths are fractions of the band.
 *
 * The band itself is drawn a little wider than the 30-day low and high so a
 * reading at the edge is visibly at the edge rather than falling off it.
 *
 * Colour never carries meaning alone. The strip is the same ink for every
 * vital; the words in `reading` say "top of your band", and `watch` adds the
 * word WATCH as text, not a hue. A reader who cannot separate hues, or who
 * hears this through a screen reader, gets the full claim.
 */
const PAD = 0.15; // the band is drawn 15% wider than the 30-day range each side

function position(v, low, high) {
  const span = (high - low) || 1;
  const left = low - span * PAD;
  const right = high + span * PAD;
  const p = (v - left) / (right - left);
  return Math.max(0, Math.min(1, p));
}

export function formatValue(item, v) {
  if (item.clock) {
    // Hours after midnight → "03:30". Sample data keeps it to quarter hours.
    const h = Math.floor(v);
    const m = Math.round((v - h) * 60);
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
  }
  const sign = item.id === 'temp' && v > 0 ? '+' : '';
  const n = Number.isInteger(v) ? String(v) : v.toFixed(1);
  return `${sign}${n}${item.unit ? ` ${item.unit}` : ''}`;
}

export default function BaselineStrip({ item, first }) {
  const bandStart = position(item.low, item.low, item.high);
  const bandEnd = position(item.high, item.low, item.high);
  const mid = position(item.median, item.low, item.high);
  const today = position(item.today, item.low, item.high);

  const label = `${item.label}. Today ${formatValue(item, item.today)}. ${item.reading}. Your usual is ${formatValue(item, item.median)}, your band runs ${formatValue(item, item.low)} to ${formatValue(item, item.high)}.${item.watch ? ' Worth watching.' : ''}`;

  return (
    <View
      style={[styles.row, !first && styles.ruled]}
      accessible
      accessibilityRole="text"
      accessibilityLabel={label}
    >
      <View style={styles.top}>
        <Text style={styles.label}>{item.label}</Text>
        <Text style={styles.value}>{formatValue(item, item.today)}</Text>
      </View>

      {/* The strip: the track is the drawn range, the band is the 30-day low to
          high, the tick is the median, the dot is today. Widths are percentages
          of the track, so it needs no measurement and no chart library. */}
      <View style={styles.track} aria-hidden>
        <View style={[styles.band, { left: `${bandStart * 100}%`, width: `${(bandEnd - bandStart) * 100}%` }]} />
        <View style={[styles.tick, { left: `${mid * 100}%` }]} />
        <View style={[styles.dot, { left: `${today * 100}%` }]} />
      </View>

      <View style={styles.bottom}>
        <Text style={styles.reading}>
          {item.watch ? <Text style={styles.watch}>WATCH · </Text> : null}
          {item.reading}
        </Text>
        <Text style={styles.range}>
          usual {formatValue(item, item.median)} · band {formatValue(item, item.low)}–{formatValue(item, item.high)}
        </Text>
      </View>
    </View>
  );
}

const DOT = 14;

const styles = StyleSheet.create({
  row: { paddingVertical: space(2), gap: space(1) },
  ruled: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },
  top: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline', gap: space(2) },
  label: { ...type.body, color: colors.ink, fontWeight: '600', flex: 1 },
  value: { ...type.title, color: colors.ink, fontVariant: ['tabular-nums'] },

  track: { height: DOT, justifyContent: 'center' },
  band: { position: 'absolute', height: 6, borderRadius: 3, backgroundColor: colors.border },
  tick: { position: 'absolute', width: 2, height: DOT, marginLeft: -1, backgroundColor: colors.faint },
  dot: {
    position: 'absolute', width: DOT, height: DOT, borderRadius: DOT / 2, marginLeft: -DOT / 2,
    backgroundColor: colors.ink, borderWidth: 2, borderColor: colors.paper,
  },

  bottom: { gap: 2 },
  reading: { ...type.small, color: colors.ink },
  watch: { ...type.label, color: colors.ink },
  range: { ...type.small, color: colors.faint, fontVariant: ['tabular-nums'] },
});

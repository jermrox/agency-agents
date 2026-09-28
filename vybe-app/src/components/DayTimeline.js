import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, space, type } from '../theme';

/**
 * One day of eating, laid out on real clock time.
 *
 * WHY A TIMELINE AND NOT A LIST
 * The claim this screen makes is about *when* food landed, and a list of meals
 * in order cannot show that: it spaces breakfast and lunch the same distance
 * apart as lunch and a dinner six hours later. Put the same five meals on an
 * axis and the shape of the day is the argument -- a long empty afternoon, then
 * a meal pressed up against sleep.
 *
 * Drawn with Views measured in pixels after onLayout rather than a charting
 * package. Every RN chart library pulls in react-native-svg, and most pull
 * reanimated and gesture-handler behind it: three native dependencies and an
 * Expo prebuild to place five rectangles on a line.
 *
 * `hue` is passed in rather than imported, so theme.js stays the only file that
 * says what colour a dimension is.
 */

/** "21:25" -> minutes since midnight. */
export function minutesOf(hhmm) {
  const [h, m] = String(hhmm).split(':').map(Number);
  return h * 60 + m;
}

/** 95 -> "1h 35m", 40 -> "40m". Used for every duration on the screen. */
export function formatSpan(minutes) {
  const total = Math.max(0, Math.round(minutes));
  const h = Math.floor(total / 60);
  const m = total % 60;
  if (h === 0) return `${m}m`;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}m`;
}

/**
 * "07:05" -> "7:05am", for reading aloud and for captions.
 *
 * The window can end at "24:00", which is midnight and not noon -- so wrap
 * before splitting the hour, or the axis cheerfully labels the end of the day
 * 12:00pm.
 */
export function clockLabel(hhmm) {
  const mins = minutesOf(hhmm) % 1440;
  const h24 = Math.floor(mins / 60);
  const m = String(mins % 60).padStart(2, '0');
  const suffix = h24 < 12 ? 'am' : 'pm';
  const h12 = h24 % 12 === 0 ? 12 : h24 % 12;
  return `${h12}:${m}${suffix}`;
}

// The marker has to stay tappable. A ten-minute coffee is under 1% of an
// eighteen-hour day, which is three pixels -- honest as geometry, impossible as
// a touch target. So the span bar keeps the true width and the numbered marker
// sits on the midpoint at a size a thumb can actually hit.
const MARKER = 26;
const TICK_HOURS = 3;

export default function DayTimeline({ meals, sleep, hue, selectedId, onSelect }) {
  const [width, setWidth] = useState(0);

  // The window starts on the hour before the first meal and ends on the hour
  // after lights out, so the day is framed by the person's own day rather than
  // by midnight-to-midnight with six empty hours at each end.
  const firstStart = minutesOf(meals[0].start);
  const lightsOut = minutesOf(sleep.lightsOut);
  const from = Math.floor(firstStart / 60) * 60 - 60;
  const to = Math.min(1440, Math.ceil(lightsOut / 60) * 60 + 60);
  const span = to - from;

  const x = (mins) => ((mins - from) / span) * width;

  const eatFrom = firstStart;
  const eatTo = minutesOf(meals[meals.length - 1].end);

  const ticks = [];
  for (let t = Math.ceil(from / 60 / TICK_HOURS) * 60 * TICK_HOURS; t <= to; t += 60 * TICK_HOURS) {
    ticks.push(t);
  }

  const summary = meals
    .map((m) => `${m.name} at ${clockLabel(m.start)}`)
    .join(', ');

  return (
    <View>
      <View
        style={styles.plot}
        onLayout={(e) => setWidth(e.nativeEvent.layout.width)}
        accessible
        accessibilityRole="image"
        accessibilityLabel={
          `Your day on a clock, ${clockLabel(`${from / 60}:00`)} to ${clockLabel(`${to / 60}:00`)}. `
          + `${summary}. Asleep from ${clockLabel(sleep.lightsOut)}.`
        }
      >
        {width > 0 ? (
          <>
            {/* The eating window, as one continuous band: its length is itself
                a fact about the day, stated in words in the legend below. */}
            <View
              style={[
                styles.band,
                { left: x(eatFrom), width: x(eatTo) - x(eatFrom), backgroundColor: `${hue}22` },
              ]}
            />
            {/* Asleep. Grey rather than a hue, because sleep belongs to Restore
                and borrowing its colour here would imply a reading. */}
            <View
              style={[
                styles.band,
                styles.sleepBand,
                { left: x(lightsOut), width: Math.max(0, width - x(lightsOut)) },
              ]}
            />
            <View style={styles.baseline} />
            {meals.map((m, i) => {
              const s = x(minutesOf(m.start));
              const e = x(minutesOf(m.end));
              const mid = (s + e) / 2;
              const selected = m.id === selectedId;
              return (
                <React.Fragment key={m.id}>
                  <View
                    style={[styles.spanBar, { left: s, width: Math.max(2, e - s), backgroundColor: hue }]}
                  />
                  <Pressable
                    onPress={() => onSelect && onSelect(m.id)}
                    hitSlop={10}
                    accessibilityRole="button"
                    accessibilityState={{ selected }}
                    accessibilityLabel={
                      `${m.name}, ${clockLabel(m.start)} to ${clockLabel(m.end)}. ${m.items.join(', ')}.`
                    }
                    accessibilityHint="Shows what this meal was"
                    style={[
                      styles.marker,
                      {
                        left: Math.max(0, Math.min(width - MARKER, mid - MARKER / 2)),
                        borderColor: hue,
                        backgroundColor: selected ? hue : colors.surface,
                      },
                    ]}
                  >
                    {/* The number is the marker's name: it maps to the line
                        under the axis, so the meal is identifiable without
                        tapping and without cramming text into 26 pixels. */}
                    <Text style={[styles.markerNum, { color: selected ? colors.paper : hue }]}>
                      {i + 1}
                    </Text>
                  </Pressable>
                </React.Fragment>
              );
            })}
          </>
        ) : null}
      </View>

      {/* The axis, drawn only once the plot has a width to place it against. */}
      <View style={styles.axis}>
        {width > 0
          ? ticks.map((t) => (
              <Text
                key={t}
                style={[styles.tick, { left: Math.max(0, Math.min(width - 44, x(t) - 22)) }]}
              >
                {clockLabel(`${Math.floor(t / 60)}:00`)}
              </Text>
            ))
          : null}
      </View>

      {/* Both bands explained in words. A tinted rectangle tells somebody who
          cannot separate these colours nothing at all. */}
      <Text style={styles.legend}>
        {`Numbers: ${meals.map((m, i) => `${i + 1} ${m.name.toLowerCase()}`).join(' · ')}. `}
        {`Tinted band: your eating window, ${formatSpan(eatTo - eatFrom)}. `}
        {`Grey: asleep from ${clockLabel(sleep.lightsOut)}.`}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  // Three stacked registers in 66pt: the bands and markers share the top 36,
  // the day's line rules them off, and the true meal durations sit just under
  // it. Keeping the duration bars clear of the markers matters -- a 26pt
  // marker would otherwise cover a 10-minute coffee completely.
  plot: { height: 66 },
  band: { position: 'absolute', top: 0, height: 36, borderRadius: 4 },
  sleepBand: { backgroundColor: '#E6E3DA' },
  baseline: {
    position: 'absolute', top: 36, left: 0, right: 0,
    height: StyleSheet.hairlineWidth, backgroundColor: colors.border,
  },
  spanBar: { position: 'absolute', top: 40, height: 6, borderRadius: 3 },
  marker: {
    position: 'absolute',
    top: 5,
    width: MARKER,
    height: MARKER,
    borderRadius: MARKER / 2,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
  },
  markerNum: { fontSize: 12, fontWeight: '700' },
  axis: { height: 18 },
  tick: {
    position: 'absolute',
    width: 44,
    textAlign: 'center',
    ...type.small,
    fontSize: 11,
    color: colors.faint,
    fontVariant: ['tabular-nums'],
  },
  legend: { ...type.small, color: colors.muted, marginTop: space(1) },
});

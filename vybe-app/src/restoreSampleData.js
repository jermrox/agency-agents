/**
 * Sample data for the Restore detail screen.
 *
 * Kept in its own module, and every screen that renders it says on-screen
 * that it is sample data. An invented health number that looks real is the
 * one bug in this app that could actually hurt someone.
 */
export const isSample = true;

export const restoreDay = {
  date: 'Monday 21 September',
  // The headline is a sentence, not a score. Vybe's whole position is that a
  // number without a reason is what everyone else already ships.
  answer:
    'You are less recovered than usual, and the likeliest reason is the 1am bedtime after Saturday.',
  confidence: 'Moderate confidence',
  confidenceWhy:
    'Three nights of data since the change, and one known context event. More nights would raise this.',

  // Evidence rows. `direction` is for the arrow glyph; `reading` always spells
  // the direction out in words so colour and shape are never the only signal.
  evidence: [
    { id: 'hrv',      label: 'Overnight HRV',      value: '41 ms',    reading: 'Down 18% on your 30-day average',  direction: 'down', concern: true },
    { id: 'rhr',      label: 'Resting heart rate', value: '58 bpm',   reading: 'Up 4 bpm on your baseline',        direction: 'up',   concern: true },
    { id: 'duration', label: 'Time asleep',        value: '5h 42m',   reading: 'Short of your 7h 10m usual',       direction: 'down', concern: true },
    { id: 'timing',   label: 'Bedtime',            value: '01:04',    reading: 'Two hours later than your median', direction: 'up',   concern: true },
    { id: 'resp',     label: 'Respiration',        value: '14.2 /min', reading: 'Within your normal range',        direction: 'flat', concern: false },
  ],

  // Context is the differentiator: things no sensor can read. The user or a
  // connected source supplied each one, and the screen says which.
  context: [
    { id: 'c1', text: 'Late dinner Saturday, finished 22:40', source: 'You logged this' },
    { id: 'c2', text: 'Two drinks Saturday evening',          source: 'You logged this' },
    { id: 'c3', text: 'No travel, no schedule change',        source: 'From your calendar' },
  ],

  // One action, not a list. A list of six suggestions is a way of not deciding.
  action: {
    text: 'Aim for lights out by 22:30 tonight.',
    why: 'On the four previous occasions your bedtime slipped past midnight, an early night the following day returned your HRV to baseline within two days.',
  },

  // The loop closing on itself — the part competitors do not do.
  lastOutcome: {
    text: 'Last time Vybe suggested this, you did it, and your HRV recovered in one day rather than the usual two.',
    when: '2 weeks ago',
  },
};

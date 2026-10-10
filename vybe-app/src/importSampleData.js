/**
 * Sample data for the history-import screen.
 *
 * Kept in its own module, and the screen says on-screen that it is sample
 * data. An invented health number that looks real is the one bug in this app
 * that could actually hurt someone. Note what is and is not invented here:
 * these are RECORD COUNTS and date spans, not readings. No heart rate, no
 * sleep duration, no score. The screen is about what Vybe will do with a pile
 * of history, so it never needs to show a single health value.
 *
 * WHAT THIS SCREEN IS ARGUING
 * `OnboardingScreen` asks which sources you will connect. This is the next
 * screen in that lane and the one nobody builds: you connect a phone health
 * store with three years in it, and something has to decide what that history
 * is worth.
 *
 * The convenient answer is all of it. Import everything, draw one seamless
 * chart back to 2023, compute a baseline from it. That is wrong in a way the
 * person cannot see: another vendor's sleep stages and HRV come from a
 * different sensor sampled at different moments through an unpublished
 * algorithm. A baseline built on somebody else's estimate is an estimate with
 * a number on it, and every later sentence that says "below your baseline" is
 * then measuring Vybe against a competitor's guess.
 *
 * So history lands in three places, and the screen says which and why:
 *   used     — a clock reading or a direct measurement, comparable across devices
 *   shown    — kept and drawn, never computed with
 *   ignored  — not imported at all
 *
 * NOTHING ON THE SCREEN IS A STORED VERDICT. Which capabilities this history
 * unlocks is derived from the buckets and the day counts against each
 * capability's own stated requirement, so a capability cannot claim to be
 * ready while the record it depends on sits in `shown`.
 */
export const isSample = true;

export const source = {
  name: 'Apple Health',
  spanLabel: '3 years, 2 months',
  firstDate: '14 August 2023',
  lastDate: 'yesterday',
  deviceNote:
    'Written by an Apple Watch, your phone, and two other apps you have used '
    + 'along the way.',
};

/**
 * `days` is the number of days that record type actually covers, not the
 * number of records. `bucket` is the decision; `why` is the reason, in the
 * words the screen shows.
 */
export const records = [
  {
    id: 'sleepTiming',
    label: 'Sleep start and end times',
    from: 'Apple Watch, phone',
    days: 1043,
    bucket: 'used',
    why:
      'Bedtime and wake time are a clock reading. Any device that records them '
      + 'records the same thing, so Vybe can compute with these directly.',
  },
  {
    id: 'rhr',
    label: 'Resting heart rate',
    from: 'Apple Watch',
    days: 1120,
    bucket: 'used',
    why:
      'Measured rather than estimated, and comparable across devices to within '
      + 'a few beats. Three years of it is the most valuable thing in this import.',
  },
  {
    id: 'steps',
    label: 'Steps and movement',
    from: 'Apple Watch, phone',
    days: 1118,
    bucket: 'used',
    why: 'A step is a step. Devices disagree a little and not enough to matter.',
  },
  {
    id: 'meals',
    label: 'Meal times you logged',
    from: 'Nothing yet',
    days: 0,
    bucket: 'used',
    why:
      'Vybe can use this the day you start logging. Nothing in your history '
      + 'has it, which is why one of the patterns below is still out of reach.',
  },
  {
    id: 'sleepStages',
    label: 'Sleep stages — deep, REM, core',
    from: 'Apple Watch',
    days: 1043,
    bucket: 'shown',
    why:
      'Another vendor’s estimate, from a different sensor, through an '
      + 'algorithm nobody has published. Vybe will draw this history for you '
      + 'and will not build a baseline from it: a baseline made of somebody '
      + 'else’s guess is a guess with a number on it.',
  },
  {
    id: 'hrv',
    label: 'Heart-rate variability',
    from: 'Apple Watch',
    days: 892,
    bucket: 'shown',
    why:
      'HRV depends almost entirely on when and how it was sampled. Readings '
      + 'taken on another schedule are not interchangeable with Vybe’s, so '
      + 'they are history here rather than evidence.',
  },
  {
    id: 'readiness',
    label: 'Readiness and recovery scores',
    from: 'Two other apps',
    days: 640,
    bucket: 'ignored',
    why:
      'A number produced by a formula its own makers have not published. There '
      + 'is nothing in it Vybe can check or take apart, so it is not imported.',
  },
  {
    id: 'weightManual',
    label: 'Weight, typed in by hand',
    from: 'Phone',
    days: 18,
    bucket: 'ignored',
    why:
      'Eighteen entries across three years. Too sparse to trend, and hand-typed '
      + 'numbers carry typos that a trend line would treat as real.',
  },
  {
    id: 'bpSingle',
    label: 'One blood-pressure reading',
    from: 'Phone',
    days: 1,
    bucket: 'ignored',
    why:
      'A single reading from 2024. Vybe does not do blood pressure and will not '
      + 'hold on to a stray clinical number it has no way to interpret.',
  },
];

/**
 * What the history buys. `needs` names the records a capability depends on and
 * `needsDays` how much of each it wants; the screen works out the rest, so a
 * capability can never announce itself ready while its input sits in `shown`.
 */
export const capabilities = [
  {
    id: 'rhrBase',
    label: 'Your own resting-heart-rate baseline',
    needs: ['rhr'],
    needsDays: 28,
  },
  {
    id: 'sleepBase',
    label: 'Your own sleep-timing baseline',
    needs: ['sleepTiming'],
    needsDays: 28,
  },
  {
    id: 'moveTrend',
    label: 'Movement trends across months',
    needs: ['steps'],
    needsDays: 84,
  },
  {
    id: 'deepTrend',
    label: 'Deep-sleep trends',
    needs: ['sleepStages'],
    needsDays: 28,
  },
  {
    id: 'hrvTrend',
    label: 'HRV week on week',
    needs: ['hrv'],
    needsDays: 28,
  },
  {
    id: 'latePattern',
    label: 'Whether eating late costs you sleep',
    needs: ['sleepTiming', 'meals'],
    needsDays: 21,
  },
];

export const whatHappensNext =
  'Everything in the first group starts working the moment the Band is on your '
  + 'wrist. The second group becomes available as Vybe records it itself — not '
  + 'because the old numbers were bad, but because Vybe can only stand behind '
  + 'the ones it took.';

export const restraint =
  'Vybe is not throwing your history away, and it is not pretending to own it. '
  + 'Three years of somebody else’s readings are worth looking at and are '
  + 'not worth building a claim on. Any product that silently merges the two is '
  + 'about to tell you that you are below a baseline it assembled out of a '
  + 'competitor’s estimates.';

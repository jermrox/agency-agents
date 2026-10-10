/**
 * Sample data for the outcome review.
 *
 * Kept in its own module, and the screen says on-screen that it is sample
 * data. An invented health number that looks real is the one bug in this app
 * that could actually hurt someone.
 *
 * WHAT THIS SCREEN IS ARGUING
 * Every wellness product gives advice. Almost none of them come back and say
 * whether it worked, because the honest answer is sometimes no, and a product
 * grading its own homework will always pass.
 *
 * Two rules make this screen worth shipping.
 *
 * FIRST: the success criterion is recorded BEFORE the attempt. Each row below
 * carries the range Vybe predicted at the time, in the units it predicted, over
 * a stated window. Deciding afterwards what counted as working is how every
 * wellness app wins every time, and it is why nobody believes them.
 *
 * SECOND: not doing it is a third outcome, not a failure. If the person did not
 * try the suggestion then the advice was never tested — Vybe learned nothing and
 * says so, rather than scoring it against them.
 *
 * Nothing here stores a verdict. `called it` / `missed` / `no test` and the
 * headline tally are derived on screen from `adherence`, `actual` and the
 * predicted range, so the headline cannot drift away from the rows under it.
 */
export const isSample = true;

export const outcomes = {
  window: 'Eight weeks, 4 August to 22 September',

  /**
   * `adherence`: 'full' | 'partial' | 'none'.
   *   none    — never tried, so there is nothing to score
   *   partial — tried on some days; counts as a test and says so
   *   full    — tried as suggested
   *
   * `predicted` is what Vybe committed to at the time. `actual` is what
   * happened. A row with adherence 'none' carries actual: null, because there
   * is no measurement to compare — not a zero.
   */
  attempts: [
    {
      id: 'a1',
      date: 'Mon 4 Aug',
      dimension: 'restore',
      suggestion: 'Lights out by 22:30 for three nights.',
      predicted: { low: 44, high: 50, unit: 'ms', metric: 'Overnight HRV', window: 'within three nights' },
      adherence: 'full',
      actual: 47,
      note: 'Three nights at 22:20, 22:35 and 22:25.',
    },
    {
      id: 'a2',
      date: 'Thu 7 Aug',
      dimension: 'move',
      suggestion: 'Take an easy day instead of the third hard session.',
      predicted: { low: 54, high: 57, unit: 'bpm', metric: 'Resting heart rate', window: 'next morning' },
      adherence: 'full',
      actual: 59,
      note: 'You did the easy day. The number did not come back.',
      learned:
        'Vybe now waits two mornings before judging a rest day. One morning was '
        + 'its own mistake, not yours — resting heart rate lags the recovery it '
        + 'is supposed to be reporting.',
    },
    {
      id: 'a3',
      date: 'Mon 11 Aug',
      dimension: 'nourish',
      suggestion: 'Finish eating by 20:00 on work nights.',
      predicted: { low: 62, high: 72, unit: 'min', metric: 'Deep sleep', window: 'across the week' },
      adherence: 'full',
      actual: 68,
      note: 'Four of five work nights finished before 20:00.',
    },
    {
      id: 'a4',
      date: 'Fri 15 Aug',
      dimension: 'restore',
      suggestion: 'No screens after 22:00.',
      predicted: { low: 9, high: 16, unit: 'min', metric: 'Time to fall asleep', window: 'across the week' },
      adherence: 'none',
      actual: null,
      note: 'Not tried. Vybe learned nothing from this one, which is its own kind of answer.',
    },
    {
      id: 'a5',
      date: 'Tue 19 Aug',
      dimension: 'move',
      suggestion: 'A twenty-minute walk after lunch, five days.',
      predicted: { low: 8, high: 14, unit: 'min', metric: 'Awake after falling asleep', window: 'across the week' },
      adherence: 'partial',
      actual: 19,
      note: 'Three days of five. Counts as a test, and a thin one.',
      learned:
        'Nothing yet. Three days is not enough to tell a weak suggestion from a '
        + 'half-done one, and Vybe will not pretend otherwise.',
    },
    {
      id: 'a6',
      date: 'Sat 23 Aug',
      dimension: 'nourish',
      suggestion: 'Last coffee by 14:00.',
      predicted: { low: 9, high: 16, unit: 'min', metric: 'Time to fall asleep', window: 'across the week' },
      adherence: 'full',
      actual: 12,
      note: 'Held every day except the Thursday.',
    },
    {
      id: 'a7',
      date: 'Wed 27 Aug',
      dimension: 'connect',
      suggestion: 'One evening with work email closed.',
      predicted: { low: 44, high: 52, unit: 'ms', metric: 'Overnight HRV', window: 'that night' },
      adherence: 'none',
      actual: null,
      note: 'Not tried. Three of the last ten suggestions have gone this way.',
    },
    {
      id: 'a8',
      date: 'Mon 1 Sep',
      dimension: 'restore',
      suggestion: 'Same wake time every day, including the weekend.',
      predicted: { low: 0, high: 25, unit: 'min', metric: 'Bedtime variation', window: 'across the week' },
      adherence: 'full',
      actual: 18,
      note: 'The weekend held, which is the part that usually does not.',
    },
    {
      id: 'a9',
      date: 'Thu 11 Sep',
      dimension: 'move',
      suggestion: 'Swap one hard session for an easy one this week.',
      predicted: { low: 6, high: 12, unit: '%', metric: 'HRV, week on week', window: 'next week' },
      adherence: 'full',
      actual: 3,
      note: 'You made the swap. It moved, but less than Vybe said it would.',
      learned:
        'Vybe was too confident about the size of the effect. The direction was '
        + 'right and the number was not, so it has widened the range it predicts '
        + 'from a single session change.',
    },
    {
      id: 'a10',
      date: 'Tue 22 Sep',
      dimension: 'nourish',
      suggestion: 'Protein at breakfast, four mornings.',
      predicted: { low: 62, high: 72, unit: 'min', metric: 'Deep sleep', window: 'across the week' },
      adherence: 'none',
      actual: null,
      note: 'Not tried.',
    },
  ],

  /**
   * The reading of the tally that the person should take away, written for the
   * honest case rather than the flattering one.
   */
  reading:
    'Vybe is right more often than not, and not by much. Four of seven is a '
    + 'record worth showing you rather than hiding, because it tells you how '
    + 'much weight to put on tomorrow’s suggestion.',

  adherenceNote:
    'Three suggestions were never tried. That is not a failing grade — it is the '
    + 'clearest signal on this screen that Vybe asked for something that did not '
    + 'fit your week.',

  restraint:
    'Seven tests is a handful, not a study. This is a record of what happened '
    + 'when you changed one thing, in your own data, with the criterion written '
    + 'down first. It is not evidence about anybody else, and it is not a reason '
    + 'to stop asking your doctor.',
};

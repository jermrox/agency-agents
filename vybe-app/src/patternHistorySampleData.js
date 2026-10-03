/**
 * Sample data for the pattern history screen.
 *
 * Kept in its own module, and the screen says on-screen that it is sample
 * data. An invented health number that looks real is the one bug in this app
 * that could actually hurt someone.
 *
 * WHAT THIS SCREEN IS ARGUING
 * Vybe's claim is not that it can draw a line. It is that it can find a
 * relationship and say what it rests on. A history screen for that claim
 * cannot be one metric over time — it has to show the relationship week by
 * week, including the weeks it did not hold.
 *
 * So nothing here is a verdict. `verdict` is NOT stored: the screen derives it
 * from the numbers below against a rule it prints on screen, and counts the
 * weeks itself. A headline that says "held in 9 of 11 weeks" has to be
 * arithmetic over these rows or it is just a sentence that can drift away from
 * the data under it.
 */
export const isSample = true;

export const pattern = {
  window: '12 weeks, 6 July to 21 September',

  // The claim, as a sentence. The screen never shows a correlation coefficient:
  // a number nobody can interpret is the gap this product exists to close.
  claim:
    'Your deep sleep ran lower in the weeks you ate late more often than not.',

  // The rule is printed on screen rather than hidden in the code, because a
  // pattern you cannot check is indistinguishable from one that was asserted.
  rule: {
    driverThreshold: 3,
    driverLabel: 'three or more nights of eating after 21:00',
    metricLabel: 'deep sleep below your 12-week middle',
  },

  driver: { label: 'Late nights', unit: 'nights' },
  metric: {
    label: 'Deep sleep',
    unit: 'min',
    // Said every time the number appears. A wrist sensor does not get to sound
    // certain about sleep architecture.
    caveat: 'Deep sleep is an estimate from movement and heart rate, not a measurement.',
  },

  /**
   * `nights` is how many nights the Band actually recorded that week. A week
   * under five is marked thin and left OUT of the count rather than quietly
   * averaged in — a pattern scored on three nights is not evidence.
   */
  weeks: [
    { id: 'w1',  label: '6 Jul',  lateNights: 4, deepMinutes: 48, nights: 7 },
    { id: 'w2',  label: '13 Jul', lateNights: 4, deepMinutes: 52, nights: 7 },
    { id: 'w3',  label: '20 Jul', lateNights: 1, deepMinutes: 71, nights: 6 },
    { id: 'w4',  label: '27 Jul', lateNights: 0, deepMinutes: 68, nights: 7 },
    { id: 'w5',  label: '3 Aug',  lateNights: 5, deepMinutes: 44, nights: 7 },
    { id: 'w6',  label: '10 Aug', lateNights: 4, deepMinutes: 75, nights: 7 },
    { id: 'w7',  label: '17 Aug', lateNights: 2, deepMinutes: 50, nights: 3 },
    { id: 'w8',  label: '24 Aug', lateNights: 1, deepMinutes: 64, nights: 7 },
    { id: 'w9',  label: '31 Aug', lateNights: 5, deepMinutes: 46, nights: 6 },
    { id: 'w10', label: '7 Sep',  lateNights: 0, deepMinutes: 73, nights: 7 },
    { id: 'w11', label: '14 Sep', lateNights: 3, deepMinutes: 58, nights: 7 },
    { id: 'w12', label: '21 Sep', lateNights: 4, deepMinutes: 69, nights: 7 },
  ],

  /**
   * The weeks the pattern did not hold, each with what Vybe knows about them —
   * and one where the honest answer is that it knows nothing. A product that
   * explains away every exception is not explaining, it is defending.
   */
  exceptions: {
    w6: 'You were off work. Your calendar shows a late start every morning that week, so the late dinners were not costing you a wake-up time.',
    w7: 'Only three nights recorded. The Band was off your wrist from the Tuesday, so this week is not evidence either way.',
    w12: 'Vybe does not know. Nothing in your data separates this week from the ones where the pattern held. It is left here rather than explained away.',
  },

  stronger:
    'Twelve weeks is enough to notice a pattern and not enough to trust it. '
    + 'At twenty-six weeks Vybe can start telling the seasons apart from the habit.',

  restraint:
    'This is a pattern, not a cause. Vybe has shown you two things that moved '
    + 'together in your own data and the weeks they did not. It cannot tell you '
    + 'that eating earlier would have fixed those weeks — only that trying it '
    + 'for three weeks would tell you something this screen cannot.',
};

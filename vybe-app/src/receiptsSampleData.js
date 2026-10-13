/**
 * Sample data for the Receipts screen: the working behind one Ask answer.
 *
 * SAMPLE DATA. Every number here is illustrative and is labelled as such on
 * screen. None of it is a real person's reading, and the screen says so in
 * its first line. A real build fills this from the same store the Ask answer
 * was computed from, so the receipt can never disagree with the answer.
 */
export const isSample = true;

/**
 * The answer these receipts belong to. Mirrors the 'tired' worked example in
 * askSampleData so the two screens tell one story.
 */
export const receipt = {
  question: 'Why am I so tired this week?',
  answer:
    'Your sleep has not shortened — it has moved. You have gone to bed past midnight four nights running, and your deep sleep is down with it.',

  /**
   * The confidence ladder, lowest rung first. `rung` is the one this answer
   * sits on, and the word is always printed next to it: a position on a
   * ladder is not something a colour can carry on its own.
   */
  ladder: ['Observed', 'Associated', 'Personally supported', 'Hypothesis'],
  rung: 'Associated',
  rungWhy:
    'The late bedtimes and the lower deep sleep happened on the same nights, four times. That is an association in your own data. It is not yet a cause: four nights is too few to rule out a coincidence, and deep sleep is estimated from movement and heart rate, not measured in a lab.',

  /** What the Band saw, night by night. Direction is stated in words. */
  nights: [
    { id: 'n1', date: 'Mon 5 Oct', bedtime: '23:05', deep: '74 min', hrv: '+2%', note: 'on your usual pattern', late: false },
    { id: 'n2', date: 'Tue 6 Oct', bedtime: '23:20', deep: '69 min', hrv: '-1%', note: 'on your usual pattern', late: false },
    { id: 'n3', date: 'Wed 7 Oct', bedtime: '00:48', deep: '55 min', hrv: '-14%', note: 'late night, deep sleep down', late: true },
    { id: 'n4', date: 'Thu 8 Oct', bedtime: '00:41', deep: '51 min', hrv: '-19%', note: 'late night, deep sleep down', late: true },
    { id: 'n5', date: 'Fri 9 Oct', bedtime: '01:10', deep: '49 min', hrv: '-22%', note: 'late night, deep sleep down', late: true },
    { id: 'n6', date: 'Sat 10 Oct', bedtime: '00:52', deep: '53 min', hrv: '-17%', note: 'late night, deep sleep down', late: true },
    { id: 'n7', date: 'Sun 11 Oct', bedtime: '—', deep: '—', hrv: '—', note: 'Band not worn', late: null },
  ],

  /** The baseline every night above is compared against. */
  baseline: [
    { id: 'b1', label: 'Bedtime', value: '23:10', basis: 'median of the last 30 nights' },
    { id: 'b2', label: 'Deep sleep', value: '71 min', basis: 'median of the last 30 nights, estimated' },
    { id: 'b3', label: 'Overnight HRV', value: '64 ms', basis: 'your 30-night average; the percentages above are against this' },
  ],

  /** Where each kind of evidence came from. */
  sources: [
    { id: 's1', name: 'Vybe Band', what: 'Bedtime, sleep stages (estimated), overnight HRV' },
    { id: 's2', name: 'You logged this', what: 'Last meal time on three of the four late nights' },
  ],

  /** Gaps the answer was honest about. Listed here so the receipt is complete. */
  unseen: [
    'Sunday night is missing: the Band was not worn, so the week is six nights, not seven.',
    'Nothing here records what you drank. Alcohol changes deep sleep and HRV, and only a log would show it.',
    'Why the nights were late — work, a child, or choice — is not something a sensor can read.',
  ],

  /** The one thing the person can do with a receipt they disagree with. */
  challenge: 'If a night is wrong, say so. A correction here moves the answer, not just the record.',
};

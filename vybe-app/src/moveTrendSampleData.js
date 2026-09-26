/**
 * Sample data for the Move trend screen.
 *
 * Kept in its own module, and the screen that renders it says on-screen that
 * it is sample data. An invented health number that looks real is the one bug
 * in this app that could actually hurt someone.
 *
 * WHY RAW WEEKS AND NOT PRE-COMPUTED SUMMARIES
 * Everything the screen states in numbers — the four-week averages, the
 * change between them, the peak, which weeks sit outside the usual range — is
 * derived from `weeks` at render time rather than typed in here. A summary
 * typed by hand drifts away from the series it claims to describe the first
 * time someone edits a value, and then the screen is confidently wrong. Only
 * the editorial sentences below are hand-written, and they are the only things
 * a reviewer has to check against the data.
 */
export const isSample = true;

export const moveTrend = {
  metricLabel: 'Active minutes',
  metricUnit: 'minutes',
  // What counts, stated plainly. A trend is meaningless if the reader has to
  // guess what was measured.
  metricDefinition:
    'Minutes per week where your heart rate stayed above your own moderate-effort threshold for at least ten minutes at a stretch.',

  /**
   * 26 complete weeks, oldest first. `start` is the Monday the week began.
   *
   * The screen shows the last 6, 12 or 26 of these. Holding all 26 here — and
   * slicing in the screen — is what makes the range selector real rather than
   * decorative: every range is drawn from measurements that exist.
   */
  weeks: [
    { start: '2026-03-23', label: '23 Mar', minutes: 147 },
    { start: '2026-03-30', label: '30 Mar', minutes: 162 },
    { start: '2026-04-06', label: '6 Apr', minutes: 138 },
    { start: '2026-04-13', label: '13 Apr', minutes: 121 },
    { start: '2026-04-20', label: '20 Apr', minutes: 155 },
    { start: '2026-04-27', label: '27 Apr', minutes: 149 },
    { start: '2026-05-04', label: '4 May', minutes: 173 },
    { start: '2026-05-11', label: '11 May', minutes: 158 },
    { start: '2026-05-18', label: '18 May', minutes: 130 },
    { start: '2026-05-25', label: '25 May', minutes: 117 },
    { start: '2026-06-01', label: '1 Jun', minutes: 108 },
    { start: '2026-06-08', label: '8 Jun', minutes: 124 },
    { start: '2026-06-15', label: '15 Jun', minutes: 102 },
    { start: '2026-06-22', label: '22 Jun', minutes: 115 },
    { start: '2026-06-29', label: '29 Jun', minutes: 96 },
    { start: '2026-07-06', label: '6 Jul', minutes: 112 },
    { start: '2026-07-13', label: '13 Jul', minutes: 134 },
    { start: '2026-07-20', label: '20 Jul', minutes: 141 },
    { start: '2026-07-27', label: '27 Jul', minutes: 58 },
    { start: '2026-08-03', label: '3 Aug', minutes: 71 },
    { start: '2026-08-10', label: '10 Aug', minutes: 128 },
    { start: '2026-08-17', label: '17 Aug', minutes: 155 },
    { start: '2026-08-24', label: '24 Aug', minutes: 168 },
    { start: '2026-08-31', label: '31 Aug', minutes: 182 },
    { start: '2026-09-07', label: '7 Sep', minutes: 176 },
    { start: '2026-09-14', label: '14 Sep', minutes: 201 },
  ],

  /**
   * The band the screen shades behind the columns: the middle half of the 26
   * weeks above (roughly the 25th to 75th percentile, 114–159 minutes).
   *
   * It is the person's own range, not a population norm, and that distinction
   * is the product. "Above average for women your age" is a comparison nobody
   * asked for; "higher than your own normal six months running" is a fact
   * about them. The screen says so in words next to the band, because a grey
   * rectangle explains nothing on its own.
   */
  usualRange: { low: 114, high: 159, basis: 'the middle half of your last 26 weeks' },

  // The headline is a sentence, not a score — the same position the rest of
  // the app takes. Every claim in it is checkable against `weeks` above.
  verdict:
    'Your movement climbed five weeks straight out of the late-July dip, and every week since 24 August has sat above your usual range.',
  verdictCaveat:
    'Six months is enough to see a direction. It is not enough to tell a lasting change from a good season.',

  /**
   * What happened, anchored to the week it happened in.
   *
   * Rendered as a timeline rather than a stack of cards: these are events in
   * sequence, and a sequence should look like one. Each carries its source, so
   * the reader can tell what Vybe observed from what they told it.
   */
  annotations: [
    {
      id: 'a1',
      weekStart: '2026-07-27',
      weekLabel: '27 July',
      text: 'Four days away with no gym access, and the lowest week in the six months shown.',
      source: 'From your calendar',
    },
    {
      id: 'a2',
      weekStart: '2026-08-10',
      weekLabel: '10 August',
      text: 'You moved your sessions to mornings. The climb starts the week after.',
      source: 'You logged this',
    },
    {
      id: 'a3',
      weekStart: '2026-08-31',
      weekLabel: '31 August',
      text: 'First week above 180 minutes in anything Vybe has recorded for you.',
      source: 'Vybe noticed this',
    },
  ],

  // The loop closing on itself, same as the Restore screen: a trend is only
  // worth showing if something follows from it.
  whatThisChanges: {
    text: 'Vybe has stopped suggesting you add sessions, and started watching whether you can hold this.',
    why: 'Four weeks above your usual range is where added load stops being progress and starts being a question about recovery.',
  },
};

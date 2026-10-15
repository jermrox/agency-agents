/**
 * Sample data for the Vitals drift screen: six months of one slow number.
 *
 * Kept in its own module, and the screen says on-screen that it is sample
 * data. Every figure is a round, plainly illustrative value, and the screen
 * never shows one without the word "sample" above it. An invented health
 * number that looks real is the one bug in this app that could actually hurt
 * someone.
 *
 * WHAT THIS SCREEN IS ARGUING
 * The Vitals screen reads one morning against a 30-day band. That band is
 * usually drawn as if it were fixed. It is not: it moves with the season, a
 * training block, an illness, a heat wave. So the history view does not plot
 * mornings, which are noise; it plots the BAND, month by month, on one shared
 * scale. A drift is the band moving. A bad night is a dot leaving it. Those are
 * different things and every other product draws them the same way.
 *
 * WHY MONTHS HOLD RAW EDGES AND NOT A VERDICT
 * The then-and-now sentence, the "moved by" figure and the shared scale are
 * derived from `months` at render time. Only the editorial lines are typed by
 * hand, so they are the only things a reviewer has to check against the data.
 */
export const isSample = true;

export const metrics = {
  rhr: {
    id: 'rhr',
    label: 'Resting heart rate',
    unit: 'bpm',
    decimals: 0,
    definition:
      'The lowest ten-minute average heart rate during sleep, one value per night. '
      + 'Each month below is the band those nights fell inside, and the night most of them sat near.',
    verdict:
      'Your resting heart rate is where it was in April. The one real move was August, and it has come back.',
    verdictCaveat:
      'Six months of nights, 24 to 30 a month. August has 21: five nights were skipped during a cold, and the band for that month is wider because of it.',
    // Oldest first. `low`/`high` are the month's band edges, `median` the
    // usual night, `nights` how many nights the band is built from.
    months: [
      { id: 'apr', label: 'April',     low: 54, high: 63, median: 58, nights: 28 },
      { id: 'may', label: 'May',       low: 53, high: 62, median: 57, nights: 30 },
      { id: 'jun', label: 'June',      low: 52, high: 61, median: 56, nights: 29 },
      { id: 'jul', label: 'July',      low: 53, high: 63, median: 58, nights: 27 },
      { id: 'aug', label: 'August',    low: 55, high: 67, median: 60, nights: 21 },
      { id: 'sep', label: 'September', low: 52, high: 61, median: 56, nights: 30 },
    ],
    // What no sensor can read. Each line says where it came from, and which
    // month it belongs to so the screen can point at the band it moved.
    annotations: [
      { id: 'a1', monthId: 'jun', text: 'Six-week run programme started 1 June', source: 'You logged this' },
      { id: 'a2', monthId: 'jul', text: 'Heat wave, nine nights above 24 °C indoors', source: 'From local weather' },
      { id: 'a3', monthId: 'aug', text: 'A cold, 11 to 16 August; the Band came off for five nights', source: 'You logged this' },
      { id: 'a4', monthId: 'sep', text: 'Back to the June routine, no travel', source: 'From your calendar' },
    ],
    whatThisChanges: {
      text: 'Nothing to act on. The band is back where training put it in June.',
      why:
        'A month that moved and came back is weather, not climate. Vybe will say so again if '
        + 'September holds through October.',
    },
  },
  resp: {
    id: 'resp',
    label: 'Breathing rate, asleep',
    unit: 'per min',
    decimals: 1,
    definition:
      'Breaths per minute while asleep, one value per night. The slowest-moving number the Band reads, which is why it is worth a six-month view and not a daily one.',
    verdict:
      'Your breathing rate has barely moved in six months. Its band is a tenth of a breath narrower than in April.',
    verdictCaveat:
      'Six months of nights, 24 to 30 a month, with the same five-night gap in August.',
    months: [
      { id: 'apr', label: 'April',     low: 13.4, high: 15.6, median: 14.5, nights: 28 },
      { id: 'may', label: 'May',       low: 13.3, high: 15.5, median: 14.4, nights: 30 },
      { id: 'jun', label: 'June',      low: 13.2, high: 15.3, median: 14.2, nights: 29 },
      { id: 'jul', label: 'July',      low: 13.4, high: 15.6, median: 14.5, nights: 27 },
      { id: 'aug', label: 'August',    low: 13.6, high: 16.2, median: 14.9, nights: 21 },
      { id: 'sep', label: 'September', low: 13.2, high: 15.3, median: 14.3, nights: 30 },
    ],
    annotations: [
      { id: 'b1', monthId: 'aug', text: 'A cold, 11 to 16 August; the Band came off for five nights', source: 'You logged this' },
    ],
    whatThisChanges: {
      text: 'Nothing to act on. This is the number to leave alone.',
      why:
        'Breathing rate moves for a reason or not at all. A month that moved during a cold and came back is the pattern you want to see.',
    },
  },
};

export const order = ['rhr', 'resp'];

/**
 * The restraint, in the body of the screen and not a footer. A six-month view
 * of a vital is where a wearable is most tempted to sound like a clinic.
 */
export const boundary = {
  label: 'WHAT A DRIFT IS NOT',
  text: 'Vybe does not read a six-month move as a diagnosis, and will not.',
  detail:
    'Bands move with seasons, training and illness in people who are well. If your usual '
    + 'keeps moving one way for three months, Vybe will say so in plain words and point you '
    + 'to the export, so the numbers can go to a clinician who can read them.',
};

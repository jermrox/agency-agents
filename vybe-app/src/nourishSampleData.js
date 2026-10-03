/**
 * Sample data for the Nourish detail screen.
 *
 * Kept in its own module, and the screen says on-screen that it is sample data.
 * An invented health number that looks real is the one bug in this app that
 * could actually hurt someone.
 *
 * NOTHING HERE IS A SUMMARY.
 * The screen computes the gap between the last bite and lights out, the span of
 * the eating window, and the size of the late-versus-early difference from the
 * times and figures below. A summary typed by hand drifts from the data it
 * claims to describe the first time somebody edits a value, and then the screen
 * is confidently wrong. Only the editorial sentences are written by hand, which
 * makes them the only lines a reviewer has to check.
 */
export const isSample = true;

export const nourishDay = {
  date: 'Monday 28 September',

  // The answer is a sentence, and it is about TIMING rather than food, because
  // that is what this day's data actually supports. Every other nutrition app
  // opens on a calorie total, which is a number the person then has to
  // interpret alone.
  answer:
    'The strongest signal in your food data is when you stop eating, not what you ate.',
  confidence: 'Moderate confidence',
  confidenceWhy:
    'Fourteen days of meal times against your overnight readings. Two of those days have gaps in the log, so the pattern is real but not yet settled.',

  // Ordered through the day. `end` is when the meal finished, which is the
  // figure the whole screen turns on -- not when it started.
  meals: [
    {
      id: 'coffee1',
      name: 'Coffee',
      start: '06:55',
      end: '07:05',
      items: ['Flat white'],
      note: 'First of two.',
    },
    {
      id: 'breakfast',
      name: 'Breakfast',
      start: '07:20',
      end: '07:40',
      items: ['Oats', 'Greek yoghurt', 'Blueberries'],
      note: 'Your most repeated meal — 19 of the last 30 mornings.',
    },
    {
      id: 'lunch',
      name: 'Lunch',
      start: '13:10',
      end: '13:35',
      items: ['Chicken', 'Rice', 'Green salad'],
      note: 'Eaten away from a desk, which your calendar rarely allows.',
    },
    {
      id: 'coffee2',
      name: 'Coffee',
      start: '15:40',
      end: '15:50',
      items: ['Americano'],
      note: 'Well clear of the 18:00 cut-off you set yourself.',
    },
    {
      id: 'dinner',
      name: 'Dinner',
      start: '21:25',
      end: '22:05',
      items: ['Pasta', 'Bread', 'Olive oil'],
      // Counts stay tied to the fortnight the pattern below is measured over.
      // Two different windows in one screen is how a summary starts disagreeing
      // with the figures underneath it.
      note:
        'The fourth dinner after 21:00 in the last fortnight. Started after a call '
        + 'that ran over, which is the reason the log gives on three of those four nights.',
    },
  ],

  // The night that followed. Lights out is the boundary the gap is measured to.
  sleep: { lightsOut: '23:40', wake: '06:50' },

  // What "usually" means for this person, stated so the screen never has to
  // compare them to a population norm.
  usual: {
    gapLabel: 'the 3h you manage on a good week',
    gapMinutes: 180,
  },

  // Readings that are genuinely about food rather than timing. Every one states
  // its direction in words, so colour and the arrow glyph are never the only
  // signal that something moved.
  readings: [
    { id: 'protein', label: 'Protein',  value: '96 g',  reading: 'Inside your usual range',              direction: 'flat', concern: false },
    { id: 'fibre',   label: 'Fibre',    value: '21 g',  reading: 'Below your 30-day median of 29 g',     direction: 'down', concern: true },
    { id: 'water',   label: 'Water',    value: '1.9 L', reading: 'A little under your 2.3 L average',    direction: 'down', concern: true },
    { id: 'caffeine', label: 'Last caffeine', value: '15:50', reading: 'Almost eight hours before lights out', direction: 'flat', concern: false },
  ],

  /**
   * The cross-dimension pattern, which is the point of the screen.
   *
   * `deepMinutes` is an ESTIMATE from the Band, not a measurement, and the
   * screen says so where it is drawn. Overstating what a wrist sensor can know
   * about sleep architecture is how a wellness product starts sounding clinical.
   */
  pattern: {
    basis: 'the last 14 days',
    late:  { label: 'Dinner after 21:00',  nights: 4, deepMinutes: 52 },
    early: { label: 'Dinner before 20:00', nights: 3, deepMinutes: 71 },
    caveat: 'Deep sleep is an estimate from the Band, not a measurement.',
    crossLink:
      'This is a Nourish screen making a Restore argument. The five dimensions '
      + 'are one system, not five scores that never speak to each other.',
  },

  // One action. A list of six suggestions is a way of not deciding.
  action: {
    text: 'Put dinner on the calendar for 19:45 tomorrow.',
    why:
      'On the three nights in this fortnight when you finished eating before '
      + '20:00, your estimated deep sleep was the highest of the whole period. '
      + 'Moving the meal is a smaller change than moving your bedtime.',
  },

  // The honesty beat. Kept to one short passage rather than a list of promises.
  restraint:
    'Vybe does not count your calories, score your day out of ten or sort food '
    + 'into good and bad. It watches for the handful of patterns that change how '
    + 'you feel, and says so in a sentence.',
};

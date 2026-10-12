/**
 * Sample data for the Vitals detail screen.
 *
 * Kept in its own module, and the screen says on-screen that it is sample
 * data. An invented health number that looks real is the one bug in this app
 * that could actually hurt someone, so every figure here is a round, plainly
 * illustrative value, and the screen never shows one without the word
 * "sample" above it.
 */
export const isSample = true;

export const vitalsDay = {
  date: 'Monday 12 October',

  // The headline is a sentence, not a score. Vitals is the dimension where
  // every other product shows four numbers and a colour. Vybe's position is
  // the same here as everywhere: say what the numbers mean, against this
  // person, and say what it could not see.
  answer:
    'Your vitals are inside your own range this morning. Resting heart rate is the one to watch: it has sat at the top of your band for three days.',
  confidence: 'Good confidence',
  confidenceWhy:
    'Thirty-one nights of your own readings behind each band, and no gaps this week.',

  // Each vital is read against the wearer's own 30-day band, never a
  // population average. `low` and `high` are the band edges, `median` the
  // usual value, `today` this morning's reading. `reading` spells the
  // position out in words so the strip is never the only signal.
  //
  // Only the signals the product claims: heart rate, HRV, respiration, skin
  // temperature, sleep timing. No SpO2 and no ECG waveform, by design.
  vitals: [
    {
      id: 'rhr',
      label: 'Resting heart rate',
      unit: 'bpm',
      low: 52, high: 61, median: 56, today: 60,
      reading: 'Top of your band, third day running',
      watch: true,
    },
    {
      id: 'hrv',
      label: 'Overnight HRV',
      unit: 'ms',
      low: 38, high: 64, median: 51, today: 49,
      reading: 'Near your usual',
      watch: false,
    },
    {
      id: 'resp',
      label: 'Breathing rate, asleep',
      unit: 'per min',
      low: 13.1, high: 15.4, median: 14.2, today: 14.4,
      reading: 'Within your normal range',
      watch: false,
    },
    {
      id: 'temp',
      label: 'Skin temperature, overnight',
      unit: '°C from usual',
      low: -0.6, high: 0.6, median: 0, today: 0.2,
      reading: 'A touch above usual, inside the band',
      watch: false,
    },
    {
      id: 'timing',
      label: 'Sleep midpoint',
      unit: '',
      low: 2.6, high: 4.1, median: 3.3, today: 3.5,
      // Hours after midnight, shown as a clock time by the screen.
      reading: 'Twelve minutes later than your median',
      watch: false,
      clock: true,
    },
  ],

  // Context is what no sensor can read. Each line says where it came from.
  context: [
    { id: 'c1', text: 'Flight home Thursday, two time zones', source: 'From your calendar' },
    { id: 'c2', text: 'Coffee after 3pm on Saturday and Sunday', source: 'You logged this' },
    { id: 'c3', text: 'Outdoor temperature 9°C above the month’s usual', source: 'From the weather' },
  ],

  // One action, not a list.
  action: {
    text: 'Keep caffeine before 2pm today and see where resting heart rate sits on Wednesday.',
    why: 'The last two times your resting heart rate held at the top of its band for three days, it came back inside two days of an earlier caffeine cut-off. A flight week makes the signal noisier, so the band gets a day of grace before anything stronger is suggested.',
  },

  // Vitals is where honesty costs the most, so the refusal is on the screen
  // rather than buried in a settings page.
  notClinical:
    'Vybe reads trends against your own history. It is not a medical device, does not diagnose, and will not read a single reading as an alarm. A reading that worries you belongs with a clinician, and the export on the Data screen is built so you can take it there.',

  lastOutcome: {
    text: 'Last time Vybe suggested an earlier caffeine cut-off, you kept it for four days and your resting heart rate returned to the middle of its band in two.',
    when: '5 weeks ago',
  },
};

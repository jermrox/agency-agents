/**
 * Sample data for the year-on-year screen.
 *
 * Kept in its own module, and the screen says on-screen that it is sample
 * data. An invented health number that looks real is the one bug in this app
 * that could actually hurt someone.
 *
 * WHAT THIS SCREEN IS ARGUING, AND WHY IT IS NOT THE OTHER TWO
 * `MoveTrendScreen` draws one metric across twenty-six weeks. `PatternHistory`
 * tests one claim across twelve. Both answer "what did this do". Neither can
 * answer the question that decides whether any of it means anything:
 *
 *   is this a trend, or is it just November again?
 *
 * Every wearable shows a decline through the winter and lets the person
 * conclude they are getting worse. Usually they are not. It is winter. But
 * nothing can say that without more than a year of data — and the honest part
 * is that almost nobody has more than a year of data, so the screen's real job
 * is to say how much of the year it still cannot speak about.
 *
 * NOTHING HERE IS PAIRED IN ADVANCE. These are nineteen monthly readings with
 * a year and a month on each. The screen does the pairing, counts how many
 * months have a counterpart a year earlier, and works out which repeated and
 * which changed. A pre-computed pairing could quietly disagree with the
 * readings under it.
 */
export const isSample = true;

export const metric = {
  label: 'Deep sleep',
  unit: 'min',
  perLabel: 'monthly average per night',
  // Said wherever the number appears. A wrist sensor does not get to sound
  // certain about sleep architecture.
  caveat: 'Deep sleep is an estimate from movement and heart rate, not a measurement.',
};

export const window = {
  label: '19 months, March 2025 to September 2026',
  note: 'Months with fewer than 20 recorded nights are not included at all.',
};

/**
 * The rule the screen prints and scores against. A month counts as having
 * repeated when the two years land within `sameWithin` of each other — without
 * a margin, a one-minute difference would flip a verdict, and a verdict that
 * turns on one minute is noise wearing a conclusion's clothes.
 */
export const rule = {
  sameWithin: 5,
  text:
    'A month repeated if the two years came out within 5 minutes of each '
    + 'other. Anything wider is a change. Without that margin a single minute '
    + 'would decide the answer.',
};

/** Nineteen monthly readings. `month` is 1-12. */
export const readings = [
  { year: 2025, month: 3,  value: 62, nights: 29 },
  { year: 2025, month: 4,  value: 65, nights: 30 },
  { year: 2025, month: 5,  value: 68, nights: 31 },
  { year: 2025, month: 6,  value: 70, nights: 29 },
  { year: 2025, month: 7,  value: 69, nights: 31 },
  { year: 2025, month: 8,  value: 66, nights: 30 },
  { year: 2025, month: 9,  value: 64, nights: 28 },
  { year: 2025, month: 10, value: 58, nights: 30 },
  { year: 2025, month: 11, value: 54, nights: 29 },
  { year: 2025, month: 12, value: 51, nights: 27 },
  { year: 2026, month: 1,  value: 49, nights: 30 },
  { year: 2026, month: 2,  value: 52, nights: 26 },
  { year: 2026, month: 3,  value: 61, nights: 30 },
  { year: 2026, month: 4,  value: 66, nights: 29 },
  { year: 2026, month: 5,  value: 69, nights: 31 },
  { year: 2026, month: 6,  value: 71, nights: 30 },
  { year: 2026, month: 7,  value: 58, nights: 31 },
  { year: 2026, month: 8,  value: 67, nights: 30 },
  { year: 2026, month: 9,  value: 63, nights: 29 },
];

/**
 * What Vybe knows about the months that did not repeat. Keyed by month number.
 * A product that explains away every exception is not explaining, it is
 * defending — so one of these says Vybe does not know.
 */
export const exceptions = {
  7: 'You moved house on the 14th of June. July was the first full month in '
    + 'the new place, and it is the only month in nineteen that came out more '
    + 'than five minutes away from its own last year.',
};

export const whatItCannotSay =
  'Vybe has seen October, November, December, January and February exactly '
  + 'once each. They are also the five lowest months on this screen. That '
  + 'shape is what a winter looks like and it is equally what a bad stretch '
  + 'looks like, and with one of each month on record Vybe cannot tell you '
  + 'which — so it is not going to guess, and it is not going to draw you a '
  + 'seasonal curve through a single year.';

export const whenItCanSay =
  'From February 2027 Vybe will have seen every month twice. Two is enough to '
  + 'notice and not enough to trust: a month that matches once is a pair, not '
  + 'a pattern. Three passes through a year is where this screen starts being '
  + 'worth acting on, which is February 2028.';

export const restraint =
  'Nothing here is a seasonal adjustment. Vybe is not quietly correcting your '
  + 'winter numbers upward to make them look normal, and it is not telling you '
  + 'a decline is fine because it is December. It is showing you which months '
  + 'it has seen twice, what happened both times, and which months it has no '
  + 'business having an opinion about yet.';

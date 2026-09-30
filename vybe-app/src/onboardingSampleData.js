/**
 * Sample data for the first-run flow.
 *
 * Kept in its own module, and the screen says on-screen that it is sample
 * data. The device name and serial below are invented and look it on purpose —
 * an invented health number that reads as real is the one bug in this app that
 * could actually hurt someone, and the same rule applies to anything that
 * would make a person think a pairing had really happened.
 *
 * WHAT THIS SCREEN IS ARGUING
 * Onboarding is where consent is either earned or extracted. The usual pattern
 * asks for everything up front, behind category names, before the person knows
 * what any of it buys them. So every source below is described by the QUESTION
 * it lets Vybe answer, and by the thing it will never be used for. A person
 * deciding what to hand over should be reading about capability, not about
 * data categories.
 */
export const isSample = true;

export const steps = [
  { id: 'band', label: 'Your Band' },
  { id: 'sources', label: 'Sources' },
  { id: 'consent', label: 'What you agreed to' },
  { id: 'ready', label: 'What Vybe knows' },
];

export const band = {
  // Obviously a sample device. Nothing here should read as a real pairing.
  name: 'Vybe Band (sample device)',
  serial: 'SAMPLE-0000',
  // The three physical things that actually decide whether a search succeeds.
  // Real onboarding hides these behind a "Trouble connecting?" link that
  // appears after the failure. They are more useful before it.
  requirements: [
    'Bluetooth on, on this phone',
    'The Band charged enough to wake — a flat band cannot be found',
    'Hold the Band’s single button until the light pulses',
  ],
  // Said plainly, because a wearable that pairs over the internet is a
  // different product with a different threat model.
  privacyLine:
    'Pairing happens over Bluetooth, phone to Band. Nothing routes through a '
    + 'server to get here, and no account is needed to wear it.',
  skipLine:
    'You can set the Band up later. Without it Vybe has almost nothing to '
    + 'read, so it will say so rather than guess.',
};

/**
 * Optional sources. Nothing is on by default: a pre-ticked box is not consent,
 * and this is the screen where that distinction is cheapest to honour.
 *
 * `unlocks` is a real question Vybe can answer with the source and cannot
 * answer without it. `never` is the use it is excluded from, which is the half
 * a permission dialog leaves out.
 */
export const sources = [
  {
    id: 'sleep',
    name: 'Sleep from your phone',
    unlocks: '"Why am I tired this week?" — because timing needs more than one night.',
    detail: 'Bedtime and wake time, read from the phone’s own health store.',
    never: 'Never used to score your day or rank you against anyone else.',
    on: false,
  },
  {
    id: 'calendar',
    name: 'Calendar',
    unlocks: '"Was it the week, or was it me?" — travel and back-to-back days explain a lot.',
    detail: 'Event times and time zones only. Not titles, not attendees, not locations.',
    never: 'Never read for what your meetings are about, and never sent off the phone.',
    on: false,
  },
  {
    id: 'weather',
    name: 'Local weather',
    unlocks: '"Why was last night worse?" — heat moves sleep more than most people expect.',
    detail: 'Temperature and humidity for your area, by rough location.',
    never: 'Never stores where you were, only what the air was doing.',
    on: false,
  },
  {
    id: 'meals',
    name: 'What you log yourself',
    unlocks: '"Does eating late cost me?" — the one thing no sensor can see.',
    detail: 'Meal times and a note, typed by you when you feel like it.',
    never: 'No calorie count, no food score, no good and bad lists.',
    on: false,
  },
];

/**
 * The consent step is a summary of decisions already made, not a wall of text
 * read before the person knows what they are agreeing to. Two promises that can
 * be checked, and one boundary that cannot be walked back.
 */
export const promises = [
  {
    id: 'onphone',
    text: 'Your readings live on this phone.',
    detail:
      'The app shows you where every piece of it sits, and the Data screen is '
      + 'one tap from the home screen rather than four levels down in settings.',
  },
  {
    id: 'exit',
    text: 'Export and delete are one tap.',
    detail:
      'Both are on the Data screen from the first day, not added later once '
      + 'leaving has become expensive.',
  },
];

export const boundary = {
  label: 'WHAT VYBE WILL NOT DO',
  text: 'Vybe is not a medical device and will not diagnose you.',
  detail:
    'It reads your own signals and explains them. When you ask it a clinical '
    + 'question it will say no and tell you to see a clinician — and it will '
    + 'still show you the reading, because the boundary is on the claim, not on '
    + 'your own data.',
};

/**
 * The honest payoff. Every first-run flow ends on "You’re all set!", which on
 * day one is false: a wearable that has watched you for zero nights knows
 * nothing about you. Saying so is better than inventing a first insight, and it
 * sets the only expectation that survives contact with the product.
 */
export const readiness = [
  {
    id: 'now',
    when: 'Today',
    what: 'Nothing yet.',
    detail:
      'Vybe has not seen a night of your sleep or a day of your movement. Any '
      + 'answer it gave you now would be about people in general, not about you.',
  },
  {
    id: 'd3',
    when: 'After three nights',
    what: 'Your own range, roughly.',
    detail:
      'Enough to say whether a reading is unusual for you. Three nights is a '
      + 'thin baseline and Vybe will label its confidence as low.',
  },
  {
    id: 'w2',
    when: 'After two weeks',
    what: 'Patterns, and the first real answers.',
    detail:
      'Enough to connect a late night to the next day, and to start answering '
      + '"why" rather than "what".',
  },
  {
    id: 'w6',
    when: 'After six weeks',
    what: 'Did it work.',
    detail:
      'Enough history to tell you whether a change you made actually moved '
      + 'anything — the part most products never close.',
  },
];

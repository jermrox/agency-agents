/**
 * Sample data for the follow-up screen — the second half of Ask.
 *
 * Kept in its own module, and the screen says on-screen that it is sample
 * data. An invented health number that looks real is the one bug in this app
 * that could actually hurt someone.
 *
 * WHAT THIS SCREEN IS ARGUING
 * `AskScreen` is the front door: a question goes in, an answer comes out with
 * its basis and its blind spots. This is what happens next, and it is the part
 * every conversational health product skips: the person knows something the
 * sensor does not, and says so.
 *
 * Two failures are available here and both are easy. A product that ignores
 * the correction is useless. A product that agrees with every correction is
 * worse, because it will now confirm whatever the person already believed and
 * still sound certain. So corrections land in three places, and which one is
 * DERIVED from what the correction actually moved rather than written down:
 *
 *   changes   — a piece of the basis is overturned, and the answer changes
 *   narrows   — the basis survives, but a blind spot closes and the
 *               confidence moves
 *   recorded  — Vybe believes the person and still cannot use it
 *
 * THE POINT OF `source`
 * Every basis item says whether it was MEASURED or INFERRED before anybody
 * corrects anything. The item the first correction overturns is an inferred
 * one — which is the argument this screen exists to make: the part of an
 * answer most likely to be wrong is the part the product guessed, and it
 * should be labelled as a guess in advance rather than after a complaint.
 */
export const isSample = true;

export const original = {
  question: 'Why is my resting heart rate up?',

  answer:
    'Your resting heart rate has run about 4 bpm above your own baseline for '
    + 'three mornings, and the clearest thing sitting alongside it is alcohol '
    + 'on two of those evenings.',

  confidence: 'MODERATE CONFIDENCE',
  confidenceWhy: 'Three mornings is a short run, and one of the three signals is inferred.',

  /**
   * `source` is stated before any correction arrives.
   *   measured — read from the sensor
   *   inferred — Vybe's guess from a pattern, and the first thing to doubt
   */
  basis: [
    {
      id: 'rhr',
      label: 'Resting heart rate, three mornings',
      detail: '58, 59 and 57 bpm against a 30-day average of 54.',
      source: 'measured',
    },
    {
      id: 'hrv',
      label: 'Overnight HRV',
      detail: 'Down 11% across the same three nights.',
      source: 'measured',
    },
    {
      id: 'bedtime',
      label: 'Two late bedtimes',
      detail: 'Lights out after 01:00 on the Tuesday and the Thursday.',
      source: 'measured',
    },
    {
      id: 'alcohol',
      label: 'Alcohol on two evenings',
      detail:
        'Inferred from an elevated early-night heart rate and a suppressed '
        + 'drop in the first sleep cycle. Nothing was logged and nothing was '
        + 'measured — this is a pattern Vybe matched.',
      source: 'inferred',
    },
  ],

  /** What Vybe could not see when it answered. A correction may close one. */
  unseen: [
    { id: 'caffeine', label: 'Caffeine after midday — not tracked' },
    { id: 'illness', label: 'Any infection or fever — not tracked' },
    { id: 'room', label: 'Room temperature overnight — no sensor connected' },
  ],
};

/**
 * What the person might say back. Each correction states what it does to the
 * basis above; the screen computes the rest, including which of the three
 * kinds it is.
 *
 * `effects` verdicts:
 *   held       — this part of the reasoning survives
 *   overturned — the correction replaces it
 *   weakened   — it stands, but counts for less
 */
export const corrections = [
  {
    id: 'nightshift',
    text: 'Those two evenings were night shifts, not drinking.',
    effects: [
      { basisId: 'rhr', verdict: 'held' },
      { basisId: 'hrv', verdict: 'held' },
      { basisId: 'bedtime', verdict: 'weakened' },
      { basisId: 'alcohol', verdict: 'overturned' },
    ],
    added: [
      {
        label: 'Two night shifts',
        detail:
          'Told to Vybe, not measured. It explains the late bedtimes and the '
          + 'shape of the first sleep cycle at least as well as the guess it '
          + 'replaces.',
      },
    ],
    closes: [],
    revised: {
      answer:
        'Your resting heart rate has run about 4 bpm above your own baseline '
        + 'for three mornings, and two night shifts are the clearest thing '
        + 'sitting alongside it.',
      confidence: 'MODERATE CONFIDENCE',
      confidenceWhy:
        'Still three mornings, but the explanation is now something you told '
        + 'Vybe rather than something it guessed.',
    },
    note:
      'Vybe had marked the alcohol line as inferred before you said anything. '
      + 'That is the line it expected to be wrong.',
  },

  {
    id: 'decaf',
    text: 'I switched to decaf two weeks ago.',
    effects: [
      { basisId: 'rhr', verdict: 'held' },
      { basisId: 'hrv', verdict: 'held' },
      { basisId: 'bedtime', verdict: 'held' },
      { basisId: 'alcohol', verdict: 'held' },
    ],
    added: [],
    closes: ['caffeine'],
    revised: {
      answer:
        'Your resting heart rate has run about 4 bpm above your own baseline '
        + 'for three mornings, and the clearest thing sitting alongside it is '
        + 'alcohol on two of those evenings.',
      confidence: 'HIGHER CONFIDENCE',
      confidenceWhy:
        'Caffeine was one of three things Vybe could not see. It can rule that '
        + 'one out now, which makes the rest of the answer worth a little more.',
    },
    note:
      'Nothing in the answer changed. One of the things Vybe admitted it could '
      + 'not see is no longer unknown, so the same answer now rests on less '
      + 'missing information.',
  },

  {
    id: 'feelfine',
    text: 'I feel completely fine.',
    effects: [
      { basisId: 'rhr', verdict: 'held' },
      { basisId: 'hrv', verdict: 'held' },
      { basisId: 'bedtime', verdict: 'held' },
      { basisId: 'alcohol', verdict: 'held' },
    ],
    added: [],
    closes: [],
    revised: {
      answer:
        'Your resting heart rate has run about 4 bpm above your own baseline '
        + 'for three mornings, and the clearest thing sitting alongside it is '
        + 'alcohol on two of those evenings.',
      confidence: 'MODERATE CONFIDENCE',
      confidenceWhy: 'Unchanged. Nothing in the reading moved.',
    },
    note:
      'Recorded, and it does not change the number. How you feel is real and '
      + 'Vybe cannot measure it, so it will not pretend your reading is '
      + 'different because you said so — and it will not tell you something is '
      + 'wrong either. A reading above your baseline while you feel well is a '
      + 'reading above your baseline while you feel well.',
  },
];

/**
 * What it would actually take to move the reading, said plainly, so the
 * "recorded" case ends with something to do rather than a shrug.
 */
export const whatWouldMoveIt =
  'Two ordinary mornings in a row would bring this back inside your usual '
  + 'range and close the question. If it is still up after a week, that is '
  + 'worth a GP appointment rather than another conversation with Vybe.';

export const restraint =
  'Vybe will not agree with you just because you said so. It will take what '
  + 'you tell it, show you exactly which parts of its reasoning that moved, '
  + 'and leave the rest standing. An assistant that folds on every correction '
  + 'is an assistant that will confirm anything you already believed.';

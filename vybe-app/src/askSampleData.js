/**
 * Sample data for the Ask screen.
 *
 * Kept in its own module, and the screen that renders it says on-screen that
 * it is sample data. An invented health number that looks real is the one bug
 * in this app that could actually hurt someone.
 *
 * Every entry here is shaped the way a real answer has to be shaped: a
 * sentence, the signals it rests on, the window those signals cover, and the
 * things Vybe could not see. An answer without its basis is a guess with
 * good typography.
 */
export const isSample = true;

/**
 * The opening state. No transcript, no keyboard — just the invitation and
 * three questions worth asking, because a blank conversation box is the
 * fastest way to make someone close an app.
 */
export const opening = {
  lede: 'Ask about your body in your own words. Vybe answers from your own data, and says so when it cannot.',
  prompt: 'Try one of these, or type your own:',
};

/**
 * `kind` drives the treatment, not the colour:
 *   'answer'   — Vybe interpreted something and will show its working
 *   'boundary' — the question asks for a diagnosis; Vybe declines and hands off
 * The word for the kind is always printed, so the distinction survives a
 * screen reader and a viewer who cannot separate the hues.
 */
export const answers = [
  {
    id: 'tired',
    question: 'Why am I so tired this week?',
    kind: 'answer',
    answer:
      'Your sleep has not shortened — it has moved. You have gone to bed past midnight four nights running, and your deep sleep is down with it.',
    confidence: 'Moderate confidence',
    confidenceWhy:
      'Four nights since the shift, against a 30-night baseline. Deep sleep is an estimate from movement and heart rate, not a lab measurement.',
    dimensions: ['restore', 'nourish'],
    basis: [
      { id: 'b1', signal: 'Bedtime', detail: 'Median 00:52 this week, against 23:10 over 30 nights', source: 'Vybe Band' },
      { id: 'b2', signal: 'Deep sleep', detail: '52 min on late nights, 71 min on early ones', source: 'Vybe Band, estimated' },
      { id: 'b3', signal: 'Overnight HRV', detail: 'Down 18% on your 30-day average', source: 'Vybe Band' },
      { id: 'b4', signal: 'Last meal', detail: 'Finished 21:10 on three of the four late nights', source: 'You logged this' },
    ],
    unseen: [
      'Whether the late nights were work, a child, or choice — Vybe has no way to know which.',
      'Anything you drank. Alcohol changes this picture and nothing here records it unless you log it.',
    ],
    action: {
      when: 'TONIGHT',
      text: 'Put your phone down by 23:00 and eat by 20:00.',
      why: 'The two things in this picture you can move. Three nights is enough to see whether it lands.',
    },
  },
  {
    id: 'train',
    question: 'Should I train hard today?',
    kind: 'answer',
    answer:
      'Vybe would not push today, but this is close. Your recovery markers are low-normal and you have trained hard two days running.',
    confidence: 'Low confidence',
    confidenceWhy:
      'Vybe has eleven days of training data for you. It does not yet know how you respond to a third hard day, only that most people do not.',
    dimensions: ['move', 'vitals'],
    basis: [
      { id: 'b1', signal: 'Resting heart rate', detail: 'Up 4 bpm on your baseline, second morning running', source: 'Vybe Band' },
      { id: 'b2', signal: 'Overnight HRV', detail: 'At the bottom of your normal range, not below it', source: 'Vybe Band' },
      { id: 'b3', signal: 'Hard sessions', detail: 'Two in the last 48 hours', source: 'Vybe Band' },
    ],
    unseen: [
      'How you actually feel. If the session is one you have been looking forward to, that matters and Vybe cannot weigh it.',
      'Whether today is the last chance this week. Vybe does not read your calendar unless you connect it.',
    ],
    action: {
      when: 'TODAY',
      text: 'Go easy, and take the hard session tomorrow.',
      why: 'If your resting heart rate is back to baseline in the morning, that was the right call and Vybe will tell you so.',
    },
  },
  {
    id: 'apnea',
    question: 'Do I have sleep apnea?',
    kind: 'boundary',
    answer:
      'Vybe will not answer that. Sleep apnea is a diagnosis, it is made with a sleep study, and Vybe is not a medical device.',
    // The honest version of a refusal shows the data anyway. Withholding the
    // reading would be the same paternalism the product exists to avoid.
    instead:
      'Here is the overnight breathing signal it does record, which is a real thing you can take to someone who can diagnose.',
    dimensions: ['restore', 'vitals'],
    basis: [
      { id: 'b1', signal: 'Respiration rate', detail: '14.2 breaths per minute overnight, steady across 30 nights', source: 'Vybe Band' },
      { id: 'b2', signal: 'Overnight variation', detail: 'No unusual swings recorded in that window', source: 'Vybe Band' },
    ],
    handoff:
      'If you are waking unrefreshed, snoring, or someone has noticed you stop breathing, that is a conversation with a clinician. Export these 30 nights from Settings and bring them.',
  },
];

/**
 * What a typed question gets when there is no sample answer for it.
 *
 * In the shipped product this is where "not enough data yet" lives. In this
 * build it says what is actually true: this is a sample, and making up an
 * answer to an arbitrary question is exactly the failure mode the product is
 * built against.
 */
export const noAnswer = {
  kind: 'unknown',
  answer: 'There is no sample answer for that one.',
  detail:
    'This build ships three worked examples so the shape of an answer is visible. Vybe will not invent a reading about your body to fill a gap, here or anywhere else.',
};

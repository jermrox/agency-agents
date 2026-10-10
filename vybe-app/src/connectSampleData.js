/**
 * Sample data for the Connect dimension detail.
 *
 * Kept in its own module, and the screen says on-screen that it is sample
 * data. An invented health number that looks real is the one bug in this app
 * that could actually hurt someone.
 *
 * WHAT MAKES CONNECT DIFFERENT FROM THE OTHER FOUR
 * Restore, Move, Nourish and Vitals all read the body. Connect reads the
 * things that happened TO the body — the calendar, the time zones, the
 * weather — and then asks what the body did about them. That means it is the
 * one dimension whose inputs are not measurements at all, and the one
 * dimension that is routinely, structurally incomplete: a hard week has causes
 * that never reach a wrist sensor or a calendar invite.
 *
 * So the screen is built around attribution and its limit. The hours are
 * measured from the body; the names beside them come from outside it; and the
 * hours that no name explains get a block of their own rather than being
 * rounded into the nearest cause. Every product in this category assigns one
 * tidy reason to a bad week. The gap is the honest part.
 *
 * NOTHING HERE IS A STORED VERDICT
 * The named total, each source's share, the unexplained remainder and whether
 * a source has enough days behind it to say anything are all derived on the
 * screen from the numbers below, against rules it prints. A typed share can
 * drift away from the hours under it.
 *
 * HOURS ARE ASSIGNED TO ONE SOURCE ONLY. A hot afternoon in a travel day
 * belongs to the travel day, so the named hours sum rather than double-count.
 * That is a choice with a cost — it makes the first-ranked source look larger
 * than it is on its own — and the screen says so where the ranking appears.
 */
export const isSample = true;

export const connectWeek = {
  window: 'Week of 28 September',

  // The answer is a sentence about the week, not a load score. A number
  // nobody can interpret is the gap this product exists to close.
  answer:
    'This week asked more of you than your usual one, and your body spent it '
    + 'on the two travel days rather than the five busy ones.',
  confidence: 'MODERATE CONFIDENCE',
  confidenceWhy:
    'Your calendar and the weather are solid. The travel days are two days, '
    + 'which is a story rather than a pattern.',

  /**
   * `strainHours` is MEASURED, from the body: hours this week when your own
   * readings ran above your own 30-day baseline. It is the denominator the
   * shares below are taken against, and it is the only number on this screen
   * that did not come from outside you.
   */
  strainHours: 38,
  usual: { strainHours: 24, label: 'your usual week' },

  /**
   * `comparedDays` is how many days Vybe has seen that look like this one.
   * Under four it will not state a body response at all — two travel days are
   * not evidence about travel, and saying so is the whole point of the column.
   */
  sources: [
    {
      id: 'meetings',
      label: 'Back-to-back meetings',
      hours: 14,
      detail: 'Nineteen calls across Monday to Thursday, eleven of them with no gap either side.',
      comparedDays: 9,
      response: {
        metric: 'Overnight HRV',
        text: 'ran about 4 ms below your own average on days like these',
        caveat: 'Nine days is enough to notice and not enough to trust.',
      },
    },
    {
      id: 'travel',
      label: 'Two time-zone changes',
      hours: 9,
      detail: 'Out Friday on a 06:10 departure, back Sunday. Six hours each way.',
      comparedDays: 2,
      response: null,
    },
    {
      id: 'heat',
      label: 'Three days above 32°C',
      hours: 6,
      detail: 'Tuesday to Thursday. Your flat did not drop below 26°C overnight.',
      comparedDays: 6,
      response: {
        metric: 'Resting heart rate',
        text: 'sat about 3 bpm above your own average on hot nights',
        caveat: 'Six days, all of them this summer.',
      },
    },
    {
      id: 'oncall',
      label: 'On call, Thursday night',
      hours: 2,
      detail: 'One page at 02:40. You were up for about forty minutes.',
      comparedDays: 1,
      response: null,
    },
  ],

  /**
   * What Vybe says about the hours nothing explains. Written for the honest
   * case: the remainder is not a rounding error, and it is not the person's
   * fault for failing to log something.
   */
  unexplained:
    'Seven of this week’s thirty-eight hours have nothing beside them. Your '
    + 'calendar was clear, the weather was ordinary and you were home. Vybe '
    + 'does not know what those hours were, and it would rather leave them '
    + 'blank than hand them to the nearest cause on the list.',

  /**
   * The body side of the week, as readings. Reuses the same row component as
   * Restore and Nourish, because by this point in the screen the question is
   * the ordinary one those screens answer: what did the numbers do.
   */
  readings: [
    {
      id: 'hrv',
      label: 'Overnight HRV',
      value: '41 ms',
      reading: 'Down 11% on your 30-day average, lowest on Saturday',
      direction: 'down',
      concern: true,
    },
    {
      id: 'rhr',
      label: 'Resting heart rate',
      value: '58 bpm',
      reading: 'Up 4 bpm on your own baseline, back down by Sunday night',
      direction: 'up',
      concern: true,
    },
    {
      id: 'onset',
      label: 'Time to fall asleep',
      value: '24 min',
      reading: 'Up from your usual 14 minutes, worst on the two flight nights',
      direction: 'up',
      concern: false,
    },
    {
      id: 'steps',
      label: 'Daily movement',
      value: '9,400',
      reading: 'Held about level with your usual week, airports included',
      direction: 'flat',
      concern: false,
    },
  ],

  action: {
    text: 'Protect the night after you land, not the night before you fly.',
    why:
      'Your worst two readings this week both came after a flight, not before '
      + 'one. Vybe has two days of that, so this is worth one try rather than '
      + 'a rule.',
  },

  restraint:
    'Connect reads your calendar, your time zones and your weather. It does '
    + 'not know whether the meetings went well, whether the trip was worth '
    + 'making, or who you saw at the other end. It can tell you what your week '
    + 'cost your body. It cannot tell you whether that was a bad trade.',
};

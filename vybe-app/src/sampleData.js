/**
 * SAMPLE DATA — placeholder, not real measurements.
 *
 * Every value here is invented for layout purposes and is labelled as such
 * in the UI via the `isSample` flag on the screen. Replace this module with
 * the real data layer; nothing else needs to change.
 */
import { dimensions } from './theme';

export const today = {
  greeting: 'Good morning',
  dateLabel: 'Saturday, 19 September',
  suggestion: 'Why do I feel slower than usual today?',

  insight: {
    headline: 'Your later bedtime is showing up in this morning’s numbers.',
    body:
      'You went to bed about 90 minutes later than your usual window, and your resting heart rate is above your own baseline this morning. The two have moved together on six of the last eight late nights.',
    dimensionsInvolved: [dimensions.restore, dimensions.vitals],
  },

  cards: [
    {
      dimension: dimensions.restore,
      status: 'Under-recovered',
      detail: 'Short sleep and a late start, against your own 30-day pattern.',
    },
    {
      dimension: dimensions.move,
      status: 'Go easy today',
      detail: 'Two hard sessions back to back. A lighter day tends to work better for you.',
    },
    {
      dimension: dimensions.nourish,
      status: 'Hydration is low',
      detail: 'Below your typical intake by this hour on most days.',
    },
    {
      dimension: dimensions.connect,
      status: 'A heavier week',
      detail: 'More meetings than usual and one time-zone change on Tuesday.',
    },
    {
      dimension: dimensions.vitals,
      status: 'Resting HR elevated',
      detail: 'Above your baseline for a second morning.',
    },
  ],
};

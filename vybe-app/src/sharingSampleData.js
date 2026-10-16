/**
 * Sample data for SharingScreen.
 *
 * Every person, date and count below is invented to show the layout. None of
 * it is a real reading or a real share. The screen prints a sample banner while
 * `isSample` is true, so this module can never pass for someone's account.
 */

export const isSample = true;

export const sharing = {
  position:
    'You can show one person a slice of this, for a while, and take it back.',
  positionDetail:
    'They get a read-only view in a browser. No account, no app, no download ' +
    'button. Nothing leaves your phone until you name who it is for.',

  // What each dimension would actually put in front of the other person.
  // The words are the consent: a switch labelled "Restore" means nothing to
  // someone deciding whether their coach should see it.
  scope: [
    {
      key: 'restore',
      shows: 'Sleep timing and overnight HRV against your own range',
      hides: 'Notes you wrote about why a night went badly',
    },
    {
      key: 'move',
      shows: 'Training load by week and how recovery followed it',
      hides: 'Where you trained — no location ever leaves the phone',
    },
    {
      key: 'nourish',
      shows: 'Meal timing relative to sleep',
      hides: 'What you ate, and any photos',
    },
    {
      key: 'connect',
      shows: 'How many evenings had time with people, as a weekly count',
      hides: 'Who, where, and anything from your contacts',
    },
    {
      key: 'vitals',
      shows: 'Resting heart rate and breathing rate bands over months',
      hides: 'Nothing extra is held back here; it is all summary already',
    },
  ],

  // Durations stop at ninety days. There is deliberately no "always": a share
  // nobody remembers granting is how data ends up where it should not be.
  durations: [
    { id: 'd7', label: '7 days', days: 7 },
    { id: 'd30', label: '30 days', days: 30 },
    { id: 'd90', label: '90 days', days: 90 },
  ],

  draft: {
    name: 'Sample coach',
    role: 'Running coach',
    on: ['restore', 'move'],
    durationId: 'd30',
  },

  active: [
    {
      id: 'a1',
      name: 'Sample clinician',
      role: 'Primary care',
      dims: ['vitals', 'restore'],
      started: 'Thu 1 Oct',
      ends: 'Sat 31 Oct',
      daysLeft: 15,
      totalDays: 30,
      opened: 'Opened twice. Last opened Tue 13 Oct, 9:12 am.',
    },
    {
      id: 'a2',
      name: 'Sample partner',
      role: 'Family',
      dims: ['connect'],
      started: 'Fri 9 Oct',
      ends: 'Fri 16 Oct',
      daysLeft: 0,
      totalDays: 7,
      opened: 'Never opened.',
    },
  ],

  never: [
    'They cannot download, copy out or forward the view.',
    'They never see a raw reading, only the summaries named above.',
    'A share ends on its date even if you forget it.',
    'Every time they open it, the line under their name says so.',
  ],
};

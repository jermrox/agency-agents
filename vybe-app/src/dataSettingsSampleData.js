/**
 * Sample data for the Data & permissions screen.
 *
 * Kept in its own module, and the screen says on-screen that it is sample
 * data. Nothing here is a real measurement or a real sync time.
 *
 * WHY THIS SCREEN CARRIES THE LOAD IT DOES
 * Vybe's position is that a person's health data is theirs: bought once, not
 * rented, never sold. A settings screen is where that either becomes true or
 * is revealed as marketing. So the copy below states what leaves the phone and
 * what does not, in the same plain language the rest of the app uses, and the
 * screen shows the split rather than asserting it.
 */
export const isSample = true;

export const dataSettings = {
  // The position, in the fewest words that still mean something specific.
  position: 'Vybe sells bands. It does not sell you.',
  positionDetail:
    'You buy the Band once. The answers come with it. There is no subscription '
    + 'gating your own history, and there is no arrangement under which your '
    + 'readings reach anybody who did not buy them from a shop.',

  /**
   * Connected sources. `sends` is the honest list of what each one actually
   * hands over — not a category name like "Health data", which tells a person
   * nothing and is how consent forms get away with being unreadable.
   *
   * `on` is the sample state. The screen states it in words next to the
   * switch, so the toggle's position is never the only signal.
   */
  sources: [
    {
      id: 'band',
      name: 'Vybe Band',
      sends: 'ECG, heart-rate variability, sleep and movement',
      detail: 'Over Bluetooth, to this phone. Nothing routes through a server to get here.',
      lastSync: 'Synced 8 minutes ago',
      on: true,
    },
    {
      id: 'health',
      name: 'Apple Health',
      sends: 'Steps, workouts and weight',
      detail: 'Read only. Vybe writes nothing back.',
      lastSync: 'Synced this morning',
      on: true,
    },
    {
      id: 'calendar',
      name: 'Calendar',
      sends: 'How full a day is, and time-zone changes',
      detail: 'Busy and free blocks only. Vybe never reads an event title or who is invited.',
      lastSync: 'Synced this morning',
      on: true,
    },
    {
      id: 'location',
      name: 'Location',
      sends: 'Nothing right now',
      detail: 'If you turn it on, Vybe uses coarse location for weather and altitude — the two things that move your numbers without you doing anything.',
      lastSync: 'Off since you installed the app',
      on: false,
    },
  ],

  /**
   * Where the data physically sits, as shares of the whole. Drawn as one
   * proportional bar: the claim "almost all of it stays on your phone" is
   * either visible in the proportions or it is not true.
   *
   * Shares must total 100 — the screen asserts that and would otherwise
   * silently mis-draw.
   */
  residency: [
    {
      id: 'phone',
      place: 'On your phone',
      share: 88,
      what: 'Your whole history. This is the original, not a cache.',
    },
    {
      id: 'servers',
      place: "On Vybe's servers",
      share: 8,
      what: 'Only what a question you asked needed, and only until it is answered. Deleted after 30 days.',
    },
    {
      id: 'band',
      place: 'On the Band',
      share: 4,
      what: 'About three days of raw signal, overwritten as it fills.',
    },
  ],

  // Stated as flat negatives on purpose. A promise with a hedge in it is a
  // plan, not a promise.
  never: [
    'Sold. Not to advertisers, data brokers, researchers or anyone else.',
    'Shared with an insurer or an employer, whoever is paying.',
    'Used to target advertising, inside this app or outside it.',
    'Held hostage — cancel anything and your history stays readable.',
  ],

  controls: {
    exportLabel: 'Export everything',
    exportDetail: 'One file you can actually open: CSV for the readings, JSON for the rest. No request form, no waiting period.',
    deleteLabel: 'Delete everything',
    deleteDetail: 'Permanent, and it includes the copies on our servers. Finishes within seven days, and we email you when it is done.',
  },
};

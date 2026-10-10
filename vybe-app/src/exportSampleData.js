/**
 * Sample data for the export screen.
 *
 * Kept in its own module, and the screen says on-screen that it is sample
 * data. Note what is and is not invented here, as on the import screen: these
 * are RECORD COUNTS, file sizes and retention periods. No heart rate, no sleep
 * duration, no score. A screen about what leaves with you never needs to show
 * a reading.
 *
 * WHAT THIS SCREEN IS ARGUING, AND WHY IT IS THE IMPORT SCREEN BACKWARDS
 * On the import screen Vybe sorted another product's history into what it
 * would compute with, what it would only draw, and what it would not take —
 * and refused to build a baseline out of somebody else's estimates.
 *
 * This is the same company handing its own data to whatever comes next, and
 * the position only holds if it is symmetrical. Vybe's answers, confidences
 * and pattern verdicts are exactly the kind of derived value it told you not
 * to trust from a competitor. So the export says so, in the manifest, next to
 * them: take them, they are yours, and the next product should treat them the
 * way Vybe treated the last one's.
 *
 * `DataSettingsScreen` already promises "CSV for the readings, JSON for the
 * rest" and a delete that finishes within seven days. Everything below has to
 * keep that promise rather than quietly improve on it.
 *
 * NOTHING HERE IS A STORED TOTAL. The record count, the share of the export
 * that is derived, which formats carry which groups, and how much of it
 * another product can read are all computed on the screen from the groups
 * below.
 */
export const isSample = true;

export const exportInfo = {
  preparedLabel: 'Ready now',
  spanLabel: 'Everything, 14 August 2023 to today',
  sizeLabel: '38 MB',
  waitNote:
    'No request form and no waiting period. The file is built on your phone '
    + 'from what is already there.',
};

/**
 * `kind` decides what the screen says about portability.
 *   measured — a timestamp and a value. Any product can read it.
 *   derived  — Vybe's own conclusion. Yours to take, not safe to compute with.
 *   account  — what you turned on, and when.
 */
export const groups = [
  {
    id: 'readings',
    label: 'Heart, sleep and movement readings',
    kind: 'measured',
    records: 1184000,
    formats: ['csv', 'json'],
    detail: 'Timestamps and values, one row each, exactly as the Band recorded them.',
    note:
      'The portable part. Any product that reads a CSV can use these the day '
      + 'you hand them over, and nothing in them depends on Vybe being right '
      + 'about anything.',
  },
  {
    id: 'context',
    label: 'What you connected, and what you logged',
    kind: 'measured',
    records: 9420,
    formats: ['csv', 'json'],
    detail:
      'Meal times you typed, calendar shapes without titles, and the weather '
      + 'for your area. The inputs to Connect, not its conclusions.',
    note:
      'Also portable, and worth more than it looks: this is the part almost no '
      + 'other product collects, so it is the part that is hardest to rebuild '
      + 'if you leave.',
  },
  {
    id: 'answers',
    label: 'Every answer Vybe gave, and what it rested on',
    kind: 'derived',
    records: 412,
    formats: ['json', 'pdf'],
    detail:
      'The question, the answer, the readings behind it, the confidence, and '
      + 'the blind spots it stated at the time.',
    note:
      'Vybe’s conclusion, not a measurement. It is yours and it goes with '
      + 'you — and the next product should treat it the way Vybe treats an '
      + 'imported readiness score: read it, do not compute with it.',
  },
  {
    id: 'patterns',
    label: 'Patterns Vybe claimed, including the weeks they broke',
    kind: 'derived',
    records: 9,
    formats: ['json', 'pdf'],
    detail:
      'Each claim, the rule it was scored against, every week it held and '
      + 'every week it did not.',
    note:
      'The exceptions travel with the claim. A pattern exported without the '
      + 'weeks it failed would be a stronger claim than the one Vybe actually '
      + 'made.',
  },
  {
    id: 'outcomes',
    label: 'What Vybe predicted, and whether it was right',
    kind: 'derived',
    records: 37,
    formats: ['json', 'pdf'],
    detail:
      'Each suggestion, the range committed to beforehand, what happened, and '
      + 'the ones that missed.',
    note:
      'The misses are in the file. An export that carried only the successes '
      + 'would be marketing with a filename.',
  },
  {
    id: 'account',
    label: 'Settings, consents and the permission log',
    kind: 'account',
    records: 88,
    formats: ['csv', 'json'],
    detail:
      'Every source you turned on or off, with the date, and every consent '
      + 'screen you passed through.',
    note:
      'Kept so you can check what you agreed to against what Vybe did, '
      + 'without taking Vybe’s word for either.',
  },
];

export const formats = [
  {
    id: 'csv',
    label: 'CSV',
    good: 'Opens in a spreadsheet. Best for the readings and anything you want to chart yourself.',
    bad: 'Cannot carry an answer with its reasoning attached — that flattens into text nobody can follow.',
  },
  {
    id: 'json',
    label: 'JSON',
    good: 'Complete. Everything in the manifest, with the structure intact, for another product or a developer.',
    bad: 'Not readable by a person without tooling, and nobody should pretend otherwise.',
  },
  {
    id: 'pdf',
    label: 'PDF',
    good: 'The answers as they were written, in order, for a person to read — or to hand to a clinician.',
    bad: 'A record, not data. Nothing in it can be recomputed or re-imported.',
  },
];

/**
 * What stays behind after a delete, how long, and why. `days` is from the day
 * the deletion finishes.
 */
export const retention = [
  {
    id: 'billing',
    label: 'Order and payment records',
    days: 2555,
    why:
      'Seven years, because tax law requires it. It is the order, not the '
      + 'health data: what was bought, when, and for how much.',
  },
  {
    id: 'backups',
    label: 'Encrypted backups',
    days: 30,
    why:
      'Backups roll on a 30-day cycle and cannot be edited in place without '
      + 'breaking the ones around them. Your records are gone from the live '
      + 'system immediately and age out of the backups within 30 days.',
  },
  {
    id: 'crash',
    label: 'Anonymous crash reports',
    days: 90,
    why:
      'No identifier in them connects to you or your account, which is also '
      + 'why they cannot be found and removed individually.',
  },
];

export const deletePromise =
  'Deletion is permanent, includes the copies on Vybe’s servers, finishes '
  + 'within seven days, and you get an email when it is done. The three things '
  + 'above are what is left, and this screen is where they are listed rather '
  + 'than a policy page nobody opens.';

export const restraint =
  'Vybe does not hold your data to keep you. The export is built on the phone, '
  + 'needs no request form and has no waiting period, and the readings in it '
  + 'are in a format any competitor can read on the first day. The part that '
  + 'is hard to take with you is not the data — it is the months Vybe spent '
  + 'learning what is normal for you, and the honest thing to say is that a '
  + 'new product will need those months too.';

/**
 * Sample data for the fit check — the step between pairing and the first night.
 *
 * Kept in its own module, and the screen says on-screen that it is sample
 * data. Nothing here is a reading: the check reports in WORDS whether the
 * sensor can see skin, whether the Band is moving on the wrist, and whether it
 * sits where it should. A signal-quality percentage would look like a health
 * number, and an invented number that reads as real is the one bug in this app
 * that could actually hurt someone.
 *
 * WHAT THIS SCREEN IS ARGUING
 * A wearable that is worn wrong does not read badly, it reads something else:
 * a gap between sensor and skin, or the Band sliding, instead of a pulse. Every
 * product in the category discovers this on the user's behalf weeks later, as
 * a "low quality" badge on a night that is already gone. The honest place for
 * that conversation is before the first night, in plain words, with the fix
 * next to the fault.
 */
export const isSample = true;

/** The sentence a person reads before anything else on the screen. */
export const intro = {
  title: 'Wear it so it can read you.',
  lede:
    'Put the Band on the way you would wear it to bed, then run the check. '
    + 'It takes a few seconds and tells you in words what the sensor can see.',
};

/**
 * Which wrist. The choice is real (it changes what the Band expects to see
 * about movement) but neither answer is wrong, so it is a preference, not a
 * gate, and the screen says so.
 */
export const wrists = [
  { id: 'left', label: 'Left wrist' },
  { id: 'right', label: 'Right wrist' },
];

export const wristNote =
  'Either works. Most people get a cleaner night read from the wrist they use less, '
  + 'because it moves less while they sleep. You can change this any time.';

/**
 * The check is a state machine, not a spinner. Each state is a sentence a
 * screen reader can read out, and the sequence below is scripted so the
 * sample shows both outcomes: a first pass that finds one thing to fix, and a
 * second pass that reads clean. Nothing is sensed; nothing is random.
 */
export const STATUS = {
  idle: 'Not checked yet',
  reading: 'Reading the sensor…',
  adjust: 'One thing to change',
  clean: 'Reads clean',
};

/**
 * The three things that decide whether tonight's data is about a body or
 * about a loose strap. `good` and `fix` are both full sentences on purpose:
 * the result row never relies on a tick, a glyph or a colour to carry meaning.
 */
export const checks = [
  {
    id: 'contact',
    label: 'Skin contact',
    good: 'The sensor is against skin.',
    fix: 'Move the Band so the underside sits flat on your skin, not on a sleeve.',
    why: 'An optical sensor reads light coming back from skin. Through fabric or air it reads nothing and may call it something.',
  },
  {
    id: 'snug',
    label: 'Snugness',
    good: 'The Band is not sliding when you move.',
    fix: 'Tighten by one notch. You should be able to slide one finger under it, not two.',
    why: 'A Band that slides turns your own movement into a signal. Too tight, and it marks your skin and you take it off by midnight.',
  },
  {
    id: 'position',
    label: 'Position',
    good: 'The Band sits about a finger above the wrist bone.',
    fix: 'Slide it up the arm a little, away from the bone, where the wrist is flatter.',
    why: 'Over the bone the sensor rocks as the wrist turns. A finger higher it stays still.',
  },
];

/**
 * Scripted outcomes for the sample. Pass one finds the strap loose; pass two,
 * after the person "adjusts", finds everything in order. Keyed by check id.
 */
export const passes = [
  { contact: true, snug: false, position: true },
  { contact: true, snug: true, position: true },
];

/**
 * The consent axis of this screen. A fit check listens to the sensor, and a
 * person is entitled to know what happens to what it heard. The answer is
 * nothing: it is thrown away, and the screen says so where the check runs.
 */
export const recordLine = {
  label: 'WHAT THIS CHECK KEEPS',
  text: 'Nothing. The few seconds the sensor listens for are discarded as soon as the result is on screen.',
  detail:
    'Your history starts tonight, when you choose to wear it. A fit check is '
    + 'not a reading and never appears in your record.',
};

/**
 * The expectation that survives a bad night. If the fit is wrong, Vybe will
 * say it could not read rather than invent a recovery number, and that is
 * worth saying before the first night instead of after it.
 */
export const honestLine =
  'If the fit slips tonight, Vybe will tell you it could not read that stretch. It will not guess.';

export const skipLine =
  'You can skip this. The Band will still try to read tonight; it just will not have told you how it is sitting.';

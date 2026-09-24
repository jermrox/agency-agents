# Vybe Health — screens

Plain JavaScript, React Native core only. No navigation library, no icon pack,
no chart library, no UI kit. Drops into a blank Expo app and runs.

## Run

```
npx create-expo-app vybe --template blank
cd vybe
# copy App.js and src/ over the generated ones
npx expo start
```

## Screens

- **HomeScreen** — today, in reading order: the ask bar, the insight, then the
  five dimensions.
- **RestoreScreen** *(21 Sep)* — the Restore dimension in detail. Tap the
  Restore card on Home to open it.
- **MoveTrendScreen** *(new, 24 Sep)* — six months of weekly active minutes,
  and what changed. Tap the Move card on Home to open it.

## The three decisions worth keeping

**1. The answer comes first, and it is a sentence.**
RestoreScreen opens on *"You are less recovered than usual, and the likeliest
reason is the 1am bedtime after Saturday."* Not a number, not a ring, not a
score out of 100. Every competitor opens on a score and leaves the interpreting
to the user — that gap is the entire product thesis, so the top of the screen
has to be the thesis too. The readings are still there, one section down, as
evidence *for* the sentence rather than as the thing itself.

**2. Four treatments, not four cards.**
The answer is a tinted panel, the evidence is a hairline-separated list, the
context is inline notes, and the action is the one dark block on the screen.
A stack of identical rounded cards makes everything look equally important,
which means nothing reads as important. The hierarchy here is legible before
you read a word.

**3. Confidence is stated, and so is its reason.**
*"Moderate confidence — three nights of data since the change, and one known
context event."* A health app that sounds equally certain about everything is
either lying or not paying attention. Saying how sure it is, and why, is what
makes the confident statements worth believing.

## The trend screen, and why it looks like that

**A chart is not an answer, so it is not at the top.**
MoveTrendScreen opens on *"Your movement climbed five weeks straight out of the
late-July dip, and every week since 24 August has sat above your usual range"* —
and only then draws the six months it is describing. Somebody opening a history
screen wants to know whether the line is good news before being asked to read
it. The caveat sits directly underneath: six months shows a direction, not a
lasting change.

**Drawn with Views sized by value, not a charting library.**
Every RN chart package pulls in react-native-svg, and most pull reanimated and
gesture-handler behind it — three native dependencies and an Expo prebuild to
draw twenty-six rectangles. A `View` with a computed height *is* a rectangle.
`src/components/TrendColumns.js` is flexbox and arithmetic.

**The band is the person's own range.**
The shading behind the columns is the middle half of their own last 26 weeks
(114–159 minutes), not a population norm. "Above average for women your age" is
a comparison nobody asked for; "higher than your own normal, six months running"
is a fact about them. The legend says so in words, because a grey rectangle
explains nothing on its own.

**Five treatments, so the hierarchy reads before a word does.**
Oversized type on bare paper for the verdict, a full-width plot for the series,
two proportional bars lying on their side for the month-on-month comparison, a
numbered timeline on a rule for the events, and one tinted panel to close. The
plot is the only thing on the screen shaped like a chart, so the eye lands there
unprompted.

**Every number on the screen is derived from the series, not typed in.**
The four-week averages, the 77% change, the peak and which weeks sit outside the
band are all computed at render time from `src/moveTrendSampleData.js`. A summary
typed by hand drifts from the data it claims to describe the first time somebody
edits a value — and then the screen is confidently wrong. Only the editorial
sentences are hand-written, which makes them the only thing a reviewer has to
check.

## Non-negotiables held

- All placeholder data is in `src/restoreSampleData.js`, and the screen says
  **"Sample data — these are not your readings"** at the top. An invented
  health number that looks real is the one bug here that could hurt someone.
- Colour never carries meaning alone. Every reading spells out its direction
  in words ("Down 18% on your 30-day average"); the arrow glyph is decoration
  and is hidden from screen readers.
- Every interactive element has `accessibilityRole`, `accessibilityLabel` and,
  where the destination is not obvious, `accessibilityHint`.
- Readings use `fontVariant: ['tabular-nums']` so the numbers hold one optical
  column down the list.

## Brand tokens

`src/theme.js` — sampled from the real brand assets, not invented:
ink `#161C22` (the V), brand `#1F8E78` (the HEALTH wordmark), brandSoft
`#A8DCC8` (the mint ECG waveform), paper `#FBF9F5`.
Dimension hues are read off the Vybe Intelligence artwork — Restore is
periwinkle `#4B4BAE`, and Connect is rose `#96476A`, not teal.

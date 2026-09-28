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
- **MoveTrendScreen** *(24 Sep)* — six months of weekly active minutes,
  and what changed. Tap the Move card on Home to open it.
- **DataSettingsScreen** *(25 Sep)* — what is connected, where the data
  sits, and how to export or delete it. Reached from "Your data" in the Home
  header.
- **NourishScreen** *(new, 28 Sep)* — one day of eating on real clock time, and
  the gap between the last bite and lights out. Tap the Nourish card on Home.

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

## The data screen, and why it looks like that

**Every row says what the source actually hands over.**
Not "Health data" or "Analytics" — the category label is how consent forms end
up unreadable while staying technically complete. Calendar reads *how full a day
is and time-zone changes*, and the row says outright that Vybe never reads an
event title or who was invited.

**The storage split is drawn, not asserted.**
"Almost all of it stays on your phone" is either visible in the proportions or
it is not true, so one proportional bar shows 88% on the phone, 8% on Vybe's
servers and 4% on the Band. The screen refuses to draw the bar at all unless the
shares total 100, and a worded legend carries the meaning for anyone the bar
does not reach.

**Export and delete are last, and they are the point.**
They are the only lines on the screen a person can check, so they close the
argument rather than open it. Delete asks twice, and the button changes its
*words* between the two states rather than leaning on red.

**Reachable from the front door.**
A company whose position is "your data is yours" should not bury the proof three
taps down, so Home carries a "Your data" link in its header.

## The nourish screen, and why it looks like that

**The claim is about timing, so the screen is a clock.**
NourishScreen opens on *"The strongest signal in your food data is when you stop
eating, not what you ate"* — and then the middle of the screen is the day laid
out on an axis, with the meals where they actually happened. A list of meals in
order cannot make that argument: it spaces breakfast and lunch the same distance
apart as lunch and a dinner six hours later. On an axis the shape of the day *is*
the finding — a long empty afternoon, then a meal pressed up against sleep.

**Every nutrition app opens on a calorie total. This one refuses to.**
A calorie count is a number the person then has to interpret alone, which is the
gap the whole product exists to close. So the day's food gets one hairline list
of four readings, and the screen closes by saying outright what it will never do:
count calories, score the day out of ten, or sort food into good and bad.

**The one number that matters is set at 56pt on bare paper.**
`1h 35m` — last bite to lights out — with the person's own 3h for comparison, not
a guideline. It sits between the answer and the plot because it is the figure the
answer turns on, and it is computed from the meal times and the bedtime rather
than typed, so it cannot drift from the timeline drawn directly beneath it.
The same is true of the eating window, the duration of each meal, and the
19-minute difference in the pattern section.

**A Nourish screen making a Restore argument.**
The pattern section compares estimated deep sleep on the nights after a late
dinner with the nights after an early one, and says so in words: the five
dimensions are one system, not five scores that never speak to each other. It
also says, in the same breath, that deep sleep is an *estimate* from the Band and
not a measurement — a wrist sensor does not get to sound certain about sleep
architecture.

**The marker is a touch target and the bar is the truth.**
A ten-minute coffee is under 1% of an eighteen-hour day, which is three pixels:
honest as geometry, impossible as a thumb target. So `DayTimeline` draws the true
duration as a small bar under the day's line and puts a 26pt numbered marker on
the midpoint for tapping, with the numbers mapped to meal names in a line of
text under the axis. Both bands are explained in words for the same reason the
readings are — a tinted rectangle tells somebody who cannot separate these
colours nothing at all.

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

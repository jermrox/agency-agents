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
- **NourishScreen** *(28 Sep)* — one day of eating on real clock time, and
  the gap between the last bite and lights out. Tap the Nourish card on Home.
- **AskScreen** *(29 Sep)* — the conversation. Ask in your own words and
  get an answer with its basis, its blind spots and one action. Tap the ask bar
  at the top of Home.
- **OnboardingScreen** *(30 Sep)* — first run: pair the Band, choose what
  Vybe may read, see what you agreed to, and see what it can actually tell you
  yet. The app opens here.
- **PatternHistoryScreen** *(1 Oct)* — twelve weeks of one claim, and the
  weeks it broke. Reached from the pattern section of NourishScreen.
- **OutcomeScreen** *(2 Oct)* — Vybe grading itself: every suggestion it
  made, what it predicted, what happened, and the ones it got wrong. Reached
  from the "did it work last time" block on RestoreScreen.
- **ConnectScreen** *(5 Oct)* — one week of outside load: thirty-eight
  hours of elevated readings, what each of them is being blamed on, and the
  seven that nothing explains. Tap the Connect card on Home.
- **FollowUpScreen** *(6 Oct)* — what happens when you tell Vybe it is
  wrong: a correction, the parts of the reasoning it moves, and the parts still
  standing. Reached from "That's not right" on AskScreen.
- **ImportScreen** *(7 Oct)* — connecting a source that already has years
  in it: what Vybe will compute with, what it will only draw, and what it will
  not take. Reached from the sources step of OnboardingScreen.
- **SeasonScreen** *(8 Oct)* — the same months a year apart, and the five
  it has only seen once. Reached from "what would make this stronger" on
  PatternHistoryScreen.
- **ExportScreen** *(new, 9 Oct)* — what actually leaves with you, what another
  product can use, and what Vybe keeps after a delete. Reached from "Export
  everything" on DataSettingsScreen.

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

## The ask screen, and why it looks like that

**No chat bubbles.**
A bubble pair says "two people talking, both equally sure". What is actually
happening is a question and a piece of reasoning, and they do not deserve the
same weight. So the question is a quiet label over a line of ink, and the answer
is a tinted panel; the basis is a hairline list, the action is the one dark
block. Four registers, so the hierarchy reads before the words do.

**Every answer shows what Vybe could not see.**
"What this rests on" is the easy half — the signals and the window they cover.
"What Vybe could not see" is the half competitors omit: whether the late nights
were work or choice, anything the person drank, how they actually feel today. A
confident sentence with no stated blind spots is how a wellness product starts
sounding like a doctor, and that is the exact drift the product rule forbids.

**One of the three worked examples is a refusal.**
*"Do I have sleep apnea?"* gets the only outlined block on the screen and the
label OUTSIDE WHAT VYBE DOES: a diagnosis is made with a sleep study, and Vybe is
not a medical device. It then shows the overnight breathing signal anyway and
says to export the 30 nights and take them to a clinician. Withholding the
reading would be the same paternalism the product exists to avoid — the boundary
is on the claim, not on the person's own data.

**Confidence is a sentence with a reason attached.**
"Low confidence — Vybe has eleven days of training data for you. It does not yet
know how you respond to a third hard day, only that most people do not." A
percentage would be a number the person has to interpret alone, which is the gap
the product exists to close.

**A typed question with no sample answer says so.**
The composer is a real `TextInput`. Anything outside the three worked examples
returns *"There is no sample answer for that one"* rather than a generated
reading — in this build because it would be fiction, and in the shipped product
because "not enough data yet" is a real answer that has to have a place to live.

## The onboarding screen, and why it looks like that

**Sources are described by the question they unlock, not by the data they send.**
"Calendar" tells a person nothing. *"Was it the week, or was it me?"* tells them
exactly what the permission buys. The Data screen already does disclosure — what
each source hands over, and where it sits — so this screen deliberately works the
other axis: on first run you are deciding, not auditing. Each row still names the
use it is excluded from, because that is the half a permission dialog leaves out:
the calendar row reads event times and time zones and never the titles.

**Nothing is on by default.**
A ticked box the person did not tick is not consent. Every switch starts off, and
the step says so in its first line. This costs connected sources and is the point.

**Pairing is a state machine, not a spinner.**
Not looking yet → looking → found → pairing → paired, each named in words on the
screen and announced through `accessibilityLiveRegion`, because a moving circle is
not a status and a screen reader cannot read one. The three physical things that
decide whether a search succeeds — Bluetooth on, Band charged, hold the button —
are shown *before* the attempt, not behind a "trouble connecting?" link that
appears after it fails.

**Consent comes third, as a summary of decisions already made.**
Not a wall of text read before the person knows what any of it buys. The step
restates what is being read from, then the two promises that can actually be
checked (the readings live on this phone; export and delete are one tap), then the
claim boundary in the one outlined block — the same treatment the Ask screen gives
a refusal, so the app says "this is outside what Vybe does" in one visual language.

**The last step says Vybe knows nothing.**
Every first-run flow ends on "you're all set", which on day one is false: a band
that has watched you for zero nights has nothing to say about you. So the final
step reads **Today — nothing yet**, then what arrives after three nights (your own
range, roughly, labelled low confidence), two weeks (patterns, and the first real
answers) and six weeks (whether a change you made actually moved anything). It is
the only expectation that survives contact with the product, and it makes the
closing ask a small one: wear it tonight.

## The pattern history screen, and why it looks like that

**It is a history of a claim, not of a metric.**
`MoveTrendScreen` already does the other kind: one number across twenty-six
weeks. This screen tests the thing the product actually asserts — that it can
find a relationship — by showing both halves of that relationship week by week.
Two values and a verdict per week do not fit in an eight-point column, which is
why it is twelve rows down the phone rather than a dense plot across it, and why
every row has a full-size touch target and its words on it.

**The weeks it broke are the same size as the weeks it held.**
Nine of eleven is a different claim from eleven of eleven, and every product that
reports "we found a pattern" has rounded that difference away. Both exceptions sit
in the list at full size with Vybe's explanation beside them — and for one of them
the explanation is *"Vybe does not know. Nothing in your data separates this week
from the ones where the pattern held. It is left here rather than explained away."*
A product that explains away every exception is not explaining, it is defending.

**One week is excluded from the count, and the screen says so.**
Three recorded nights is not evidence in either direction, so the denominator is
eleven, not twelve, the row reads "Too few nights", and the headline adds
"1 more week had too few nights to count". The thin week is also excluded from the
middle it would otherwise be judged against.

**Nothing on the screen is a stored verdict.**
`9 of 11`, the `64 min` middle, and each row's "Held" / "Ran the other way" are
all computed at render from the numbers in `patternHistorySampleData.js`, against
a rule printed on screen. A typed headline can drift away from the rows beneath
it, and this is the screen where that would matter most.

**The rule is printed, not hidden.**
"Three or more nights of eating after 21:00 came with deep sleep below your
twelve-week middle." A pattern you cannot check is indistinguishable from one
that was asserted — and a correlation coefficient would be a number the person
has to interpret alone, which is the gap the whole product exists to close.

**The last word is that this is not a cause.**
The closing dark block says Vybe has shown two things that moved together in the
person's own data and the weeks they did not, and that it cannot tell them
eating earlier would have fixed those weeks — only that trying it for three weeks
would tell them something this screen cannot.

## The outcome screen, and why it looks like that

This is the screen the rest of the app points at. Every other screen ends with
one suggestion; this one comes back and says whether the suggestion was any good.

**The criterion is written down before the attempt.**
Each row carries the range Vybe committed to at the time — the metric, the
numbers, the units, the window. *"Said 44–50 ms within three nights · was 47."*
Deciding after the fact what counted as working is how every product in this
category wins every time, and it is why none of them are believed.

**Not doing it is a third outcome, not a failure.**
Three of the ten were never attempted, so the advice was never tested and Vybe
learned nothing. Scoring those against the person would make the tally
flattering — it would hide Vybe's weak suggestions behind somebody's difficult
week. The screen says the opposite outright: the untried ones are *"the clearest
signal on this screen that Vybe asked for something that did not fit your week."*

**The record is a fraction, not a percentage.**
`4 of 7`, set large on bare paper. "57%" would throw away the sample size, which
is the most important thing about it. The reading beside it is equally plain:
*"Vybe is right more often than not, and not by much."*

**There is a section called What Vybe Got Wrong.**
Three tested suggestions missed, and each one says what changed as a result —
including one where the honest answer is *"Nothing yet. Three days is not enough
to tell a weak suggestion from a half-done one, and Vybe will not pretend
otherwise."* It gets the outlined block, the same treatment the Ask screen gives
a refusal, because both are the app admitting a limit.

**The tally is arithmetic over the ledger.**
`4 of 7`, the miss count and every row's verdict are computed at render from
`adherence`, `actual` and the predicted range. On a screen whose whole claim is
"we are not marking our own homework", a headline that disagreed with its own
rows would be the only bug that matters.

**This row is type, not a plot.**
The app has three plots already. A predicted *range*, one actual, and whether one
fell inside the other is three numbers and a word — it reads faster set as type,
and drawing it would be a picture of a sentence.

## The connect screen, and why it looks like that

Four of the five dimensions read the body. Connect reads what happened *to* it —
the calendar, the time zones, the weather — then asks what the body did about it.
That makes it the only dimension whose inputs are not measurements, and the only
one that is structurally incomplete: a hard week has causes that never reach a
wrist sensor or a calendar invite.

**So the claim is an attribution, and attribution needs a form that shows
composition.**
`38h` of elevated readings, broken into four named parts. Restore's hairline list
cannot show that one quantity is *made of* other quantities; a single bar read
left to right can. The app's two existing bar treatments answer a different
question — `TrendColumns` is one value per week across twenty-six weeks,
`PatternWeeks` is one value per week against a line — so neither was reusable.

**The hours nothing explains are drawn, ranked and given a block of their own.**
Seven of the thirty-eight have no cause beside them: clear calendar, ordinary
weather, home all week. Every product in this category hands those to the busy
week and shows a tidy pie. This one says it *"would rather leave them blank than
hand them to the nearest cause on the list"*, and the remainder gets a segment
with an outline and no fill, at the end of the bar and the bottom of the list.
A screen that can only produce complete explanations is a screen that invents
them.

**A source with too few comparable days says so instead of reporting an
effect.**
Two time-zone changes are the single largest thing that happened this week, and
Vybe still refuses to say what travel does to you, because two days is a story.
The floor is four comparable days, printed on screen, and the screen adds up what
it is holding open rather than explaining: 7 unexplained hours plus 11 under thin
sources is **47% of the week**.

**The bar is the second reading, never the only one.**
Its segments are steps of the one Connect hue, applied as opacity rather than new
tokens — and steps of a single hue are exactly what somebody with low contrast
sensitivity cannot separate. So every segment's name, hours and share are printed
in the list beneath it, the bar is hidden from screen readers, and removing it
loses nothing.

**Every figure is arithmetic over the sources.**
The named total, each share, the remainder, the 14-hour difference from a usual
week and the count of sources Vybe will not read are computed at render. The
shares sum to exactly 100, so the bar fills without overflowing. `unexplainedOf`
clamps at zero and the screen swaps in an overlap note, so a future data source
that double-counts produces a caveat rather than a backwards bar.

## The follow-up screen, and why it looks like that

`AskScreen` is the front door: a question in, an answer out with its basis and
its blind spots. This is the half that comes after, and almost nothing in this
category ships it — the person usually knows something the sensor does not, and
the moment they say so decides whether a health assistant is useful or finished.

**Vybe does not fold.**
Three corrections are on offer and only one changes the answer. A product that
accepts every correction will confirm whatever the person already believed and
still sound certain doing it, which is worse than ignoring them, because it is
wrong in the direction nobody checks. The third correction — *"I feel completely
fine"* — is recorded, believed, and changes nothing: *"a reading above your
baseline while you feel well is a reading above your baseline while you feel
well."*

**The part that gets overturned was labelled a guess first.**
Every line of the basis carries `source`: measured, or inferred by Vybe. The
inferred line — alcohol on two evenings, matched from a heart-rate pattern with
nothing logged — is the one the night-shift correction overturns. The screen can
then say, as arithmetic rather than as a claim, that 2 of 4 parts moved and 1 of
them was something Vybe had already marked as a guess.

**Three outcomes, and which one is derived.**
`kindOf()` compares what moved against whether the answer text actually changed:
a correction that moves a basis item *and* changes the answer is `changes`; one
that closes a blind spot or shifts confidence is `narrows`; one that does
neither is `recorded`. A label typed into the data could read "this changed the
answer" above an answer identical to the one it replaced. Verified in node: one
correction of each kind, every effect naming a real basis id, every basis item
covered.

**No left-border accent, and no colour alone.**
The verdict is a word in its own fixed gutter — Held, Counts for less,
Overturned — and an overturned line is struck through as well. The same three
states survive being read aloud.

**The blind-spot list stays on the page.**
A correction can close one, and the closed item is struck through in place
rather than disappearing. A list that quietly shrinks is a list nobody can audit.

## The import screen, and why it looks like that

`OnboardingScreen` asks which sources you will connect. This is the screen
immediately after it, and the one nobody builds: the phone health store opens
and three years of somebody else's readings come out.

**The convenient thing is wrong in a way the person cannot see.**
Import all of it, draw one seamless chart back to 2023, compute a baseline from
the lot. But another product's sleep stages and HRV come from a different
sensor, sampled at different moments, through an algorithm nobody has published.
Build a baseline on those and every later sentence that says *"below your
baseline"* is quietly measuring Vybe against a competitor's guess.

**So history lands in three groups, and the rule sits above each one.**
*Compute with* — a clock reading or a direct measurement, comparable between
devices: sleep timing, resting heart rate, steps. *Show and never compute with*
— three years of sleep stages and 892 days of HRV, drawn for you and unusable.
*Not imported at all* — readiness scores from a formula nobody published,
eighteen hand-typed weights, one stray blood-pressure reading.

**The groups are consequential, not cosmetic.**
Six capabilities are listed with their state derived from the buckets and the
day counts: `statusFor()` returns `blocked` when an input sits outside the
compute-with group and names the record that blocked it, `waiting` with the
shortfall when an input is too short, `ready` otherwise. A capability can never
announce itself ready while its input is in the group Vybe refuses to compute
with. Verified in node: 1,120 usable days, 3 ready, 2 blocked by `shown`
records, 1 waiting on meal logs it has 0 days of.

**No health value appears anywhere on it.**
The sample module holds record counts and date spans — no heart rate, no sleep
duration, no score. A screen about what to do with a pile of history never needs
to show a reading, which removes the risk entirely rather than labelling it.

**The state is a word in its own column.**
Ready, Not from this, Waiting — never a colour alone, and the day counts use
tabular figures in a fixed right column so three years and eighteen days are
comparable at a glance.

## The year-on-year screen, and why it looks like that

The app had two history screens already. `MoveTrendScreen` draws one metric
across twenty-six weeks; `PatternHistoryScreen` tests one claim across twelve.
Both answer *what did this do*. Neither can answer the question that decides
whether any of it means anything: **is this a trend, or is it just November
again?**

**The tempting fix is the one that hides everything.**
Every wearable shows a decline through the winter and lets the person conclude
they are getting worse. Usually they are not; it is winter. A seasonal
adjustment would quietly lift the winter numbers and draw a flat line — and
destroy the only fact worth having. So this screen does the opposite: it reports
how many months it can actually compare, and refuses to draw a seasonal curve
through a single year.

**The headline is a limit, not an achievement.**
`7 of 12` — seven calendar months have a counterpart a year earlier, six of
those came out the same both times, one did not, and five months exist on
exactly one year. The months seen once are rows too, with a dash where the
second year should be. Dropping them would be the whole bug: a list of only the
comparable months reads as a complete year and is not one, and the months that
would go missing are exactly the winter ones people worry about.

**The screen checks its worst claim instead of asserting it.**
`worstAreThinnest` compares the five lowest readings against the five months
seen only once. They are the same five — January, December, February, November,
October — so the screen can say, as arithmetic, that the thinnest evidence and
the worst numbers are the same months. If a future dataset broke that, the
sentence changes rather than lying.

**A verdict that turns on one minute is noise wearing a conclusion's clothes.**
Two years count as the same month when they land within five minutes of each
other, and the rule is printed on screen. Six of the seven compared months
differ by a minute or less; without the margin, each of them would be a coin
flip. Verified in node: 19 readings, 12 calendar rows, 7 compared, 6 repeated,
1 changed — July, down 11 minutes, the month after a house move.

**It says when it becomes useful.**
February 2027 for a second pass through every month, February 2028 for a third:
*"a month that matches once is a pair, not a pattern."*

## The export screen, and why it looks like that

`DataSettingsScreen` offers "Export everything" and promises CSV for the
readings, JSON for the rest, and a delete that finishes within seven days. This
is the screen behind that tap, and its job is to keep that promise in detail
rather than quietly improve on it. Until today that button's handler was a
`TODO`.

**It is the import screen, backwards, and that is the point.**
On Wednesday Vybe refused to compute with another product's sleep stages and
HRV — somebody else's estimate, different sensor, unpublished algorithm. That
position only holds if it points both ways. So Vybe's own answers, pattern
verdicts and outcome records are listed here under a heading that says what
they are, and the manifest tells the next product to treat them exactly as Vybe
treated the last one's: *"read, not computed with."*

**The misses are in the file.**
The outcome records export with the predictions that failed, and the patterns
export with the weeks they broke. An export carrying only the successes would
be *"marketing with a filename."*

**The derived records are a rounding error by count and most of the value.**
458 conclusions against 1.19 million readings — the screen says that as
arithmetic rather than as a boast.

**A rounding bug the verification caught.**
Computing the portable share on its own rounds to `100%`, directly above a
caption reading "the remaining 0.04%" — a screen contradicting itself. The
portable share is now the complement of the derived share at the same
precision, so the two always sum to exactly 100: `99.96%` and `0.04%`. 99.96%
is also the more honest headline: virtually all, without claiming all.

**The format choice has consequences, and they are computed.**
CSV carries three of the six groups, JSON all six, PDF three — derived from
each group's own format list, so a format cannot claim to carry something the
group does not offer. Each one says what it is bad at: a PDF is *"a record, not
data"*; JSON is *"not readable by a person without tooling, and nobody should
pretend otherwise."*

**What Vybe keeps after a delete is on the screen, not in a policy page.**
Seven years of order records because tax law requires it, 30 days for backups
that roll on a cycle, 90 days of crash reports with no identifier in them —
each with the reason beside it.

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

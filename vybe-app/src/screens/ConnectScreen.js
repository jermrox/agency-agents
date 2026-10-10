import React, { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { colors, dimensions, radius, space, type } from '../theme';
import { connectWeek, isSample } from '../connectSampleData';
import EvidenceRow from '../components/EvidenceRow';
import LoadSources, {
  MIN_DAYS,
  confidenceFor,
  namedHoursOf,
  shareOf,
  unexplainedOf,
} from '../components/LoadSources';

const D = dimensions.connect;

/**
 * Connect — the dimension detail screen.
 *
 * Same spine as Restore and Nourish (answer, evidence, context, action,
 * restraint), because a reader who has seen one dimension screen should not
 * have to learn a second grammar. The middle is different because the question
 * is different.
 *
 * WHY THIS SCREEN IS NOT A LIST OF READINGS
 * The other four dimensions measure the body. Connect measures what happened
 * to it: the calendar, the time zones, the weather. So its claim is an
 * attribution — thirty-eight hours of elevated readings, and here is what each
 * of them is being blamed on — and attribution needs a form that shows
 * composition. Restore's hairline list of readings cannot show that one
 * quantity is made of four named parts. A single bar broken into those parts
 * can, so the middle of this screen is one bar over a ranked list.
 *
 * THE DECISION THAT MAKES THIS SCREEN
 * The hours nothing explains are drawn, ranked and given a block of their own.
 * Seven of thirty-eight hours have no cause beside them, and every product in
 * this category would have handed them to the busy week and shown a tidy pie.
 * A screen that can only produce complete explanations is a screen that
 * invents them.
 *
 * AND THE SECOND ONE: a source with too few comparable days says so instead of
 * reporting an effect. Two time-zone changes are the largest single thing that
 * happened this week and Vybe still refuses to tell you what travel does to
 * you, because two days is a story. The restraint is where the credibility is.
 *
 * NOTHING ON THIS SCREEN IS A STORED VERDICT. The named total, each share, the
 * remainder, the week-on-week difference and the count of sources Vybe will
 * not read are computed here from the sample module against the rules the
 * screen prints. A typed headline drifts away from the rows under it.
 *
 * Six treatments, so the hierarchy reads before the words: a tinted panel for
 * the answer, oversized type on bare paper for the hours, one composition bar
 * over a ranked list for the attribution, an outlined block for the part Vybe
 * cannot account for — the same treatment the Ask screen gives a refusal — a
 * hairline list for the body readings, and the one dark block for the action.
 */
export default function ConnectScreen({ onBack, onOpenOutcomes }) {
  const { sources, strainHours, usual, readings } = connectWeek;

  // Derived, never typed. The bar, the shares and these sentences all read
  // from the same two functions, so they cannot disagree with each other.
  const named = namedHoursOf(sources);
  const unexplained = unexplainedOf(sources, strainHours);
  const overUsual = strainHours - usual.strainHours;
  const overlapping = named > strainHours;

  // How much of the week Vybe will not interpret: the unexplained hours plus
  // the hours under sources with too few comparable days behind them.
  const thin = sources.filter((s) => confidenceFor(s) === 'thin');
  const thinHours = namedHoursOf(thin);

  const [selectedId, setSelectedId] = useState(sources[0].id);
  const selected = sources.find((s) => s.id === selectedId) || sources[0];
  const selectedMatched = confidenceFor(selected) === 'matched';

  return (
    <ScrollView
      style={styles.page}
      contentContainerStyle={styles.content}
      accessibilityLabel="Connect detail"
    >
      {isSample ? (
        <View style={styles.sampleBar}>
          <Text style={styles.sampleText}>Sample data — this is not your week.</Text>
        </View>
      ) : null}

      <View style={styles.header}>
        <Pressable
          onPress={onBack}
          accessibilityRole="button"
          accessibilityLabel="Back to today"
          accessibilityHint="Returns to the home screen"
          style={({ pressed }) => [styles.back, pressed && styles.pressed]}
        >
          <Text style={styles.backText}>Today</Text>
        </Pressable>
        <Text style={[styles.eyebrow, { color: D.hue }]}>CONNECT</Text>
        <Text style={styles.date}>{connectWeek.window}</Text>
      </View>

      {/* THE ANSWER — a sentence about the week. Not a load score. */}
      <View style={[styles.answerPanel, { backgroundColor: D.tint }]}>
        <Text style={styles.answer}>{connectWeek.answer}</Text>
        <Text style={[styles.confidence, { color: D.hue }]}>{connectWeek.confidence}</Text>
        <Text style={styles.confidenceWhy}>{connectWeek.confidenceWhy}</Text>
      </View>

      {/* THE FIGURE — bare paper, no panel. It is the one measured number on a
          screen otherwise built out of things that happened to you. */}
      <View style={styles.figureBlock}>
        <Text style={styles.figure} accessibilityRole="text">{strainHours}h</Text>
        <Text style={styles.figureCaption}>
          {'of this week your own readings ran above your own baseline'}
          {overUsual > 0
            ? ` — ${overUsual} hours more than ${usual.label}.`
            : overUsual < 0
              ? ` — ${Math.abs(overUsual)} hours fewer than ${usual.label}.`
              : ` — level with ${usual.label}.`}
        </Text>
      </View>

      {/* THE READOUT — what a tapped source says, in words. Opens on the
          largest one, so the section shows its own evidence before anybody
          taps anything. */}
      <View style={styles.readout}>
        <Text style={styles.readoutText}>
          {selected.label}: {selected.hours} hours,{' '}
          {shareOf(selected.hours, strainHours)}% of the week. {selected.detail}{' '}
          {selectedMatched
            ? `Across ${selected.comparedDays} days like these, ${selected.response.metric.toLowerCase()} ${selected.response.text}. ${selected.response.caveat}`
            : `Vybe has ${selected.comparedDays} ${selected.comparedDays === 1 ? 'day' : 'days'} like this, under the ${MIN_DAYS} it needs, so it will not tell you what this did to you.`}
        </Text>
      </View>

      {/* THE ATTRIBUTION */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Where those hours came from</Text>
        <Text style={styles.sectionLede}>
          {`Each hour is assigned to one source only, so the parts add up — a hot `}
          {`afternoon inside a travel day counts as travel. That flatters whichever `}
          {`source ranks first, and ${sources[0].label.toLowerCase()} ranks first.`}
        </Text>
        <LoadSources
          sources={sources}
          strainHours={strainHours}
          hue={D.hue}
          selectedId={selectedId}
          onSelect={setSelectedId}
        />
        <Text style={styles.plotNote}>
          {overlapping
            ? 'The named sources add up past the measured hours, which means they overlap. Treat the shares as approximate.'
            : `Named: ${named} of ${strainHours} hours. The bar is a second reading of the list — every name, hour and share above is also written out.`}
        </Text>
      </View>

      {/* WHAT VYBE CANNOT ACCOUNT FOR — the one outlined block, and the label
          says what the outline means so the treatment never carries it alone. */}
      <View style={styles.gapPanel}>
        <Text style={styles.gapLabel}>WHAT VYBE CANNOT ACCOUNT FOR</Text>
        <Text style={styles.gapText}>{connectWeek.unexplained}</Text>
        <Text style={styles.gapAside}>
          {`${unexplained} hours have no cause beside them, and another ${thinHours} `}
          {`sit under ${thin.length === 1 ? 'a source' : `${thin.length} sources`} with too few `}
          {`comparable days to read. That is ${shareOf(unexplained + thinHours, strainHours)}% of `}
          {'the week Vybe is holding open rather than explaining.'}
        </Text>
      </View>

      {/* WHAT YOUR BODY DID — by here the question is the ordinary one, so it
          gets the ordinary form, shared with Restore and Nourish. */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>What your body did about it</Text>
        <View>
          {readings.map((item, i) => (
            <EvidenceRow key={item.id} item={item} first={i === 0} />
          ))}
        </View>
        {/* The screen has just made a claim about what helps. The outcome
            record is where Vybe's claims get marked, and a reader who has been
            told "protect the night after you land" is owed the link to how
            often advice like that has actually worked. */}
        {onOpenOutcomes ? (
          <Pressable
            onPress={onOpenOutcomes}
            accessibilityRole="button"
            accessibilityLabel="See whether Vybe's suggestions have worked"
            accessibilityHint="Opens the record of past suggestions, including the ones that missed"
            style={({ pressed }) => [styles.outcomeLink, pressed && styles.pressed]}
          >
            <Text style={styles.outcomeLinkText}>
              See whether suggestions like this have worked
            </Text>
          </Pressable>
        ) : null}
      </View>

      {/* ACTION — one, and the only dark block on the screen. */}
      <View style={styles.actionPanel}>
        <Text style={styles.actionEyebrow}>NEXT TRIP</Text>
        <Text style={styles.actionText}>{connectWeek.action.text}</Text>
        <Text style={styles.actionWhy}>{connectWeek.action.why}</Text>
      </View>

      {/* What the screen refuses to do, which is as much of the product as what
          it does. */}
      <View style={styles.restraint}>
        <Text style={styles.restraintLabel}>What Connect is not</Text>
        <Text style={styles.restraintText}>{connectWeek.restraint}</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: colors.paper },
  content: { padding: space(3), paddingBottom: space(8), gap: space(4) },

  sampleBar: {
    backgroundColor: colors.brandSoft, borderRadius: radius.pill,
    paddingVertical: space(1), paddingHorizontal: space(2), alignSelf: 'flex-start',
  },
  sampleText: { ...type.small, color: colors.deep, fontWeight: '600' },

  header: { gap: space(0.5) },
  back: { alignSelf: 'flex-start', paddingVertical: space(0.5), paddingRight: space(2) },
  backText: { ...type.small, color: colors.brand, fontWeight: '600' },
  pressed: { opacity: 0.6 },
  eyebrow: { ...type.label, marginTop: space(1) },
  date: { ...type.display, color: colors.ink },

  answerPanel: { borderRadius: radius.card, padding: space(3), gap: space(1.5) },
  answer: { fontSize: 22, lineHeight: 31, color: colors.ink, fontWeight: '500' },
  confidence: { ...type.label },
  confidenceWhy: { ...type.small, color: colors.muted },

  figureBlock: { gap: space(0.5) },
  figure: {
    fontSize: 56, lineHeight: 60, fontWeight: '600', color: colors.ink,
    letterSpacing: -1, fontVariant: ['tabular-nums'],
  },
  // Held to a readable measure rather than the full width, like the Nourish
  // caption: this is a sentence, and a 44-character line beats a 70.
  figureCaption: { ...type.body, color: colors.muted, maxWidth: space(40) },

  readout: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    padding: space(2),
    minHeight: 76,
    justifyContent: 'center',
  },
  readoutText: { ...type.body, color: colors.ink, lineHeight: 23 },

  section: { gap: space(1) },
  sectionTitle: { ...type.title, color: colors.ink },
  sectionLede: { ...type.small, color: colors.muted, lineHeight: 19 },
  plotNote: { ...type.small, color: colors.faint, lineHeight: 20, paddingTop: space(0.75) },

  gapPanel: {
    borderWidth: 1,
    borderColor: colors.ink,
    borderRadius: radius.card,
    padding: space(3),
    gap: space(1.5),
  },
  gapLabel: { ...type.label, color: colors.ink },
  gapText: { ...type.body, color: colors.ink, lineHeight: 24 },
  gapAside: { ...type.small, color: colors.muted, lineHeight: 20 },

  outcomeLink: { alignSelf: 'flex-start', paddingVertical: space(1), marginTop: space(0.5) },
  outcomeLinkText: { ...type.body, color: colors.brand, fontWeight: '600' },

  actionPanel: { backgroundColor: colors.ink, borderRadius: radius.card, padding: space(3), gap: space(1) },
  actionEyebrow: { ...type.label, color: colors.brandSoft },
  actionText: { fontSize: 24, lineHeight: 32, color: colors.paper, fontWeight: '600' },
  actionWhy: { ...type.small, color: '#C9D2D8', lineHeight: 21 },

  restraint: {
    borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border,
    paddingTop: space(2), gap: space(0.5),
  },
  restraintLabel: { ...type.label, color: colors.brand },
  restraintText: { ...type.small, color: colors.muted, lineHeight: 20 },
});

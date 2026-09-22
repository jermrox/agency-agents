import React from 'react';
import { ScrollView, StatusBar, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native';
import AskBar from '../components/AskBar';
import DimensionCard from '../components/DimensionCard';
import InsightCard from '../components/InsightCard';
import { colors, space, type } from '../theme';
import { today } from '../sampleData';

/**
 * Vybe Home.
 *
 * Reading order is deliberate and matches the product thesis:
 *   1. the question you can ask          (the product's front door)
 *   2. what connected today              (the thing only Vybe can say)
 *   3. the five dimensions underneath    (the evidence, if you want it)
 *
 * A conventional wearable app inverts this — metrics first, meaning last.
 * Calm technology means the answer is at the top and the charts are optional.
 */
export default function HomeScreen({ onAsk, onOpenDimension, isSample = true }) {
  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="dark-content" backgroundColor={colors.paper} />
      <ScrollView
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <Text style={styles.date}>{today.dateLabel.toUpperCase()}</Text>
          <Text style={styles.greeting}>{today.greeting}</Text>
        </View>

        <AskBar onPress={onAsk} suggestion={today.suggestion} />

        <InsightCard
          headline={today.insight.headline}
          body={today.insight.body}
          dimensionsInvolved={today.insight.dimensionsInvolved}
        />

        <View style={styles.section}>
          <Text style={styles.sectionLabel}>TODAY, ACROSS FIVE DIMENSIONS</Text>
          <View style={styles.cards}>
            {today.cards.map((c) => (
              <DimensionCard
                key={c.dimension.key}
                dimension={c.dimension}
                status={c.status}
                detail={c.detail}
                onPress={() => onOpenDimension && onOpenDimension(c.dimension.key)}
              />
            ))}
          </View>
        </View>

        {isSample ? (
          <Text style={styles.sampleNote}>
            Sample data for layout. No real measurements are shown.
          </Text>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.paper },
  scroll: { padding: space(2.5), gap: space(2), paddingBottom: space(6) },
  header: { gap: space(0.5) },
  date: { ...type.label, color: colors.faint },
  greeting: { ...type.display, color: colors.ink },
  section: { gap: space(1.5) },
  sectionLabel: { ...type.label, color: colors.faint },
  cards: { gap: space(1.25) },
  sampleNote: {
    ...type.small,
    color: colors.faint,
    textAlign: 'center',
    paddingTop: space(1),
  },
});

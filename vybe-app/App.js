import React, { useState } from 'react';
import { SafeAreaView, StatusBar, StyleSheet } from 'react-native';
import HomeScreen from './src/screens/HomeScreen';
import RestoreScreen from './src/screens/RestoreScreen';
import MoveTrendScreen from './src/screens/MoveTrendScreen';
import NourishScreen from './src/screens/NourishScreen';
import ConnectScreen from './src/screens/ConnectScreen';
import AskScreen from './src/screens/AskScreen';
import FollowUpScreen from './src/screens/FollowUpScreen';
import PatternHistoryScreen from './src/screens/PatternHistoryScreen';
import SeasonScreen from './src/screens/SeasonScreen';
import OutcomeScreen from './src/screens/OutcomeScreen';
import OnboardingScreen from './src/screens/OnboardingScreen';
import ImportScreen from './src/screens/ImportScreen';
import DataSettingsScreen from './src/screens/DataSettingsScreen';
import { colors } from './src/theme';

/**
 * Vybe Health — entry point.
 *
 * One piece of state instead of a navigation library. There are twelve screens
 * now, and they are still a flat set: Nourish links across to the pattern
 * history, the pattern history links on to the year-on-year view, Restore and
 * Connect link across to the outcome record, Ask links across to the follow-up,
 * and onboarding links across to the history import — the one place a screen
 * returns to where it came from rather than to Home, which one remembered
 * string still covers. Pulling in
 * react-navigation would add a dependency, a gesture handler and a reanimated
 * peer to switch a string. Swap this the day a screen has to open on top of
 * another one and return to it.
 *
 * The app opens on onboarding, because that is what a fresh install does: the
 * Band is not paired and no source is connected. Both its exits land on Home,
 * and the first step's "Set up later" is one tap, so getting past it is cheap.
 * Persisting "already onboarded" needs storage this build does not have — swap
 * the initial state the day there is somewhere to remember it.
 */
export default function App() {
  const [screen, setScreen] = useState('onboarding');

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar barStyle="dark-content" backgroundColor={colors.paper} />
      {screen === 'onboarding' ? (
        <OnboardingScreen
          onFinish={() => setScreen('home')}
          onSkip={() => setScreen('home')}
          onImport={() => setScreen('import')}
        />
      ) : screen === 'import' ? (
        <ImportScreen
          onBack={() => setScreen('onboarding')}
          onContinue={() => setScreen('onboarding')}
        />
      ) : screen === 'restore' ? (
        <RestoreScreen
          onBack={() => setScreen('home')}
          onOpenOutcomes={() => setScreen('outcomes')}
        />
      ) : screen === 'move' ? (
        <MoveTrendScreen onBack={() => setScreen('home')} />
      ) : screen === 'nourish' ? (
        <NourishScreen
          onBack={() => setScreen('home')}
          onOpenHistory={() => setScreen('pattern')}
        />
      ) : screen === 'connect' ? (
        <ConnectScreen
          onBack={() => setScreen('home')}
          onOpenOutcomes={() => setScreen('outcomes')}
        />
      ) : screen === 'outcomes' ? (
        <OutcomeScreen onBack={() => setScreen('home')} />
      ) : screen === 'pattern' ? (
        <PatternHistoryScreen
          onBack={() => setScreen('home')}
          onOpenSeasons={() => setScreen('seasons')}
        />
      ) : screen === 'seasons' ? (
        <SeasonScreen onBack={() => setScreen('home')} />
      ) : screen === 'ask' ? (
        <AskScreen
          onBack={() => setScreen('home')}
          onFollowUp={() => setScreen('followup')}
        />
      ) : screen === 'followup' ? (
        <FollowUpScreen onBack={() => setScreen('home')} />
      ) : screen === 'data' ? (
        <DataSettingsScreen onBack={() => setScreen('home')} />
      ) : (
        <HomeScreen
          isSample
          onOpenData={() => setScreen('data')}
          onAsk={() => setScreen('ask')}
          onOpenDimension={(key) => {
            // Four of the five dimensions have detail screens now; Vitals
            // falls through rather than opening an empty shell.
            if (key === 'restore') setScreen('restore');
            if (key === 'move') setScreen('move');
            if (key === 'nourish') setScreen('nourish');
            if (key === 'connect') setScreen('connect');
          }}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.paper },
});

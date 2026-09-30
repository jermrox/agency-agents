import React, { useState } from 'react';
import { SafeAreaView, StatusBar, StyleSheet } from 'react-native';
import HomeScreen from './src/screens/HomeScreen';
import RestoreScreen from './src/screens/RestoreScreen';
import MoveTrendScreen from './src/screens/MoveTrendScreen';
import NourishScreen from './src/screens/NourishScreen';
import AskScreen from './src/screens/AskScreen';
import OnboardingScreen from './src/screens/OnboardingScreen';
import DataSettingsScreen from './src/screens/DataSettingsScreen';
import { colors } from './src/theme';

/**
 * Vybe Health — entry point.
 *
 * One piece of state instead of a navigation library. There are six screens
 * now, but they are still a flat set: every detail screen returns to Home and
 * nothing stacks, so there is no back stack for a router to manage. Pulling in
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
        />
      ) : screen === 'restore' ? (
        <RestoreScreen onBack={() => setScreen('home')} />
      ) : screen === 'move' ? (
        <MoveTrendScreen onBack={() => setScreen('home')} />
      ) : screen === 'nourish' ? (
        <NourishScreen onBack={() => setScreen('home')} />
      ) : screen === 'ask' ? (
        <AskScreen onBack={() => setScreen('home')} />
      ) : screen === 'data' ? (
        <DataSettingsScreen onBack={() => setScreen('home')} />
      ) : (
        <HomeScreen
          isSample
          onOpenData={() => setScreen('data')}
          onAsk={() => setScreen('ask')}
          onOpenDimension={(key) => {
            // Restore, Move and Nourish have detail screens; Connect and Vitals
            // fall through rather than opening an empty shell.
            if (key === 'restore') setScreen('restore');
            if (key === 'move') setScreen('move');
            if (key === 'nourish') setScreen('nourish');
          }}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.paper },
});

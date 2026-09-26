import React, { useState } from 'react';
import { SafeAreaView, StatusBar, StyleSheet } from 'react-native';
import HomeScreen from './src/screens/HomeScreen';
import RestoreScreen from './src/screens/RestoreScreen';
import MoveTrendScreen from './src/screens/MoveTrendScreen';
import DataSettingsScreen from './src/screens/DataSettingsScreen';
import { colors } from './src/theme';

/**
 * Vybe Health — entry point.
 *
 * One piece of state instead of a navigation library. There are three screens
 * now, but they are still a flat set: every detail screen returns to Home and
 * nothing stacks, so there is no back stack for a router to manage. Pulling in
 * react-navigation would add a dependency, a gesture handler and a reanimated
 * peer to switch a string. Swap this the day a screen has to open on top of
 * another one and return to it.
 */
export default function App() {
  const [screen, setScreen] = useState('home');

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar barStyle="dark-content" backgroundColor={colors.paper} />
      {screen === 'restore' ? (
        <RestoreScreen onBack={() => setScreen('home')} />
      ) : screen === 'move' ? (
        <MoveTrendScreen onBack={() => setScreen('home')} />
      ) : screen === 'data' ? (
        <DataSettingsScreen onBack={() => setScreen('home')} />
      ) : (
        <HomeScreen
          isSample
          onOpenData={() => setScreen('data')}
          onAsk={() => {
            // TODO: the conversation screen.
          }}
          onOpenDimension={(key) => {
            // Restore and Move have detail screens; the rest fall through
            // rather than opening an empty shell.
            if (key === 'restore') setScreen('restore');
            if (key === 'move') setScreen('move');
          }}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.paper },
});

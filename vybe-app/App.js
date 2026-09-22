import React, { useState } from 'react';
import { SafeAreaView, StatusBar, StyleSheet } from 'react-native';
import HomeScreen from './src/screens/HomeScreen';
import RestoreScreen from './src/screens/RestoreScreen';
import { colors } from './src/theme';

/**
 * Vybe Health — entry point.
 *
 * One piece of state instead of a navigation library. The app has two screens;
 * pulling in react-navigation to switch between two screens would add a
 * dependency, a gesture handler and a reanimated peer before the product has
 * decided what its navigation model even is. Swap this for a router the day a
 * third screen needs a back stack.
 */
export default function App() {
  const [screen, setScreen] = useState('home');

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar barStyle="dark-content" backgroundColor={colors.paper} />
      {screen === 'restore' ? (
        <RestoreScreen onBack={() => setScreen('home')} />
      ) : (
        <HomeScreen
          isSample
          onAsk={() => {
            // TODO: the conversation screen.
          }}
          onOpenDimension={(key) => {
            // Only Restore has a detail screen so far; the others fall through
            // rather than opening an empty shell.
            if (key === 'restore') setScreen('restore');
          }}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.paper },
});

/**
 * Vybe Health — design tokens.
 *
 * One source of truth for colour and type. Every component reads from here,
 * so a brand change is one edit rather than a search across screens.
 *
 * Every value below is sampled from the brand assets, not invented: the V is
 * a deep charcoal-navy, the waveform through it is mint, and the five hues are
 * read off the Vybe Intelligence artwork (Restore periwinkle, Connect rose).
 *
 * The five dimension hues are the product's own language, not decoration:
 * a colour always appears next to the dimension's name, never alone, so the
 * screen stays readable for anyone who cannot separate these hues.
 */

export const colors = {
  ink: '#161C22',
  paper: '#FBF9F5',
  surface: '#FFFFFF',
  border: '#DFDBD1',
  muted: '#4E5960',
  faint: '#889298',
  brand: '#1F8E78',
  brandSoft: '#A8DCC8',
  brandBright: '#3FBFA0',
  deep: '#12292B',
};

export const dimensions = {
  restore: { key: 'restore', label: 'Restore', hue: '#4B4BAE', tint: '#EDEDF8' },
  move:    { key: 'move',    label: 'Move',    hue: '#C25A3C', tint: '#FBEDE7' },
  nourish: { key: 'nourish', label: 'Nourish', hue: '#5A8040', tint: '#EFF4E9' },
  connect: { key: 'connect', label: 'Connect', hue: '#96476A', tint: '#F8EBF1' },
  vitals:  { key: 'vitals',  label: 'Vitals',  hue: '#A83848', tint: '#F9E9EB' },
};

export const order = ['restore', 'move', 'nourish', 'connect', 'vitals'];

export const type = {
  display: { fontSize: 34, fontWeight: '600', letterSpacing: -0.4 },
  title:   { fontSize: 22, fontWeight: '600' },
  body:    { fontSize: 16, lineHeight: 23 },
  label:   { fontSize: 12, fontWeight: '600', letterSpacing: 1.4 },
  small:   { fontSize: 13, lineHeight: 19 },
};

export const space = (n) => n * 8;

export const radius = { card: 18, pill: 999 };

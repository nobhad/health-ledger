/**
 * PostCSS build for static/css/health-ledger.css -> static/css/dist/health-ledger.css
 *
 * postcss-import inlines the @import chain (keeping each sheet's layer()),
 * postcss-custom-media resolves the @custom-media breakpoints the vendored
 * design system defines, and autoprefixer adds vendor prefixes.
 * postcss-discard-comments strips every comment: the bundle is what ships
 * inside the downloadable apps and what any browser's devtools show, and the
 * source comments are developer notes that point at internal documents.
 * Nothing else is transformed: what ships is the source files, flattened.
 */
module.exports = {
  plugins: {
    'postcss-import': {},
    'postcss-custom-media': {},
    autoprefixer: {},
    'postcss-discard-comments': { removeAll: true },
  },
};

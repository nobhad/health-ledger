/**
 * PostCSS build for static/css/health-ledger.css -> static/css/dist/health-ledger.css
 *
 * postcss-import inlines the @import chain (keeping each sheet's layer()),
 * postcss-custom-media resolves the @custom-media breakpoints the vendored
 * design system defines, and autoprefixer adds vendor prefixes. There is no
 * other transform: what ships is the source files, flattened.
 */
module.exports = {
  plugins: {
    'postcss-import': {},
    'postcss-custom-media': {},
    autoprefixer: {},
  },
};

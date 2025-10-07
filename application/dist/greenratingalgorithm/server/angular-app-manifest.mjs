
export default {
  bootstrap: () => import('./main.server.mjs').then(m => m.default),
  inlineCriticalCss: true,
  baseHref: '/',
  locale: undefined,
  routes: [
  {
    "renderMode": 2,
    "route": "/"
  },
  {
    "renderMode": 2,
    "route": "/cattura"
  }
],
  entryPointToBrowserMapping: undefined,
  assets: {
    'index.csr.html': {size: 24674, hash: '6b99bd69eafd3e75bf14c132bf894be791edca605c65fed8ad99a042aff858f0', text: () => import('./assets-chunks/index_csr_html.mjs').then(m => m.default)},
    'index.server.html': {size: 17117, hash: 'a18f78b8af3c1ca6b2e8a52d3ad2df7d879cbfb17d1e12a8698269b38a1d4beb', text: () => import('./assets-chunks/index_server_html.mjs').then(m => m.default)},
    'index.html': {size: 63613, hash: 'b08381926d728bae725a5de6f8ae294f6a37c191d292392c00604b5280cf07e1', text: () => import('./assets-chunks/index_html.mjs').then(m => m.default)},
    'cattura/index.html': {size: 37672, hash: 'da0a04386ee759d6fa895cbe41d7d5e384c63369213c7d531709fd7e690a5d15', text: () => import('./assets-chunks/cattura_index_html.mjs').then(m => m.default)},
    'styles-HRWATBXE.css': {size: 19181, hash: 'tRCtaFrkaqk', text: () => import('./assets-chunks/styles-HRWATBXE_css.mjs').then(m => m.default)}
  },
};

// There is no bundling step; this just verifies the files the app loads exist.
const fs = require('fs');
const path = require('path');
for (const f of ['src/main/main.js', 'src/main/menu.js', 'src/renderer/index.html', 'src/renderer/clock.js', 'src/renderer/themes.css']) {
  if (!fs.existsSync(path.join(__dirname, '..', f))) {
    console.error('Missing ' + f);
    process.exit(1);
  }
}
console.log('ok');

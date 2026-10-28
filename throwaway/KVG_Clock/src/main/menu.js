const { app, Menu, shell } = require('electron');

const REPO_URL = 'https://github.com/gerp93/KVG_Clock';

function isSafeExternalUrl(url) {
  try {
    const { protocol } = new URL(url);
    return protocol === 'https:' || protocol === 'http:';
  } catch {
    return false;
  }
}

function openExternal(url) {
  if (isSafeExternalUrl(url)) shell.openExternal(url);
}

function setupApplicationMenu() {
  const isMac = process.platform === 'darwin';
  const devItems = app.isPackaged
    ? []
    : [{ role: 'reload' }, { role: 'forceReload' }, { role: 'toggleDevTools' }, { type: 'separator' }];

  const template = [
    ...(isMac
      ? [{
          label: app.name,
          submenu: [
            { role: 'about' },
            { type: 'separator' },
            { role: 'services' },
            { type: 'separator' },
            { role: 'hide' },
            { role: 'hideOthers' },
            { role: 'unhide' },
            { type: 'separator' },
            { role: 'quit' },
          ],
        }]
      : []),
    {
      label: 'View',
      submenu: [
        ...devItems,
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomIn', accelerator: 'CmdOrCtrl+Shift+=', visible: false },
        { role: 'zoomIn', accelerator: 'CmdOrCtrl+numadd', visible: false },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
      ],
    },
    {
      label: 'Help',
      submenu: [
        { label: 'KVG Clock on GitHub', click: () => openExternal(REPO_URL) },
        { label: 'Report an Issue', click: () => openExternal(`${REPO_URL}/issues`) },
        { type: 'separator' },
        { label: `Version ${app.getVersion()}`, enabled: false },
      ],
    },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

// Edit menu is dropped, so keep cut/copy/paste/select-all reachable by right-click.
function attachContextMenu(win) {
  win.webContents.on('context-menu', (_event, params) => {
    const { editFlags } = params;
    const items = [];
    if (params.isEditable && editFlags.canCut) items.push({ role: 'cut' });
    if (editFlags.canCopy) items.push({ role: 'copy' });
    if (params.isEditable && editFlags.canPaste) items.push({ role: 'paste' });
    if (editFlags.canSelectAll && params.isEditable) items.push({ role: 'selectAll' });
    if (items.length) Menu.buildFromTemplate(items).popup({ window: win });
  });
}

module.exports = { setupApplicationMenu, attachContextMenu, isSafeExternalUrl };

async page => {
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto('http://127.0.0.1:5175/?character=scorpio-05');
  await page.waitForFunction(() => window.atlas?.stats.character === 'scorpio-05');
  const inventory = await page.evaluate(() => atlas.stats);
  if (inventory.clips.length !== 6) throw Error('Incorrect Scorpio clips: ' + inventory.clips.length);
  const poses = [
    ['IDLE', 'Sentinel', 0],
    ['STINGER STRIKE', 'StingerStrike', 2.12],
    ['PINCER STRIKE', 'ClawSlash', 1.04],
    ['RUN', 'Run', 0.35],
    ['KNEEL & FIRE', 'KneelFire', 3.1],
    ['BACKFLIP', 'Backflip', 1.8]
  ];
  const reports = [];
  for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
    await page.setViewportSize(viewport);
    for (const [label, clip, time] of poses) {
      await page.getByRole('button', { name: label, exact: true }).click();
      await page.getByRole('button', { name: 'Pause animation', exact: true }).click();
      await page.evaluate(t => atlas.mixer.setTime(t), time);
      await page.screenshot({ path: `output/playwright/scorpio-${viewport.width}-${clip}.png` });
      reports.push(await page.evaluate(() => ({
        clip: atlas.stats.activeClip,
        width: innerWidth,
        overflow: document.documentElement.scrollWidth > innerWidth,
        drawCalls: atlas.renderer.info.render.calls,
        modelDownload: document.querySelector('.download').href
      })));
    }
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  for (const [label, id, count] of [
    ['ATLAS / 09', 'atlas-09', 7],
    ['AETHER / 02', 'aether-02', 7],
    ['SERAPH / 03', 'seraph-03', 6],
    ['RONIN / 04', 'ronin-04', 6],
    ['SCORPIO / 05', 'scorpio-05', 6]
  ]) {
    await page.getByRole('button', { name: label, exact: true }).click();
    await page.waitForFunction(id => atlas.stats.character === id, id);
    if (await page.locator('[data-clip]').count() !== count) throw Error('Incorrect buttons after swap to ' + id);
  }
  await page.getByRole('button', { name: 'STINGER STRIKE', exact: true }).click();
  const before = await page.evaluate(() => atlas.mixer.time);
  await page.evaluate(() => new Promise(resolve => {
    let n = 15;
    function next() {
      if (--n === 0) resolve();
      else requestAnimationFrame(next);
    }
    requestAnimationFrame(next);
  }));
  const after = await page.evaluate(() => atlas.mixer.time);
  if (after <= before) throw Error('Playback failed');
  if (errors.length || reports.some(r => r.overflow)) throw Error(JSON.stringify({ errors, reports }));
  return { inventory, reports, playbackAdvanced: after > before, errors };
}

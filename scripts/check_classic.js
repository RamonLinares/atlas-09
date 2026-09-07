// Playwright routine (same style as check_scorpio.js): run inside a Playwright
// page context against `npm run dev` on port 5175. Verifies both classic frames.
async page => {
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  const frames = {
    'titan-06': { clips: 6, poses: [['IDLE', 'Sentinel', 0], ['ROCKET PUNCH', 'RocketPunch', 1.45], ['CHEST BEAM', 'ChestBeam', 2.0], ['RUN', 'Run', 0.35], ['KNEEL & FIRE', 'KneelFire', 3.1], ['BACKFLIP', 'Backflip', 1.8]] },
    'vanguard-07': { clips: 7, poses: [['IDLE', 'Sentinel', 0], ['RIFLE BURST', 'RifleBurst', 1.25], ['SHIELD GUARD', 'ShieldGuard', 1.5], ['BOOST JUMP', 'BoostJump', 1.6], ['RUN', 'Run', 0.35], ['KNEEL & FIRE', 'KneelFire', 3.1], ['BACKFLIP', 'Backflip', 1.8]] },
  };
  const reports = [];
  for (const [id, { clips, poses }] of Object.entries(frames)) {
    await page.goto(`http://127.0.0.1:5175/?character=${id}`);
    await page.waitForFunction(id => window.atlas?.stats.character === id, id);
    const inventory = await page.evaluate(() => atlas.stats);
    if (inventory.clips.length !== clips) throw Error(`Incorrect ${id} clips: ${inventory.clips.length}`);
    for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
      await page.setViewportSize(viewport);
      for (const [label, clip, time] of poses) {
        await page.getByRole('button', { name: label, exact: true }).click();
        await page.getByRole('button', { name: 'Pause animation', exact: true }).click();
        await page.evaluate(t => atlas.mixer.setTime(t), time);
        await page.screenshot({ path: `output/playwright/${id}-${viewport.width}-${clip}.png` });
        reports.push(await page.evaluate(() => ({ character: atlas.stats.character, clip: atlas.stats.activeClip, width: innerWidth, fx: atlas.stats.motionFX, overflow: document.documentElement.scrollWidth > innerWidth })));
      }
    }
  }
  const fx = reports.filter(r => ['RocketPunch', 'ChestBeam', 'BoostJump'].includes(r.clip));
  if (!fx.every(r => r.fx.flame || r.fx.beam)) throw Error('Missing beam or flame effect: ' + JSON.stringify(fx));
  if (errors.length || reports.some(r => r.overflow)) throw Error(JSON.stringify({ errors, reports }));
  return { reports, errors };
}

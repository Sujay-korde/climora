import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import { injectVirtualCursor, moveCursorSmooth, clickWithRipple, processRecordedVideo } from './capture_scene_01.mjs';

const VIEWPORT = { width: 2560, height: 1440 };

// -------------------------------------------------------------
// SCENE 05: /explore/pune (Geospatial Explorer)
// -------------------------------------------------------------
async function recordScene05() {
  console.log('>>> RECORDING SCENE 05: /explore/pune');
  const events = [];
  const startTime = Date.now();
  const logEvent = (name, details = {}) => {
    events.push({ time_ms: Date.now() - startTime, name, ...details });
  };

  const tempDir = path.resolve('capture/temp_05');
  fs.mkdirSync(tempDir, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: VIEWPORT,
    recordVideo: { dir: tempDir, size: VIEWPORT }
  });

  const page = await context.newPage();
  const curX = { val: 1280 };
  const curY = { val: 720 };

  logEvent('navigate_start', { url: 'http://127.0.0.1:3000/explore/pune' });
  await page.goto('http://127.0.0.1:3000/explore/pune', { waitUntil: 'networkidle' });
  await injectVirtualCursor(page);
  await page.waitForTimeout(2000); // let map tiles settle
  logEvent('map_initialized');

  // Hover over the Thermal Legend in bottom left
  await moveCursorSmooth(page, 140, 1380, 800, curX, curY);
  logEvent('hover_thermal_legend');
  await page.waitForTimeout(1000);

  // Switch to Exposure layer
  // The MapControls has buttons or we can click layer toggles
  const buttons = await page.locator('button').all();
  for (const b of buttons) {
    const text = await b.innerText();
    if (text.includes('Exposure') || text.includes('WorldPop')) {
      const box = await b.boundingBox();
      if (box) {
        await moveCursorSmooth(page, box.x + box.width / 2, box.y + box.height / 2, 600, curX, curY);
        await clickWithRipple(page, curX, curY);
        logEvent('layer_toggle_exposure');
        await page.waitForTimeout(1200);
        break;
      }
    }
  }

  // Switch to Climate Risk layer
  for (const b of buttons) {
    const text = await b.innerText();
    if (text.includes('Risk') || text.includes('H × E × V')) {
      const box = await b.boundingBox();
      if (box) {
        await moveCursorSmooth(page, box.x + box.width / 2, box.y + box.height / 2, 600, curX, curY);
        await clickWithRipple(page, curX, curY);
        logEvent('layer_toggle_risk');
        await page.waitForTimeout(1200);
        break;
      }
    }
  }

  // Glide cursor to center-north cluster of Pune (priority hotspot) and click
  // Target coordinates in Pune center: around x=1240, y=680
  await moveCursorSmooth(page, 1260, 680, 1000, curX, curY);
  logEvent('click_priority_cell', { target_cell: '89608850003ffff' });
  await clickWithRipple(page, curX, curY);
  await page.waitForTimeout(1500);

  // Inspect the right panel / bottom sheet
  await moveCursorSmooth(page, 2200, 350, 700, curX, curY);
  logEvent('inspect_cell_metrics', { lst_degc: 47.06, population: 4757, planned_trees: 76 });
  await page.waitForTimeout(2000);

  await page.close();
  await context.close();
  await browser.close();

  const files = fs.readdirSync(tempDir).filter(f => f.endsWith('.webm'));
  if (files.length > 0) {
    const rawVideo = path.join(tempDir, files[0]);
    const targetMp4 = 'capture/scene_05.mp4';
    processRecordedVideo(rawVideo, targetMp4, 'scene_05');
    fs.writeFileSync('capture/scene_05.events.json', JSON.stringify({ scene: 'scene_05', duration_ms: Date.now() - startTime, events }, null, 2));
    console.log(`Scene 05 saved: ${targetMp4}`);
  }
}

// -------------------------------------------------------------
// SCENE 06: /optimizer (Portfolio Optimizer)
// -------------------------------------------------------------
async function recordScene06() {
  console.log('>>> RECORDING SCENE 06: /optimizer');
  const events = [];
  const startTime = Date.now();
  const logEvent = (name, details = {}) => {
    events.push({ time_ms: Date.now() - startTime, name, ...details });
  };

  const tempDir = path.resolve('capture/temp_06');
  fs.mkdirSync(tempDir, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: VIEWPORT,
    recordVideo: { dir: tempDir, size: VIEWPORT }
  });

  const page = await context.newPage();
  const curX = { val: 1280 };
  const curY = { val: 720 };

  logEvent('navigate_start', { url: 'http://127.0.0.1:3000/optimizer' });
  await page.goto('http://127.0.0.1:3000/optimizer', { waitUntil: 'networkidle' });
  await injectVirtualCursor(page);
  await page.waitForTimeout(1500);

  // Hover over the formulation badge
  await moveCursorSmooth(page, 450, 180, 700, curX, curY);
  logEvent('hover_formulation_badge', { formulation: 'F-24.6 HIGHS MILP' });
  await page.waitForTimeout(1000);

  // Hover over presets
  const presetButtons = await page.locator('button').all();
  let btn1Cr = null;
  let btnExec = null;

  for (const b of presetButtons) {
    const text = await b.innerText();
    if (text.includes('1 Crore') || text.includes('Benchmark') || text.includes('100.0L')) {
      btn1Cr = b;
    }
    if (text.includes('Execute HiGHS') || text.includes('Optimization')) {
      btnExec = b;
    }
  }

  if (btn1Cr) {
    const box = await btn1Cr.boundingBox();
    if (box) {
      await moveCursorSmooth(page, box.x + box.width / 2, box.y + box.height / 2, 800, curX, curY);
      await clickWithRipple(page, curX, curY);
      logEvent('select_budget_preset', { budget: '₹1 Crore (Benchmark)' });
      await page.waitForTimeout(1500);
    }
  }

  if (btnExec) {
    const box = await btnExec.boundingBox();
    if (box) {
      await moveCursorSmooth(page, box.x + box.width / 2, box.y + box.height / 2, 700, curX, curY);
      await clickWithRipple(page, curX, curY);
      logEvent('execute_highs_solver', { solver: 'HiGHS (scipy.optimize.milp)' });
      await page.waitForTimeout(2000);
    }
  }

  // Scroll down to inspect the resulting metrics
  await page.evaluate(() => window.scrollBy({ top: 380, behavior: 'smooth' }));
  logEvent('scroll_to_results');
  await page.waitForTimeout(1000);

  // Hover over the summary results: 28 cells, ₹9.99M, 2,695 trees
  await moveCursorSmooth(page, 620, 520, 700, curX, curY);
  logEvent('highlight_result_cells', { cells_count: 28, pct_of_city: '0.88%' });
  await page.waitForTimeout(800);

  await moveCursorSmooth(page, 1050, 520, 600, curX, curY);
  logEvent('highlight_result_trees', { planned_trees: 2695 });
  await page.waitForTimeout(800);

  await moveCursorSmooth(page, 1480, 520, 600, curX, curY);
  logEvent('highlight_result_citizens', { citizens_protected: 118941 });
  await page.waitForTimeout(1500);

  await page.close();
  await context.close();
  await browser.close();

  const files = fs.readdirSync(tempDir).filter(f => f.endsWith('.webm'));
  if (files.length > 0) {
    const rawVideo = path.join(tempDir, files[0]);
    const targetMp4 = 'capture/scene_06.mp4';
    processRecordedVideo(rawVideo, targetMp4, 'scene_06');
    fs.writeFileSync('capture/scene_06.events.json', JSON.stringify({ scene: 'scene_06', duration_ms: Date.now() - startTime, events }, null, 2));
    console.log(`Scene 06 saved: ${targetMp4}`);
  }
}

// -------------------------------------------------------------
// SCENE 07: /projects/canonical (Cedar Governance & Provenance)
// -------------------------------------------------------------
async function recordScene07() {
  console.log('>>> RECORDING SCENE 07: Cedar Governance');
  const events = [];
  const startTime = Date.now();
  const logEvent = (name, details = {}) => {
    events.push({ time_ms: Date.now() - startTime, name, ...details });
  };

  const tempDir = path.resolve('capture/temp_07');
  fs.mkdirSync(tempDir, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: VIEWPORT,
    recordVideo: { dir: tempDir, size: VIEWPORT }
  });

  const page = await context.newPage();
  const curX = { val: 1280 };
  const curY = { val: 720 };

  // Navigate via home page link to trigger client-side React router cleanly
  await page.goto('http://127.0.0.1:3000/', { waitUntil: 'networkidle' });
  await injectVirtualCursor(page);
  await page.waitForTimeout(1000);

  logEvent('click_nav_project');
  await page.click('text="View project"');
  await page.waitForTimeout(1500);

  // Inspect the Cedar Governance Persona Selector at the top
  await moveCursorSmooth(page, 650, 190, 800, curX, curY);
  logEvent('hover_cedar_persona_banner');
  await page.waitForTimeout(1000);

  // Click Dr. Rajesh Patil (Commissioner)
  const commissionerRadio = page.locator('text="Dr. Rajesh Patil"');
  if (await commissionerRadio.count() > 0) {
    const box = await commissionerRadio.first().boundingBox();
    if (box) {
      await moveCursorSmooth(page, box.x + 20, box.y + 10, 600, curX, curY);
      await clickWithRipple(page, curX, curY);
      logEvent('select_actor_commissioner', { actor_id: 'pmc_commissioner' });
      await page.waitForTimeout(1500);
    }
  }

  // Scroll down to project action buttons
  await page.evaluate(() => window.scrollBy({ top: 350, behavior: 'smooth' }));
  logEvent('scroll_project_actions');
  await page.waitForTimeout(1000);

  // Click Generate Tender Brief if available
  const tenderBtn = page.locator('button:has-text("Brief"), button:has-text("Tender"), button:has-text("Dossier")');
  if (await tenderBtn.count() > 0) {
    const box = await tenderBtn.first().boundingBox();
    if (box) {
      await moveCursorSmooth(page, box.x + box.width / 2, box.y + box.height / 2, 700, curX, curY);
      await clickWithRipple(page, curX, curY);
      logEvent('open_tender_brief_modal');
      await page.waitForTimeout(2000);
    }
  }

  // Hover over SHA-256 provenance hash
  await moveCursorSmooth(page, 1280, 650, 700, curX, curY);
  logEvent('highlight_sha256_provenance', { hash_prefix: 'BA225D6A' });
  await page.waitForTimeout(2000);

  await page.close();
  await context.close();
  await browser.close();

  const files = fs.readdirSync(tempDir).filter(f => f.endsWith('.webm'));
  if (files.length > 0) {
    const rawVideo = path.join(tempDir, files[0]);
    const targetMp4 = 'capture/scene_07.mp4';
    processRecordedVideo(rawVideo, targetMp4, 'scene_07');
    fs.writeFileSync('capture/scene_07.events.json', JSON.stringify({ scene: 'scene_07', duration_ms: Date.now() - startTime, events }, null, 2));
    console.log(`Scene 07 saved: ${targetMp4}`);
  }
}

// -------------------------------------------------------------
// SCENE 08: /mrv (Empirical Evidence & Tripartite Framework)
// -------------------------------------------------------------
async function recordScene08() {
  console.log('>>> RECORDING SCENE 08: MRV & Impact');
  const events = [];
  const startTime = Date.now();
  const logEvent = (name, details = {}) => {
    events.push({ time_ms: Date.now() - startTime, name, ...details });
  };

  const tempDir = path.resolve('capture/temp_08');
  fs.mkdirSync(tempDir, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: VIEWPORT,
    recordVideo: { dir: tempDir, size: VIEWPORT }
  });

  const page = await context.newPage();
  const curX = { val: 1280 };
  const curY = { val: 720 };

  logEvent('navigate_start', { url: 'http://127.0.0.1:3000/mrv' });
  await page.goto('http://127.0.0.1:3000/mrv', { waitUntil: 'networkidle' });
  await injectVirtualCursor(page);
  await page.waitForTimeout(1500);

  // Hover over the Tripartite Separation header
  await moveCursorSmooth(page, 480, 200, 700, curX, curY);
  logEvent('hover_tripartite_header', { status: 'Pending Post-Deployment Observation' });
  await page.waitForTimeout(1200);

  // Scroll down to the status cards
  await page.evaluate(() => window.scrollBy({ top: 380, behavior: 'smooth' }));
  logEvent('scroll_to_did_status');
  await page.waitForTimeout(1200);

  // Hover over PREDICTED, OBSERVED, VERIFIED cards
  await moveCursorSmooth(page, 600, 520, 600, curX, curY);
  logEvent('hover_predicted_card', { quantity: '2,695 trees' });
  await page.waitForTimeout(800);

  await moveCursorSmooth(page, 1050, 520, 600, curX, curY);
  logEvent('hover_observed_card', { status: 'Satellite Scheduled' });
  await page.waitForTimeout(800);

  await moveCursorSmooth(page, 1500, 520, 600, curX, curY);
  logEvent('hover_verified_card', { status: 'NOT_STARTED (Honest Limit)' });
  await page.waitForTimeout(1500);

  // Scroll down to Detectability limits & scientific foundation
  await page.evaluate(() => window.scrollBy({ top: 400, behavior: 'smooth' }));
  logEvent('scroll_to_detectability_limits');
  await page.waitForTimeout(1500);

  await moveCursorSmooth(page, 750, 650, 800, curX, curY);
  logEvent('highlight_mde_limits', { single_cell_mde: '6.91°C', cluster_threshold: '2 cells' });
  await page.waitForTimeout(2000);

  await page.close();
  await context.close();
  await browser.close();

  const files = fs.readdirSync(tempDir).filter(f => f.endsWith('.webm'));
  if (files.length > 0) {
    const rawVideo = path.join(tempDir, files[0]);
    const targetMp4 = 'capture/scene_08.mp4';
    processRecordedVideo(rawVideo, targetMp4, 'scene_08');
    fs.writeFileSync('capture/scene_08.events.json', JSON.stringify({ scene: 'scene_08', duration_ms: Date.now() - startTime, events }, null, 2));
    console.log(`Scene 08 saved: ${targetMp4}`);
  }
}

async function main() {
  await recordScene05();
  await recordScene06();
  await recordScene07();
  await recordScene08();
  console.log('>>> ALL UI SCENES RECORDED SUCCESSFULLY!');
}

main().catch(console.error);


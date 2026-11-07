import { chromium } from 'playwright';
import fs from 'fs';

async function runRecon() {
  const results = {
    timestamp: new Date().toISOString(),
    pages: {},
    console_errors: []
  };

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 2560, height: 1440 },
    deviceScaleFactor: 1
  });
  const page = await context.newPage();

  page.on('console', msg => {
    if (msg.type() === 'error') results.console_errors.push(msg.text());
  });

  // 1. Overview Page
  let t0 = Date.now();
  await page.goto('http://127.0.0.1:3000/', { waitUntil: 'networkidle' });
  const loadOverview = (Date.now() - t0) / 1000;
  await page.waitForTimeout(1000);
  const overviewBody = await page.locator('body').innerText();
  
  results.pages.overview = {
    load_time_s: loadOverview,
    url: page.url(),
    title: await page.title(),
    has_hero: overviewBody.includes('Turning planetary observations into fundable urban interventions'),
    metric_baseline: overviewBody.includes('46.36°C') ? '46.36°C' : 'N/A',
    metric_cells: overviewBody.includes('28 H3 cells') ? '28 H3 cells' : 'N/A',
    metric_trees: overviewBody.includes('2,695 trees') ? '2,695 trees' : 'N/A',
    metric_cost: overviewBody.includes('₹9.99M') || overviewBody.includes('₹10.0M') ? '₹9.99M' : 'N/A'
  };

  // 2. Explore Page
  t0 = Date.now();
  await page.goto('http://127.0.0.1:3000/explore/pune', { waitUntil: 'networkidle' });
  const loadExplore = (Date.now() - t0) / 1000;
  await page.waitForTimeout(2000);
  const exploreButtons = await page.locator('button').allInnerTexts();
  const exploreText = await page.locator('body').innerText();

  results.pages.explore = {
    load_time_s: loadExplore,
    url: page.url(),
    buttons: exploreButtons.map(b => b.trim()).filter(Boolean),
    text_sample: exploreText.slice(0, 400)
  };

  // 3. Optimizer Page
  t0 = Date.now();
  await page.goto('http://127.0.0.1:3000/optimizer', { waitUntil: 'networkidle' });
  const loadOpt = (Date.now() - t0) / 1000;
  await page.waitForTimeout(1500);
  const optButtons = await page.locator('button').allInnerTexts();
  const optText = await page.locator('body').innerText();

  results.pages.optimizer = {
    load_time_s: loadOpt,
    url: page.url(),
    buttons: optButtons.map(b => b.trim()).filter(Boolean),
    text_sample: optText.slice(0, 500)
  };

  // 4. Project Page
  t0 = Date.now();
  await page.goto('http://127.0.0.1:3000/projects/PROJ-PUNE-2025-BA225D6A', { waitUntil: 'networkidle' });
  const loadProj = (Date.now() - t0) / 1000;
  await page.waitForTimeout(1500);
  const projButtons = await page.locator('button').allInnerTexts();
  const projText = await page.locator('body').innerText();

  results.pages.project = {
    load_time_s: loadProj,
    url: page.url(),
    buttons: projButtons.map(b => b.trim()).filter(Boolean),
    text_sample: projText.slice(0, 500)
  };

  // 5. MRV Page
  t0 = Date.now();
  await page.goto('http://127.0.0.1:3000/mrv', { waitUntil: 'networkidle' });
  const loadMrv = (Date.now() - t0) / 1000;
  await page.waitForTimeout(1500);
  const mrvButtons = await page.locator('button').allInnerTexts();
  const mrvText = await page.locator('body').innerText();

  results.pages.mrv = {
    load_time_s: loadMrv,
    url: page.url(),
    buttons: mrvButtons.map(b => b.trim()).filter(Boolean),
    text_sample: mrvText.slice(0, 500)
  };

  await browser.close();

  fs.writeFileSync('docs/recon_results.json', JSON.stringify(results, null, 2));
  console.log('Recon successfully finished! Output written to docs/recon_results.json');
}

runRecon().catch(err => {
  console.error(err);
  process.exit(1);
});


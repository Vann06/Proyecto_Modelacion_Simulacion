/* UI acceptance against an existing real quick-job result. No new search.
 * node scripts/project2_verify_quick_ui.cjs <playwright-package-path> <job-id> [origin]
 * Playwright is a test tool only; it is not a production dependency.
 */
const {chromium}=require(process.argv[2]);
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const path=require('node:path');
async function main(){
 const jobId=process.argv[3],origin=process.argv[4]||'http://127.0.0.1:8024';
 const actual=await (await fetch(origin+'/api/quick-nsga2/'+jobId)).json();
 assert.equal(actual.status,'completed');assert.equal(actual.result.K,8);
 console.log('Loaded real K8 front:',actual.result.solutions.length,'solutions');
 const folder=path.resolve('docs/project2/screenshots/quick-nsga');await fs.mkdir(folder,{recursive:true});
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1500,height:1050},deviceScaleFactor:1});
  page.setDefaultTimeout(120000);
  await page.route(/https:\/\/fonts\.(googleapis|gstatic)\.com\//,route=>route.abort());
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  let starts=0,individuals=0;
  page.on('request',r=>{if(r.method()==='POST'&&r.url().endsWith('/simulate'))individuals++;});
  // Replay the real completed response only for the search-start request.
  // Backend execution, generation progress and timings are tested separately.
  await page.route('**/api/quick-nsga2',async route=>{
   assert.equal(route.request().method(),'POST');const body=route.request().postDataJSON();
   assert.equal(body.K,8);assert.equal(body.method,'NSGA2');assert.equal(body.optimizer_seed,2026);
   starts++;await route.fulfill({json:actual});
  });
  await page.goto(origin,{waitUntil:'domcontentloaded',timeout:120000});console.log('App opened');await page.getByRole('button',{name:'Abejas en movimiento',exact:true}).click();
  await page.getByRole('heading',{name:'Configura una pregunta'}).waitFor();
  console.log('Scenario controls loaded');
  await page.getByText('EXPLORA EL MAPA',{exact:true}).click();
  await page.getByLabel('Propuesta de ubicaciones').selectOption('NSGA2');
  await page.getByLabel('Modo NSGA-II').selectOption('quick');
  const K=page.getByRole('slider',{name:'Número de colmenas',exact:true});
  await K.focus();await K.press('Home');for(let i=1;i<8;i++)await K.press('ArrowRight');
  console.log('Configured K8 quick mode');
  await page.screenshot({path:path.join(folder,'01-configuracion.png'),fullPage:true,timeout:30000});
  await page.getByRole('button',{name:'Ejecutar búsqueda rápida',exact:true}).click();
  await page.getByLabel('Solución rápida',{exact:true}).waitFor();
  console.log('Loaded interactive real front');
  await page.getByLabel('Solución rápida',{exact:true}).selectOption(actual.result.solutions[0].solution_id);
  await page.getByRole('heading',{name:'8 colmenas. Cada viaje cuenta.',exact:true}).waitFor();
  assert.equal(await page.locator('.movement-colonies button').count(),8);
  assert.equal(await page.locator('.movement-hive-icon').count(),8);
  assert.equal(await page.locator('.movement-player').count(),0);
  const second=actual.result.solutions[1]||actual.result.solutions[0];
  await page.getByLabel('Solución rápida',{exact:true}).selectOption(second.solution_id);
  const symbols=page.locator('.quick-pareto .recharts-scatter-symbol');
  if(await symbols.count())await symbols.first().click();
  await page.screenshot({path:path.join(folder,'02-frente-y-vista-previa.png'),fullPage:true});
  assert.equal(starts,1);assert.equal(individuals,0);
  await page.getByRole('button',{name:'Simular solución seleccionada',exact:true}).click();
  await page.getByLabel('Reproducción de viajes',{exact:true}).waitFor({timeout:120000});
  assert.equal(await page.locator('.movement-colonies button').count(),8);
  const clock=page.getByRole('slider',{name:'Minuto de la jornada'});await clock.focus();await clock.press('Home');for(let i=0;i<4;i++)await clock.press('PageUp');
  await page.getByRole('button',{name:'Reproducir',exact:true}).click();
  await page.getByRole('button',{name:'Pausar',exact:true}).click();
  await page.evaluate(()=>window.scrollTo(0,0));
  await page.screenshot({path:path.join(folder,'03-simulacion-individual-k8.png'),fullPage:true});
  assert.equal(starts,1);assert.equal(individuals,1);assert.deepEqual(errors,[]);
  // Small viewport: controls must not create horizontal page overflow.
  await page.setViewportSize({width:430,height:900});
  await page.evaluate(()=>window.scrollTo(0,0));
  const size=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth}));
  assert.ok(size.scroll<=size.client+1,JSON.stringify(size));
  await page.screenshot({path:path.join(folder,'04-movil-k8.png'),fullPage:true});
  await fs.writeFile(path.resolve('docs/project2/QUICK_NSGA_UI_VERIFICATION.json'),JSON.stringify({job_id:jobId,origin,K:8,search_response:'replayed real completed backend result; no extra optimization',search_clicks:starts,individual_simulations:individuals,console_errors:errors,mobile_width:size,captures:await fs.readdir(folder)},null,2));
  console.log('UI acceptance passed: eight hives, Pareto selection, one individual run, playback, mobile.');
 }finally{await browser.close();}
}
main().catch(e=>{console.error(e);process.exitCode=1});

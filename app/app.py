"""Aplicación local de integración: resultados archivados y escenarios interactivos."""
from pathlib import Path
import hashlib
import json
import sys
from urllib.parse import quote
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import pydeck as pdk
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'app')]
from bee_sim.project2 import load_config, with_parameters, simulate
from bee_sim.project2.strategies.random_baseline import select_sites as random_select
from bee_sim.project2.strategies.greedy_baseline import select_sites as greedy_select
from bee_sim.analysis.project2_comparison import build_comparison
from project2_view import geographic_points, travel_snapshot, resource_snapshot

st.set_page_config(page_title='Oslo · Abejas y paisaje', page_icon='🐝', layout='wide')
st.markdown('''<style>
.stApp {background:#f7f8f4;} h1,h2,h3 {color:#173c37;}
div[data-testid="stMetric"] {background:white;border:1px solid #e1e8df;border-radius:12px;padding:14px;}
.hero {padding:18px 24px;border-radius:16px;background:#163e37;color:#fff;margin-bottom:18px;}
.hero h1 {color:white;margin:0;font-size:2rem;} .hero p {margin:8px 0 0;color:#d5e8df;}
</style>''', unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>Oslo · Abejas y paisaje</h1><p>Explora las ubicaciones, compara las estrategias y observa cómo cambian los viajes.</p></div>', unsafe_allow_html=True)
st.caption('Geografía real de Oslo · recursos y comportamiento sintéticos · horizonte 18 julio–4 agosto de 2017')


@st.cache_data(show_spinner=False)
def archived():
    return build_comparison(ROOT, n_boot=2000)


@st.cache_data(show_spinner=False)
def geography():
    folder = ROOT / 'data/project2/processed'
    candidates = geographic_points(pd.read_csv(folder / 'candidate_hive_sites.csv'))
    resources = pd.read_csv(folder / 'resource_patches.csv')
    parks = gpd.read_file(folder / 'resource_patches.geojson').to_crs(25833)
    parks.geometry = parks.geometry.simplify(8, preserve_topology=True)
    zones = gpd.read_file(folder / 'bee_free_zones.geojson').to_crs(25833)
    zones.geometry = zones.geometry.simplify(8, preserve_topology=True)
    names = pd.read_csv(folder / 'spatial_patches.csv').set_index('patch_id').Navn.fillna('Espacio verde')
    candidates['place_name'] = candidates.patch_id.map(names).fillna('Espacio verde')
    candidates['label'] = candidates.place_name
    candidates['detail'] = 'Sitio candidato válido bajo el filtro espacial'
    park_json = json.loads(parks.to_crs(4326).to_json())
    for feature in park_json['features']:
        feature['properties']['label'] = str(names.get(feature['properties']['patch_id'], 'Espacio verde'))
    return candidates, resources, park_json, json.loads(zones[['geometry']].to_crs(4326).to_json())


try:
    comparison = archived()
    candidates, resources, park_geojson, zone_geojson = geography()
    base = load_config(ROOT / 'config/project2/base.yaml')
    bank = pd.read_csv(ROOT / base['seed_bank_file'])
except (ValueError, FileNotFoundError) as exc:
    st.error(f'No se pudo cargar una entrada común: {exc}')
    st.info('Revisa el README de integración y ejecuta la preparación de datos antes de abrir la app.')
    st.stop()

meta = comparison['metadata']
front = json.loads((ROOT / 'results/project2/nsga2/front.json').read_text())
front_by_id = {s['solution_id']: s for s in front['solutions']}
unique_ids = comparison['nsga_installations'].loc[~comparison['nsga_installations'].physical_duplicate].solution_id.tolist()
method_labels = ['GREEDY', 'RANDOM', 'NSGA-II guardado', 'Manual']
st.sidebar.title('Escenario interactivo')
method = st.sidebar.selectbox('Propuesta de ubicaciones', method_labels)
if method == 'NSGA-II guardado':
    selected_front = st.sidebar.selectbox('Solución del frente conservado', unique_ids)
    K = len(front_by_id[selected_front]['site_ids'])
    st.sidebar.caption(f'{K} colmenas fijas de la solución guardada. Cambiar causas la reevalúa; no ejecuta otra búsqueda.')
else:
    K = st.sidebar.slider('Número de colmenas', 1, 20, 5)
optimizer_seed = st.sidebar.number_input('Semilla de selección RANDOM', min_value=0, max_value=999999, value=2026, step=1)
with st.sidebar.expander('Causas del escenario', expanded=True):
    resource_factor = st.slider('Disponibilidad relativa de recurso', 0., 3., 1., .1)
    regeneration = st.slider('Regeneración diaria', 0., .5, .1, .01)
    radius = st.slider('Radio de forrajeo (m)', 250, 6000, 3000, 250)
    departures = st.slider('Oportunidades por colmena y día', 0, 100, 12)
    alpha = st.slider('Penalización de competencia', 0., 5., 1., .1)
    beta = st.slider('Sensibilidad a la distancia', 0., 5., 2., .1)
    speed = st.slider('Velocidad de vuelo (m/s)', 2., 10., 5.5, .5)
st.sidebar.caption('Estos controles son supuestos del modelo. No representan efectos causales medidos ni recursos observados.')
replication = st.sidebar.selectbox('Réplica común', bank.replication_id.tolist(), index=30)
n_replicas = st.sidebar.slider('Réplicas para la prueba rápida', 1, min(5, 101 - replication), 1)
cfg = with_parameters(base, K=K, initial_resource_total=base['initial_resource_total'] * resource_factor,
                      regeneration_rate=regeneration, max_foraging_distance_m=float(radius),
                      departures_per_day=float(departures), alpha=alpha, beta=beta, flight_speed_m_s=speed)
manual = []
if method == 'Manual':
    labels = candidates.set_index('site_id').place_name.to_dict()
    manual = st.sidebar.multiselect('Escoge exactamente K sitios', candidates.site_id.tolist(),
                                    format_func=lambda s: f'{labels[s]} · {s.rsplit("_", 1)[-1]}')
run_clicked = st.sidebar.button('Simular escenario', type='primary', width='stretch')
if run_clicked:
    try:
        if method == 'GREEDY':
            sites = greedy_select(cfg)['site_ids']
        elif method == 'RANDOM':
            sites = list(random_select(candidates, K, int(optimizer_seed)))
        elif method == 'NSGA-II guardado':
            sites = front_by_id[selected_front]['site_ids']
        else:
            sites = manual
        chosen_bank = bank.loc[bank.replication_id.between(replication, replication + n_replicas - 1)]
        with st.spinner('Evaluando con el motor común…'):
            runs = [simulate(sites, int(row.seed), cfg) for row in chosen_bank.itertuples()]
        signature = (cfg.config_hash, method, int(optimizer_seed), int(replication), int(n_replicas), tuple(sorted(sites)))
        st.session_state['last_run'] = {'runs': runs, 'config': cfg, 'method': method, 'sites': sites, 'signature': signature,
                                       'replications': chosen_bank.replication_id.tolist()}
        st.sidebar.success('Escenario calculado')
    except (ValueError, FileNotFoundError) as exc:
        st.sidebar.error(str(exc))

tab_results, tab_live, tab_audit = st.tabs(['Comparar resultados guardados', 'Mapa y escenario', 'Auditoría y siguientes pasos'])
with tab_results:
    st.subheader('Tres métodos, las mismas 70 réplicas reservadas')
    st.caption(f'RANDOM: 30 instalaciones · GREEDY: una instalación · NSGA-II: {meta["selected_nsga_solution"]}, ejemplo seleccionado con las medias de búsqueda congeladas.')
    table = comparison['summary']
    key_metrics = table.loc[table.metric.eq('total_resource_obtained')].set_index('method')
    columns = st.columns(3)
    for col, name in zip(columns, ['RANDOM', 'GREEDY', 'NSGA2']):
        col.metric(name.replace('NSGA2', 'NSGA-II'), f'{key_metrics.loc[name, "mean"]:,.1f} RU')
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))
    colors = ['#c39135', '#287c68', '#606ab7']
    for ax, (metric, label) in zip(axes, [('total_resource_obtained', 'Recurso entregado'), ('mean_distance_m', 'Distancia media de ida (m)'), ('competition_pressure', 'Presión de competencia')]):
        for idx, name in enumerate(['RANDOM', 'GREEDY', 'NSGA2']):
            row = table.loc[table.method.eq(name) & table.metric.eq(metric)].iloc[0]
            ax.bar(idx, row['mean'], color=colors[idx])
            ax.plot([idx, idx], [row.ci95_low, row.ci95_high], color='#183d36', lw=2)
        ax.set_xticks(range(3), ['RANDOM', 'GREEDY', 'NSGA-II'])
        ax.set_title(label, fontsize=10)
        ax.grid(axis='y', alpha=.15)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
    st.caption('IC 95% condicionales a las instalaciones guardadas. RANDOM se promedia por seed; no se cuentan 2,100 filas como réplicas independientes. Comparación descriptiva sintética, no validación ecológica.')
    cloud = comparison['nsga_installations'].loc[~comparison['nsga_installations'].physical_duplicate]
    st.subheader('Recurso frente a distancia')
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.scatter(cloud.mean_distance_m, cloud.total_resource_obtained, label='NSGA-II: ubicaciones físicas distintas', color='#606ab7')
    for name, color in [('RANDOM', '#c39135'), ('GREEDY', '#287c68')]:
        means = comparison['frames'][name].groupby('solution_id')[['mean_distance_m', 'total_resource_obtained']].mean()
        ax.scatter(means.mean_distance_m, means.total_resource_obtained, label=name, color=color, marker='x' if name == 'RANDOM' else 'D')
    ax.set(xlabel='Distancia media de ida (m)', ylabel='Recurso entregado (synthetic_RU)')
    ax.legend(fontsize=8)
    ax.grid(alpha=.2)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
    with st.expander('Tablas e intervalos completos'):
        st.dataframe(table, hide_index=True, width='stretch')
        st.dataframe(comparison['paired'], hide_index=True, width='stretch')
    st.download_button('Descargar comparación CSV', table.to_csv(index=False), 'comparison_summary.csv', 'text/csv')

with tab_live:
    stored = st.session_state.get('last_run')
    st.subheader('Paisaje, colmenas y viajes')
    if stored:
        result, run_cfg = stored['runs'][0], stored['config']
        old_signature = stored['signature']
        selection_changed = (method == 'NSGA-II guardado' and tuple(sorted(front_by_id[selected_front]['site_ids'])) != old_signature[5]) or (method == 'Manual' and tuple(sorted(manual)) != old_signature[5])
        if selection_changed or old_signature[:5] != (cfg.config_hash, method, int(optimizer_seed), int(replication), int(n_replicas)):
            st.info('Hay cambios de controles pendientes. El mapa sigue mostrando la última corrida; pulsa Simular escenario para aplicarlos.')
        st.caption(f'Última corrida: {stored["method"]} · {len(stored["sites"])} colmenas · réplica {stored["replications"][0]}. Los viajes del mapa corresponden a esa réplica.')
        dates = sorted(result['resource_log'].date.unique())
        day = st.select_slider('Día del modelo', options=dates, value=dates[0])
        minute = st.slider('Minuto de la jornada', 0, int(run_cfg['day_minutes']), min(180, int(run_cfg['day_minutes'])), 5)
        bees = travel_snapshot(result, candidates, resources, day, minute)
        resource_state = resource_snapshot(result, day, minute, run_cfg['day_minutes'])
        available = resource_state.set_index('patch_id').available.to_dict()
        original = resources.set_index('patch_id').exclusive_area_m2 / resources.exclusive_area_m2.sum() * run_cfg['initial_resource_total']
        hives = candidates.loc[candidates.site_id.isin(stored['sites'])].copy().sort_values('site_id')
        hives['hive_label'] = [str(i + 1) for i in range(len(hives))]
        hives['label'] = 'Colmena ' + hives.hive_label
        hives['detail'] = hives.place_name
        cards = st.columns(4)
        means = pd.DataFrame([r['metrics'] for r in stored['runs']]).mean(numeric_only=True)
        cards[0].metric('Recurso entregado · corrida', f'{means.get("total_resource_obtained", 0):.1f} RU')
        distance_value = means.get('mean_distance_m', np.nan)
        cards[1].metric('Distancia media · corrida', f'{distance_value:.0f} m' if pd.notna(distance_value) else 'Sin viajes')
        cards[2].metric('Viajes en curso · instante', len(bees))
        cards[3].metric('Stock disponible · instante', f'{resource_state.available.sum():.1f} RU')
    else:
        st.info('Elige una propuesta y pulsa Simular escenario para ver colmenas, viajes y recursos. Los controles no lanzan búsquedas largas automáticamente.')
        bees, hives, available = pd.DataFrame(), candidates.iloc[:0].copy(), {}
        original = pd.Series(dtype=float)
    parks_view = json.loads(json.dumps(park_geojson))
    for feature in parks_view['features']:
        props = feature['properties']
        patch_id = props['patch_id']
        ratio = available.get(patch_id, 1) / max(float(original.get(patch_id, 1)), .000001)
        shade = min(1., max(0., ratio))
        props['fill_color'] = [int(150 - 115 * shade), int(155 + 30 * shade), int(135 - 15 * shade), 145]
        props['detail'] = f"Stock disponible: {available[patch_id]:.2f} synthetic_RU" if patch_id in available else 'Geometría exclusiva de recurso; escenario sin ejecutar'
    layers = [pdk.Layer('GeoJsonLayer', parks_view, filled=True, stroked=True, get_fill_color='properties.fill_color', get_line_color=[70, 100, 80, 90], line_width_min_pixels=.5, pickable=True),
              pdk.Layer('GeoJsonLayer', zone_geojson, filled=True, stroked=True, get_fill_color=[193, 68, 68, 24], get_line_color=[193, 68, 68, 180], line_width_min_pixels=1, pickable=False)]
    show_candidates = st.checkbox('Mostrar todos los candidatos', value=False)
    if show_candidates:
        layers.append(pdk.Layer('ScatterplotLayer', candidates, get_position=['longitude', 'latitude'], get_radius=25, radius_min_pixels=2, get_fill_color=[105, 115, 120, 90], pickable=True))
    if stored and len(hives):
        layers.extend([pdk.Layer('ScatterplotLayer', hives, get_position=['longitude', 'latitude'], get_radius=85, radius_min_pixels=9, get_fill_color=[224, 162, 43, 240], get_line_color=[80, 55, 20], stroked=True, pickable=True),
                       pdk.Layer('TextLayer', hives, get_position=['longitude', 'latitude'], get_text='hive_label', get_size=13, get_color=[255, 255, 255], pickable=False)])
    if len(bees):
        show_routes = st.checkbox('Mostrar recorridos activos', value=True)
        visible = bees.head(400)
        if show_routes:
            layers.append(pdk.Layer('LineLayer', visible, get_source_position='source', get_target_position='target', get_color=[42, 126, 112, 100], get_width=1))
        svg = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><ellipse cx="22" cy="20" rx="12" ry="9" fill="#d9f3fa"/><ellipse cx="42" cy="20" rx="12" ry="9" fill="#d9f3fa"/><ellipse cx="32" cy="36" rx="22" ry="15" fill="#efb32c" stroke="#292e2a" stroke-width="3"/><path d="M24 23v26M36 23v26" stroke="#292e2a" stroke-width="6"/><circle cx="48" cy="33" r="3" fill="#292e2a"/></svg>'
        layers.append(pdk.Layer('IconLayer', visible, get_position=['longitude', 'latitude'], get_icon='icon', get_size=27,
                                icon_atlas=pdk.types.String('data:image/svg+xml;charset=utf-8,' + quote(svg)),
                                icon_mapping={'bee': {'x': 0, 'y': 0, 'width': 64, 'height': 64, 'mask': False}}, pickable=True))
        if len(bees) > 400:
            st.caption(f'Se dibujan 400 de {len(bees)} viajes para mantener el mapa fluido.')
    online_map = st.checkbox('Mapa base en línea', value=True)
    deck = pdk.Deck(layers=layers, initial_view_state=pdk.ViewState(latitude=59.91, longitude=10.76, zoom=10.5, pitch=15),
                    map_style='https://basemaps.cartocdn.com/gl/positron-gl-style/style.json' if online_map else None,
                    tooltip={'text': '{label}\n{detail}'})
    st.pydeck_chart(deck, width='stretch', height=570)
    st.caption('Verde: recurso asignado · rojo: zonas restringidas para colmenas · dorado: colmenas · iconos de abeja: viajes modelados en curso, no abejas únicas observadas. La intensidad verde se satura al stock inicial; el total puede aumentar por regeneración.')
    if stored:
        series = result['resource_log'].groupby('date')[['consumption', 'regeneration', 'R_after']].sum()
        st.line_chart(series.rename(columns={'consumption': 'Consumo', 'regeneration': 'Regeneración', 'R_after': 'Recurso al cierre'}))
        st.download_button('Descargar viajes de la réplica', result['trips'].to_csv(index=False), 'scenario_trips.csv', 'text/csv')
        with st.expander('Parámetros y reproducción de la corrida'):
            st.json({'version': result['provenance']['engine_version'], 'seed': result['provenance']['seed'],
                     'mode': 'synthetic', 'config_hash': result['provenance']['config_hash']})
            params = pd.DataFrame(stored['config'].records).T.reset_index().rename(columns={'index': 'Parámetro', 'value': 'Valor', 'status': 'Procedencia', 'source': 'Justificación', 'provisional': 'Provisional'})
            params['Valor'] = params['Valor'].astype(str)
            st.dataframe(params, hide_index=True, width='stretch')

with tab_audit:
    st.subheader('Lo integrado y lo que sigue')
    st.dataframe(comparison['audit'][['method', 'original_rows', 'holdout_rows', 'solutions', 'holdout_replications']], hide_index=True, width='stretch')
    cols = st.columns(3)
    cols[0].metric('Simulaciones de búsqueda NSGA-II', f'{meta["search_simulations"]:,}')
    cols[1].metric('Tiempo guardado de búsqueda', f'{meta["search_recorded_hours"]:.2f} h')
    cols[2].metric('Instalaciones físicas del frente', f'{meta["physical_front_installations"]} / {meta["original_front_solutions"]} IDs')
    st.write('Las ramas y los resultados originales se conservan. La comparación usa únicamente las réplicas 31–100 y comprueba configuración, motor, datos y contrato. El holdout ya había sido inspeccionado por el equipo: el análisis es descriptivo.')
    st.write('Pendientes científicos: calibrar recursos y comportamiento, validar operadores de observación frente a Dryad, estudiar sensibilidad de solapamientos y reforzar objetivos si la competencia casi siempre es cero.')
    st.write('Las siete horas no se repiten al abrir esta app. Las nuevas búsquedas requieren presupuesto, una carpeta nueva y una orden explícita; la app reevalúa ubicaciones existentes con el motor común.')
    st.download_button('Descargar auditoría de resultados', comparison['audit'].to_csv(index=False), 'integration_audit.csv', 'text/csv')

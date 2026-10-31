"""Preparación explícita de propiedad exclusiva del recurso y distancias comunes."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.ops import unary_union

POLICY = 'lexicographic_patch_id_priority_v1'
SOURCE_NAMES = ('spatial_patches.csv', 'oslo_parks.geojson', 'bee_free_zones.geojson',
                'candidate_hive_sites.csv', 'hive_patch_distances.npz')
ASSET_NAMES = ('resource_patches.csv', 'resource_patches.geojson', 'resource_patch_distances.npz')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare_resources(root):
    """Cada punto de terreno pertenece al primer patch_id, sin editar originales."""
    folder = Path(root) / 'data/project2/processed'
    source_hashes = {name: digest(folder / name) for name in SOURCE_NAMES}
    source = gpd.read_file(folder / 'oslo_parks.geojson').to_crs(25833).sort_values('patch_id').reset_index(drop=True)
    candidates = pd.read_csv(folder / 'candidate_hive_sites.csv').sort_values('site_id').reset_index(drop=True)
    if source.patch_id.duplicated().any() or not source.geometry.is_valid.all():
        raise ValueError('IDs o geometrías de origen inválidos')
    flags = pd.read_csv(folder / 'spatial_patches.csv').set_index('patch_id')
    zones = gpd.read_file(folder / 'bee_free_zones.geojson').to_crs(25833)
    if (source.geometry.is_empty.any() or source.geometry.isna().any() or
            not zones.geometry.is_valid.all() or zones.geometry.is_empty.any() or zones.geometry.isna().any()):
        raise ValueError('Geometrías vacías/ausentes o zonas inválidas')
    if set(source.patch_id) != set(flags.index) or not flags.index.is_unique:
        raise ValueError('Catálogos espaciales incompatibles')
    restricted = unary_union(zones.geometry)
    recalculated = source.geometry.intersects(restricted).to_numpy()
    aligned_flags = flags.loc[source.patch_id]
    if (not np.array_equal(recalculated, aligned_flags.intersects_restricted_zone) or
            not np.array_equal(~recalculated, aligned_flags.is_initial_candidate)):
        raise ValueError('Restricciones desactualizadas: ejecutar y validar la etapa espacial')
    if not candidates.site_id.is_unique or not set(candidates.patch_id).issubset(set(source.patch_id)):
        raise ValueError('Sitios candidatos duplicados o sin parque de origen')
    candidate_points = gpd.GeoSeries(gpd.points_from_xy(candidates.x_m, candidates.y_m), crs=25833)
    parents = source.set_index('patch_id').loc[candidates.patch_id].geometry.reset_index(drop=True)
    if (not parents.covers(candidate_points).all() or candidate_points.intersects(restricted).any() or
            not flags.loc[candidates.patch_id].is_initial_candidate.all()):
        raise ValueError('Sitio fuera de parque o dentro de una zona restringida')
    index = source.sindex
    owned = []
    for i, geometry in enumerate(source.geometry):
        prior = [int(k) for k in index.query(geometry, predicate='intersects') if k < i]
        piece = geometry.difference(unary_union(source.geometry.iloc[prior])) if prior else geometry
        if not piece.is_valid:
            raise ValueError('La diferencia produjo geometría inválida; revisar sin reparación silenciosa')
        owned.append(piece)
    exclusive = gpd.GeoSeries(owned, crs=25833)
    areas = exclusive.area.to_numpy()
    union = unary_union(source.geometry)
    if not np.isclose(areas.sum(), union.area, rtol=1e-8, atol=.01):
        raise ValueError('La política no conserva el área de unión')
    positive = areas > 0
    union_exclusive = unary_union(exclusive.loc[positive])
    if union.symmetric_difference(union_exclusive).area > .01:
        raise ValueError('Se perdió superficie de recurso')
    # El punto original es solo referencia finita para las columnas sin área: nunca reciben R>0.
    references = source.geometry.representative_point()
    references.loc[positive] = exclusive.loc[positive].representative_point()
    catalog = pd.DataFrame({'patch_id': source.patch_id, 'exclusive_area_m2': areas,
                            'has_resource_geometry': positive, 'resource_x_m': references.x,
                            'resource_y_m': references.y, 'overlap_policy': POLICY,
                            'reference_point_kind': np.where(positive, 'exclusive_geometry_interior', 'original_reference_zero_resource')})
    layer = gpd.GeoDataFrame(catalog.loc[positive].copy(), geometry=exclusive.loc[positive], crs=25833)
    catalog.to_csv(folder / ASSET_NAMES[0], index=False, lineterminator='\n')
    (folder / ASSET_NAMES[1]).write_text(layer.to_crs(4326).to_json(drop_id=True, to_wgs84=True), encoding='utf-8')
    site_xy = candidates[['x_m', 'y_m']].to_numpy(float)
    patch_xy = catalog[['resource_x_m', 'resource_y_m']].to_numpy(float)
    distances = np.linalg.norm(site_xy[:, None, :] - patch_xy[None, :, :], axis=2)
    with (folder / ASSET_NAMES[2]).open('wb') as handle:
        np.savez_compressed(handle, distances_m=distances,
                            site_ids=candidates.site_id.to_numpy(dtype=str), patch_ids=catalog.patch_id.to_numpy(dtype=str),
                            crs=np.array('EPSG:25833'), policy=np.array(POLICY), site_xy_m=site_xy, patch_xy_m=patch_xy)
    manifest = {'policy': POLICY, 'crs': 'EPSG:25833', 'source_hashes': source_hashes,
                'asset_hashes': {name: digest(folder / name) for name in ASSET_NAMES},
                'original_patch_count': len(source), 'positive_resource_geometries': int(positive.sum()),
                'union_area_m2': union.area, 'sum_original_areas_m2': source.area.sum()}
    (folder / 'resource_preparation.json').write_text(json.dumps(manifest, sort_keys=True, indent=2), encoding='utf-8')
    if source_hashes != {name: digest(folder / name) for name in SOURCE_NAMES}:
        raise ValueError('Los originales cambiaron durante la preparación')
    return manifest


def load_landscape(config):
    folder = config.root / 'data/project2/processed'
    manifest_path = folder / 'resource_preparation.json'
    if not manifest_path.is_file():
        raise FileNotFoundError('Faltan derivados: ejecute python scripts/project2_run.py prepare')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest['policy'] != POLICY:
        raise ValueError('Política de solapamientos distinta del motor común')
    for name, expected in {**manifest['source_hashes'], **manifest['asset_hashes']}.items():
        if digest(folder / name) != expected:
            raise ValueError(f'Fuente/derivado cambió: {name}; prepare y valide explícitamente')
    candidates = pd.read_csv(folder / 'candidate_hive_sites.csv').sort_values('site_id').reset_index(drop=True)
    patches = pd.read_csv(folder / 'resource_patches.csv')
    source_flags = pd.read_csv(folder / 'spatial_patches.csv').set_index('patch_id')
    if (not candidates.site_id.is_unique or not patches.patch_id.is_unique or
            set(patches.patch_id) != set(source_flags.index) or
            not source_flags.loc[candidates.patch_id, 'is_initial_candidate'].all()):
        raise ValueError('Catálogos/IDs no corresponden a la restricción común')
    with np.load(folder / 'resource_patch_distances.npz', allow_pickle=False) as archive:
        distances = archive['distances_m'].copy()
        if (archive['site_ids'].tolist() != candidates.site_id.tolist() or
                archive['patch_ids'].tolist() != patches.patch_id.tolist() or str(archive['crs']) != 'EPSG:25833'):
            raise ValueError('Orden/CRS de matriz inconsistente')
    if distances.shape != (len(candidates), len(patches)) or not np.isfinite(distances).all() or (distances < 0).any():
        raise ValueError('Distancias inválidas')
    if not np.isfinite(patches.exclusive_area_m2).all() or (patches.exclusive_area_m2 < 0).any():
        raise ValueError('Áreas exclusivas inválidas')
    return candidates, patches, distances, manifest

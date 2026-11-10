"""Geometría de presentación y posiciones de viajes calculadas desde logs reales."""
import json
import numpy as np
import pandas as pd
from pyproj import Transformer

TO_GEO = Transformer.from_crs(25833, 4326, always_xy=True)


def geographic_points(frame, x='x_m', y='y_m'):
    result = frame.copy()
    result['longitude'], result['latitude'] = TO_GEO.transform(result[x].to_numpy(float), result[y].to_numpy(float))
    return result


def travel_snapshot(result, candidates, resources, date, minute):
    """Un marcador por viaje activo; no estima abejas únicas ni vuelos observados."""
    trips = result['trips']
    trips = trips.loc[trips.date.eq(date) & trips.departure_min.le(minute)]
    sites = candidates.set_index('site_id')
    patches = resources.set_index('patch_id')
    rows = []
    for trip in trips.itertuples():
        if pd.notna(trip.return_min) and minute >= trip.return_min:
            continue
        home = sites.loc[trip.site_id, ['x_m', 'y_m']].to_numpy(float)
        patch = patches.loc[trip.patch_id, ['resource_x_m', 'resource_y_m']].to_numpy(float)
        if minute < trip.arrival_min:
            duration = trip.arrival_min - trip.departure_min
            f = (minute - trip.departure_min) / duration if duration > 0 else 1
            point, phase = home + f * (patch - home), 'Ida'
        elif pd.notna(trip.foraging_end_min) and minute >= trip.foraging_end_min:
            duration = trip.return_min - trip.foraging_end_min
            f = (minute - trip.foraging_end_min) / duration if duration > 0 else 1
            point, phase = patch + f * (home - patch), 'Regreso'
        else:
            point, phase = patch, 'Búsqueda / forrajeo'
        lon, lat = TO_GEO.transform(*point)
        source = list(TO_GEO.transform(*home))
        target = list(TO_GEO.transform(*patch))
        rows.append({'longitude': lon, 'latitude': lat, 'source': source, 'target': target,
                     'icon': 'bee', 'label': f'Viaje de colmena {trip.hive_slot + 1}',
                     'detail': phase, 'phase': phase})
    return pd.DataFrame(rows, columns=['longitude', 'latitude', 'source', 'target', 'icon', 'label', 'detail', 'phase'])


def resource_snapshot(result, date, minute, day_minutes):
    frame = result['resource_log'].loc[result['resource_log'].date.eq(date)].copy()
    if minute >= day_minutes:
        frame['available'] = frame.R_after
    else:
        trips = result['trips']
        taken = trips.loc[trips.date.eq(date) & trips.foraging_start_min.le(minute)].groupby('patch_id').resource_consumed.sum()
        frame['available'] = frame.R_before - frame.patch_id.map(taken).fillna(0)
        frame['available'] = frame.available.clip(lower=0)  # solo redondeo de presentación; el motor valida el balance.
    return frame

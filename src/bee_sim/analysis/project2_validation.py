"""Referentes empíricos independientes del motor de recursos sintéticos.

No existe operador RU -> flores, o viajes -> individuos/minuto. Los modelos aquí
son referencias estadísticas de observación, no calibración del motor de colmenas.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd


def load_table(path):
    for encoding in ('utf-8-sig', 'cp1252'):
        try:
            df = pd.read_csv(path, sep='\t', encoding=encoding, na_values=['NA', 'N/A', ''])
            for col in df.select_dtypes('object'):
                df[col] = df[col].str.strip()
            return df
        except UnicodeDecodeError:
            continue
    raise ValueError(f'Codificación no reconocida: {path}')


def floral_dates(series):
    explicit = pd.to_datetime(series, format='%d.%m.%Y', errors='coerce')
    parts = series.str.lower().str.extract(r'^(\d{1,2})\.(jul|aug)(?:\.(\d{2}|\d{4}))?$')
    year = parts[2].where(parts[2].str.len().eq(4), '20' + parts[2]).fillna('2017')
    contextual = pd.to_datetime(year + '-' + parts[1].map({'jul':'07','aug':'08'}) + '-' + parts[0], errors='coerce')
    return explicit.fillna(contextual), explicit.isna() & parts[2].isna() & contextual.notna()


def prepare_observations(root):
    raw = Path(root) / 'data/project2/raw/oslo'
    flora = load_table(raw / 'floral_density_data_dryad_version.txt')
    visits = load_table(raw / 'floral_visitation_data_dryad_version.txt')
    flora['date'], flora['year_contextualized'] = floral_dates(flora.inventory_date)
    flora['area_m2'] = flora.transect_width_cm / 100 * flora.transect_length_m
    flora['count_valid'] = flora.flower_number.notna() & flora.flower_number.ge(0) & flora.area_m2.gt(0)
    grouped = flora.groupby(['trap_number','date'], dropna=False)
    flowers = grouped.agg(observed_count=('flower_number',lambda x:x.sum(min_count=1)),
                          area_m2=('area_m2','first'), dimensions=('area_m2','nunique'),
                          complete=('count_valid','all'), year_contextualized=('year_contextualized','any')).reset_index()
    flowers['eligible'] = flowers.complete & flowers.dimensions.eq(1) & flowers.date.notna()
    flowers['observed'] = flowers.observed_count / flowers.area_m2
    flowers['stratum'] = flowers.date.dt.month.astype(str)
    visits['date'] = pd.to_datetime(visits.inventory_date, format='%d.%m.%Y', errors='coerce')
    visits['observed_count'] = visits[['individuals_flying','individuals_sitting']].sum(axis=1, min_count=2)
    start = pd.to_datetime(visits.observation_start,format='%H:%M',errors='coerce')
    end = pd.to_datetime(visits.observation_end,format='%H:%M',errors='coerce')
    visits['start_min'] = start.dt.hour * 60 + start.dt.minute
    visits['end_min'] = end.dt.hour * 60 + end.dt.minute
    visits['duration_min'] = visits.end_min - visits.start_min
    keys = ['trap_number','date','observation_start','observation_end','observer1','observer2']
    grouped = visits.groupby(keys, dropna=False)
    sessions = grouped.agg(observed_count=('observed_count',lambda x:x.sum(min_count=1)),
        complete=('observed_count',lambda x:x.notna().all() and x.ge(0).all()),
        duration_min=('duration_min','first'), start_min=('start_min','first'),end_min=('end_min','first'),
        temperature_C=('temperature_C','first'), temperature_values=('temperature_C','nunique')).reset_index()
    sessions['overlap'] = False
    for _, group in sessions.groupby(['trap_number','date']):
        for index, row in group.iterrows():
            other = group.drop(index)
            sessions.loc[index,'overlap'] = ((other.start_min < row.end_min) & (other.end_min > row.start_min)).any()
    sessions['eligible'] = sessions.complete & sessions.duration_min.gt(0) & sessions.date.notna() & ~sessions.overlap & sessions.temperature_values.eq(1)
    sessions['observed'] = sessions.observed_count / sessions.duration_min.where(sessions.duration_min.gt(0))
    # Bins fixed before looking at held-out outcomes; not a fitted thermal response.
    sessions['stratum'] = pd.cut(sessions.temperature_C, [-np.inf,15,20,np.inf], labels=['<=15','15–20','>20'], right=True).astype(str)
    summary = {'floral_rows':len(flora), 'visitation_rows':len(visits),
        'floral_traps':int(flora.trap_number.nunique()), 'visitation_traps':int(visits.trap_number.nunique()),
        'floral_dates_contextualized':int(flora.year_contextualized.sum()),
        'floral_start':str(flora.date.min().date()), 'floral_end':str(flora.date.max().date()),
        'visitation_start':str(visits.date.min().date()), 'visitation_end':str(visits.date.max().date()),
        'floral_complete_units':int(flowers.eligible.sum()), 'floral_excluded_units':int((~flowers.eligible).sum()),
        'candidate_sessions':len(sessions), 'activity_eligible_sessions':int(sessions.eligible.sum()),
        'activity_excluded_sessions':int((~sessions.eligible).sum()), 'overlapping_sessions':int(sessions.overlap.sum()),
        'floral_exact_duplicate_rows_retained':int(flora.duplicated(subset=load_table(raw/'floral_density_data_dryad_version.txt').columns).sum()),
        'visitation_exact_duplicate_rows_retained':int(visits.duplicated(subset=load_table(raw/'floral_visitation_data_dryad_version.txt').columns).sum()),
        'source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in raw.glob('*.txt')}}
    return flowers, sessions, summary


def benchmark(frame, label, unit, seeds, n_boot=2000):
    """80/20 split by trap; 30 train-site bootstrap fits. No test tuning.

    Point estimates use all training sites; intervals for errors bootstrap test
    sites (paired for both models). Fit draws quantify training uncertainty only.
    """
    df = frame.loc[frame.eligible].copy()
    traps = sorted(df.trap_number.unique())
    shuffled = np.random.default_rng(20261107).permutation(traps)
    holdout = set(shuffled[:max(2, int(np.ceil(.2*len(traps))))])
    df['split'] = np.where(df.trap_number.isin(holdout),'evaluation','calibration')
    train, test = df.loc[df.split.eq('calibration')], df.loc[df.split.eq('evaluation')].copy()
    assert not set(train.trap_number) & set(test.trap_number)

    def predict(training):
        base = float(training.observed.mean())
        groups = training.groupby('stratum')['observed'].mean()
        return np.full(len(test),base), test.stratum.map(groups).fillna(base).to_numpy(float)

    base, stratified = predict(train)
    test['reference_base'] = base
    test['reference_stratified'] = stratified
    test['unseen_stratum'] = ~test.stratum.isin(train.stratum)
    draws = []
    train_ids = train.trap_number.unique()
    for replication_id, seed in seeds:
        rng = np.random.default_rng(seed)
        sampled = pd.concat([train.loc[train.trap_number.eq(t)] for t in rng.choice(train_ids,len(train_ids),replace=True)])
        for method, predictions in zip(['global','stratified'],predict(sampled)):
            for pos, (_, row) in enumerate(test.iterrows()):
                draws.append({'dataset':label,'replication_id':replication_id,'seed':seed,'trap_number':row.trap_number,
                              'method':method,'predicted':float(predictions[pos]),'observed':row.observed,'unit':unit})
    rows = []
    ids = test.trap_number.unique()
    samples = np.random.default_rng(17).choice(ids,size=(n_boot,len(ids)),replace=True)
    for method,col in [('global','reference_base'),('stratified','reference_stratified')]:
        residual = test[col]-test.observed
        for metric, values in [('MAE',residual.abs()),('RMSE',residual**2)]:
            by_site = pd.DataFrame({'trap_number':test.trap_number,'error':values}).groupby('trap_number').error.mean()
            boots = by_site.reindex(samples.ravel()).to_numpy().reshape(samples.shape).mean(1)
            estimate = float(by_site.mean())
            if metric=='RMSE': boots,estimate = np.sqrt(boots),np.sqrt(estimate)
            lo,hi=np.quantile(boots,[.025,.975])
            rows.append({'dataset':label,'method':method,'metric':metric,'estimate':estimate,'ci95_low':lo,'ci95_high':hi,
                         'unit':unit,'train_sites':train.trap_number.nunique(),'test_sites':len(ids),
                         'train_units':len(train),'test_units':len(test),'train_bootstrap_replicates':len(seeds)})
    return df, test, pd.DataFrame(draws),pd.DataFrame(rows)


def percentage_change(new, baseline):
    """Undefined if baseline is zero; never substitute infinity or 100%."""
    return None if baseline == 0 or not np.isfinite(baseline) else 100*(new-baseline)/abs(baseline)

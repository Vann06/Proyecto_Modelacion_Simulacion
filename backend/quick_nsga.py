"""Bounded local jobs around the existing NSGA-II; archives are never outputs."""
from pathlib import Path
import json
import os
import signal
import subprocess
import sys
import threading
import time
import uuid
from types import SimpleNamespace

from . import service

LABEL = 'Optimización exploratoria rápida — NSGA-II'
MAX_SIMULATIONS = 96  # 8 initial + 5 * 8 offspring, two search replications.
TIMEOUT_SECONDS = 900
OUTPUT = 'results/project2/quick_nsga2'


def write_json(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2), encoding='utf-8')
    # Windows may briefly deny replace while an API reader has the file open.
    for attempt in range(20):
        try:
            temp.replace(path)
            return
        except PermissionError:
            if attempt == 19:raise
            time.sleep(.025)


def read_json(path):
    for attempt in range(20):
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except PermissionError:
            if attempt == 19:raise
            time.sleep(.025)


def job_path(root, job_id):
    # Never accept user-provided paths.
    if len(job_id) != 32 or any(c not in '0123456789abcdef' for c in job_id):
        raise ValueError('Identificador de búsqueda inválido')
    path = root / OUTPUT / job_id
    if not (path / 'request.json').is_file():
        raise ValueError('Búsqueda no encontrada')
    return path


class QuickJobs:
    """One local backend process, one active job; same lock as individual runs."""

    def __init__(self, root, run_lock):
        self.root, self.run_lock = Path(root), run_lock
        self.lock = threading.Lock()
        self.active = None

    def start(self, request):
        if request['method'] != 'NSGA2':
            raise ValueError('Selecciona NSGA-II para iniciar la búsqueda rápida')
        # Validate scenario and landscape before launching an expensive process.
        config = service.scenario_config(SimpleNamespace(**request))
        import pandas as pd
        from math import comb
        catalog = pd.read_csv(self.root / 'data/project2/processed/candidate_hive_sites.csv')
        if config['K'] > catalog.site_id.nunique() or comb(catalog.site_id.nunique(), config['K']) < 8:
            raise ValueError('No existen ocho instalaciones distintas con ese K')
        with self.lock:
            if self.active or not self.run_lock.acquire(blocking=False):
                raise BlockingIOError('Ya hay una búsqueda o escenario en ejecución')
            path = None
            try:
                job_id = uuid.uuid4().hex
                path = self.root / OUTPUT / job_id
                path.mkdir(parents=True, exist_ok=False)
                write_json(path / 'request.json', {**request, 'optimizer_seed': 2026})
                write_json(path / 'status.json', {'status': 'starting', 'label': LABEL})
                log = (path / 'worker.log').open('w', encoding='utf-8')
                try:
                    proc = subprocess.Popen([sys.executable, '-m', 'backend.quick_nsga_worker', '--job-id', job_id],
                        cwd=self.root, stdout=log, stderr=subprocess.STDOUT,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                        start_new_session=os.name != 'nt')
                finally:
                    log.close()
                started = time.monotonic()
                self.active = (job_id, proc, started)
                threading.Thread(target=self._watch, args=(job_id, proc, started), daemon=True).start()
                return {'job_id': job_id, **self.status(job_id)}
            except Exception:
                if path:
                    write_json(path / 'status.json', {'status': 'failed', 'error': 'No se pudo iniciar el proceso.'})
                self.run_lock.release()
                raise

    @staticmethod
    def _stop(proc):
        if proc.poll() is not None:
            return
        if os.name == 'nt':
            subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], capture_output=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=15)

    def _watch(self, job_id, proc, started):
        path = self.root / OUTPUT / job_id
        try:
            while proc.poll() is None:
                if time.monotonic() - started > TIMEOUT_SECONDS:
                    self._stop(proc)
                    write_json(path / 'status.json', {'status': 'failed', 'error': 'Se alcanzó el límite de 15 minutos. No hay un frente definitivo.'})
                    break
                time.sleep(.5)
            state = read_json(path / 'status.json')
            if state['status'] not in ('completed', 'failed', 'interrupted'):
                write_json(path / 'status.json', {**state, 'status': 'interrupted',
                    'error': 'El proceso se interrumpió. Checkpoints conservados; no hay un frente definitivo.'})
        finally:
            with self.lock:
                if self.active and self.active[0] == job_id:
                    self.active = None
                    self.run_lock.release()

    def status(self, job_id):
        path = job_path(self.root, job_id)
        state = read_json(path / 'status.json')
        state.update(job_id=job_id, label=LABEL, max_simulations=MAX_SIMULATIONS, generations=5)
        if self.active and self.active[0] == job_id and state['status'] not in ('completed', 'failed', 'interrupted'):
            state['elapsed_s'] = time.monotonic() - self.active[2]
        elif state['status'] in ('starting', 'running'):
            # A restarted backend never presents an abandoned provisional archive as final.
            state.update(status='interrupted', error='El backend se reinició; no hay un frente definitivo disponible.')
        if state['status'] == 'completed':
            state['result'] = read_json(path / 'result.json')
        return state

    def close(self):
        if self.active:
            _, proc, _ = self.active
            self._stop(proc)


def selected_run(job_id, solution_id, replication_id):
    """Use the frozen scenario, not possibly edited sliders or supplied sites."""
    path = job_path(service.ROOT, job_id)
    if read_json(path / 'status.json')['status'] != 'completed':
        raise ValueError('La búsqueda no terminó; no se puede simular un frente provisional')
    result = read_json(path / 'result.json')
    solution = next((s for s in result['solutions'] if s['solution_id'] == solution_id), None)
    if solution is None:
        raise ValueError('Solución rápida no encontrada')
    options = SimpleNamespace(**{**result['request'], 'method': 'MANUAL',
        'site_ids': solution['site_ids'], 'replication_id': replication_id})
    from bee_sim.project2.strategies.nsga2 import current_input_hash
    from bee_sim.project2.simulation import _engine_hash
    config = service.scenario_config(options)
    identity = result['identity']
    if (identity['config_hash'] != config.config_hash or identity['engine_hash'] != _engine_hash()
            or identity['input_hash'] != current_input_hash(config)):
        raise ValueError('El motor, datos o configuración cambiaron desde la búsqueda; inicia otra búsqueda')
    run = service.run(options)
    run.update(method='NSGA2', kind='quick_nsga_individual_run')
    run['provenance'].update(quick_job_id=job_id, quick_solution_id=solution_id,
        search_replication_ids=[1, 2], individual_replication_id=replication_id)
    # Persist individual evidence separately too; UUID avoids overwriting another run.
    write_json(path / ('individual-' + uuid.uuid4().hex + '.json'), run)
    return run

"""Smoke test opcional de Streamlit y escenarios sin recursos."""
from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(importlib.util.find_spec('streamlit'), 'Instalar requirements.txt para probar la app')
class AppTests(unittest.TestCase):
    def test_run_map_zero_resource_and_frozen_front(self):
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_file(str(ROOT / 'app/app.py')).run(timeout=60)
        self.assertFalse(at.exception)
        def run():
            next(b for b in at.button if b.label == 'Simular escenario').click().run(timeout=60)
            self.assertFalse(at.exception)
            self.assertIn('last_run', at.session_state)
        run()
        next(s for s in at.slider if s.label == 'Minuto de la jornada').set_value(10).run(timeout=60)
        self.assertFalse(at.exception)
        chart = at.get('deck_gl_json_chart')[0].proto
        self.assertIn('IconLayer', chart.json)
        self.assertNotIn('@@=data:', chart.json)
        next(s for s in at.slider if s.label == 'Disponibilidad relativa de recurso').set_value(0.).run(timeout=60)
        run()
        self.assertEqual(at.session_state['last_run']['runs'][0]['metrics']['total_resource_obtained'], 0)
        self.assertTrue(at.session_state['last_run']['runs'][0]['trips'].empty)
        next(s for s in at.selectbox if s.label == 'Propuesta de ubicaciones').select('NSGA-II guardado').run(timeout=60)
        run()
        self.assertEqual(len(at.session_state['last_run']['sites']), 5)

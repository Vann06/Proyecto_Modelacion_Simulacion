"""El entorno: disponibilidad floral y los parametros que arrastra. Paso 3."""

from ..generators.uniform import categorica

NIVELES = ("baja", "media", "alta")


class Environment:
    """A_f no es un valor que se guarde: es un estado que mueve tres perillas.

    Un nivel de disponibilidad fija a la vez la media de flores visitadas
    (mu_flowers), la escala del tiempo de busqueda (search_scale) y la escala
    del nectar por flor (nectar_scale). Notese que search_scale va en
    direccion contraria a las otras dos: un parche rico cuesta MENOS
    encontrarlo. Esa inversion es la que hace que la escasez cueste tiempo y
    no solo rendimiento.
    """

    def __init__(self, probabilidades, niveles, modo="sample"):
        self.probabilidades = list(probabilidades)
        self.niveles = niveles
        self.modo = modo

    @classmethod
    def desde_config(cls, cfg):
        env = cfg["environment"]
        return cls(env["availability_probs"], env["levels"], env["flower_availability"])

    @property
    def sortea(self):
        """True cuando el nivel es variable aleatoria; False cuando es factor."""
        return self.modo == "sample"

    def sortear_nivel(self, rng):
        """Paso 3. Devuelve 'baja', 'media' o 'alta'.

        IMPORTANTE para la reproducibilidad: cuando el escenario fija el nivel
        (FLORES-BAJA, FLORES-ALTA) esta funcion NO consume ningun uniforme,
        porque ahi la disponibilidad es un factor experimental y no una
        variable aleatoria. Eso hace que dos escenarios con la misma semilla
        recorran la secuencia de uniformes de manera distinta, cosa que hay
        que tener presente al comparar corridas viaje por viaje.
        """
        if not self.sortea:
            return self.modo
        return NIVELES[categorica(self.probabilidades, rng)]

    def parametros(self, nivel):
        """Las tres perillas que suelta el nivel."""
        try:
            return self.niveles[nivel]
        except KeyError:
            raise ValueError("nivel de disponibilidad desconocido: %r" % nivel)

    def mu_flores(self, nivel):
        return self.parametros(nivel)["mu_flowers"]

    def escala_busqueda(self, nivel):
        return self.parametros(nivel)["search_scale"]

    def escala_nectar(self, nivel):
        return self.parametros(nivel)["nectar_scale"]

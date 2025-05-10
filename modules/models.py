# modules/models.py

class Gasto:
    def __init__(self, categoria, monto, periodicidad, fecha, etapa):
        self.categoria = categoria
        self.monto = monto
        self.periodicidad = periodicidad  # 'único', 'mensual', 'anual'
        self.fecha = fecha
        self.etapa = etapa

    def calcular_total(self, periodos):
        if self.periodicidad == "único":
            return self.monto
        elif self.periodicidad == "mensual":
            return self.monto * periodos
        elif self.periodicidad == "anual":
            return self.monto * (periodos / 12)
        else:
            return 0


class Etapa:
    def __init__(self, nombre, duracion_meses):
        self.nombre = nombre
        self.duracion_meses = duracion_meses
        self.gastos = []  # Lista de objetos Gasto

    def agregar_gasto(self, gasto):
        self.gastos.append(gasto)

    def calcular_total_gastos(self):
        return sum(gasto.calcular_total(self.duracion_meses) for gasto in self.gastos)


class PlanVida:
    def __init__(self):
        self.etapas = []  # Ejemplo: "Embarazo", "Nacimiento", "Primer Año", etc.

    def agregar_etapa(self, etapa):
        self.etapas.append(etapa)

    def calcular_total_plan(self):
        return sum(etapa.calcular_total_gastos() for etapa in self.etapas)


class Ingreso:
    def __init__(self, tipo, monto, periodicidad, fecha, descripcion=""):
        self.tipo = tipo
        self.monto = monto
        self.periodicidad = periodicidad
        self.fecha = fecha
        self.descripcion = descripcion

    def calcular_total(self, duracion):
        if self.periodicidad == "único":
            return self.monto
        elif self.periodicidad == "mensual":
            return self.monto * duracion
        elif self.periodicidad == "anual":
            return self.monto * (duracion / 12)
        else:
            return 0

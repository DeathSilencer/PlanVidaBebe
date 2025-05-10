# modules/services.py

class ServiceExpense:
    def __init__(self, servicio, costo, periodicidad):
        self.servicio = servicio
        self.costo = costo
        self.periodicidad = periodicidad

    def total(self, periodos):
        if self.periodicidad == "único":
            return self.costo
        elif self.periodicidad == "mensual":
            return self.costo * periodos
        elif self.periodicidad == "anual":
            return self.costo * (periodos / 12)
        else:
            return 0

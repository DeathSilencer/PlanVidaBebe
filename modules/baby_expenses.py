# modules/baby_expenses.py

class BabyExpense:
    def __init__(self, item, costo, periodicidad, frecuencia=1):
        self.item = item
        self.costo = costo
        self.periodicidad = periodicidad
        self.frecuencia = frecuencia

    def total(self, periodos):
        if self.periodicidad == "único":
            return self.costo * self.frecuencia
        elif self.periodicidad == "mensual":
            return self.costo * self.frecuencia * periodos
        elif self.periodicidad == "anual":
            return self.costo * self.frecuencia * (periodos / 12)
        else:
            return 0

# modules/home_expenses.py

class HomeExpense:
    def __init__(self, nombre, monto, periodicidad):
        self.nombre = nombre
        self.monto = monto
        self.periodicidad = periodicidad

    def total(self, periodos):
        if self.periodicidad == "único":
            return self.monto
        elif self.periodicidad == "mensual":
            return self.monto * periodos
        elif self.periodicidad == "anual":
            return self.monto * (periodos / 12)
        else:
            return 0

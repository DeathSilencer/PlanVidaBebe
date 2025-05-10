# modules/finances.py

def calcular_inversion(initial, monthly, rate, term):
    total = initial
    monthly_rate = (1 + rate) ** (1/12) - 1
    for _ in range(term):
        total = total * (1 + monthly_rate) + monthly
    return total

def evaluar_inversion(rate_type, initial, monthly, term):
    if rate_type == '6%':
        rate = 0.06
    elif rate_type == '12%':
        rate = 0.12
    else:
        raise ValueError("Tasa no soportada, usa '6%' o '12%'.")
    return calcular_inversion(initial, monthly, rate, term)

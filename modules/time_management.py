# modules/time_management.py

import pandas as pd

def generar_cronograma_financiero():
    data = {
        "Mes": list(range(1, 61)),
        "Gastos": [0] * 60,
        "Ingresos": [0] * 60,
        "Balance": [0] * 60
    }
    df = pd.DataFrame(data)
    return df

def actualizar_cronograma(df, mes, gastos, ingresos):
    df.loc[df['Mes'] == mes, 'Gastos'] = gastos
    df.loc[df['Mes'] == mes, 'Ingresos'] = ingresos
    df.loc[df['Mes'] == mes, 'Balance'] = ingresos - gastos
    return df

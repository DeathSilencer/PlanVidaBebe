# modules/family_organization.py

def distribuir_tiempo(responsabilidades):
    total = sum(responsabilidades.values())
    if total > 24:
        raise ValueError("La suma de horas asignadas supera las 24 horas.")
    return total, responsabilidades

def planificar_horarios(responsabilidades):
    total, dist = distribuir_tiempo(responsabilidades)
    reporte = "Distribución de Horas:\n"
    for rol, horas in dist.items():
        reporte += f"{rol}: {horas} horas\n"
    reporte += f"Total asignado: {total} horas"
    return reporte

# modules/family_support.py

def total_apoyo(recursos):
    """
    Suma una lista de apoyos familiares (por ejemplo, regalos o herencias).
    recursos: lista de montos (MXN)
    """
    return sum(recursos)

def agregar_recurso(apoyos, recurso):
    """
    Agrega un nuevo recurso a la lista de apoyos.
    apoyos: lista de recursos.
    recurso: monto a agregar.
    """
    apoyos.append(recurso)
    return apoyos

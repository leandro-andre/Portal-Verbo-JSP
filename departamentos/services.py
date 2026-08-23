INVALID_DEPARTMENT_TRANSITION = "INVALID_DEPARTMENT_TRANSITION"


class DepartmentError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)


def deactivate_department(department):
    if not department.ativo:
        raise DepartmentError(
            INVALID_DEPARTMENT_TRANSITION,
            "Somente departamentos ativos podem ser inativados.",
        )

    department.ativo = False
    department.save(update_fields=["ativo"])
    return department


def reactivate_department(department):
    if department.ativo:
        raise DepartmentError(
            INVALID_DEPARTMENT_TRANSITION,
            "Somente departamentos inativos podem ser reativados.",
        )

    department.ativo = True
    department.save(update_fields=["ativo"])
    return department

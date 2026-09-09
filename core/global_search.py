from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Case, IntegerField, Q, Value, When

from church_journey.enums import ChurchStatus
from departamentos.models import Departamento
from pessoas.models import Person
from pessoas.serializers import get_photo_url
from pessoas.validators import normalize_brazilian_mobile
from usuarios.projections import ACCESS_STATUS_LABELS
from usuarios.roles import DEPARTMENT_VIEW, PEOPLE_VIEW, USER_VIEW
from usuarios.services import AccessStatus, get_access_status


MIN_QUERY_LENGTH = 2
GROUP_LIMIT = 5

CHURCH_STATUS_LABELS = {
    ChurchStatus.UNKNOWN: "Sem jornada",
    ChurchStatus.VISITOR: "Visitante",
    ChurchStatus.MEMBER: "Membro",
    ChurchStatus.INACTIVE_MEMBER: "Membro inativo",
}


def normalize_query(query):
    return str(query or "").strip()


def search_global(*, viewer, query, request=None):
    normalized_query = normalize_query(query)
    if len(normalized_query) < MIN_QUERY_LENGTH:
        return {"query": normalized_query, "groups": []}

    groups = []
    for builder in (search_people, search_users, search_departments):
        group = builder(viewer=viewer, query=normalized_query, request=request)
        if group is not None:
            groups.append(group)

    return {"query": normalized_query, "groups": groups}


def _priority_case(*, exact, startswith):
    return Case(
        When(exact, then=Value(0)),
        When(startswith, then=Value(1)),
        default=Value(2),
        output_field=IntegerField(),
    )


def _church_status_from_loaded_person(person):
    membership = getattr(person, "membership", None)
    if membership is not None:
        if membership.status == "ACTIVE":
            return ChurchStatus.MEMBER
        if membership.status == "INACTIVE":
            return ChurchStatus.INACTIVE_MEMBER
    if hasattr(person, "church_journey"):
        return ChurchStatus.VISITOR
    user_account = getattr(person, "user_account", None)
    if getattr(user_account, "status_eclesiastico", None) == "membro":
        return ChurchStatus.MEMBER
    if getattr(user_account, "status_eclesiastico", None) == "visitante":
        return ChurchStatus.VISITOR
    return ChurchStatus.UNKNOWN


def search_people(*, viewer, query, request=None):
    if not viewer.has_perm(PEOPLE_VIEW):
        return None

    phone_digits = normalize_brazilian_mobile(query)
    filters = Q(full_name__icontains=query) | Q(preferred_name__icontains=query) | Q(email__icontains=query)
    if phone_digits:
        filters |= Q(phone__icontains=phone_digits)

    exact = Q(full_name__iexact=query) | Q(preferred_name__iexact=query) | Q(email__iexact=query)
    startswith = Q(full_name__istartswith=query) | Q(preferred_name__istartswith=query) | Q(email__istartswith=query)
    if phone_digits:
        exact |= Q(phone__iexact=phone_digits)
        startswith |= Q(phone__istartswith=phone_digits)

    people = (
        Person.objects.filter(filters)
        .select_related("membership", "church_journey", "user_account")
        .annotate(search_priority=_priority_case(exact=exact, startswith=startswith))
        .order_by("search_priority", "full_name", "birth_date", "id")[:GROUP_LIMIT]
    )

    return {
        "type": "people",
        "label": "Pessoas",
        "items": [
            {
                "id": person.id,
                "title": person.display_name,
                "subtitle": CHURCH_STATUS_LABELS[_church_status_from_loaded_person(person)],
                "photo_url": get_photo_url(person, request),
                "url": f"/pessoas/{person.id}",
            }
            for person in people
        ],
    }


def search_users(*, viewer, query, request=None):
    if not viewer.has_perm(USER_VIEW):
        return None

    user_model = get_user_model()
    filters = (
        Q(username__icontains=query)
        | Q(email__icontains=query)
        | Q(person__full_name__icontains=query)
        | Q(person__preferred_name__icontains=query)
    )
    exact = (
        Q(username__iexact=query)
        | Q(email__iexact=query)
        | Q(person__full_name__iexact=query)
        | Q(person__preferred_name__iexact=query)
    )
    startswith = (
        Q(username__istartswith=query)
        | Q(email__istartswith=query)
        | Q(person__full_name__istartswith=query)
        | Q(person__preferred_name__istartswith=query)
    )
    users = (
        user_model.objects.filter(filters)
        .select_related("person")
        .annotate(search_priority=_priority_case(exact=exact, startswith=startswith))
        .order_by("search_priority", "username", "id")[:GROUP_LIMIT]
    )

    return {
        "type": "users",
        "label": "Usuarios",
        "items": [
            {
                "id": usuario.id,
                "title": usuario.username,
                "subtitle": _user_subtitle(usuario),
                "photo_url": get_photo_url(usuario.person, request) if usuario.person_id else None,
                "url": f"/usuarios/{usuario.id}",
            }
            for usuario in users
        ],
    }


def _user_subtitle(usuario):
    access_status = get_access_status(usuario)
    status_label = ACCESS_STATUS_LABELS.get(access_status, ACCESS_STATUS_LABELS[AccessStatus.BLOCKED])
    if usuario.person_id:
        return f"{usuario.person.display_name} - {status_label}"
    return status_label


def search_departments(*, viewer, query, request=None):
    if not viewer.has_perm(DEPARTMENT_VIEW):
        return None

    departments = (
        Departamento.objects.filter(Q(nome__icontains=query))
        .annotate(
            search_priority=_priority_case(
                exact=Q(nome__iexact=query),
                startswith=Q(nome__istartswith=query),
            )
        )
        .order_by("search_priority", "nome", "id")[:GROUP_LIMIT]
    )

    return {
        "type": "departments",
        "label": "Departamentos",
        "items": [
            {
                "id": department.id,
                "title": department.nome,
                "subtitle": _department_subtitle(department),
                "photo_url": None,
                "url": f"/departamentos/{department.id}",
            }
            for department in departments
        ],
    }


def _department_subtitle(department):
    description = (department.descricao or "").strip()
    if description:
        return description[:117] + "..." if len(description) > 120 else description
    return "Departamento ativo" if department.ativo else "Departamento inativo"

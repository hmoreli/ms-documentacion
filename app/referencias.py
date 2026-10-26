"""Ids de otros servicios: se verifica que existan antes de guardar."""

from rrhh_common import Referencia

FUNCIONARIO = Referencia("funcionario_id", "funcionarios", "/funcionarios/{id}", "funcionario")

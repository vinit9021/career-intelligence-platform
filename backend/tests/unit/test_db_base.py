from app.db.base import NAMING_CONVENTION, Base


def test_base_uses_predictable_constraint_names() -> None:
    assert Base.metadata.naming_convention == NAMING_CONVENTION

    assert NAMING_CONVENTION["ix"] == "ix_%(column_0_label)s"
    assert NAMING_CONVENTION["uq"] == "uq_%(table_name)s_%(column_0_name)s"
    assert NAMING_CONVENTION["ck"] == "ck_%(table_name)s_%(constraint_name)s"
    assert NAMING_CONVENTION["pk"] == "pk_%(table_name)s"
    assert NAMING_CONVENTION["fk"] == (
        "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
    )

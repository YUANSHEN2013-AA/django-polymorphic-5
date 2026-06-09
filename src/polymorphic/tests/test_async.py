"""
Tests for PolymorphicQuerySet async support.

These tests verify that aget(), afirst(), alast(), aiterator(),
acount(), aexists() methods and async iteration (async for)
correctly maintain polymorphic downcast behavior.

Supports both SQLite and PostgreSQL via the RDBMS environment variable.
"""
from django.db.models import Q
from django.test import TestCase

from polymorphic.tests.models import (
    Base,
    Model2A,
    Model2B,
    Model2C,
    Model2D,
    ModelX,
    ModelY,
)


class AsyncQuerySetTests(TestCase):
    """Tests for PolymorphicQuerySet async methods."""

    def setUp(self) -> None:
        """Create test data for async queryset tests."""
        self.a1 = Model2A.objects.create(field1="A1")
        self.b1 = Model2B.objects.create(field1="B1", field2="B2")
        self.c1 = Model2C.objects.create(field1="C1", field2="C2", field3="C3")
        self.d1 = Model2D.objects.create(field1="D1", field2="D2", field3="D3", field4="D4")

    def test_aget_returns_polymorphic_instance(self) -> None:
        """aget() returns the correct downcast polymorphic instance."""
        async def run_test() -> None:
            obj = await Model2A.objects.aget(pk=self.b1.pk)
            assert obj.__class__ is Model2B, f"Expected Model2B, got {obj.__class__}"
            assert obj.field1 == "B1"
            assert obj.field2 == "B2"

            obj2 = await Model2A.objects.aget(pk=self.c1.pk)
            assert obj2.__class__ is Model2C, f"Expected Model2C, got {obj2.__class__}"
            assert obj2.field3 == "C3"

            obj3 = await Model2A.objects.aget(pk=self.a1.pk)
            assert obj3.__class__ is Model2A, f"Expected Model2A, got {obj3.__class__}"

        import asyncio
        asyncio.run(run_test())

    def test_aget_does_not_exist(self) -> None:
        """aget() raises DoesNotExist for missing records."""
        async def run_test() -> None:
            try:
                await Model2A.objects.aget(pk=999999)
            except Model2A.DoesNotExist:
                return
            raise AssertionError("Expected DoesNotExist exception")

        import asyncio
        asyncio.run(run_test())

    def test_aget_multiple_objects_returned(self) -> None:
        """aget() raises MultipleObjectsReturned when multiple records match."""
        async def run_test() -> None:
            try:
                await Model2A.objects.aget(field1__startswith="")
            except Model2A.MultipleObjectsReturned:
                return
            raise AssertionError("Expected MultipleObjectsReturned exception")

        import asyncio
        asyncio.run(run_test())

    def test_afirst_returns_polymorphic_instance(self) -> None:
        """afirst() returns the first instance as a downcast polymorphic instance."""
        async def run_test() -> None:
            obj = await Model2A.objects.order_by("pk").afirst()
            assert obj is not None
            assert obj.__class__ is Model2A, f"Expected Model2A, got {obj.__class__}"

        import asyncio
        asyncio.run(run_test())

    def test_afirst_returns_none(self) -> None:
        """afirst() returns None for an empty queryset."""
        async def run_test() -> None:
            obj = await Model2A.objects.none().afirst()
            assert obj is None

        import asyncio
        asyncio.run(run_test())

    def test_alast_returns_polymorphic_instance(self) -> None:
        """alast() returns the last instance as a downcast polymorphic instance."""
        async def run_test() -> None:
            obj = await Model2A.objects.order_by("pk").alast()
            assert obj is not None
            assert obj.__class__ is Model2D, f"Expected Model2D, got {obj.__class__}"

        import asyncio
        asyncio.run(run_test())

    def test_alast_returns_none(self) -> None:
        """alast() returns None for an empty queryset."""
        async def run_test() -> None:
            obj = await Model2A.objects.none().alast()
            assert obj is None

        import asyncio
        asyncio.run(run_test())

    def test_aiterator_yields_polymorphic_instances(self) -> None:
        """aiterator() yields downcast polymorphic instances."""
        async def run_test() -> None:
            classes = []
            async for obj in Model2A.objects.order_by("pk").aiterator():
                classes.append(obj.__class__)
            assert classes == [Model2A, Model2B, Model2C, Model2D], (
                f"Expected [Model2A, Model2B, Model2C, Model2D], got {classes}"
            )

        import asyncio
        asyncio.run(run_test())

    def test_aiterator_with_chunk_size(self) -> None:
        """aiterator(chunk_size=N) works correctly with chunking."""
        async def run_test() -> None:
            classes = []
            async for obj in Model2A.objects.order_by("pk").aiterator(chunk_size=2):
                classes.append(obj.__class__)
            assert classes == [Model2A, Model2B, Model2C, Model2D], (
                f"Expected [Model2A, Model2B, Model2C, Model2D], got {classes}"
            )

        import asyncio
        asyncio.run(run_test())

    def test_async_for_iteration(self) -> None:
        """Async for loop over a PolymorphicQuerySet yields downcast instances."""
        async def run_test() -> None:
            classes = []
            async for obj in Model2A.objects.order_by("pk"):
                classes.append(obj.__class__)
            assert classes == [Model2A, Model2B, Model2C, Model2D], (
                f"Expected [Model2A, Model2B, Model2C, Model2D], got {classes}"
            )

        import asyncio
        asyncio.run(run_test())

    def test_acount(self) -> None:
        """acount() returns the correct number of records."""
        async def run_test() -> None:
            count = await Model2A.objects.acount()
            assert count == 4, f"Expected 4, got {count}"

        import asyncio
        asyncio.run(run_test())

    def test_aexists_true(self) -> None:
        """aexists() returns True for a non-empty queryset."""
        async def run_test() -> None:
            exists = await Model2A.objects.aexists()
            assert exists is True

        import asyncio
        asyncio.run(run_test())

    def test_aexists_false(self) -> None:
        """aexists() returns False for an empty queryset."""
        async def run_test() -> None:
            exists = await Model2A.objects.filter(pk=999999).aexists()
            assert exists is False

        import asyncio
        asyncio.run(run_test())

    def test_instance_of_with_aget(self) -> None:
        """instance_of() filtering works correctly with aget()."""
        async def run_test() -> None:
            obj = await Model2A.objects.instance_of(Model2B).order_by("pk").aget(pk=self.b1.pk)
            assert obj.__class__ is Model2B, f"Expected Model2B, got {obj.__class__}"

        import asyncio
        asyncio.run(run_test())

    def test_instance_of_with_async_for(self) -> None:
        """instance_of() filtering works correctly with async iteration."""
        async def run_test() -> None:
            classes = []
            async for obj in Model2A.objects.instance_of(Model2B).order_by("pk"):
                classes.append(obj.__class__)
            assert Model2B in classes
            assert Model2A not in classes

        import asyncio
        asyncio.run(run_test())

    def test_not_instance_of_with_async(self) -> None:
        """not_instance_of() filtering works correctly with async methods."""
        async def run_test() -> None:
            classes = []
            async for obj in Model2A.objects.not_instance_of(Model2B).order_by("pk"):
                classes.append(obj.__class__)
            assert Model2B not in classes
            assert Model2A in classes

        import asyncio
        asyncio.run(run_test())

    def test_non_polymorphic_with_aget(self) -> None:
        """non_polymorphic() returns the base class instance via aget()."""
        async def run_test() -> None:
            obj = await Model2A.objects.non_polymorphic().aget(pk=self.b1.pk)
            assert obj.__class__ is Model2A, (
                f"Expected Model2A (non-polymorphic), got {obj.__class__}"
            )

        import asyncio
        asyncio.run(run_test())

    def test_non_polymorphic_with_async_for(self) -> None:
        """non_polymorphic() with async for yields base class instances."""
        async def run_test() -> None:
            classes = set()
            async for obj in Model2A.objects.non_polymorphic():
                classes.add(obj.__class__)
            assert classes == {Model2A}, f"Expected only Model2A, got {classes}"

        import asyncio
        asyncio.run(run_test())

    def test_queryset_union_with_async(self) -> None:
        """Queryset union with polymorphic models works with async iteration."""
        Base.objects.create(field_b="B_base")
        x1 = ModelX.objects.create(field_b="X_base", field_x="X_x")
        y1 = ModelY.objects.create(field_b="Y_base", field_y="Y_y")

        async def run_test() -> None:
            qs_x = Base.objects.instance_of(ModelX).order_by("pk")
            qs_y = Base.objects.instance_of(ModelY).order_by("pk")
            union_qs = qs_x.union(qs_y).order_by("pk")

            classes = []
            async for obj in union_qs:
                classes.append(obj.__class__)
            assert ModelX in classes and ModelY in classes, (
                f"Expected ModelX and ModelY instances, got {classes}"
            )

        import asyncio
        asyncio.run(run_test())

    def test_aiterator_chunks_same_as_sync(self) -> None:
        """aiterator() yields the same objects as the sync iterator()."""
        async def run_test() -> None:
            sync_classes = [o.__class__ for o in Model2A.objects.order_by("pk").iterator()]
            async_classes = []
            async for obj in Model2A.objects.order_by("pk").aiterator():
                async_classes.append(obj.__class__)
            assert sync_classes == async_classes, (
                f"Sync classes {sync_classes} differ from async classes {async_classes}"
            )

        import asyncio
        asyncio.run(run_test())

    def test_instance_of_complex_filter_with_async(self) -> None:
        """Complex Q(instance_of) filters work correctly with async methods."""
        Base.objects.create(field_b="B_base")
        ModelX.objects.create(field_b="X_base", field_x="X_x")
        ModelY.objects.create(field_b="Y_base", field_y="Y_y")

        async def run_test() -> None:
            classes = []
            async for obj in Base.objects.filter(
                Q(instance_of=ModelX) | Q(instance_of=ModelY)
            ).order_by("pk"):
                classes.append(obj.__class__)
            assert Base not in classes
            assert ModelX in classes and ModelY in classes

        import asyncio
        asyncio.run(run_test())

    def test_acount_with_filters(self) -> None:
        """acount() with filter() returns correct count."""
        async def run_test() -> None:
            count = await Model2A.objects.filter(field2__startswith="B").acount()
            assert count == 1, f"Expected 1 (just Model2B), got {count}"

            count_all = await Model2A.objects.acount()
            assert count_all == 4, f"Expected 4, got {count_all}"

        import asyncio
        asyncio.run(run_test())

    def test_ordered_qset_alast(self) -> None:
        """alast() on an explicitly ordered queryset returns the correct last object."""
        async def run_test() -> None:
            obj = await Model2A.objects.order_by("pk").alast()
            assert obj is not None
            assert obj.pk == self.d1.pk, f"Expected pk={self.d1.pk}, got pk={obj.pk}"

            obj2 = await Model2A.objects.order_by("-pk").alast()
            assert obj2 is not None
            assert obj2.pk == self.a1.pk, f"Expected pk={self.a1.pk}, got pk={obj2.pk}"

        import asyncio
        asyncio.run(run_test())

    def test_aiterator_large_chunk(self) -> None:
        """aiterator(chunk_size=1000) with more records than chunk size works."""
        async def run_test() -> None:
            classes = []
            async for obj in Model2A.objects.order_by("pk").aiterator(chunk_size=1000):
                classes.append(obj.__class__)
            assert classes == [Model2A, Model2B, Model2C, Model2D]

        import asyncio
        asyncio.run(run_test())

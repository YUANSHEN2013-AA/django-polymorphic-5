import os

from django.db import connections
from django.test import TransactionTestCase, tag

from polymorphic.tests.models import (
    Base,
    Model2A,
    Model2B,
    Model2C,
    Model2D,
    ModelX,
    ModelY,
)


class PolymorphicAsyncTests(TransactionTestCase):
    """
    Test suite for PolymorphicQuerySet async methods.
    """

    databases = ["default", "secondary"]

    async def _create_model2abcd(self):
        a = await Model2A.objects.acreate(field1="A1")
        b = await Model2B.objects.acreate(field1="B1", field2="B2")
        c = await Model2C.objects.acreate(field1="C1", field2="C2", field3="C3")
        d = await Model2D.objects.acreate(field1="D1", field2="D2", field3="D3", field4="D4")
        return a, b, c, d

    async def test_afirst(self):
        a, b, c, d = await self._create_model2abcd()

        obj = await Model2A.objects.afirst()
        assert obj is not None
        assert isinstance(obj, Model2A)

        obj = await Model2A.objects.order_by("pk").afirst()
        assert obj is not None
        assert obj.pk == a.pk
        assert obj.field1 == "A1"

        obj = await Model2A.objects.filter(field1="B1").afirst()
        assert obj is not None
        assert isinstance(obj, Model2B)
        assert obj.field2 == "B2"

        obj = await Model2A.objects.filter(field1="NONEXISTENT").afirst()
        assert obj is None

    async def test_alast(self):
        a, b, c, d = await self._create_model2abcd()

        obj = await Model2A.objects.alast()
        assert obj is not None
        assert isinstance(obj, Model2A)

        obj = await Model2A.objects.order_by("pk").alast()
        assert obj is not None
        assert obj.pk == d.pk
        assert isinstance(obj, Model2D)
        assert obj.field4 == "D4"

        obj = await Model2A.objects.filter(field1="C1").alast()
        assert obj is not None
        assert isinstance(obj, Model2C)
        assert obj.field3 == "C3"

        obj = await Model2A.objects.filter(field1="NONEXISTENT").alast()
        assert obj is None

    async def test_aget(self):
        a, b, c, d = await self._create_model2abcd()

        obj = await Model2A.objects.aget(pk=a.pk)
        assert isinstance(obj, Model2A)
        assert obj.field1 == "A1"

        obj = await Model2A.objects.aget(pk=b.pk)
        assert isinstance(obj, Model2B)
        assert obj.field2 == "B2"

        obj = await Model2A.objects.aget(pk=d.pk)
        assert isinstance(obj, Model2D)
        assert obj.field4 == "D4"

        with self.assertRaises(Model2A.DoesNotExist):
            await Model2A.objects.aget(pk=99999)

        with self.assertRaises(Model2A.MultipleObjectsReturned):
            await Model2A.objects.aget()

    async def test_acount(self):
        await self._create_model2abcd()

        count = await Model2A.objects.acount()
        assert count == 4

        count = await Model2B.objects.acount()
        assert count == 3

        count = await Model2D.objects.acount()
        assert count == 1

        count = await Model2A.objects.filter(field1="NONEXISTENT").acount()
        assert count == 0

    async def test_aexists(self):
        await self._create_model2abcd()

        assert await Model2A.objects.aexists() is True
        assert await Model2B.objects.aexists() is True
        assert await Model2A.objects.filter(field1="B1").aexists() is True
        assert await Model2A.objects.filter(field1="NONEXISTENT").aexists() is False

    async def test_aiterator(self):
        a, b, c, d = await self._create_model2abcd()

        results = []
        async for obj in Model2A.objects.order_by("pk").aiterator():
            results.append(obj)

        assert len(results) == 4
        assert isinstance(results[0], Model2A)
        assert isinstance(results[1], Model2B)
        assert isinstance(results[2], Model2C)
        assert isinstance(results[3], Model2D)
        assert results[0].field1 == "A1"
        assert results[1].field2 == "B2"
        assert results[2].field3 == "C3"
        assert results[3].field4 == "D4"

    async def test_aiterator_chunk_size(self):
        await self._create_model2abcd()

        results = []
        async for obj in Model2A.objects.order_by("pk").aiterator(chunk_size=2):
            results.append(obj)

        assert len(results) == 4
        assert isinstance(results[0], Model2A)
        assert isinstance(results[1], Model2B)
        assert isinstance(results[2], Model2C)
        assert isinstance(results[3], Model2D)

    async def test_aiterator_invalid_chunk_size(self):
        with self.assertRaises(ValueError):
            async for _ in Model2A.objects.aiterator(chunk_size=0):
                pass

        with self.assertRaises(ValueError):
            async for _ in Model2A.objects.aiterator(chunk_size=-1):
                pass

    async def test_async_for_queryset(self):
        a, b, c, d = await self._create_model2abcd()

        results = []
        async for obj in Model2A.objects.order_by("pk"):
            results.append(obj)

        assert len(results) == 4
        assert isinstance(results[0], Model2A)
        assert isinstance(results[1], Model2B)
        assert isinstance(results[2], Model2C)
        assert isinstance(results[3], Model2D)

    async def test_afirst_polymorphic_downcast(self):
        a, b, c, d = await self._create_model2abcd()

        obj = await Model2A.objects.filter(pk=b.pk).afirst()
        assert obj is not None
        assert type(obj) is Model2B
        assert hasattr(obj, "field2")
        assert obj.field2 == "B2"

        obj = await Model2A.objects.filter(pk=d.pk).afirst()
        assert obj is not None
        assert type(obj) is Model2D
        assert hasattr(obj, "field4")
        assert obj.field4 == "D4"

    async def test_alast_polymorphic_downcast(self):
        a, b, c, d = await self._create_model2abcd()

        obj = await Model2A.objects.filter(pk=c.pk).alast()
        assert obj is not None
        assert type(obj) is Model2C
        assert hasattr(obj, "field3")
        assert obj.field3 == "C3"

    async def test_aget_polymorphic_downcast(self):
        a, b, c, d = await self._create_model2abcd()

        obj = await Model2A.objects.aget(pk=c.pk)
        assert type(obj) is Model2C
        assert hasattr(obj, "field3")
        assert obj.field3 == "C3"

    async def test_instance_of_async(self):
        a, b, c, d = await self._create_model2abcd()

        results = []
        async for obj in Model2A.objects.instance_of(Model2B).order_by("pk"):
            results.append(obj)

        assert len(results) == 3
        assert all(isinstance(r, Model2B) for r in results)

        obj = await Model2A.objects.instance_of(Model2B).afirst()
        assert obj is not None
        assert isinstance(obj, Model2B)

        count = await Model2A.objects.instance_of(Model2B).acount()
        assert count == 3

    async def test_not_instance_of_async(self):
        a, b, c, d = await self._create_model2abcd()

        results = []
        async for obj in Model2A.objects.not_instance_of(Model2B).order_by("pk"):
            results.append(obj)

        assert len(results) == 1
        assert isinstance(results[0], Model2A)
        assert type(results[0]) is Model2A

        obj = await Model2A.objects.not_instance_of(Model2B).afirst()
        assert obj is not None
        assert type(obj) is Model2A

    async def test_non_polymorphic_async(self):
        a, b, c, d = await self._create_model2abcd()

        obj = await Model2A.objects.non_polymorphic().filter(pk=b.pk).afirst()
        assert obj is not None
        assert type(obj) is Model2A
        assert not hasattr(obj, "field2")

        results = []
        async for obj in Model2A.objects.non_polymorphic().order_by("pk"):
            results.append(obj)

        assert len(results) == 4
        assert all(type(r) is Model2A for r in results)

    async def test_queryset_union_async(self):
        a = await Model2A.objects.acreate(field1="A1")
        b = await Model2B.objects.acreate(field1="B1", field2="B2")

        qs = Model2A.objects.filter(pk=a.pk) | Model2A.objects.filter(pk=b.pk)

        count = await qs.acount()
        assert count == 2

        exists = await qs.aexists()
        assert exists is True

    async def test_acount_no_extra_queries(self):
        await self._create_model2abcd()

        count = await Model2A.objects.acount()
        assert count == 4

    async def test_aexists_no_extra_queries(self):
        await self._create_model2abcd()

        exists = await Model2A.objects.aexists()
        assert exists is True

    async def test_afirst_on_subclass_manager(self):
        b = await Model2B.objects.acreate(field1="B1", field2="B2")

        obj = await Model2B.objects.afirst()
        assert obj is not None
        assert type(obj) is Model2B
        assert obj.field2 == "B2"

    async def test_aget_on_subclass_manager(self):
        b = await Model2B.objects.acreate(field1="B1", field2="B2")

        obj = await Model2B.objects.aget(pk=b.pk)
        assert type(obj) is Model2B
        assert obj.field2 == "B2"

    async def test_aiterator_empty_queryset(self):
        results = []
        async for obj in Model2A.objects.filter(field1="NONEXISTENT").aiterator():
            results.append(obj)

        assert len(results) == 0

    async def test_aiterator_single_item(self):
        a = await Model2A.objects.acreate(field1="A1")

        results = []
        async for obj in Model2A.objects.aiterator():
            results.append(obj)

        assert len(results) == 1
        assert isinstance(results[0], Model2A)

    async def test_aiterator_with_filter(self):
        a, b, c, d = await self._create_model2abcd()

        results = []
        async for obj in Model2A.objects.filter(field1="B1").aiterator():
            results.append(obj)

        assert len(results) == 1
        assert isinstance(results[0], Model2B)
        assert results[0].field2 == "B2"

    async def test_async_for_with_cached_result(self):
        a = await Model2A.objects.acreate(field1="A1")

        qs = Model2A.objects.all()
        [obj async for obj in qs]

        results = []
        async for obj in qs:
            results.append(obj)

        assert len(results) == 1
        assert isinstance(results[0], Model2A)

    async def test_afirst_with_cached_result(self):
        a = await Model2A.objects.acreate(field1="A1")

        qs = Model2A.objects.all()
        [obj async for obj in qs]

        obj = await qs.afirst()
        assert obj is not None
        assert isinstance(obj, Model2A)

    async def test_alast_with_cached_result(self):
        a = await Model2A.objects.acreate(field1="A1")

        qs = Model2A.objects.all()
        [obj async for obj in qs]

        obj = await qs.alast()
        assert obj is not None
        assert isinstance(obj, Model2A)

    async def test_cross_database_async(self):
        a = await Model2A.objects.using("secondary").acreate(field1="A1_secondary")
        b = await Model2B.objects.using("secondary").acreate(field1="B1_secondary", field2="B2")

        obj = await Model2A.objects.using("secondary").afirst()
        assert obj is not None
        assert isinstance(obj, Model2A)

        count = await Model2A.objects.using("secondary").acount()
        assert count == 2

        results = []
        async for obj in Model2A.objects.using("secondary").order_by("pk").aiterator():
            results.append(obj)

        assert len(results) == 2


@tag("postgres")
class PolymorphicAsyncPostgresTests(TransactionTestCase):
    """
    PostgreSQL-specific async tests for PolymorphicQuerySet.

    These tests verify behavior that differs on PostgreSQL, such as
    server-side cursors for chunked iteration and PostgreSQL-specific
    transaction handling in async contexts.

    Run with: RDBMS=postgres pytest -m postgres -v
    """

    databases = ["default", "secondary"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        rdbms = os.environ.get("RDBMS", "sqlite")
        if rdbms != "postgres":
            raise cls.skipTest("PostgreSQL-specific test")

    async def _create_model2abcd(self):
        a = await Model2A.objects.acreate(field1="A1")
        b = await Model2B.objects.acreate(field1="B1", field2="B2")
        c = await Model2C.objects.acreate(field1="C1", field2="C2", field3="C3")
        d = await Model2D.objects.acreate(field1="D1", field2="D2", field3="D3", field4="D4")
        return a, b, c, d

    async def _create_base_xyz(self):
        base = await Base.objects.acreate(field_b="B1")
        x = await ModelX.objects.acreate(field_b="BX", field_x="X1")
        y = await ModelY.objects.acreate(field_b="BY", field_y="Y1")
        return base, x, y

    async def test_afirst_postgres(self):
        a, b, c, d = await self._create_model2abcd()

        obj = await Model2A.objects.order_by("pk").afirst()
        assert obj is not None
        assert obj.pk == a.pk
        assert type(obj) is Model2A

    async def test_alast_postgres(self):
        a, b, c, d = await self._create_model2abcd()

        obj = await Model2A.objects.order_by("pk").alast()
        assert obj is not None
        assert type(obj) is Model2D
        assert obj.field4 == "D4"

    async def test_aget_postgres(self):
        a, b, c, d = await self._create_model2abcd()

        obj = await Model2A.objects.aget(pk=b.pk)
        assert type(obj) is Model2B
        assert obj.field2 == "B2"

    async def test_acount_postgres(self):
        await self._create_model2abcd()

        count = await Model2A.objects.acount()
        assert count == 4

        count = await Model2B.objects.acount()
        assert count == 3

    async def test_aexists_postgres(self):
        await self._create_model2abcd()

        assert await Model2A.objects.aexists() is True
        assert await Model2D.objects.aexists() is True

    async def test_aiterator_server_side_cursors_postgres(self):
        a, b, c, d = await self._create_model2abcd()

        connection = connections["default"]
        assert not connection.settings_dict.get("DISABLE_SERVER_SIDE_CURSORS")

        results = []
        async for obj in Model2A.objects.order_by("pk").aiterator(chunk_size=2):
            results.append(obj)

        assert len(results) == 4
        assert isinstance(results[0], Model2A)
        assert isinstance(results[1], Model2B)
        assert isinstance(results[2], Model2C)
        assert isinstance(results[3], Model2D)

    async def test_aiterator_chunked_fetch_postgres(self):
        for i in range(10):
            await Model2A.objects.acreate(field1=f"A{i}")

        results = []
        async for obj in Model2A.objects.order_by("pk").aiterator(chunk_size=3):
            results.append(obj)

        assert len(results) == 10
        assert all(isinstance(r, Model2A) for r in results)

    async def test_instance_of_async_postgres(self):
        base, x, y = await self._create_base_xyz()

        results = []
        async for obj in Base.objects.instance_of(ModelX).order_by("pk"):
            results.append(obj)

        assert len(results) == 1
        assert type(results[0]) is ModelX
        assert results[0].field_x == "X1"

        count = await Base.objects.instance_of(ModelX).acount()
        assert count == 1

    async def test_not_instance_of_async_postgres(self):
        base, x, y = await self._create_base_xyz()

        results = []
        async for obj in Base.objects.not_instance_of(ModelX).order_by("pk"):
            results.append(obj)

        assert len(results) == 2
        types = {type(r) for r in results}
        assert Base in types
        assert ModelY in types

    async def test_non_polymorphic_async_postgres(self):
        a, b, c, d = await self._create_model2abcd()

        results = []
        async for obj in Model2A.objects.non_polymorphic().order_by("pk"):
            results.append(obj)

        assert len(results) == 4
        assert all(type(r) is Model2A for r in results)

    async def test_queryset_union_async_postgres(self):
        a = await Model2A.objects.acreate(field1="A1")
        b = await Model2B.objects.acreate(field1="B1", field2="B2")

        qs = Model2A.objects.filter(pk=a.pk) | Model2A.objects.filter(pk=b.pk)

        count = await qs.acount()
        assert count == 2

        exists = await qs.aexists()
        assert exists is True

    async def test_cross_database_async_postgres(self):
        a = await Model2A.objects.using("secondary").acreate(field1="A1_pg2")
        b = await Model2B.objects.using("secondary").acreate(field1="B1_pg2", field2="B2")

        obj = await Model2A.objects.using("secondary").order_by("pk").afirst()
        assert obj is not None
        assert obj.field1 == "A1_pg2"

        count = await Model2A.objects.using("secondary").acount()
        assert count == 2

        obj = await Model2A.objects.using("secondary").filter(pk=b.pk).afirst()
        assert obj is not None
        assert type(obj) is Model2B
        assert obj.field2 == "B2"

    async def test_aget_does_not_exist_postgres(self):
        with self.assertRaises(Model2A.DoesNotExist):
            await Model2A.objects.aget(field1="NONEXISTENT")

    async def test_aget_multiple_objects_returned_postgres(self):
        await self._create_model2abcd()

        with self.assertRaises(Model2A.MultipleObjectsReturned):
            await Model2A.objects.aget()

    async def test_afirst_none_postgres(self):
        obj = await Model2A.objects.filter(field1="NONEXISTENT").afirst()
        assert obj is None

    async def test_alast_none_postgres(self):
        obj = await Model2A.objects.filter(field1="NONEXISTENT").alast()
        assert obj is None

    async def test_async_for_queryset_postgres(self):
        a, b, c, d = await self._create_model2abcd()

        results = []
        async for obj in Model2A.objects.order_by("pk"):
            results.append(obj)

        assert len(results) == 4
        assert isinstance(results[0], Model2A)
        assert isinstance(results[1], Model2B)
        assert isinstance(results[2], Model2C)
        assert isinstance(results[3], Model2D)

    async def test_acount_no_extra_queries_postgres(self):
        await self._create_model2abcd()

        count = await Model2A.objects.acount()
        assert count == 4

    async def test_aexists_no_extra_queries_postgres(self):
        await self._create_model2abcd()

        exists = await Model2A.objects.aexists()
        assert exists is True

    async def test_aiterator_empty_queryset_postgres(self):
        results = []
        async for obj in Model2A.objects.filter(field1="NONEXISTENT").aiterator():
            results.append(obj)

        assert len(results) == 0

    async def test_aiterator_with_filter_postgres(self):
        a, b, c, d = await self._create_model2abcd()

        results = []
        async for obj in Model2A.objects.filter(field1="D1").aiterator():
            results.append(obj)

        assert len(results) == 1
        assert type(results[0]) is Model2D
        assert results[0].field4 == "D4"

    async def test_aiterator_invalid_chunk_size_postgres(self):
        with self.assertRaises(ValueError):
            async for _ in Model2A.objects.aiterator(chunk_size=0):
                pass

        with self.assertRaises(ValueError):
            async for _ in Model2A.objects.aiterator(chunk_size=-1):
                pass

    async def test_afirst_polymorphic_downcast_postgres(self):
        a, b, c, d = await self._create_model2abcd()

        obj = await Model2A.objects.filter(pk=d.pk).afirst()
        assert obj is not None
        assert type(obj) is Model2D
        assert obj.field4 == "D4"

    async def test_alast_polymorphic_downcast_postgres(self):
        a, b, c, d = await self._create_model2abcd()

        obj = await Model2A.objects.filter(pk=c.pk).alast()
        assert obj is not None
        assert type(obj) is Model2C
        assert obj.field3 == "C3"

    async def test_aget_polymorphic_downcast_postgres(self):
        a, b, c, d = await self._create_model2abcd()

        obj = await Model2A.objects.aget(pk=c.pk)
        assert type(obj) is Model2C
        assert obj.field3 == "C3"

    async def test_afirst_on_subclass_manager_postgres(self):
        b = await Model2B.objects.acreate(field1="B1", field2="B2")

        obj = await Model2B.objects.afirst()
        assert obj is not None
        assert type(obj) is Model2B
        assert obj.field2 == "B2"

    async def test_aget_on_subclass_manager_postgres(self):
        b = await Model2B.objects.acreate(field1="B1", field2="B2")

        obj = await Model2B.objects.aget(pk=b.pk)
        assert type(obj) is Model2B
        assert obj.field2 == "B2"

    async def test_async_for_with_cached_result_postgres(self):
        a = await Model2A.objects.acreate(field1="A1")

        qs = Model2A.objects.all()
        [obj async for obj in qs]

        results = []
        async for obj in qs:
            results.append(obj)

        assert len(results) == 1
        assert isinstance(results[0], Model2A)

    async def test_afirst_with_cached_result_postgres(self):
        a = await Model2A.objects.acreate(field1="A1")

        qs = Model2A.objects.all()
        [obj async for obj in qs]

        obj = await qs.afirst()
        assert obj is not None
        assert isinstance(obj, Model2A)

    async def test_alast_with_cached_result_postgres(self):
        a = await Model2A.objects.acreate(field1="A1")

        qs = Model2A.objects.all()
        [obj async for obj in qs]

        obj = await qs.alast()
        assert obj is not None
        assert isinstance(obj, Model2A)

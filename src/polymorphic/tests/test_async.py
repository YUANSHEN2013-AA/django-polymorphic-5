from __future__ import annotations

import asyncio

from django.db.models import Count
from django.test import TransactionTestCase

from polymorphic.tests.models import (
    Model2A,
    Model2B,
    Model2C,
    Model2D,
    ModelExtraA,
    ModelExtraB,
    ModelExtraC,
    ModelShow1,
    ModelShow2,
    ModelShow3,
    One2OneRelatingModel,
    One2OneRelatingModelDerived,
    PlainA,
    PlainB,
    PlainC,
    RelationA,
    RelationB,
    RelationBase,
)


class PolymorphicAsyncTests(TransactionTestCase):
    def test_aiterator(self):
        asyncio.run(self._test_aiterator())

    async def _test_aiterator(self):
        Model2A.objects.create(field1="A1")
        Model2B.objects.create(field1="B1", field2="B2")
        Model2C.objects.create(field1="C1", field2="C2", field3="C3")

        results: list[Model2A] = []
        async for obj in Model2A.objects.aiterator(chunk_size=2):
            results.append(obj)

        assert len(results) == 3
        assert set(type(obj).__name__ for obj in results) == {
            "Model2A",
            "Model2B",
            "Model2C",
        }

    def test_async_for_loop(self):
        asyncio.run(self._test_async_for_loop())

    async def _test_async_for_loop(self):
        Model2A.objects.create(field1="A1")
        Model2B.objects.create(field1="B1", field2="B2")
        Model2C.objects.create(field1="C1", field2="C2", field3="C3")

        results: list[Model2A] = []
        async for obj in Model2A.objects.all():
            results.append(obj)

        assert len(results) == 3
        assert set(type(obj).__name__ for obj in results) == {
            "Model2A",
            "Model2B",
            "Model2C",
        }

    def test_aget(self):
        asyncio.run(self._test_aget())

    async def _test_aget(self):
        a = await Model2A.objects.acreate(field1="A1")
        b = await Model2B.objects.acreate(field1="B1", field2="B2")

        result = await Model2A.objects.aget(pk=a.pk)
        assert type(result).__name__ == "Model2A"
        assert result.field1 == "A1"

        result_b = await Model2A.objects.aget(pk=b.pk)
        assert type(result_b).__name__ == "Model2B"
        assert result_b.field1 == "B1"
        assert result_b.field2 == "B2"

    def test_aget_not_found(self):
        asyncio.run(self._test_aget_not_found())

    async def _test_aget_not_found(self):
        with self.assertRaises(Model2A.DoesNotExist):
            await Model2A.objects.aget(pk=99999)

    def test_afirst(self):
        asyncio.run(self._test_afirst())

    async def _test_afirst(self):
        a = await Model2A.objects.acreate(field1="A1")
        b = await Model2B.objects.acreate(field1="B1", field2="B2")
        c = await Model2C.objects.acreate(field1="C1", field2="C2", field3="C3")

        result = await Model2A.objects.order_by("pk").afirst()
        assert result is not None
        assert type(result).__name__ == "Model2A"
        assert result.pk == a.pk

        result = await Model2A.objects.filter(field1="B1").afirst()
        assert result is not None
        assert type(result).__name__ == "Model2B"
        assert result.pk == b.pk

        result_none = await Model2A.objects.filter(pk=99999).afirst()
        assert result_none is None

    def test_alast(self):
        asyncio.run(self._test_alast())

    async def _test_alast(self):
        a = await Model2A.objects.acreate(field1="A1")
        b = await Model2B.objects.acreate(field1="B1", field2="B2")
        c = await Model2C.objects.acreate(field1="C1", field2="C2", field3="C3")

        result = await Model2A.objects.order_by("pk").alast()
        assert result is not None
        assert type(result).__name__ == "Model2C"
        assert result.pk == c.pk

        result = await Model2A.objects.filter(field1="B1").alast()
        assert result is not None
        assert type(result).__name__ == "Model2B"
        assert result.pk == b.pk

        result_none = await Model2A.objects.filter(pk=99999).alast()
        assert result_none is None

    def test_acount(self):
        asyncio.run(self._test_acount())

    async def _test_acount(self):
        await Model2A.objects.acreate(field1="A1")
        await Model2B.objects.acreate(field1="B1", field2="B2")
        await Model2C.objects.acreate(field1="C1", field2="C2", field3="C3")

        count = await Model2A.objects.acount()
        assert count == 3

        count_filtered = await Model2A.objects.filter(field1="B1").acount()
        assert count_filtered == 1

    def test_aexists(self):
        asyncio.run(self._test_aexists())

    async def _test_aexists(self):
        await Model2A.objects.acreate(field1="A1")

        exists = await Model2A.objects.aexists()
        assert exists is True

        no_exists = await Model2A.objects.filter(pk=99999).aexists()
        assert no_exists is False

    def test_instance_of_async(self):
        asyncio.run(self._test_instance_of_async())

    async def _test_instance_of_async(self):
        await Model2A.objects.acreate(field1="A1")
        await Model2B.objects.acreate(field1="B1", field2="B2")
        await Model2C.objects.acreate(field1="C1", field2="C2", field3="C3")

        results: list[Model2A] = []
        async for obj in Model2A.objects.instance_of(Model2B).aiterator():
            results.append(obj)

        assert len(results) == 2
        assert all(type(obj).__name__ in ("Model2B", "Model2C") for obj in results)

    def test_not_instance_of_async(self):
        asyncio.run(self._test_not_instance_of_async())

    async def _test_not_instance_of_async(self):
        await Model2A.objects.acreate(field1="A1")
        await Model2B.objects.acreate(field1="B1", field2="B2")
        await Model2C.objects.acreate(field1="C1", field2="C2", field3="C3")

        results: list[Model2A] = []
        async for obj in Model2A.objects.not_instance_of(Model2B).aiterator():
            results.append(obj)

        assert len(results) == 1
        assert all(type(obj).__name__ == "Model2A" for obj in results)

    def test_non_polymorphic_async(self):
        asyncio.run(self._test_non_polymorphic_async())

    async def _test_non_polymorphic_async(self):
        await Model2A.objects.acreate(field1="A1")
        await Model2B.objects.acreate(field1="B1", field2="B2")

        results: list[Model2A] = []
        async for obj in Model2A.objects.non_polymorphic().aiterator():
            results.append(obj)

        assert len(results) == 2
        assert all(type(obj).__name__ == "Model2A" for obj in results)

    def test_queryset_union_async(self):
        asyncio.run(self._test_queryset_union_async())

    async def _test_queryset_union_async(self):
        a = await Model2A.objects.acreate(field1="A1")
        b = await Model2B.objects.acreate(field1="B1", field2="B2")

        qs1 = Model2A.objects.filter(pk=a.pk)
        qs2 = Model2A.objects.filter(pk=b.pk)
        union_qs = qs1.union(qs2)

        results: list[Model2A] = []
        async for obj in union_qs.aiterator():
            results.append(obj)

        assert len(results) == 2
        pks = {obj.pk for obj in results}
        assert pks == {a.pk, b.pk}

    def test_deep_inheritance_async(self):
        asyncio.run(self._test_deep_inheritance_async())

    async def _test_deep_inheritance_async(self):
        await Model2A.objects.acreate(field1="A1")
        await Model2B.objects.acreate(field1="B1", field2="B2")
        await Model2C.objects.acreate(field1="C1", field2="C2", field3="C3")
        await Model2D.objects.acreate(field1="D1", field2="D2", field3="D3", field4="D4")

        results: list[Model2A] = []
        async for obj in Model2A.objects.aiterator():
            results.append(obj)

        assert len(results) == 4
        assert set(type(obj).__name__ for obj in results) == {
            "Model2A",
            "Model2B",
            "Model2C",
            "Model2D",
        }

    def test_aiterator_chunking(self):
        asyncio.run(self._test_aiterator_chunking())

    async def _test_aiterator_chunking(self):
        for i in range(10):
            await Model2A.objects.acreate(field1=f"A{i}")

        results: list[Model2A] = []
        async for obj in Model2A.objects.aiterator(chunk_size=3):
            results.append(obj)

        assert len(results) == 10
        assert all(type(obj).__name__ == "Model2A" for obj in results)

    def test_aiterator_no_results(self):
        asyncio.run(self._test_aiterator_no_results())

    async def _test_aiterator_no_results(self):
        results: list[Model2A] = []
        async for obj in Model2A.objects.aiterator():
            results.append(obj)

        assert len(results) == 0

    def test_async_annotate(self):
        asyncio.run(self._test_async_annotate())

    async def _test_async_annotate(self):
        a = await Model2A.objects.acreate(field1="A1")
        b = await Model2B.objects.acreate(field1="B1", field2="B2")

        qs = Model2A.objects.annotate(count=Count("pk"))

        results: list[Model2A] = []
        async for obj in qs.order_by("pk").aiterator():
            results.append(obj)

        assert len(results) == 2
        assert results[0].count == 1
        assert results[1].count == 1

    def test_aiterator_with_extra_models(self):
        asyncio.run(self._test_aiterator_with_extra_models())

    async def _test_aiterator_with_extra_models(self):
        await ModelExtraA.objects.acreate(field1="E1")
        await ModelExtraB.objects.acreate(field1="E2", field2="EB2")
        await ModelExtraC.objects.acreate(field1="E3", field2="EC2", field3="EC3")

        results: list[ModelExtraA] = []
        async for obj in ModelExtraA.objects.aiterator():
            results.append(obj)

        assert len(results) == 3
        assert set(type(obj).__name__ for obj in results) == {
            "ModelExtraA",
            "ModelExtraB",
            "ModelExtraC",
        }

    def test_aiterator_with_showfield_models(self):
        asyncio.run(self._test_aiterator_with_showfield_models())

    async def _test_aiterator_with_showfield_models(self):
        await ModelShow1.objects.acreate(field1="S1")
        await ModelShow2.objects.acreate(field1="S2")
        await ModelShow3.objects.acreate(field1="S3")

        count = await ModelShow1.objects.acount()
        assert count == 1

    def test_async_cross_types_aget(self):
        asyncio.run(self._test_async_cross_types_aget())

    async def _test_async_cross_types_aget(self):
        await ModelExtraA.objects.acreate(field1="EA1")
        b = await ModelExtraB.objects.acreate(field1="EB1", field2="EB2")
        c = await ModelExtraC.objects.acreate(field1="EC1", field2="EC2", field3="EC3")

        result_a = await ModelExtraA.objects.aget(field1="EA1")
        assert type(result_a).__name__ == "ModelExtraA"

        result_b = await ModelExtraA.objects.aget(pk=b.pk)
        assert type(result_b).__name__ == "ModelExtraB"
        assert result_b.field2 == "EB2"

        result_c = await ModelExtraA.objects.aget(pk=c.pk)
        assert type(result_c).__name__ == "ModelExtraC"
        assert result_c.field3 == "EC3"

    def test_afirst_returns_correct_type(self):
        asyncio.run(self._test_afirst_returns_correct_type())

    async def _test_afirst_returns_correct_type(self):
        await Model2B.objects.acreate(field1="B1", field2="B2")
        await Model2A.objects.acreate(field1="A1")

        result = await Model2A.objects.order_by("pk").afirst()
        assert result is not None
        assert type(result).__name__ == "Model2B"
        assert result.field2 == "B2"
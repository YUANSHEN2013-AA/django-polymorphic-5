import pytest
from django.db import connection
from django.test import TransactionTestCase

from polymorphic.tests.models import Model2A, Model2B, Model2C, Model2D


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class AsyncQuerySetTests(TransactionTestCase):
    async def test_aget(self):
        a = await Model2A.objects.acreate(field1="A1")
        b = await Model2B.objects.acreate(field1="A2", field2="B2")
        c = await Model2C.objects.acreate(field1="A3", field2="B3", field3="C3")

        obj_a = await Model2A.objects.aget(field1="A1")
        assert type(obj_a) is Model2A

        obj_b = await Model2A.objects.aget(field1="A2")
        assert type(obj_b) is Model2B
        assert obj_b.field2 == "B2"

        obj_c = await Model2A.objects.aget(field1="A3")
        assert type(obj_c) is Model2C
        assert obj_c.field3 == "C3"

    async def test_afirst_alast(self):
        await Model2A.objects.acreate(field1="A1")
        await Model2B.objects.acreate(field1="A2", field2="B2")
        await Model2C.objects.acreate(field1="A3", field2="B3", field3="C3")

        first = await Model2A.objects.order_by("field1").afirst()
        assert type(first) is Model2A
        assert first.field1 == "A1"

        last = await Model2A.objects.order_by("field1").alast()
        assert type(last) is Model2C
        assert last.field1 == "A3"

    async def test_aiterator(self):
        await Model2A.objects.acreate(field1="A1")
        await Model2B.objects.acreate(field1="A2", field2="B2")
        await Model2C.objects.acreate(field1="A3", field2="B3", field3="C3")

        results = []
        async for obj in Model2A.objects.order_by("field1").aiterator():
            results.append(obj)

        assert len(results) == 3
        assert type(results[0]) is Model2A
        assert type(results[1]) is Model2B
        assert type(results[2]) is Model2C

    async def test_acount_aexists(self):
        await Model2A.objects.acreate(field1="A1")
        await Model2B.objects.acreate(field1="A2", field2="B2")

        count = await Model2A.objects.acount()
        assert count == 2

        exists = await Model2A.objects.filter(field1="A2").aexists()
        assert exists is True

        not_exists = await Model2A.objects.filter(field1="A3").aexists()
        assert not_exists is False

    async def test_instance_of_async(self):
        await Model2A.objects.acreate(field1="A1")
        await Model2B.objects.acreate(field1="A2", field2="B2")
        await Model2C.objects.acreate(field1="A3", field2="B3", field3="C3")

        results = [obj async for obj in Model2A.objects.instance_of(Model2B).order_by("field1")]
        assert len(results) == 2
        assert type(results[0]) is Model2B
        assert type(results[1]) is Model2C

    async def test_not_instance_of_async(self):
        await Model2A.objects.acreate(field1="A1")
        await Model2B.objects.acreate(field1="A2", field2="B2")
        await Model2C.objects.acreate(field1="A3", field2="B3", field3="C3")

        results = [obj async for obj in Model2A.objects.not_instance_of(Model2B).order_by("field1")]
        assert len(results) == 1
        assert type(results[0]) is Model2A

    async def test_non_polymorphic_async(self):
        await Model2A.objects.acreate(field1="A1")
        await Model2B.objects.acreate(field1="A2", field2="B2")

        results = [obj async for obj in Model2A.objects.non_polymorphic().order_by("field1")]
        assert len(results) == 2
        assert type(results[0]) is Model2A
        assert type(results[1]) is Model2A

    async def test_union_async(self):
        await Model2A.objects.acreate(field1="A1")
        await Model2B.objects.acreate(field1="A2", field2="B2")
        await Model2C.objects.acreate(field1="A3", field2="B3", field3="C3")

        qs1 = Model2A.objects.filter(field1="A1")
        qs2 = Model2A.objects.filter(field1="A3")

        qs_union = qs1.union(qs2).order_by("field1")
        
        results = [obj async for obj in qs_union]
        assert len(results) == 2
        assert type(results[0]) is Model2A
        assert type(results[1]) is Model2C

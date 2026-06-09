from asgiref.sync import async_to_sync
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from polymorphic.tests.models import Base, Model2A, Model2B, Model2C, Model2D, ModelX, ModelY


class TestAsyncPolymorphicQuerySet(TestCase):
    def create_model2abcd(self):
        a = Model2A.objects.create(field1="A1")
        b = Model2B.objects.create(field1="B1", field2="B2")
        c = Model2C.objects.create(field1="C1", field2="C2", field3="C3")
        d = Model2D.objects.create(field1="D1", field2="D2", field3="D3", field4="D4")
        return a, b, c, d

    def warm_content_type_cache(self) -> None:
        for model in (Model2A, Model2B, Model2C, Model2D, Base, ModelX, ModelY):
            ContentType.objects.get_for_model(model, for_concrete_model=False)
            ContentType.objects.get_for_model(model, for_concrete_model=True)

    def test_async_queryset_methods_preserve_polymorphic_behavior(self):
        self.create_model2abcd()
        Base.objects.create(field_b="B0")
        ModelX.objects.create(field_b="B1", field_x="X1")
        ModelY.objects.create(field_b="B2", field_y="Y1")

        async def run():
            found = await Model2A.objects.aget(field1="C1")
            first = await Model2A.objects.instance_of(Model2B).order_by("pk").afirst()
            last = await Model2A.objects.order_by("pk").alast()
            non_polymorphic_last = await Model2A.objects.non_polymorphic().order_by("pk").alast()
            count = await Model2A.objects.instance_of(Model2B).acount()
            exists = await Model2A.objects.not_instance_of(Model2B).aexists()
            missing_exists = await Model2A.objects.filter(field1="missing").aexists()
            missing_first = await Model2A.objects.filter(field1="missing").afirst()
            union_items = [
                item
                async for item in Base.objects.instance_of(ModelX)
                .union(Base.objects.instance_of(ModelY))
                .order_by("field_b")
                .aiterator(chunk_size=1)
            ]
            return {
                "found": found,
                "first": first,
                "last": last,
                "non_polymorphic_last": non_polymorphic_last,
                "count": count,
                "exists": exists,
                "missing_exists": missing_exists,
                "missing_first": missing_first,
                "union_items": union_items,
            }

        result = async_to_sync(run)()

        assert isinstance(result["found"], Model2C)
        assert isinstance(result["first"], Model2B)
        assert isinstance(result["last"], Model2D)
        assert type(result["non_polymorphic_last"]) is Model2A
        assert result["count"] == 3
        assert result["exists"] is True
        assert result["missing_exists"] is False
        assert result["missing_first"] is None
        assert [obj.__class__ for obj in result["union_items"]] == [ModelX, ModelY]

    def test_async_query_counts_match_sync_counterparts(self):
        self.create_model2abcd()
        self.warm_content_type_cache()

        with CaptureQueriesContext(connection) as sync_get_queries:
            sync_get = Model2A.objects.get(field1="D1")
        with CaptureQueriesContext(connection) as async_get_queries:
            async_get = async_to_sync(Model2A.objects.aget)(field1="D1")

        assert isinstance(sync_get, Model2D)
        assert isinstance(async_get, Model2D)
        assert len(async_get_queries) == len(sync_get_queries)

        with CaptureQueriesContext(connection) as sync_count_queries:
            sync_count = Model2A.objects.instance_of(Model2B).count()
        with CaptureQueriesContext(connection) as async_count_queries:
            async_count = async_to_sync(Model2A.objects.instance_of(Model2B).acount)()

        assert sync_count == 3
        assert async_count == sync_count
        assert len(async_count_queries) == len(sync_count_queries)

        with CaptureQueriesContext(connection) as sync_exists_queries:
            sync_exists = Model2A.objects.filter(field1="D1").exists()
        with CaptureQueriesContext(connection) as async_exists_queries:
            async_exists = async_to_sync(Model2A.objects.filter(field1="D1").aexists)()

        assert async_exists is sync_exists is True
        assert len(async_exists_queries) == len(sync_exists_queries)

    def test_async_iterator_chunking_matches_sync_iterator_queries(self):
        for i in range(250):
            Model2B.objects.create(field1=f"B1-{i}", field2=f"B2-{i}")
        for i in range(1000):
            Model2C.objects.create(
                field1=f"C1-{i + 250}", field2=f"C2-{i + 250}", field3=f"C3-{i + 250}"
            )
        for i in range(2000):
            Model2D.objects.create(
                field1=f"D1-{i + 1250}",
                field2=f"D2-{i + 1250}",
                field3=f"D3-{i + 1250}",
                field4=f"D4-{i + 1250}",
            )

        self.warm_content_type_cache()
        ContentType.objects.clear_cache()
        self.warm_content_type_cache()

        with CaptureQueriesContext(connection) as sync_iterator_queries:
            sync_types = [
                obj.__class__
                for obj in Model2A.objects.order_by("pk").iterator(chunk_size=1000)
            ]

        ContentType.objects.clear_cache()
        self.warm_content_type_cache()

        async def iterate_async():
            return [
                obj.__class__
                async for obj in Model2A.objects.order_by("pk").aiterator(chunk_size=1000)
            ]

        with CaptureQueriesContext(connection) as async_iterator_queries:
            async_types = async_to_sync(iterate_async)()

        assert async_types == sync_types
        assert len(async_iterator_queries) == len(sync_iterator_queries)


class TestAsyncPolymorphicQuerySetMultipleDatabases(TestCase):
    databases = ["default", "secondary"]

    def test_async_methods_respect_database_aliases(self):
        Model2A.objects.db_manager("secondary").create(field1="A1")
        Model2C.objects.db_manager("secondary").create(field1="C1", field2="C2", field3="C3")
        Base.objects.db_manager("secondary").create(field_b="B0")
        ModelX.objects.db_manager("secondary").create(field_b="B1", field_x="X1")
        ModelY.objects.db_manager("secondary").create(field_b="B2", field_y="Y1")

        async def run():
            first = await Model2A.objects.db_manager("secondary").order_by("pk").afirst()
            last = await Model2A.objects.db_manager("secondary").order_by("pk").alast()
            found = await Model2A.objects.db_manager("secondary").instance_of(Model2C).aget(
                field1="C1"
            )
            non_polymorphic_last = await (
                Model2A.objects.db_manager("secondary")
                .non_polymorphic()
                .order_by("pk")
                .alast()
            )
            union_items = [
                item
                async for item in Base.objects.db_manager("secondary")
                .instance_of(ModelX)
                .union(Base.objects.db_manager("secondary").instance_of(ModelY))
                .order_by("field_b")
                .aiterator(chunk_size=1)
            ]
            return {
                "first": first,
                "last": last,
                "found": found,
                "non_polymorphic_last": non_polymorphic_last,
                "union_items": union_items,
            }

        self.assertNumQueries(0, lambda: async_to_sync(run)())
        result = async_to_sync(run)()

        assert result["first"] is not None
        assert result["last"] is not None
        assert result["non_polymorphic_last"] is not None
        assert result["first"]._state.db == "secondary"
        assert result["last"]._state.db == "secondary"
        assert result["found"]._state.db == "secondary"
        assert result["non_polymorphic_last"]._state.db == "secondary"
        assert isinstance(result["found"], Model2C)
        assert type(result["non_polymorphic_last"]) is Model2A
        assert [obj.__class__ for obj in result["union_items"]] == [ModelX, ModelY]
        assert {obj._state.db for obj in result["union_items"]} == {"secondary"}

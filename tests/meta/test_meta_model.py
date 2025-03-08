# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import asyncio
import pytest
import pytest_asyncio

from unittest import IsolatedAsyncioTestCase

from uno.apps.meta.models import MetaBase
from uno.config import settings


class TestMetaBaseModel(IsolatedAsyncioTestCase):

    def setUp(self):
        self.loop = asyncio.get_event_loop()
        asyncio.set_event_loop(self.loop)

    def test_meta_record_model_structure(self):
        assert "id" in MetaBase.model_fields.keys()
        assert "meta_type_id" in MetaBase.model_fields.keys()

    def test_meta_record_fields(self):
        meta_record = MetaBase(
            id="01JNH7SBRV60R5RC1G61E30C1G",
            meta_type_id="01JNH7SBRV60R5RC1G61E30C1G",
        )
        assert meta_record.id == "01JNH7SBRV60R5RC1G61E30C1G"
        assert meta_record.meta_type_id == "01JNH7SBRV60R5RC1G61E30C1G"

    def test_meta_record_model_set_display_names(self):
        assert MetaBase.table_name == "meta"
        assert MetaBase.display_name == "Meta"
        assert MetaBase.display_name_plural == "Metas"

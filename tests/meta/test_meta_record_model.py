# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import asyncio
import pytest
import pytest_asyncio

from unittest import IsolatedAsyncioTestCase

from uno.apps.meta.models import MetaRecord
from uno.config import settings


class TestMetaRecordModel(IsolatedAsyncioTestCase):

    def setUp(self):
        self.loop = asyncio.get_event_loop()
        asyncio.set_event_loop(self.loop)

    def test_meta_record_model_structure(self):
        assert "id" in MetaRecord.model_fields.keys()
        assert "meta_type_id" in MetaRecord.model_fields.keys()

    def test_meta_record_fields(self):
        meta_record = MetaRecord(
            id="01JNH7SBRV60R5RC1G61E30C1G",
            meta_type_id="01JNH7SBRV60R5RC1G61E30C1G",
        )
        assert meta_record.id == "01JNH7SBRV60R5RC1G61E30C1G"
        assert meta_record.meta_type_id == "01JNH7SBRV60R5RC1G61E30C1G"

    def test_meta_record_model_set_display_names(self):
        assert MetaRecord.table_name == "meta_record"
        assert MetaRecord.display_name == "Meta Record"
        assert MetaRecord.display_name_plural == "Meta Records"

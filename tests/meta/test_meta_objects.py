# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import asyncio
import pytest
import pytest_asyncio

from unittest import IsolatedAsyncioTestCase

from uno.meta.models import MetaRecordModel
from uno.settings import uno_settings


class TestMetaBaseModel(IsolatedAsyncioTestCase):

    def setUp(self):
        self.loop = asyncio.get_event_loop()
        asyncio.set_event_loop(self.loop)

    def test_meta_record_model_structure(self):
        assert "id" in MetaRecordModel.__table__.columns.keys()
        assert "meta_type_id" in MetaRecordModel.__table__.columns.keys()

    def test_meta_record_fields(self):
        meta_record = MetaRecordModel(
            id="01JNH7SBRV60R5RC1G61E30C1G",
            meta_type_id="01JNH7SBRV60R5RC1G61E30C1G",
        )
        assert meta_record.id == "01JNH7SBRV60R5RC1G61E30C1G"
        assert meta_record.meta_type_id == "01JNH7SBRV60R5RC1G61E30C1G"

    def test_meta_record_model_set_display_names(self):
        assert MetaRecordModel.__tablename__ == "meta_record"

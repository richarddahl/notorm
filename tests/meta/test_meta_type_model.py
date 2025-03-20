# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import asyncio
import pytest
import pytest_asyncio

from unittest import IsolatedAsyncioTestCase

from uno.apps.meta.models import MetaType
from uno.config import settings


class TestMetaTypeModel(IsolatedAsyncioTestCase):

    def setUp(self):
        self.loop = asyncio.get_event_loop()
        asyncio.set_event_loop(self.loop)

    def test_meta_type_model_structure(self):
        assert "id" in MetaType.model_fields.keys()

    def test_minimal_user_model_fields(self):
        meta_type = MetaType(id="meta_type")
        assert meta_type.id == "meta_type"

    def test_meta_type_model_set_display_names(self):
        assert MetaType.table_name == "meta_type"
        assert MetaType.display_name == "Meta Type"
        assert MetaType.display_name_plural == "Meta Types"

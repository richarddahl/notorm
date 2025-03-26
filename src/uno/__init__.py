# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.pkgs.attr import models as attr_models
from uno.pkgs.auth import models as auth_models
from uno.pkgs.fltr import models as fltr_models
from uno.pkgs.meta import models as meta_models

# from uno.pkgs.msg import models as msg_models
# from uno.pkgs.rprt import models as rpt_models
# from uno.pkgs.val import models as val_models
# from uno.pkgs.wkflw import models as wkflw_models
from uno.utilities import import_from_path
from uno.config import settings


if settings.APP_PATH:
    for pkg in settings.LOAD_PACKAGES:
        file_path = f"{settings.APP_PATH}/{pkg.replace('.', '/')}/models.py"
        mod_obj = import_from_path(pkg, file_path)

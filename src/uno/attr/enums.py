# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import enum


# Enumerations
class AttributePurpose(str, enum.Enum):
    SCOPE = "Scope"
    POSTURE = "Posture"
    DESIGN = "Design"
    VULNERABILITY = "Vulnerability"
    INFORMATION = "Information"
    RISK = "Risk"


class AttributeDataType(str, enum.Enum):
    CHOICE = "Choice"
    OBJECT = "Object"


class AttributeValueWidget(str, enum.Enum):
    TABLE = "Table"
    BUTTONS = "Buttons"

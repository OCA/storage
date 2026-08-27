# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from unittest import mock

from odoo.addons.base.tests.common import BaseCommon

from ..models.models import BaseModel


class TestAvatar(BaseCommon):
    def test_avatar(self):
        with mock.patch.object(BaseModel, "manage_bin_size") as mock_manage:
            mock_manage.return_value = self.partner.with_context(bin_size=True)
            _avatar = self.partner.avatar_128
            mock_manage.assert_called()

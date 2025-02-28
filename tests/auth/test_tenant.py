# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT
import pytest

import sqlalchemy as sa

# from uno.auth.tables import Tenant
# from uno.auth.enums import TenantType
# from uno.auth.tables import User
# from uno.cmd import create_db, drop_db


'''
class TestTenant:
    @pytest.mark.parametrize("session", ["uno_test_tenant"], indirect=["session"])
    def test_super_user_select_tenant(
        self,
        session,
        mock_rls_vars,
        data_dict,
    ):
        """Tests that a tenant can be read by a superuser with each of the db ROLEs."""
        with session as session:
            session.execute(text(mock_rls_vars))

            # Test with admin role
            session.execute(func(uno.mock_role("admin")))
            stmt = select(func.count()).select_from(Tenant)
            tenant_count = session.execute(stmt)
            assert tenant_count.scalar() == 4

            # Test with writer role
            stmt = select(func.count()).select_from(Tenant)
            tenant_count = session.execute(stmt)
            assert tenant_count.scalar() == 4

            # Test with reader role
            stmt = select(func.count()).select_from(Tenant)
            tenant_count = session.execute(stmt)
            assert tenant_count.scalar() == 4

    @pytest.mark.parametrize("session", ["uno_test_tenant"], indirect=["session"])
    def test_reader_role_cannot_create_tenant(self, session, mock_rls_vars):
        """Tests that a tenant cannot be created by the reader role."""
        with session as session:
            session.execute(text(mock_rls_vars))
            unotech = Tenant(name="uno.tech", tenant_type=TenantType.INDIVIDUAL)
            session.add(unotech)
            with pytest.raises(exc.ProgrammingError):
                session.commit()

    @pytest.mark.parametrize("session", ["uno_test_tenant"], indirect=["session"])
    def test_writer_role_can_create_tenant(self, session, mock_rls_vars):
        """Tests that a tenant can be created by the writer role."""
        with session as session:
            session.execute(text(mock_rls_vars))
            unotech = Tenant(name="uno.tech", tenant_type=TenantType.INDIVIDUAL)
            session.add(unotech)
            assert session.commit() is None

    @pytest.mark.parametrize("session", ["uno_test_tenant"], indirect=["session"])
    def test_super_user_create_tenant(self, session, mock_rls_vars):
        """Tests that a tenant can be created by a superuser ."""
        with session as session:
            session.execute(text(mock_rls_vars))
            new_tenant = Tenant(name="New Tenant", tenant_type=TenantType.ENTERPRISE)
            session.add(new_tenant)
            assert session.commit() is None

'''

'''
@pytest.mark.asyncio
async def test_group_dict_on_tenant_creation(async_session, admin_user):
    admin_user = await admin_user
    async with async_session() as session:
        await session.execute(text(f"SET ROLE {settings.DB_NAME}_writer"))

        acme = Tenant(name="Acme Inc.", tenant_type=TenantType.ENTERPRISE)
        nacme = Tenant(name="NAcme Inc.", tenant_type=TenantType.CORPORATE)
        coyote = Tenant(
            name="Wiley Coyote", tenant_type=TenantType.BUSINESS
        )
        bird = Tenant(name="Road Runner", tenant_type=TenantType.INDIVIDUAL)
        tenants = [acme, nacme, coyote, bird]
        session.add_all(tenants)
        await session.commit()

        tenant_count = await session.execute(
            select(func.count()).select_from(Tenant)
        )
        assert tenant_count.scalar() == 4
        group_count = await session.execute(select(func.count()).select_from(Group))
        assert group_count.scalar() == 4


@pytest.mark.asyncio
async def test_tenant_graphs(async_session, admin_user):
    admin_user = await admin_user
    async with async_session() as session:
        await session.execute(text(f"SET ROLE {settings.DB_NAME}_admin"))
        stmt = text(
            """
            SELECT * FROM cypher('graph', $$
            MATCH (c:Tenant)
            RETURN properties(c)
            $$) as (type agtype);
            """
        )
        tenant_vertex = await session.execute(stmt)
        for props in tenant_vertex.fetchall():
            properties = json.loads(props[0])
            assert properties["created_at"] is not None
            assert properties["modified_at"] is not None
            with pytest.raises(KeyError):
                properties["deleted_at"]
    # assert properties["name"] == "Acme Inc."
    # assert properties["tenant_type"] == "ENTERPRISE"
    # assert properties["created_at"] is not None
    # assert properties["modified_at"] is not None
    # with pytest.raises(KeyError):
    #     properties["deleted_at"]


    # Create roles
    acme_admin_role = Role(
        name="Admin", description="Administrator role", tenant_id=acme.id
    )
    acme_user_role = Role(
        name="User", description="Regular user role", tenant_id=acme.id
    )
    nacme_admin_role = Role(
        name="Admin", description="Administrator role", tenant_id=nacme.id
    )
    nacme_user_role = Role(
        name="User", description="Regular user role", tenant_id=nacme.id
    )
    coyote_admin_role = Role(
        name="Admin", description="Administrator role", tenant_id=coyote.id
    )
    coyote_user_role = Role(
        name="User", description="Regular user role", tenant_id=coyote.id
    )
    bird_admin_role = Role(
        name="Admin", description="Administrator role", tenant_id=bird.id
    )
    bird_user_role = Role(
        name="User", description="Regular user role", tenant_id=bird.id
    )
    session.add_all(
        [
            acme_admin_role,
            acme_user_role,
            nacme_admin_role,
            nacme_user_role,
            coyote_admin_role,
            coyote_user_role,
            bird_admin_role,
            bird_user_role,
        ]
    )
    session.commit()
    # Create groups
    group_sales = Group(name="Sales", tenant_id=acme.id)
    group_support = Group(name="Support", tenant_id=acme.id)
    session.add_all([group_sales, group_support])
    session.commit()
    group_sales = Group(name="Sales", tenant_id=nacme.id)
    group_support = Group(name="Support", tenant_id=nacme.id)
    session.add_all([group_sales, group_support])
    session.commit()
    group_sales = Group(name="Sales", tenant_id=coyote.id)
    group_support = Group(name="Support", tenant_id=coyote.id)
    session.add_all([group_sales, group_support])
    session.commit()
    assert session.query(Group).count() == 10
    """
    # Create users
    user_john = User(
        email="john@example.com",
        handle="john",
        full_name="John Doe",
        tenant_id="1",
        default_group_id=group_sales.id,
    )
    user_jane = User(
        email="jane@example.com",
        handle="jane",
        full_name="Jane Doe",
        tenant_id="1",
        default_group_id=group_support.id,
    )
    session.add_all([user_john, user_jane])
    session.commit()

    # Assign roles to users in groups
    user_group_role_john = UserGroupRole(
        user_id=user_john.id, group_id=group_sales.id, role_id=role_admin.id
    )
    user_group_role_jane = UserGroupRole(
        user_id=user_jane.id, group_id=group_support.id, role_id=role_user.id
    )
    session.add_all([user_group_role_john, user_group_role_jane])
    session.commit()
    """

    # Verify data_dict
    assert session.query(Role).count() == 8
    # assert session.query(User).count() == 8
    # assert session.query(Group).count() == 2
    # assert session.query(UserGroupRole).count() == 2

    session.close()






    def test_tenant_get_route(self, create_test_functions):
        token = encode_test_token()
        response = client.get("/api/auth/tenants", headers={"Authorization": token})
        assert response.status_code == 200
        assert response.json() is not None
'''

import pytest

from uno.core.feature_factory import FeatureFactory

try:
    from fastapi import APIRouter
except ImportError:
    APIRouter = None  # type: ignore


@pytest.mark.parametrize("feature,repo_attr,svc_attr", [
    ("api", "ApiResourceRepositoryProtocol", "ApiResourceServiceProtocol"),
])
def test_get_repositories_and_services(feature, repo_attr, svc_attr):
    factory = FeatureFactory(feature)
    repos = factory.get_repositories()
    # The repositories module should define the expected protocol
    assert hasattr(repos, repo_attr), f"{feature}.domain_repositories missing {repo_attr}"
    svcs = factory.get_services()
    assert hasattr(svcs, svc_attr), f"{feature}.domain_services missing {svc_attr}"


def test_get_router_returns_fastapi_router():
    factory = FeatureFactory("api")
    router = factory.get_router()
    assert APIRouter is not None, "FastAPI must be installed to run this test"
    assert isinstance(router, APIRouter)


def test_missing_modules_raise_error():
    factory = FeatureFactory("nonexistent_feature_123")
    with pytest.raises(ModuleNotFoundError):
        factory.get_repositories()
    with pytest.raises(ModuleNotFoundError):
        factory.get_services()
    with pytest.raises(ModuleNotFoundError):
        factory.get_router()
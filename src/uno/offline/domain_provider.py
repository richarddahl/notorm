"""
Domain provider for the Offline module.

This module configures dependency injection for the Offline module.
"""

import logging
from typing import Optional

import inject
from uno.database.provider import get_db_session

from uno.offline.domain_repositories import (
    DocumentRepository,
    CollectionRepository,
    TransactionRepository,
    ChangeRepository,
    SyncRepository,
    ConflictRepository,
    NetworkStateRepository,
    DocumentRepositoryProtocol,
    CollectionRepositoryProtocol,
    TransactionRepositoryProtocol,
    ChangeRepositoryProtocol,
    SyncRepositoryProtocol,
    ConflictRepositoryProtocol,
    NetworkStateRepositoryProtocol
)
from uno.offline.domain_services import (
    DocumentService,
    CollectionService,
    TransactionService,
    SyncService,
    NetworkService,
    OfflineService
)


def configure_offline_dependencies(binder: inject.Binder) -> None:
    """
    Configure dependencies for the Offline module.
    
    Args:
        binder: Dependency injection binder
    """
    # Create logger
    logger = logging.getLogger("uno.offline")
    
    # Bind repositories
    binder.bind(
        DocumentRepositoryProtocol,
        lambda: DocumentRepository(get_db_session())
    )
    binder.bind(
        CollectionRepositoryProtocol,
        lambda: CollectionRepository(get_db_session())
    )
    binder.bind(
        TransactionRepositoryProtocol,
        lambda: TransactionRepository(get_db_session())
    )
    binder.bind(
        ChangeRepositoryProtocol,
        lambda: ChangeRepository(get_db_session())
    )
    binder.bind(
        SyncRepositoryProtocol,
        lambda: SyncRepository(get_db_session())
    )
    binder.bind(
        ConflictRepositoryProtocol,
        lambda: ConflictRepository(get_db_session())
    )
    binder.bind(
        NetworkStateRepositoryProtocol,
        lambda: NetworkStateRepository(get_db_session())
    )
    
    # Bind services
    binder.bind(
        DocumentService,
        lambda: DocumentService(
            inject.instance(DocumentRepositoryProtocol),
            inject.instance(ChangeRepositoryProtocol),
            logger.getChild("document")
        )
    )
    binder.bind(
        CollectionService,
        lambda: CollectionService(
            inject.instance(CollectionRepositoryProtocol),
            logger.getChild("collection")
        )
    )
    binder.bind(
        TransactionService,
        lambda: TransactionService(
            inject.instance(TransactionRepositoryProtocol),
            inject.instance(DocumentRepositoryProtocol),
            logger.getChild("transaction")
        )
    )
    binder.bind(
        SyncService,
        lambda: SyncService(
            inject.instance(SyncRepositoryProtocol),
            inject.instance(ChangeRepositoryProtocol),
            inject.instance(ConflictRepositoryProtocol),
            inject.instance(DocumentRepositoryProtocol),
            inject.instance(NetworkStateRepositoryProtocol),
            logger.getChild("sync")
        )
    )
    binder.bind(
        NetworkService,
        lambda: NetworkService(
            inject.instance(NetworkStateRepositoryProtocol),
            logger.getChild("network")
        )
    )
    
    # Bind coordinating service
    binder.bind(
        OfflineService,
        lambda: OfflineService(
            inject.instance(DocumentService),
            inject.instance(CollectionService),
            inject.instance(TransactionService),
            inject.instance(SyncService),
            inject.instance(NetworkService),
            logger
        )
    )


def get_document_service() -> DocumentService:
    """
    Get the document service.
    
    Returns:
        DocumentService instance
    """
    return inject.instance(DocumentService)


def get_collection_service() -> CollectionService:
    """
    Get the collection service.
    
    Returns:
        CollectionService instance
    """
    return inject.instance(CollectionService)


def get_transaction_service() -> TransactionService:
    """
    Get the transaction service.
    
    Returns:
        TransactionService instance
    """
    return inject.instance(TransactionService)


def get_sync_service() -> SyncService:
    """
    Get the sync service.
    
    Returns:
        SyncService instance
    """
    return inject.instance(SyncService)


def get_network_service() -> NetworkService:
    """
    Get the network service.
    
    Returns:
        NetworkService instance
    """
    return inject.instance(NetworkService)


def get_offline_service() -> OfflineService:
    """
    Get the offline service.
    
    Returns:
        OfflineService instance
    """
    return inject.instance(OfflineService)
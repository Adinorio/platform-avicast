"""
Main views module for image_processing app
Imports and organizes views from specialized modules
"""

# Import all view functions from specialized modules
from .api_views import (  # noqa: F401
    debug_form_view, health_status_view, clear_upload_results,
    model_selection_view, benchmark_models_view
)
from .processing_views import (  # noqa: F401
    process_batch_view, api_batch_process,
    process_image_with_storage, _create_failed_processing_result,
    _create_fallback_processing_result
)
from .review_views import (  # noqa: F401
    review_view, annotation_view, save_annotations, species_management_view,
    api_species_management, approve_result, reject_result, override_result,
    allocate_view
)
from .storage_views import (  # noqa: F401
    storage_status_view, storage_cleanup_view, optimize_uncompressed_images,
    dashboard_view
)
from .upload_views import (  # noqa: F401
    image_upload_view, image_list_view, image_detail_view, image_delete_view,
    restore_archived_image, api_upload_progress, api_storage_stats,
    api_image_search, api_get_progress, api_progress
)

# Re-export key functions for backward compatibility and URL configuration
__all__ = [
    # Upload views
    "image_upload_view",
    "image_list_view",
    "image_detail_view",
    "image_delete_view",
    "restore_archived_image",
    "api_upload_progress",
    "api_storage_stats",
    "api_image_search",
    "api_get_progress",
    "api_progress",
    # Processing views
    "process_batch_view",
    "api_batch_process",
    "process_image_with_storage",
    "_create_failed_processing_result",
    "_create_fallback_processing_result",
    # Review views
    "review_view",
    "annotation_view",
    "save_annotations",
    "species_management_view",
    "api_species_management",
    "approve_result",
    "reject_result",
    "override_result",
    "allocate_view",
    # Storage views
    "storage_status_view",
    "storage_cleanup_view",
    "optimize_uncompressed_images",
    "dashboard_view",
    # API views
    "debug_form_view",
    "health_status_view",
    "clear_upload_results",
    "model_selection_view",
    "benchmark_models_view",
]


# Lazy storage manager initialization
def get_storage_manager():
    """Get storage manager instance when needed"""
    from .local_storage import LocalStorageManager

    return LocalStorageManager()

"""
Main views module for image_processing app
Imports and organizes views from specialized modules
"""

# Import all view functions from specialized modules
from .analytics_api import api_kfold_evaluation, api_reviewed_summary  # noqa: F401
from .analytics_comparison import model_comparison, reviewed_analytics_view  # noqa: F401

# Import analytics views from organized modules
from .analytics_dashboard import analytics_dashboard, image_selection_view  # noqa: F401
from .analytics_evaluation import (  # noqa: F401
    api_evaluation_status,
    create_evaluation_run,
    delete_evaluation_run,
    evaluation_results,
    evaluation_runs_list,
)
from .api_views import (  # noqa: F401
    benchmark_models_view,
    clear_upload_results,
    debug_form_view,
    health_status_view,
    model_selection_view,
)
from .processing_views import (  # noqa: F401
    _create_failed_processing_result,
    _create_fallback_processing_result,
    api_batch_process,
    process_batch_view,
    process_image_with_storage,
)
from .review_views import (  # noqa: F401
    allocate_view,
    annotation_view,
    api_species_management,
    approve_result,
    override_result,
    reject_result,
    review_view,
    save_annotations,
    species_management_view,
)
from .storage_views import (  # noqa: F401
    dashboard_view,
    optimize_uncompressed_images,
    storage_cleanup_view,
    storage_status_view,
)
from .upload_views import (  # noqa: F401
    api_get_progress,
    api_image_search,
    api_progress,
    api_storage_stats,
    api_upload_progress,
    image_delete_view,
    image_detail_view,
    image_list_view,
    image_upload_view,
    restore_archived_image,
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
    # Analytics views - Dashboard
    "analytics_dashboard",
    "image_selection_view",
    # Analytics views - Evaluation
    "create_evaluation_run",
    "evaluation_results",
    "evaluation_runs_list",
    "api_evaluation_status",
    "delete_evaluation_run",
    # Analytics views - Comparison
    "model_comparison",
    "reviewed_analytics_view",
    # Analytics views - API
    "api_kfold_evaluation",
    "api_reviewed_summary",
]


# Lazy storage manager initialization
def get_storage_manager():
    """Get storage manager instance when needed"""
    from .local_storage import LocalStorageManager

    return LocalStorageManager()

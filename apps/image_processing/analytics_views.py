"""
Model Performance Analytics Views
Advanced dashboard for YOLO model comparison and thesis analysis
"""
import json
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Avg, Count, Max, Min
from django.core.paginator import Paginator

from .models import ImageUpload, ImageProcessingResult
from .analytics_models import (
    ModelEvaluationRun, ModelPerformanceMetrics,
    SpeciesPerformanceMetrics, ConfusionMatrixEntry, ImageEvaluationResult
)
from .analytics_service import ModelAnalyticsService
from .analytics_config import (
    ANALYTICS_CONFIG, UI_TEXT, get_available_models, get_target_species,
    get_confusion_matrix_species, get_model_file_size, get_admin_roles,
    get_date_filter_days, log_debug, get_helpful_tips
)

@login_required
def analytics_dashboard(request):
    """
    Main Model Performance Analytics Dashboard
    Advanced MLOps metrics for thesis analysis
    """
    if not request.user.can_access_feature('image_processing'):
        messages.error(request, "You don't have permission to access analytics.")
        return redirect('image_processing:list')
    
    # Get available models for filtering (dynamic)
    available_models = get_available_models()

    # Get recent evaluation runs
    recent_runs = ModelEvaluationRun.objects.filter(
        status='COMPLETED'
    ).order_by('-created_at')[:ANALYTICS_CONFIG['RECENT_RUNS_LIMIT']]
    
    # Get overall statistics
    total_processed_images = ImageProcessingResult.objects.filter(
        processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED
    ).count()
    
    total_approved_results = ImageProcessingResult.objects.filter(
        review_status__in=[
            ImageProcessingResult.ReviewStatus.APPROVED,
            ImageProcessingResult.ReviewStatus.OVERRIDDEN
        ]
    ).count()
    
    # Get model usage statistics
    model_usage = ImageProcessingResult.objects.filter(
        processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED
    ).values('ai_model').annotate(
        count=Count('id'),
        avg_confidence=Avg('confidence_score'),
        avg_inference_time=Avg('inference_time')
    ).order_by('-count')
    
    # Get species detection statistics
    species_stats = []
    target_species = get_target_species()
    for species in target_species:
        count = ImageProcessingResult.objects.filter(
            detected_species__icontains=species,
            review_status__in=[
                ImageProcessingResult.ReviewStatus.APPROVED,
                ImageProcessingResult.ReviewStatus.OVERRIDDEN
            ]
        ).count()
        species_stats.append({
            'name': species,
            'count': count
        })
    
    context = {
        'available_models': available_models,
        'recent_runs': recent_runs,
        'total_processed_images': total_processed_images,
        'total_approved_results': total_approved_results,
        'model_usage': model_usage,
        'species_stats': species_stats,
        'target_species': target_species,
    }
    
    return render(request, 'image_processing/analytics_dashboard.html', context)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def create_evaluation_run(request):
    """
    Create and execute a new model evaluation run
    """
    if not request.user.can_access_feature('image_processing'):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        log_debug(f"Request body: {request.body}")
        data = json.loads(request.body)
        log_debug(f"Parsed data: {data}")
        
        # Create evaluation run with configurable defaults
        evaluation_run = ModelEvaluationRun.objects.create(
            name=data.get('name', f"Evaluation Run {timezone.now().strftime('%Y-%m-%d %H:%M')}"),
            description=data.get('description', ''),
            created_by=request.user,
            iou_threshold=data.get('iou_threshold', ANALYTICS_CONFIG['DEFAULT_IOU_THRESHOLD']),
            confidence_threshold=data.get('confidence_threshold', ANALYTICS_CONFIG['DEFAULT_CONFIDENCE_THRESHOLD']),
            models_evaluated=data.get('models', []),
            species_filter=data.get('species', [])
        )
        
        # Parse date range if provided
        date_range = None
        if data.get('date_start') and data.get('date_end'):
            date_start = datetime.fromisoformat(data['date_start'].replace('Z', '+00:00'))
            date_end = datetime.fromisoformat(data['date_end'].replace('Z', '+00:00'))
            evaluation_run.date_range_start = date_start
            evaluation_run.date_range_end = date_end
            evaluation_run.save()
            date_range = (date_start, date_end)
        
        # Run REAL evaluation in background
        from .real_evaluation_workflow import RealEvaluationWorkflow
        workflow = RealEvaluationWorkflow()
        workflow.start_evaluation(evaluation_run)
        
        return JsonResponse({
            'success': True,
            'evaluation_run_id': str(evaluation_run.id),
            'redirect_url': f'/image-processing/analytics/results/{evaluation_run.id}/'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Failed to create evaluation run: {str(e)}'
        }, status=500)

@login_required
def evaluation_results(request, run_id):
    """
    Display detailed results for a specific evaluation run
    """
    if not request.user.can_access_feature('image_processing'):
        messages.error(request, "You don't have permission to access analytics.")
        return redirect('image_processing:list')
    
    evaluation_run = get_object_or_404(ModelEvaluationRun, id=run_id)
    
    # Get model performance metrics
    model_metrics = evaluation_run.model_metrics.all().order_by('-f1_score')
    
    # Get species performance for the best model
    best_model = model_metrics.first()
    species_metrics = []
    if best_model:
        species_metrics = best_model.species_metrics.all().order_by('species_name')
    
    # Get confusion matrix data
    confusion_data = []
    species_names = get_confusion_matrix_species()
    
    # Initialize confusion matrix
    confusion_matrix = {}
    for actual in species_names:
        confusion_matrix[actual] = {}
        for predicted in species_names:
            confusion_matrix[actual][predicted] = 0
    
    # Populate confusion matrix from image results
    for image_result in evaluation_run.image_results.all():
        # Count true positives
        for match in image_result.matches:
            actual_species = match['ground_truth']['species']
            predicted_species = match['prediction']['species']
            confusion_matrix[actual_species][predicted_species] += 1
        
        # Count false positives (predictions with no match)
        for fp_pred in image_result.unmatched_predictions:
            predicted_species = fp_pred['species']
            confusion_matrix['Background'][predicted_species] += 1
        
        # Count false negatives (ground truth with no match)
        for fn_gt in image_result.unmatched_ground_truth:
            actual_species = fn_gt['species']
            confusion_matrix[actual_species]['Background'] += 1
    
    # Prepare chart data for visualization
    precision_recall_data = []
    for metrics in model_metrics:
        precision_recall_data.append({
            'model': metrics.model_name,
            'precision': float(metrics.precision) if metrics.precision else 0,
            'recall': float(metrics.recall) if metrics.recall else 0,
            'f1_score': float(metrics.f1_score) if metrics.f1_score else 0,
            'map_50': float(metrics.map_50) if metrics.map_50 else 0
        })
    
    # Get performance over time (if multiple runs exist)
    historical_runs = ModelEvaluationRun.objects.filter(
        status='COMPLETED',
        created_at__gte=timezone.now() - timedelta(days=ANALYTICS_CONFIG['HISTORICAL_DATA_DAYS'])
    ).order_by('created_at')

    performance_timeline = []
    for run in historical_runs:
        if run.overall_map_50:
            performance_timeline.append({
                'date': run.created_at.strftime('%Y-%m-%d'),
                'map_50': float(run.overall_map_50),
                'run_name': run.name
            })

    # Get sample failure cases for analysis
    failure_cases = evaluation_run.image_results.filter(
        image_recall__lt=ANALYTICS_CONFIG['FAILURE_RECALL_THRESHOLD']
    ).order_by('image_recall')[:ANALYTICS_CONFIG['FAILURE_CASES_LIMIT']]
    
    context = {
        'evaluation_run': evaluation_run,
        'model_metrics': model_metrics,
        'species_metrics': species_metrics,
        'confusion_matrix': confusion_matrix,
        'species_names': species_names[:-1],  # Exclude 'Background' from display
        'precision_recall_data': json.dumps(precision_recall_data),
        'performance_timeline': json.dumps(performance_timeline),
        'failure_cases': failure_cases,
        'total_models_compared': model_metrics.count(),
        'best_model_name': best_model.model_name if best_model else 'N/A',
        'best_model_f1': float(best_model.f1_score) if best_model and best_model.f1_score else 0,
    }
    
    return render(request, 'image_processing/evaluation_results.html', context)

@login_required
def evaluation_runs_list(request):
    """
    List all evaluation runs with filtering and pagination
    """
    if not request.user.can_access_feature('image_processing'):
        messages.error(request, "You don't have permission to access analytics.")
        return redirect('image_processing:list')
    
    # Get all runs with filtering
    runs = ModelEvaluationRun.objects.all().order_by('-created_at')
    
    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter:
        runs = runs.filter(status=status_filter)

    # Model filtering
    model_filter = request.GET.get('model')
    if model_filter:
        runs = runs.filter(models_evaluated__contains=[model_filter])

    # Date range filtering
    date_start = request.GET.get('date_start')
    date_end = request.GET.get('date_end')
    if date_start:
        runs = runs.filter(created_at__date__gte=date_start)
    if date_end:
        runs = runs.filter(created_at__date__lte=date_end)

    # Created by filtering
    created_by_filter = request.GET.get('created_by')
    if created_by_filter:
        runs = runs.filter(created_by__employee_id__icontains=created_by_filter)

    # Date preset filtering
    date_filter = request.GET.get('date_range')
    if date_filter:
        if date_filter == 'today':
            runs = runs.filter(created_at__date=timezone.now().date())
        elif date_filter == 'week':
            runs = runs.filter(created_at__gte=timezone.now() - timedelta(days=get_date_filter_days('week')))
        elif date_filter == 'month':
            runs = runs.filter(created_at__gte=timezone.now() - timedelta(days=get_date_filter_days('month')))
    
    # Pagination
    paginator = Paginator(runs, ANALYTICS_CONFIG['PAGINATION_LIMIT'])
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Summary statistics
    total_runs = runs.count()
    completed_runs = runs.filter(status='COMPLETED').count()
    processing_runs = runs.filter(status='PROCESSING').count()
    failed_runs = runs.filter(status='FAILED').count()
    avg_processing_time = runs.filter(
        status='COMPLETED',
        processing_duration__isnull=False
    ).aggregate(avg_time=Avg('processing_duration'))['avg_time']
    
    # Get unique models that have been evaluated
    all_models = ModelEvaluationRun.objects.values_list('models_evaluated', flat=True)
    available_models = set()
    for model_list in all_models:
        if model_list:
            available_models.update(model_list)

    # Sort models for consistent display
    available_models = sorted(list(available_models))

    context = {
        'evaluation_runs': page_obj,  # Template expects this variable name
        'page_obj': page_obj,
        'total_runs': total_runs,
        'completed_runs': completed_runs,
        'processing_runs': processing_runs,
        'failed_runs': failed_runs,
        'avg_processing_time': avg_processing_time,
        'available_models': available_models,
        'status_filter': status_filter,
        'model_filter': model_filter,
        'created_by_filter': created_by_filter,
        'date_filter': date_filter,
        'date_start': date_start,
        'date_end': date_end,
    }
    
    return render(request, 'image_processing/evaluation_runs_list.html', context)

@login_required
def model_comparison(request):
    """
    Compare multiple models side by side
    """
    if not request.user.can_access_feature('image_processing'):
        messages.error(request, "You don't have permission to access analytics.")
        return redirect('image_processing:list')
    
    # Get model comparison data from recent completed runs
    recent_run = ModelEvaluationRun.objects.filter(
        status='COMPLETED'
    ).order_by('-created_at').first()
    
    comparison_data = []
    model_metrics = []
    
    if recent_run:
        model_metrics = recent_run.model_metrics.all().order_by('-f1_score')
        
        for metrics in model_metrics:
            # Get model file size if available
            model_size = None
            model_params = None
            
            # Try to get model file size from filesystem
            model_size = get_model_file_size(metrics.model_name)
            
            comparison_data.append({
                'model_name': metrics.model_name,
                'precision': float(metrics.precision) if metrics.precision else 0,
                'recall': float(metrics.recall) if metrics.recall else 0,
                'f1_score': float(metrics.f1_score) if metrics.f1_score else 0,
                'map_50': float(metrics.map_50) if metrics.map_50 else 0,
                'avg_inference_time_ms': float(metrics.avg_inference_time_ms) if metrics.avg_inference_time_ms else 0,
                'images_processed': metrics.images_processed,
                'true_positives': metrics.true_positives,
                'false_positives': metrics.false_positives,
                'false_negatives': metrics.false_negatives,
                'model_size_mb': round(model_size, 1) if model_size else None,
                'model_parameters_millions': float(metrics.model_parameters_millions) if metrics.model_parameters_millions else None
            })
    
    # Create performance radar chart data
    radar_data = {
        'labels': ['Precision', 'Recall', 'F1-Score', 'mAP@0.5', 'Speed (1/ms)'],
        'datasets': []
    }

    for i, data in enumerate(comparison_data[:ANALYTICS_CONFIG['RADAR_CHART_LIMIT']]):
        speed_score = 1000 / data['avg_inference_time_ms'] if data['avg_inference_time_ms'] > 0 else 0
        speed_normalized = min(speed_score / ANALYTICS_CONFIG['SPEED_NORMALIZATION_FACTOR'], 1.0)

        radar_data['datasets'].append({
            'label': data['model_name'],
            'data': [
                data['precision'],
                data['recall'],
                data['f1_score'],
                data['map_50'],
                speed_normalized
            ],
            'backgroundColor': ANALYTICS_CONFIG['CHART_COLORS'][i % len(ANALYTICS_CONFIG['CHART_COLORS'])] + '40',
            'borderColor': ANALYTICS_CONFIG['CHART_COLORS'][i % len(ANALYTICS_CONFIG['CHART_COLORS'])],
            'borderWidth': 2
        })
    
    context = {
        'comparison_data': comparison_data,
        'radar_chart_data': json.dumps(radar_data),
        'recent_run': recent_run,
        'total_models': len(comparison_data),
        'best_overall_model': comparison_data[0] if comparison_data else None,
        'fastest_model': min(comparison_data, key=lambda x: x['avg_inference_time_ms']) if comparison_data else None,
        'most_accurate_model': max(comparison_data, key=lambda x: x['map_50']) if comparison_data else None,
    }
    
    return render(request, 'image_processing/model_comparison.html', context)

@login_required
def api_evaluation_status(request, run_id):
    """
    API endpoint to check evaluation run status (for REAL progress monitoring)
    """
    if not request.user.can_access_feature('image_processing'):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        from .real_evaluation_workflow import RealEvaluationWorkflow
        
        evaluation_run = get_object_or_404(ModelEvaluationRun, id=run_id)
        
        # Get real-time progress from the workflow
        workflow = RealEvaluationWorkflow()
        progress = workflow.get_progress(run_id)

        # Add debug information to help users understand the evaluation state
        try:
            debug_info = {
                'models_evaluated': evaluation_run.models_evaluated,
                'species_filter': evaluation_run.species_filter,
                'iou_threshold': float(evaluation_run.iou_threshold),
                'confidence_threshold': float(evaluation_run.confidence_threshold),
                'total_images_evaluated': evaluation_run.total_images_evaluated,
                'has_image_results': evaluation_run.image_results.exists() if hasattr(evaluation_run, 'image_results') else False,
                'has_model_metrics': evaluation_run.model_metrics.exists() if hasattr(evaluation_run, 'model_metrics') else False,
                'has_species_metrics': evaluation_run.species_metrics.exists() if hasattr(evaluation_run, 'species_metrics') else False,
            }
        except Exception as debug_error:
            debug_info = {
                'models_evaluated': evaluation_run.models_evaluated,
                'species_filter': evaluation_run.species_filter,
                'iou_threshold': float(evaluation_run.iou_threshold),
                'confidence_threshold': float(evaluation_run.confidence_threshold),
                'total_images_evaluated': evaluation_run.total_images_evaluated,
                'debug_error': str(debug_error)
            }

        # Get contextual helpful tips
        helpful_tips = get_helpful_tips(evaluation_run.status, progress)

        response_data = {
            'id': str(evaluation_run.id),
            'status': evaluation_run.status,
            'name': evaluation_run.name,
            'created_at': evaluation_run.created_at.isoformat(),
            'total_images': evaluation_run.total_images_evaluated,
            'overall_precision': float(evaluation_run.overall_precision) if evaluation_run.overall_precision else None,
            'overall_recall': float(evaluation_run.overall_recall) if evaluation_run.overall_recall else None,
            'overall_f1_score': float(evaluation_run.overall_f1_score) if evaluation_run.overall_f1_score else None,
            'overall_map_50': float(evaluation_run.overall_map_50) if evaluation_run.overall_map_50 else None,
            'processing_duration': str(evaluation_run.processing_duration) if evaluation_run.processing_duration else None,
            'error_message': evaluation_run.error_message if evaluation_run.status == 'FAILED' else None,
            # Real progress information
            'progress_percentage': progress.progress_percentage,
            'current_step': progress.current_step,
            'completed_steps': progress.completed_steps,
            'total_steps': progress.total_steps,
            'processing_status': progress.status,
            # Debug and helpful information
            'debug_info': debug_info,
            'helpful_tips': helpful_tips
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["DELETE"])
def delete_evaluation_run(request, run_id):
    """
    Delete an evaluation run and all associated data
    """
    if not request.user.can_access_feature('image_processing'):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        evaluation_run = get_object_or_404(ModelEvaluationRun, id=run_id)
        
        # Check if user can delete (only creator or admin)
        admin_roles = get_admin_roles()
        if evaluation_run.created_by != request.user and request.user.role not in admin_roles:
            return JsonResponse({'error': UI_TEXT['ERROR_MESSAGES']['DELETE_PERMISSION']}, status=403)
        
        evaluation_run.delete()
        
        return JsonResponse({'success': True, 'message': UI_TEXT['SUCCESS_MESSAGES']['RUN_DELETED']})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

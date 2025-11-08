from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from assets.models import Asset
from .models import AssetRequest, AssetReturn
from django.urls import reverse
from django.db.models import OuterRef, Subquery
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.core.paginator import Paginator

# --------------------------
# STAFF: Manage Requests
# --------------------------

@login_required
def staff_manage_requests(request):
    """Staff can view all user asset requests with pagination."""
    all_requests = AssetRequest.objects.select_related('user', 'asset').order_by('-request_date')
    paginator = Paginator(all_requests, 5)  # Show 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'requests/staff_manage_requests.html', {
        'page_obj': page_obj,
        'all_requests': page_obj.object_list,
    })
    
    
@login_required
def update_request_status(request, pk, action):
    """Approve, reject, or mark an asset as returned."""
    borrow_request = get_object_or_404(AssetRequest, pk=pk)

    if action == 'approve':
        borrow_request.status = 'approved'
        borrow_request.approval_date = timezone.now()
        borrow_request.approved_by = request.user
        messages.success(request, f"Request approved for {borrow_request.user.username}.")

    elif action == 'reject':
        borrow_request.status = 'rejected'
        borrow_request.approval_date = timezone.now()
        borrow_request.approved_by = request.user
        messages.warning(request, f"Request rejected for {borrow_request.user.username}.")

    elif action == 'return':
        if request.method == 'POST':
            condition = request.POST.get('condition_on_return', 'good')
            remarks = request.POST.get('remarks', '')
            borrow_request.status = 'returned'

            # Create return record
            AssetReturn.objects.create(
                borrow_request=borrow_request,
                condition_on_return=condition,
                received_by=request.user,
                remarks=remarks
            )

            messages.info(request, f"Asset returned by {borrow_request.user.username}.")
        else:
            messages.error(request, "Invalid return submission.")
            return redirect('requests:manage_requests')

    else:
        messages.error(request, "Invalid action.")
        return redirect('requests:manage_requests')

    borrow_request.save()
    return redirect('requests:manage_requests')


# --------------------------
# STAFF: Approve / Reject requests
# --------------------------
@login_required
def update_request_status(request, pk, action):
    borrow_request = get_object_or_404(AssetRequest, pk=pk)
    asset = borrow_request.asset

    if request.method == "POST":
        remarks = request.POST.get("remarks", "")

        if action == 'approve':
            borrow_request.status = 'approved'
            asset.status = 'borrowed'
            messages.success(request, f"Request approved for {borrow_request.user.username}.")
        elif action == 'reject':
            borrow_request.status = 'rejected'
            asset.status = 'available'
            messages.warning(request, f"Request rejected for {borrow_request.user.username}.")
        else:
            messages.error(request, "Invalid action.")
            return redirect('requests:manage_requests')

        borrow_request.remarks = remarks
        borrow_request.approved_by = request.user
        borrow_request.approval_date = timezone.now()

        asset.save()
        borrow_request.save()

    return redirect('requests:manage_requests')


@login_required
def staff_manage_returns(request):
    # Get all approved or returned requests
    approved_requests = AssetRequest.objects.select_related(
        'user', 'asset', 'approved_by'
    ).filter(
        status__in=['approved', 'returned']
    ).prefetch_related('returns').order_by('-request_date')

    # Pagination setup (10 per page)
    paginator = Paginator(approved_requests, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'all_returns': page_obj,
        'today': timezone.localdate(),
        'page_obj': page_obj,
    }
    return render(request, 'requests/staff_manage_returns.html', context)



@login_required
def staff_mark_returned(request, req_id):
    asset_request = get_object_or_404(AssetRequest, pk=req_id)

    if request.method == "POST":
        condition = request.POST.get("condition")
        returned_date = request.POST.get("returned_date")
        remarks = request.POST.get("remarks", "")

        asset_return = AssetReturn.objects.create(
            borrow_request=asset_request,
            received_by=request.user,
            condition_on_return=condition,
            returned_date=parse_date(returned_date),
            remarks=remarks
        )

        asset_request.status = 'returned'
        asset_request.save()

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "success": True,
                "return_id": asset_return.id,
                "condition": asset_return.condition_on_return,
                "returned_date": asset_return.returned_date.strftime("%Y-%m-%d"),
                "remarks": asset_return.remarks
            })

    return redirect('requests:staff_manage_returns')


@login_required
def staff_update_return_condition(request, return_id):
    asset_return = get_object_or_404(AssetReturn, pk=return_id)
    if request.method == "POST":
        new_condition = request.POST.get('condition')
        if new_condition in dict(AssetReturn.CONDITION_CHOICES).keys():
            asset_return.condition_on_return = new_condition
            asset_return.save()
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({
                    "success": True,
                    "condition": new_condition
                })
    return redirect('requests:staff_manage_returns')


# --------------------------
# USER: View available assets
# --------------------------

@login_required
def available_assets(request):
    # Get search and filter parameters
    query = request.GET.get('q', '').strip()
    condition_filter = request.GET.get('condition', '').strip()

    # Base queryset: only available assets
    asset_list = Asset.objects.filter(status='available')

    # Apply search by asset_name or model
    if query:
        asset_list = asset_list.filter(
            Q(asset_name__icontains=query) | Q(model__icontains=query)
        )

    # Apply condition filter if selected
    if condition_filter in ['good', 'fair', 'poor']:
        asset_list = asset_list.filter(asset_condition=condition_filter)

    # Paginate the results
    paginator = Paginator(asset_list, 5)  # 5 assets per page
    page_number = request.GET.get('page')
    assets = paginator.get_page(page_number)

    # Pass current search/filter values to template for form defaults
    context = {
        'assets': assets,
        'query': query,
        'condition_filter': condition_filter,
    }

    return render(request, 'requests/available_assets.html', context)


# --------------------------
# USER: Dashboard
# --------------------------
@login_required
def normal_dashboard(request):
    # Count only available assets
    total_available_assets = Asset.objects.filter(status='available').count()

    # Count of user's requests by status
    pending_count = AssetRequest.objects.filter(user=request.user, status='pending').count()
    approved_count = AssetRequest.objects.filter(user=request.user, status='approved').count()
    rejected_count = AssetRequest.objects.filter(user=request.user, status='rejected').count()
    returned_count = AssetRequest.objects.filter(user=request.user, status='returned').count()

    # Total processed requests (approved + rejected + returned)
    processed_count = approved_count + rejected_count + returned_count

    context = {
        'total_assets': total_available_assets,
        'pending_requests_count': pending_count,
        'processed_requests_count': processed_count,
    }

    return render(request, 'accounts/normal_dashboard.html', context)


# --------------------------
# USER: Request an Asset
# --------------------------
@login_required
def request_asset(request, pk):
    asset = get_object_or_404(Asset, pk=pk)

    if request.method == 'POST':
        request_date = request.POST.get('request_date')
        return_date = request.POST.get('return_date')

        if not request_date or not return_date:
            messages.error(request, "Please select both request and return dates.")
            return redirect('requests:request_asset', pk=pk)

        # Prevent duplicate pending requests for the same asset
        existing = AssetRequest.objects.filter(user=request.user, asset=asset, status='pending')
        if existing.exists():
            messages.warning(request, "You already have a pending request for this asset.")
            return redirect('requests:my_requests')

        AssetRequest.objects.create(
            user=request.user,
            asset=asset,
            request_date=request_date,
            return_date=return_date,
        )
        messages.success(request, "Your request has been submitted successfully!")
        return redirect('requests:my_requests')

    return render(request, 'requests/request_asset_form.html', {'asset': asset})


# --------------------------
# USER: View own requests
# --------------------------
@login_required
def my_requests(request):
    query = request.GET.get('q', '')  # Search query
    status_filter = request.GET.get('status', '')  # Status filter

    requests_list = AssetRequest.objects.filter(user=request.user).select_related('asset')

    if query:
        requests_list = requests_list.filter(
            Q(asset__asset_name__icontains=query) |
            Q(asset__model__icontains=query)
        )

    if status_filter:
        requests_list = requests_list.filter(status=status_filter)

    paginator = Paginator(requests_list, 5)
    page_number = request.GET.get('page')
    requests_page = paginator.get_page(page_number)

    context = {
        'requests': requests_page,
        'query': query,
        'status_filter': status_filter,
    }
    return render(request, 'requests/my_requests.html', context)

# --------------------------
# USER: Cancel a pending request
# --------------------------
@login_required
def cancel_request(request, pk):
    borrow_request = get_object_or_404(AssetRequest, pk=pk, user=request.user)

    if borrow_request.status != 'pending':
        messages.error(request, "Only pending requests can be cancelled.")
    else:
        borrow_request.status = 'cancelled'
        borrow_request.asset.status = 'available'  # Make asset available again
        borrow_request.asset.save()
        borrow_request.save()
        messages.success(request, "Your request has been cancelled successfully.")

    return redirect('requests:my_requests')




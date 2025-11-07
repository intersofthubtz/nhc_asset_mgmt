from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from assets.models import Asset
from .models import AssetRequest


# --------------------------
# STAFF: Manage Requests
# --------------------------
@login_required
def manage_requests(request):
    """Staff can view all user asset requests."""
    all_requests = AssetRequest.objects.select_related('user', 'asset').order_by('-request_date')
    return render(request, 'requests/manage_requests.html', {'all_requests': all_requests})


@login_required
def update_request_status(request, pk, action):
    """Approve or reject a specific asset request."""
    borrow_request = get_object_or_404(AssetRequest, pk=pk)
    asset = borrow_request.asset

    if action == 'approve':
        borrow_request.status = 'approved'
        borrow_request.approval_date = timezone.now()
        borrow_request.approved_by = request.user
        asset.status = 'borrowed'
        messages.success(request, f"Request approved for {borrow_request.user.username}.")
    elif action == 'reject':
        borrow_request.status = 'rejected'
        borrow_request.approval_date = timezone.now()
        borrow_request.approved_by = request.user
        asset.status = 'available'
        messages.warning(request, f"Request rejected for {borrow_request.user.username}.")
    else:
        messages.error(request, "Invalid action.")
        return redirect('requests:manage_requests')

    asset.save()
    borrow_request.save()

    return redirect('requests:manage_requests')


# --------------------------
# USER: View available assets
# --------------------------
@login_required
def available_assets(request):
    assets = Asset.objects.filter(status='available')
    return render(request, 'requests/available_assets.html', {'assets': assets})


# --------------------------
# User Dashboard
# --------------------------
@login_required
def normal_dashboard(request):
    # Only assets whose own status is 'available'
    total_available_assets = Asset.objects.filter(status='available').count()

    # Count of user's requests by status
    pending_count = AssetRequest.objects.filter(user=request.user, status='pending').count()
    approved_count = AssetRequest.objects.filter(user=request.user, status='approved').count()
    rejected_count = AssetRequest.objects.filter(user=request.user, status='rejected').count()
    returned_count = AssetRequest.objects.filter(user=request.user, status='returned').count()

    # Total processed requests
    processed_count = approved_count + rejected_count + returned_count

    context = {
        'total_assets': total_available_assets,
        'pending_requests_count': pending_count,
        'processed_requests_count': processed_count,
    }

    return render(request, 'accounts/normal_dashboard.html', context)




# --------------------------
# Request an Asset
# --------------------------
@login_required
def request_asset(request, pk):
    asset = get_object_or_404(Asset, pk=pk)

    if request.method == 'POST':
        request_date = request.POST.get('request_date')
        return_date = request.POST.get('return_date')
        remarks = request.POST.get('remarks')

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
            remarks=remarks,
        )
        messages.success(request, "Your request has been submitted successfully!")
        return redirect('requests:my_requests')

    return render(request, 'requests/request_asset_form.html', {'asset': asset})


# --------------------------
# User's own requests
# --------------------------
@login_required
def my_requests(request):
    requests_list = AssetRequest.objects.filter(user=request.user).select_related('asset')
    return render(request, 'requests/my_requests.html', {'requests': requests_list})


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

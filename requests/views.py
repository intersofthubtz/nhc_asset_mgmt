from datetime import datetime
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
from django.db.models import Case, When, Value, IntegerField
from django.core.exceptions import ValidationError

# --------------------------
# STAFF: Manage Requests
# --------------------------
@login_required
def staff_manage_requests(request):
    """Staff view all user requests with pending ones on top, paginated with search and filter."""
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', 'all')

    # Base queryset
    requests_qs = AssetRequest.objects.select_related('user', 'asset')

    # Apply search across username, asset name, and status
    if search_query:
        requests_qs = requests_qs.filter(
            Q(user__username__icontains=search_query) |
            Q(asset__asset_name__icontains=search_query) |
            Q(status__icontains=search_query)
        )

    # Apply status filter (skip "all")
    if status_filter != 'all':
        requests_qs = requests_qs.filter(status=status_filter)

    # Order pending requests first, then by request_date descending
    requests_qs = requests_qs.annotate(
        pending_order=Case(
            When(status='pending', then=Value(0)),
            default=Value(1),
            output_field=IntegerField()
        )
    ).order_by('pending_order', '-request_date', '-id')  # tie-breaker by ID

    # Pagination
    paginator = Paginator(requests_qs, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'all_requests': page_obj.object_list,
        'search_query': search_query,
        'status_filter': status_filter,
    }

    return render(request, 'requests/staff_manage_requests.html', context)


# --------------------------
# STAFF: Approve / Reject requests
# --------------------------
@login_required
def update_request_status(request, pk, action):
    """Approve or reject a pending request."""
    borrow_request = get_object_or_404(AssetRequest, pk=pk)
    asset = borrow_request.asset

    if borrow_request.status != 'pending':
        messages.error(request, "Only pending requests can be updated.")
        return redirect('requests:staff_manage_requests')

    if request.method == 'POST':
        remarks = request.POST.get('remarks', '')

        if action == 'approve':
            borrow_request.status = 'approved'
            asset.status = 'borrowed'
            messages.success(request, f"Request approved for {borrow_request.user.username}.")
        elif action == 'reject':
            borrow_request.status = 'rejected'
            asset.status = 'borrowed'
            messages.warning(request, f"Request rejected for {borrow_request.user.username}.")
        else:
            messages.error(request, "Invalid action.")
            return redirect('requests:staff_manage_requests')

        borrow_request.remarks = remarks
        borrow_request.approved_by = request.user
        borrow_request.approval_date = timezone.now()

        asset.save()
        borrow_request.save()

    return redirect('requests:staff_manage_requests')


@login_required
def staff_manage_returns(request):

    search_query = request.GET.get("search", "").strip()
    condition_filter = request.GET.get("condition", "all")

    # Base queryset
    approved_requests = (
        AssetRequest.objects.select_related("user", "asset", "approved_by")
        .filter(status="approved")
        .prefetch_related("returns")
        .order_by("-request_date")
    )

    # --- SEARCH ---
    if search_query:
        approved_requests = approved_requests.filter(
            Q(user__username__icontains=search_query)
            | Q(asset__asset_name__icontains=search_query)
            | Q(asset__model__icontains=search_query)
            | Q(returns__remarks__icontains=search_query)
        ).distinct()

    # --- CONDITION FILTER ---
    if condition_filter != "all":
        if condition_filter == "not returned":
            approved_requests = approved_requests.filter(returns__isnull=True)
        else:
            approved_requests = approved_requests.filter(
                returns__condition_on_return__iexact=condition_filter
            )

    # Pagination
    paginator = Paginator(approved_requests, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "today": timezone.localdate(),
        "search_query": search_query,
        "condition_filter": condition_filter,
    }

    return render(request, "requests/staff_manage_returns.html", context)


# Mapping condition -> asset status
CONDITION_STATUS_MAP = {
    "good": "returned",     
    "fair": "returned",   
    "poor": "retired",    
}   

@login_required
def staff_mark_returned(request, req_id):
    """
    Mark an asset as returned.
    Creates AssetReturn record and updates the linked Asset.
    """
    asset_request = get_object_or_404(AssetRequest, pk=req_id)
    asset = asset_request.asset

    if request.method == "POST":
        condition = request.POST.get("condition")  # good, fair, poor
        returned_date = request.POST.get("returned_date")
        remarks = request.POST.get("remarks", "")

        if condition not in CONDITION_STATUS_MAP:
            msg = "Invalid condition selected."
            messages.error(request, msg)
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False, "error": msg})
            return redirect("requests:staff_manage_returns")

        # Create AssetReturn
        asset_return = AssetReturn.objects.create(
            borrow_request=asset_request,
            received_by=request.user,
            condition_on_return=condition,
            returned_date=parse_date(returned_date),
            remarks=remarks,
        )

        # Update asset condition + status
        asset.asset_condition = condition
        asset.status = CONDITION_STATUS_MAP[condition]
        asset.save(update_fields=["asset_condition", "status"])

        messages.success(request, "Asset return recorded successfully.")

        # AJAX response
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "success": True,
                "asset_id": asset.id,
                "status": asset.status,
                "condition": asset.asset_condition,
                "return_id": asset_return.id,
                "returned_date": asset_return.returned_date.strftime("%Y-%m-%d"),
                "remarks": asset_return.remarks
            })

    return redirect("requests:staff_manage_returns")


@login_required
def staff_update_return_condition(request, return_id):
    """
    Update the condition of an already returned asset.
    Also updates linked asset condition and status.
    """
    asset_return = get_object_or_404(AssetReturn, pk=return_id)
    asset = asset_return.borrow_request.asset

    if request.method == "POST":
        new_condition = request.POST.get("condition")

        if new_condition not in CONDITION_STATUS_MAP:
            msg = "Invalid condition update."
            messages.error(request, msg)
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False, "error": msg})
            return redirect("requests:staff_manage_returns")

        # Update return record
        asset_return.condition_on_return = new_condition
        asset_return.remarks = request.POST.get("remarks", asset_return.remarks)
        asset_return.save(update_fields=["condition_on_return", "remarks"])

        # Update asset
        asset.asset_condition = new_condition
        asset.status = CONDITION_STATUS_MAP[new_condition]
        asset.save(update_fields=["asset_condition", "status"])

        messages.success(request, "Return details updated successfully.")

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "success": True,
                "new_condition": new_condition,
                "new_status": asset.status,
                "remarks": asset_return.remarks,
            })

    return redirect("requests:staff_manage_returns")


@login_required
def available_assets(request):
    """
    Display all available assets with search, filter, and pagination.
    Handle POST submission of asset requests from modal.
    """
    # -------------------------------
    # 1. Handle POST submission
    # -------------------------------
    if request.method == "POST":
        asset_id = request.POST.get("asset_id")
        request_date = request.POST.get("request_date")
        return_date = request.POST.get("return_date")

        # Validate asset exists + available
        try:
            asset = Asset.objects.get(id=asset_id, status="available")
        except Asset.DoesNotExist:
            messages.error(request, "The selected asset is no longer available.")
            return redirect("requests:available_assets")

        # Validate date logic
        if request_date > return_date:
            messages.error(request, "Return date must be AFTER request date.")
            return redirect("requests:available_assets")

        # Check for duplicate pending request by same user
        if AssetRequest.objects.filter(user=request.user, asset=asset, status="pending").exists():
            messages.warning(request, "You already have a pending request for this asset.")
            return redirect("requests:available_assets")

        # Create AssetRequest
        AssetRequest.objects.create(
            user=request.user,
            asset=asset,
            request_date=request_date,
            return_date=return_date,
            status="pending"
        )

        messages.success(
            request,
            f"You have successfully submitted a request for '{asset.asset_name}'."
        )
        return redirect("requests:available_assets")

    # -------------------------------
    # 2. Handle GET: search + filter + pagination
    # -------------------------------
    query = request.GET.get("q", "").strip()
    condition_filter = request.GET.get("condition", "").strip()

    asset_list = Asset.objects.filter(status="available")

    if query:
        asset_list = asset_list.filter(
            Q(asset_name__icontains=query) |
            Q(model__icontains=query)
        )

    if condition_filter in ["good", "fair", "poor"]:
        asset_list = asset_list.filter(asset_condition=condition_filter)

    # Fix Pagination warning by ordering
    asset_list = asset_list.order_by("asset_name")

    paginator = Paginator(asset_list, 5)  # 5 assets per page
    page_number = request.GET.get("page")
    assets = paginator.get_page(page_number)

    context = {
        "assets": assets,
        "query": query,
        "condition_filter": condition_filter,
    }

    return render(request, "requests/available_assets.html", context)


# --------------------------
# USER: Request an Asset
# --------------------------

@login_required
def request_asset(request, pk):
    asset = get_object_or_404(Asset, pk=pk)

    if request.method == 'POST':
        request_date = request.POST.get('request_date')
        return_date = request.POST.get('return_date')

        # Missing fields
        if not request_date or not return_date:
            messages.error(request, "Please select both request and return dates.")
            return redirect('requests:request_asset', pk=pk)

        # Convert dates safely
        try:
            req_date_obj = datetime.strptime(request_date, "%Y-%m-%d").date()
            ret_date_obj = datetime.strptime(return_date, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect('requests:request_asset', pk=pk)

        # Prevent duplicate pending requests
        if AssetRequest.objects.filter(user=request.user, asset=asset, status='pending').exists():
            messages.warning(request, "You already have a pending request for this asset.")
            return redirect('requests:request_asset', pk=pk)

        # Construct but don't save yet
        new_request = AssetRequest(
            user=request.user,
            asset=asset,
            request_date=req_date_obj,
            return_date=ret_date_obj,
        )

        # Validate with model clean()
        try:
            new_request.full_clean()
            new_request.save()
            messages.success(request, "Your request has been submitted successfully!")
        except ValidationError as e:
            messages.error(request, e.message)
            return redirect('requests:request_asset', pk=pk)

        return redirect('requests:request_asset', pk=pk)

    return render(request, 'requests/request_asset_form.html', {'asset': asset})


# --------------------------
# USER: View own requests
# --------------------------
@login_required
def my_requests(request):
    query = request.GET.get('q', '').strip()  # Search query
    status_filter = request.GET.get('status', '').strip()  # Status filter

    # Base queryset: requests of the logged-in user
    requests_list = AssetRequest.objects.filter(user=request.user).select_related('asset')

    # Apply search by asset name or model
    if query:
        requests_list = requests_list.filter(
            Q(asset__asset_name__icontains=query) |
            Q(asset__model__icontains=query)
        )

    # Apply status filter if selected
    if status_filter in ['pending', 'approved', 'rejected', 'returned']:
        requests_list = requests_list.filter(status=status_filter)

    # Paginate the results
    paginator = Paginator(requests_list, 5)  # 5 requests per page
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




from datetime import datetime
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from assets.models import Asset
from requests.forms import AssetRequestForm
from .models import AssetRequest, AssetReturn
from django.urls import reverse
from django.db.models import OuterRef, Subquery
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.core.paginator import Paginator
from django.db.models import Case, When, Value, IntegerField
from django.core.exceptions import ValidationError


# --------------------------
# ADMIN: Manage Requests
# --------------------------
@login_required
def admin_manage_requests(request):
    """Admin view all requests with search and filter, paginated."""
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', 'all')

    # Base queryset
    requests_qs = AssetRequest.objects.select_related('user', 'assigned_asset')

    # Apply search across username, asset name, and status
    if search_query:
        requests_qs = requests_qs.filter(
            Q(user__username__icontains=search_query) |
            Q(asset_category__icontains=search_query) |
            Q(status__icontains=search_query) |
            Q(assigned_asset__model__icontains=search_query) |
            Q(assigned_asset__serial_number__icontains=search_query)
        )

    # Apply status filter (skip "all")
    if status_filter != 'all':
        requests_qs = requests_qs.filter(status=status_filter)

    # Order by request_date descending
    requests_qs = requests_qs.order_by('-request_date', '-id')  # tie-breaker by ID

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

    return render(request, 'requests/admin_manage_requests.html', context)

@login_required
def admin_request_details(request, pk):
    # Load request
    req = get_object_or_404(AssetRequest, pk=pk)

    # ---------------------------------------
    # Filter ONLY available assets of same category
    # ---------------------------------------
    available_assets = Asset.objects.filter(
        asset_category=req.asset_category,
        status="available"
    ).order_by("model")

    # ---------------------------------------
    # Optional pre-assignment from dropdown
    # ---------------------------------------
    assign_id = request.GET.get("assign")

    if assign_id:
        try:
            asset = Asset.objects.get(id=assign_id, status="available")

            # Assign the asset to the request
            req.assigned_asset = asset
            req.save()

            messages.success(
                request,
                f"Asset '{asset.model}' has been pre-assigned to this request."
            )

            # Correct URL name = get_request_details
            return redirect("requests:admin_get_request_details", pk=req.pk)

        except Asset.DoesNotExist:
            messages.error(
                request,
                "The selected asset is no longer available."
            )
            return redirect("requests:admin_get_request_details", pk=req.pk)

    # ---------------------------------------
    # Render Page
    # ---------------------------------------
    context = {
        "req": req,
        "assets": available_assets,
    }

    return render(request, "requests/admin_request_details.html", context)


@login_required
def assign_asset(request, pk):
    req = get_object_or_404(AssetRequest, pk=pk)

    # Only allow asset assignment when pending
    if req.status != "pending":
        messages.warning(request, "Cannot assign asset. Request is already processed.")
        return redirect("requests:admin_get_request_details", pk)

    asset_id = request.GET.get("asset_id")

    if not asset_id:
        messages.error(request, "No asset selected.")
        return redirect("requests:admin_get_request_details", pk)

    asset = get_object_or_404(Asset, pk=asset_id)

    # Ensure asset category matches request category
    if asset.asset_category != req.asset_category:
        messages.error(request, "Asset category does not match request category.")
        return redirect("requests:admin_get_request_details", pk)

    # Ensure asset is available
    if asset.status != "available":
        messages.error(request, "Asset is not available.")
        return redirect("requests:admin_get_request_details", pk)

    # Assign asset
    req.assigned_asset = asset
    req.save()

    messages.success(request, f"Asset {asset.model} assigned successfully.")
    return redirect("requests:admin_get_request_details", pk)


@login_required
def admin_update_request_status(request, pk, action):
    req = get_object_or_404(AssetRequest, pk=pk)

    if req.status != "pending":
        messages.warning(request, "This request has already been processed.")
        return redirect("requests:admin_get_request_details", req.pk)

    # Save remarks if submitted
    if request.method == "POST":
        remarks = request.POST.get("remarks")
        if remarks:
            req.remarks = remarks

    # APPROVE
    if action == "approve":

        if not req.assigned_asset:
            messages.error(request, "You must assign an asset before approving.")
            return redirect("requests:admin_get_request_details", pk)

        req.status = "approved"
        req.approved_by = request.user
        req.approval_date = timezone.now()

        # Update asset status
        asset = req.assigned_asset
        asset.status = "borrowed"
        asset.save()

        req.save()

        # ➤ CREATE AssetReturn placeholder
        AssetReturn.objects.create(
            borrow_request=req,
            received_by=None,         # admin will fill later
            remarks=None,             # empty
            condition_on_return="good"  # default
            # returned_date auto created
        )

        messages.success(request, "Request approved successfully and return record created.")
        return redirect("requests:admin_get_request_details", pk)

    # REJECT
    elif action == "reject":
        req.status = "rejected"
        req.approved_by = request.user
        req.approval_date = timezone.now()
        req.assigned_asset = None

        req.save()

        messages.error(request, "Request rejected.")
        return redirect("requests:admin_get_request_details", pk)

    else:
        messages.error(request, "Invalid action.")
        return redirect("requests:admin_get_request_details", pk)


@login_required
def admin_manage_returns(request):
    search_query = request.GET.get("search", "").strip()
    condition_filter = request.GET.get("condition", "all")

    returns = AssetReturn.objects.select_related(
        "borrow_request__assigned_asset",
        "borrow_request__user",
        "received_by",
    )

    # Search filter
    if search_query:
        returns = returns.filter(
            Q(borrow_request__user__username__icontains=search_query) |
            Q(borrow_request__assigned_asset__model__icontains=search_query) |
            Q(borrow_request__assigned_asset__serial_number__icontains=search_query)
        )

    # Condition filter
    if condition_filter != "all":
        returns = returns.filter(condition_on_return=condition_filter)

    paginator = Paginator(returns, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "requests/admin_manage_returns.html", {
        "page_obj": page_obj,
        "search_query": search_query,
        "condition_filter": condition_filter,
    })



@login_required
def admin_return_detail(request, return_id):
    ret = get_object_or_404(AssetReturn, pk=return_id)
    return render(request, "requests/admin_return_detail.html", {"ret": ret})

@login_required
def admin_mark_returned(request, req_id):

    borrow_request = get_object_or_404(AssetRequest, id=req_id)

    if request.method == "POST":

        returned_date = request.POST.get("returned_date")
        condition = request.POST.get("condition_on_return")
        remarks = request.POST.get("remarks")

        # Convert datetime-local to timezone-aware datetime
        returned_dt = timezone.make_aware(
            timezone.datetime.fromisoformat(returned_date)
        )

        # Prevent multiple return records for same request
        AssetReturn.objects.filter(borrow_request=borrow_request).delete()

        # Create/Save return record
        AssetReturn.objects.create(
            borrow_request=borrow_request,
            returned_date=returned_dt,
            condition_on_return=condition,
            remarks=remarks,
            received_by=request.user
        )

        # ============================
        # UPDATE ASSET STATUS HERE
        # ============================
        assigned_asset = borrow_request.assigned_asset
        if assigned_asset:
            assigned_asset.status = "returned"         # <--- IMPORTANT
            assigned_asset.asset_condition = condition  # Sync condition
            assigned_asset.save()

        # Mark borrow request as fully returned
        borrow_request.is_fully_returned = True
        borrow_request.save()

        messages.success(request, "Asset marked as returned successfully.")
        return redirect("requests:admin_manage_returns")

    return redirect("requests:admin_manage_returns")


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
            Q(description__icontains=query)
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
# STAFF: Manage Requests
# --------------------------
@login_required
def staff_manage_requests(request):
    """Staff view all requests with search and filter, paginated."""
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', 'all')

    # Base queryset
    requests_qs = AssetRequest.objects.select_related('user', 'assigned_asset')

    # Apply search across username, asset name, and status
    if search_query:
        requests_qs = requests_qs.filter(
            Q(user__username__icontains=search_query) |
            Q(asset_category__icontains=search_query) |
            Q(status__icontains=search_query) |
            Q(assigned_asset__model__icontains=search_query) |
            Q(assigned_asset__serial_number__icontains=search_query)
        )

    # Apply status filter (skip "all")
    if status_filter != 'all':
        requests_qs = requests_qs.filter(status=status_filter)

    # Order by request_date descending
    requests_qs = requests_qs.order_by('-request_date', '-id')  # tie-breaker by ID

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


@login_required
def staff_request_details(request, pk):
    # Load request
    req = get_object_or_404(AssetRequest, pk=pk)

    # ---------------------------------------
    # Filter ONLY available assets of same category
    # ---------------------------------------
    available_assets = Asset.objects.filter(
        asset_category=req.asset_category,
        status="available"
    ).order_by("model")

    # ---------------------------------------
    # Optional pre-assignment from dropdown
    # ---------------------------------------
    assign_id = request.GET.get("assign")

    if assign_id:
        try:
            asset = Asset.objects.get(id=assign_id, status="available")

            # Assign the asset to the request
            req.assigned_asset = asset
            req.save()

            messages.success(
                request,
                f"Asset '{asset.model}' has been pre-assigned to this request."
            )

            # Correct URL name = get_request_details
            return redirect("requests:staff_get_request_details", pk=req.pk)

        except Asset.DoesNotExist:
            messages.error(
                request,
                "The selected asset is no longer available."
            )
            return redirect("requests:staff_get_request_details", pk=req.pk)

    # ---------------------------------------
    # Render Page
    # ---------------------------------------
    context = {
        "req": req,
        "assets": available_assets,
    }

    return render(request, "requests/request_details.html", context)

# --------------------------
# STAFF: Approve / Reject requests
# --------------------------
@login_required
def update_request_status(request, pk, action):
    req = get_object_or_404(AssetRequest, pk=pk)

    if req.status != "pending":
        messages.warning(request, "This request has already been processed.")
        return redirect("requests:staff_get_request_details", req.pk)

    # Save remarks if submitted
    if request.method == "POST":
        remarks = request.POST.get("remarks")
        if remarks:
            req.remarks = remarks

    # APPROVE
    if action == "approve":

        if not req.assigned_asset:
            messages.error(request, "You must assign an asset before approving.")
            return redirect("requests:staff_get_request_details", pk)

        req.status = "approved"
        req.approved_by = request.user
        req.approval_date = timezone.now()

        # Update asset
        asset = req.assigned_asset
        asset.status = "borrowed"
        asset.save()

        req.save()

        messages.success(request, "Request approved successfully.")
        return redirect("requests:staff_get_request_details", pk)

    # REJECT
    elif action == "reject":
        req.status = "rejected"
        req.approved_by = request.user
        req.approval_date = timezone.now()
        req.assigned_asset = None

        req.save()

        messages.error(request, "Request rejected.")
        return redirect("requests:staff_get_request_details", pk)

    else:
        messages.error(request, "Invalid action.")
        return redirect("requests:staff_get_request_details", pk)


@login_required
def staff_manage_returns(request):
    search_query = request.GET.get("search", "").strip()
    condition_filter = request.GET.get("condition", "all")

    returns = AssetReturn.objects.select_related(
        "borrow_request__assigned_asset",
        "borrow_request__user",
        "received_by",
    )

    # Search filter
    if search_query:
        returns = returns.filter(
            Q(borrow_request__user__username__icontains=search_query) |
            Q(borrow_request__assigned_asset__model__icontains=search_query) |
            Q(borrow_request__assigned_asset__serial_number__icontains=search_query)
        )

    # Condition filter
    if condition_filter != "all":
        returns = returns.filter(condition_on_return=condition_filter)

    paginator = Paginator(returns, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "requests/staff_manage_returns.html", {
        "page_obj": page_obj,
        "search_query": search_query,
        "condition_filter": condition_filter,
    })


@login_required
def staff_return_detail(request, return_id):
    ret = get_object_or_404(AssetReturn, pk=return_id)
    return render(request, "requests/return_detail.html", {"ret": ret})


@login_required
def staff_mark_returned(request, req_id):

    borrow_request = get_object_or_404(AssetRequest, id=req_id)

    if request.method == "POST":

        returned_date = request.POST.get("returned_date")
        condition = request.POST.get("condition_on_return")
        remarks = request.POST.get("remarks")

        # Convert datetime-local to timezone-aware datetime
        returned_dt = timezone.make_aware(
            timezone.datetime.fromisoformat(returned_date)
        )

        # Prevent multiple return records for same request
        AssetReturn.objects.filter(borrow_request=borrow_request).delete()

        # Create/Save return record
        AssetReturn.objects.create(
            borrow_request=borrow_request,
            returned_date=returned_dt,
            condition_on_return=condition,
            remarks=remarks,
            received_by=request.user
        )

        # ============================
        # UPDATE ASSET STATUS HERE
        # ============================
        assigned_asset = borrow_request.assigned_asset
        if assigned_asset:
            assigned_asset.status = "returned"         # <--- IMPORTANT
            assigned_asset.asset_condition = condition  # Sync condition
            assigned_asset.save()

        # Mark borrow request as fully returned
        borrow_request.is_fully_returned = True
        borrow_request.save()

        messages.success(request, "Asset marked as returned successfully.")
        return redirect("requests:staff_manage_returns")

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
            Q(description__icontains=query)
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
def make_request(request):
    if request.method == 'POST':
        form = AssetRequestForm(request.POST)
        if form.is_valid():
            asset_request = form.save(commit=False)
            asset_request.user = request.user
            asset_request.request_date = form.cleaned_data["request_date"]
            asset_request.return_date = form.cleaned_data["return_date"]
            asset_request.save()
            messages.success(request, "Your asset request has been submitted successfully!")
            return redirect('accounts:normal_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
            return redirect('accounts:normal_dashboard')

    return redirect('accounts:normal_dashboard')


@login_required
def my_requests(request):
    user_requests = AssetRequest.objects.filter(
        user=request.user
    ).select_related("user", "assigned_asset", "approved_by")

    return render(request, "accounts/normal_dashboard.html", {
        "requests": user_requests
    })



# --------------------------
# USER: View own requests
# --------------------------
# @login_required
# def my_requests(request):
#     query = request.GET.get('q', '').strip()  # Search query
#     status_filter = request.GET.get('status', '').strip()  # Status filter

#     # Base queryset: requests of the logged-in user
#     requests_list = AssetRequest.objects.filter(user=request.user).select_related('asset')

#     # Apply search by asset name or model
#     if query:
#         requests_list = requests_list.filter(
#             Q(asset__asset_name__icontains=query) |
#             Q(asset__model__icontains=query)
#         )

#     # Apply status filter if selected
#     if status_filter in ['pending', 'approved', 'rejected', 'returned']:
#         requests_list = requests_list.filter(status=status_filter)

#     # Paginate the results
#     paginator = Paginator(requests_list, 5)  # 5 requests per page
#     page_number = request.GET.get('page')
#     requests_page = paginator.get_page(page_number)

#     context = {
#         'requests': requests_page,
#         'query': query,
#         'status_filter': status_filter,
#     }
#     return render(request, 'requests/my_requests.html', context)


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




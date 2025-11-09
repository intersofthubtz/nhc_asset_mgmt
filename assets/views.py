from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import openpyxl
from django.utils import timezone
import datetime
from openpyxl.styles import Font, PatternFill
from .models import Asset
from .forms import AssetForm
from requests.models import AssetRequest
from django.db.models import Count
import json
from django.core.paginator import Paginator
from django.http import HttpResponse


@login_required
def staff_manage_assets(request):
    assets = Asset.objects.all().order_by('-created_at')
    paginator = Paginator(assets, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'assets/staff_manage_assets.html', {
        'page_obj': page_obj
    })

@login_required
def asset_detail(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    return render(request, 'assets/asset_detail.html', {'asset': asset})

@login_required
def add_asset(request):
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.created_by = request.user
            asset.save()
            messages.success(request, 'Asset added successfully!')
            return redirect('assets:staff_manage_assets')
    else:
        form = AssetForm()
    return render(request, 'assets/asset_form.html', {'form': form, 'title': 'Add Asset'})

@login_required
def edit_asset(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            form.save()
            messages.success(request, 'Asset updated successfully!')
            return redirect('assets:staff_manage_assets')
    else:
        form = AssetForm(instance=asset)
    return render(request, 'assets/asset_form.html', {'form': form, 'title': 'Edit Asset'})

@login_required
def delete_asset(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == 'POST':
        asset.delete()
        messages.success(request, 'Asset deleted successfully!')
        return redirect('assets:staff_manage_assets')
    return render(request, 'assets/asset_confirm_delete.html', {'asset': asset})



@login_required
def staff_dashboard(request):
    total_assets = Asset.objects.count()
    # You can add more counts, e.g., total requests if you have a Request model
    context = {
        'total_assets': total_assets,
        'user': request.user,
    }
    return render(request, 'accounts/staff_dashboard.html', context)







def export_report_excel(request, report_type):
    # Flexible date filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    try:
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    except ValueError:
        start_date = None

    try:
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
    except ValueError:
        end_date = None

    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    header_fill = PatternFill(start_color="FFCCEEFF", end_color="FFCCEEFF", fill_type="solid")
    header_font = Font(bold=True)

    if report_type == 'asset_usage':
        ws.title = "Asset Usage Report"
        headers = ["Asset Name", "Model", "Serial Number", "Total Requests", "Approved Requests"]
        ws.append(headers)
        for col, _ in enumerate(headers, 1):
            ws.cell(row=1, column=col).font = header_font
            ws.cell(row=1, column=col).fill = header_fill

        assets = Asset.objects.all()
        for asset in assets:
            requests_qs = asset.asset_requests.all()  # use related_name in AssetRequest
            if start_date:
                requests_qs = requests_qs.filter(request_date__gte=start_date)
            if end_date:
                requests_qs = requests_qs.filter(request_date__lte=end_date)
            total_requests = requests_qs.count()
            approved_requests = requests_qs.filter(status='approved').count()
            ws.append([asset.asset_name, asset.model or "-", asset.serial_number or "-", total_requests, approved_requests])

    elif report_type == 'request_summary':
        ws.title = "Request Summary"
        headers = ["User", "Asset", "Model", "Request Date", "Return Date", "Status", "Remarks"]
        ws.append(headers)
        for col, _ in enumerate(headers, 1):
            ws.cell(row=1, column=col).font = header_font
            ws.cell(row=1, column=col).fill = header_fill

        requests = AssetRequest.objects.select_related('asset', 'user').all()
        if start_date and end_date:
            requests = requests.filter(request_date__gte=start_date, request_date__lte=end_date)
        elif start_date:
            requests = requests.filter(request_date__gte=start_date)
        elif end_date:
            requests = requests.filter(request_date__lte=end_date)

        for req in requests:
            ws.append([
                req.user.username,
                req.asset.asset_name,
                req.asset.model or "-",
                req.request_date.strftime("%Y-%m-%d"),
                req.return_date.strftime("%Y-%m-%d"),
                req.status.capitalize(),
                req.remarks or "-"
            ])
    else:
        return HttpResponse("Invalid report type", status=400)

    # Auto-adjust column widths
    for column_cells in ws.columns:
        max_length = max(len(str(cell.value or "")) for cell in column_cells)
        ws.column_dimensions[column_cells[0].column_letter].width = max_length + 2

    # Prepare HTTP response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"{report_type}_{timezone.localdate()}.xlsx"
    response['Content-Disposition'] = f'attachment; filename={filename}'
    wb.save(response)
    return response
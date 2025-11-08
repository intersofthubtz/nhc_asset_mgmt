from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Asset
from .forms import AssetForm
from django.db.models import Count
import json
from django.core.paginator import Paginator


@login_required
def staff_manage_assets(request):
    assets = Asset.objects.all().order_by('asset_name')
    paginator = Paginator(assets, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'assets/staff_manage_assets.html', {'page_obj': page_obj})


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
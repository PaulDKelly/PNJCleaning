@extends('layouts.app')

@section('content')
    <div class="space-y-6">

        <!-- Top Bar -->
        <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
                <h1 class="text-2xl font-bold text-slate-800">Data Management</h1>
                <p class="text-slate-500 text-sm">Manage clients, sites, and franchises.</p>
            </div>
        </div>

        <!-- Main Tabs -->
        <div role="tablist" class="tabs tabs-lifted tabs-lg w-full">

            <!-- Tab 1: Client Portfolio -->
            <input type="radio" name="manager_tabs" role="tab" class="tab font-bold" aria-label="Client Portfolio"
                checked />
            <div role="tabpanel" class="tab-content bg-base-100 border-base-300 rounded-box p-6 space-y-8">
                <div class="card bg-white border border-slate-100 shadow-sm">
                    <div class="card-body">
                        <!-- Filter Bar -->
                        <div class="flex flex-col lg:flex-row justify-between items-start lg:items-end mb-4 gap-4">
                            <div>
                                <h3 class="card-title text-slate-700">Client Portfolio</h3>
                                <p class="text-xs text-slate-400">View and manage client accounts.</p>
                            </div>
                            <div class="flex flex-wrap gap-2 items-center">
                                <!-- Filter by Client -->
                                <div class="form-control w-full sm:w-auto">
                                    <label class="label py-0"><span
                                            class="label-text-alt text-[10px] font-bold uppercase text-slate-400">Client</span></label>
                                    <select name="client_name" id="pf-client-filter"
                                        class="select select-bordered select-sm text-xs w-40"
                                        hx-get="{{ route('admin.clients.table') }}" hx-target="#clients-table-body"
                                        hx-include="#pf-brand-filter, #pf-site-filter">
                                        <option value="">All Clients</option>
                                        @foreach($clients as $c)
                                            <option value="{{ $c->client_name }}">{{ $c->client_name }}</option>
                                        @endforeach
                                    </select>
                                </div>

                                <!-- Filter by Brand -->
                                <div class="form-control w-full sm:w-auto">
                                    <label class="label py-0"><span
                                            class="label-text-alt text-[10px] font-bold uppercase text-slate-400">Brand</span></label>
                                    <select name="brand_name" id="pf-brand-filter"
                                        class="select select-bordered select-sm text-xs w-32"
                                        hx-get="{{ route('admin.clients.table') }}" hx-target="#clients-table-body"
                                        hx-include="#pf-client-filter, #pf-site-filter">
                                        <option value="">All Brands</option>
                                        @foreach($brands as $b)
                                            <option value="{{ $b->brand_name }}">{{ $b->brand_name }}</option>
                                        @endforeach
                                    </select>
                                </div>

                                <!-- Filter by Site -->
                                <div class="form-control w-full sm:w-auto">
                                    <label class="label py-0"><span
                                            class="label-text-alt text-[10px] font-bold uppercase text-slate-400">Site</span></label>
                                    <select name="site_id" id="pf-site-filter"
                                        class="select select-bordered select-sm text-xs w-48"
                                        hx-get="{{ route('admin.clients.table') }}" hx-target="#clients-table-body"
                                        hx-include="#pf-client-filter, #pf-brand-filter"
                                        hx-trigger="change, updateSites from:body">
                                        <option value="">All Sites</option>
                                    </select>
                                </div>

                                <button class="btn btn-sm btn-ghost text-slate-400" onclick="clearPortfolioFilters()">
                                    Clear
                                </button>
                            </div>
                        </div>

                        <div class="overflow-x-auto">
                            <table class="table w-full">
                                <thead>
                                    <tr class="text-slate-400 uppercase text-[10px]">
                                        <th>Client / Company</th>
                                        <th>Sites Linked</th>
                                        <th>Portal Access</th>
                                        <th class="text-right">Action</th>
                                    </tr>
                                </thead>
                                <tbody id="clients-table-body" class="text-sm" hx-get="{{ route('admin.clients.table') }}"
                                    hx-trigger="load">
                                    <!-- Loaded via HTMX -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tab 2: Registered Venues -->
            <input type="radio" name="manager_tabs" role="tab" class="tab font-bold" aria-label="Registered Venues" />
            <div role="tabpanel" class="tab-content bg-base-100 border-base-300 rounded-box p-6 space-y-8">
                <div class="card bg-white border border-slate-100 shadow-sm">
                    <div class="card-body">
                        <div class="flex justify-between items-center mb-4">
                            <h3 class="card-title text-slate-700">Site List</h3>
                            <div class="flex gap-2 items-center">
                                <select name="client_name" id="site-filter-select"
                                    class="select select-bordered select-sm text-xs"
                                    hx-get="{{ route('admin.sites.table') }}" hx-target="#sites-table-body"
                                    hx-include="[name='show_archived'], #site-filter-brand">
                                    <option value="">All Clients</option>
                                    @foreach($clients as $c)
                                        <option value="{{ $c->client_name }}">{{ $c->client_name }}</option>
                                    @endforeach
                                </select>

                                <!-- Hidden Brand Filter (Synced) -->
                                <input type="hidden" name="brand_name" id="site-filter-brand" value="">

                                <label class="label cursor-pointer gap-2 border rounded-lg px-2 py-1 hover:bg-slate-50">
                                    <span class="label-text text-xs font-bold text-slate-500">Show Archived</span>
                                    <input type="checkbox" name="show_archived"
                                        class="checkbox checkbox-xs checkbox-primary"
                                        hx-get="{{ route('admin.sites.table') }}" hx-target="#sites-table-body"
                                        hx-include="#site-filter-select, #site-filter-brand" />
                                </label>
                            </div>
                        </div>

                        <div class="overflow-x-auto">
                            <table class="table w-full">
                                <thead>
                                    <tr class="text-slate-400 uppercase text-[10px]">
                                        <th>Site Name</th>
                                        <th>Brand</th>
                                        <th>Client Owner</th>
                                        <th>Status</th>
                                        <th class="text-right">Action</th>
                                    </tr>
                                </thead>
                                <tbody id="sites-table-body" class="text-sm" hx-get="{{ route('admin.sites.table') }}"
                                    hx-trigger="load">
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const pfClient = document.getElementById('pf-client-filter');
        const pfBrand = document.getElementById('pf-brand-filter');
        const pfSite = document.getElementById('pf-site-filter');
        const siteFilterSelect = document.getElementById('site-filter-select');
        const siteFilterBrand = document.getElementById('site-filter-brand');

        function updatePortfolioSites() {
            const client = pfClient.value;
            const brand = pfBrand.value;

            // 1. Update Site Dropdown
            fetch(`{{ route('admin.sites.lookup') }}?client_name=${encodeURIComponent(client)}&brand_name=${encodeURIComponent(brand)}`)
                .then(r => r.text())
                .then(html => pfSite.innerHTML = html);

            // 2. Sync with Registered Venues
            let changed = false;
            if (siteFilterSelect) {
                if (client) {
                    if (siteFilterSelect.value !== client) {
                        siteFilterSelect.value = client;
                        changed = true;
                    }
                } else {
                    if (siteFilterSelect.value !== "") {
                        siteFilterSelect.value = "";
                        changed = true;
                    }
                }
            }
            if (siteFilterBrand) {
                if (siteFilterBrand.value !== brand) {
                    siteFilterBrand.value = brand;
                    changed = true;
                }
            }
            if (changed && siteFilterSelect) {
                htmx.trigger(siteFilterSelect, 'change');
            }
        }

        function updatePortfolioClients() {
            const brand = pfBrand.value;
            const currentClient = pfClient.value;

            fetch(`{{ route('admin.clients.lookup') }}?brand_name=${encodeURIComponent(brand)}`)
                .then(r => r.text())
                .then(html => {
                    pfClient.innerHTML = html;
                    if (currentClient) {
                        pfClient.value = currentClient;
                        if (pfClient.value !== currentClient) {
                            // Client no longer valid, trigger update
                            updatePortfolioSites();
                            htmx.trigger(pfClient, 'change');
                        }
                    }
                });
        }

        if (pfClient && pfBrand) {
            pfClient.addEventListener('change', updatePortfolioSites);
            pfBrand.addEventListener('change', function () {
                updatePortfolioSites();
                updatePortfolioClients();
            });
        }

        function clearPortfolioFilters() {
            pfClient.value = '';
            pfBrand.value = '';
            pfSite.value = '';
            // Reset Registered Venues too
            if (siteFilterSelect) siteFilterSelect.value = '';
            if (siteFilterBrand) siteFilterBrand.value = '';

            updatePortfolioSites();
            updatePortfolioClients();

            htmx.trigger(pfClient, 'change');
        }
    </script>
@endsection
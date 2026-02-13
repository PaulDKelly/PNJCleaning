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

        <!-- Section 1: Client Portfolio -->
        <div class="w-full bg-white border border-slate-200 rounded-xl shadow-sm mb-8">
            <div class="p-6 border-b border-slate-100 bg-slate-50 rounded-t-xl">
                <h2 class="text-lg font-semibold text-slate-800">1. Client Portfolio</h2>
            </div>

            <div class="p-6">
                <!-- Filter Bar -->
                <div class="flex flex-col lg:flex-row justify-between items-start lg:items-end mb-6 gap-4">
                    <div>
                        <h3 class="text-sm font-semibold text-slate-700">Filter Clients</h3>
                        <p class="text-xs text-slate-500 mt-1">Use dropdowns to filter the table.</p>
                    </div>
                    <div class="flex flex-wrap gap-3 items-center w-full lg:w-auto">
                        <!-- Add Client Trigger -->
                        <button onclick="document.getElementById('add-client-modal').classList.remove('hidden')"
                            class="bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold py-1.5 px-3 rounded-lg transition-colors flex items-center gap-2">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24"
                                stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                            </svg>
                            Add Client
                        </button>

                        <div class="h-6 w-px bg-slate-200 mx-2 hidden sm:block"></div>

                        <!-- Filter by Client -->
                        <div class="flex flex-col w-full sm:w-auto">
                            <label class="text-[10px] font-bold uppercase text-slate-400 mb-1">Client</label>
                            <select name="client_name" id="pf-client-filter"
                                class="w-full sm:w-40 rounded-lg border-slate-300 text-sm focus:ring-blue-500 focus:border-blue-500 py-1.5"
                                hx-get="{{ route('admin.clients.table') }}" hx-target="#clients-table-body"
                                hx-include="#pf-brand-filter, #pf-site-filter">
                                <option value="">All Clients</option>
                                @foreach($clients as $c)
                                    <option value="{{ $c->client_name }}">{{ $c->client_name }}</option>
                                @endforeach
                            </select>
                        </div>

                        <!-- Filter by Brand -->
                        <div class="flex flex-col w-full sm:w-auto">
                            <label class="text-[10px] font-bold uppercase text-slate-400 mb-1">Brand</label>
                            <select name="brand_name" id="pf-brand-filter"
                                class="w-full sm:w-32 rounded-lg border-slate-300 text-sm focus:ring-blue-500 focus:border-blue-500 py-1.5"
                                hx-get="{{ route('admin.clients.table') }}" hx-target="#clients-table-body"
                                hx-include="#pf-client-filter, #pf-site-filter">
                                <option value="">All Brands</option>
                                @foreach($brands as $b)
                                    <option value="{{ $b->brand_name }}">{{ $b->brand_name }}</option>
                                @endforeach
                            </select>
                        </div>

                        <!-- Filter by Site -->
                        <div class="flex flex-col w-full sm:w-auto">
                            <label class="text-[10px] font-bold uppercase text-slate-400 mb-1">Site</label>
                            <select name="site_id" id="pf-site-filter"
                                class="w-full sm:w-48 rounded-lg border-slate-300 text-sm focus:ring-blue-500 focus:border-blue-500 py-1.5"
                                hx-get="{{ route('admin.clients.table') }}" hx-target="#clients-table-body"
                                hx-include="#pf-client-filter, #pf-brand-filter" hx-trigger="change, updateSites from:body">
                                <option value="">All Sites</option>
                            </select>
                        </div>

                        <button
                            class="text-slate-400 hover:text-slate-600 text-sm font-medium px-2 py-1 transition-colors mt-4 sm:mt-0"
                            onclick="clearPortfolioFilters()">
                            Clear
                        </button>
                    </div>
                </div>

                <div class="overflow-hidden border border-slate-200 rounded-lg">
                    <table class="min-w-full divide-y divide-slate-200">
                        <thead class="bg-slate-50">
                            <tr>
                                <th scope="col"
                                    class="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                    Client / Company</th>
                                <th scope="col"
                                    class="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                    Sites Linked</th>
                                <th scope="col"
                                    class="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                    Portal Access</th>
                                <th scope="col"
                                    class="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                    Action</th>
                            </tr>
                        </thead>
                        <tbody id="clients-table-body" class="bg-white divide-y divide-slate-200"
                            hx-get="{{ route('admin.clients.table') }}" hx-trigger="load">
                            <!-- Loaded via HTMX -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Section 2: Registered Venues -->
        <div class="w-full bg-white border border-slate-200 rounded-xl shadow-sm">
            <div class="p-6 border-b border-slate-100 bg-slate-50 rounded-t-xl">
                <h2 class="text-lg font-semibold text-slate-800">2. Registered Venues</h2>
            </div>

            <div class="p-6">
                <div class="flex flex-col sm:flex-row justify-between items-center mb-6 gap-4">
                    <h3 class="text-sm font-semibold text-slate-700">All Sites</h3>
                    <div class="flex flex-wrap gap-2 items-center">
                        <select name="client_name" id="site-filter-select"
                            class="rounded-lg border-slate-300 text-sm focus:ring-blue-500 focus:border-blue-500 py-1.5"
                            hx-get="{{ route('admin.sites.table') }}" hx-target="#sites-table-body"
                            hx-include="[name='show_archived'], #site-filter-brand">
                            <option value="">All Clients</option>
                            @foreach($clients as $c)
                                <option value="{{ $c->client_name }}">{{ $c->client_name }}</option>
                            @endforeach
                        </select>

                        <!-- Hidden Brand Filter (Synced) -->
                        <input type="hidden" name="brand_name" id="site-filter-brand" value="">

                        <label
                            class="inline-flex items-center gap-2 px-3 py-1.5 border border-slate-200 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors">
                            <span class="text-xs font-semibold text-slate-600">Show Archived</span>
                            <input type="checkbox" name="show_archived"
                                class="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4"
                                hx-get="{{ route('admin.sites.table') }}" hx-target="#sites-table-body"
                                hx-include="#site-filter-select, #site-filter-brand" />
                        </label>

                        <div class="h-6 w-px bg-slate-200 mx-2 hidden sm:block"></div>

                        <button onclick="document.getElementById('add-site-modal').classList.remove('hidden')"
                            class="bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold py-1.5 px-3 rounded-lg transition-colors flex items-center gap-2">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24"
                                stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                            </svg>
                            Add Site
                        </button>
                    </div>
                </div>

                <!-- Add Site Modal -->
                <div id="add-site-modal"
                    class="fixed inset-0 bg-slate-900/50 z-50 hidden flex items-center justify-center backdrop-blur-sm">
                    <div class="bg-white rounded-xl shadow-xl w-full max-w-md p-6 transform transition-all">
                        <div class="flex justify-between items-center mb-6">
                            <h3 class="text-lg font-bold text-slate-800">Add New Site</h3>
                            <button onclick="document.getElementById('add-site-modal').classList.add('hidden')"
                                class="text-slate-400 hover:text-slate-600">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24"
                                    stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                        d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                        <form action="{{ route('admin.sites.store') }}" method="POST" class="space-y-4">
                            @csrf
                            <div>
                                <label class="block text-sm font-medium text-slate-700 mb-1">Site Name</label>
                                <input type="text" name="site_name" required
                                    class="w-full rounded-lg border-slate-300 focus:border-blue-500 focus:ring-blue-500 text-sm">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-slate-700 mb-1">Assign to Client</label>
                                <select name="client_name" required
                                    class="w-full rounded-lg border-slate-300 focus:border-blue-500 focus:ring-blue-500 text-sm">
                                    <option value="">Select Client...</option>
                                    @foreach($clients as $c)
                                        <option value="{{ $c->client_name }}">{{ $c->client_name }}</option>
                                    @endforeach
                                </select>
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-slate-700 mb-1">Brand (Optional)</label>
                                <input type="text" name="brand_name"
                                    class="w-full rounded-lg border-slate-300 focus:border-blue-500 focus:ring-blue-500 text-sm">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-slate-700 mb-1">Address (Optional)</label>
                                <input type="text" name="address"
                                    class="w-full rounded-lg border-slate-300 focus:border-blue-500 focus:ring-blue-500 text-sm">
                            </div>
                            <div class="pt-4 flex justify-end gap-3">
                                <button type="button"
                                    onclick="document.getElementById('add-site-modal').classList.add('hidden')"
                                    class="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg text-sm font-medium transition-colors">Cancel</button>
                                <button type="submit"
                                    class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors">Create
                                    Site</button>
                            </div>
                        </form>
                    </div>
                </div>

                <div class="overflow-hidden border border-slate-200 rounded-lg">
                    <table class="min-w-full divide-y divide-slate-200">
                        <thead class="bg-slate-50">
                            <tr>
                                <th scope="col"
                                    class="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                    Site Name</th>
                                <th scope="col"
                                    class="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                    Brand</th>
                                <th scope="col"
                                    class="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                    Client Owner</th>
                                <th scope="col"
                                    class="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                    Status</th>
                                <th scope="col"
                                    class="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                    Action</th>
                            </tr>
                        </thead>
                        <tbody id="sites-table-body" class="bg-white divide-y divide-slate-200"
                            hx-get="{{ route('admin.sites.table') }}" hx-trigger="load">
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <!-- Add Client Modal -->
    <div id="add-client-modal"
        class="fixed inset-0 bg-slate-900/50 z-50 hidden flex items-center justify-center backdrop-blur-sm">
        <div class="bg-white rounded-xl shadow-xl w-full max-w-md p-6 transform transition-all">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-slate-800">Add New Client</h3>
                <button onclick="document.getElementById('add-client-modal').classList.add('hidden')"
                    class="text-slate-400 hover:text-slate-600">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24"
                        stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
            <form action="{{ route('admin.clients.store') }}" method="POST" class="space-y-4">
                @csrf
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Client Name</label>
                    <input type="text" name="client_name" required
                        class="w-full rounded-lg border-slate-300 focus:border-blue-500 focus:ring-blue-500 text-sm">
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Company / Group (Optional)</label>
                    <input type="text" name="company"
                        class="w-full rounded-lg border-slate-300 focus:border-blue-500 focus:ring-blue-500 text-sm">
                </div>
                <div class="pt-4 flex justify-end gap-3">
                    <button type="button" onclick="document.getElementById('add-client-modal').classList.add('hidden')"
                        class="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg text-sm font-medium transition-colors">Cancel</button>
                    <button type="submit"
                        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors">Create
                        Client</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Generic Edit Modal Container (Loaded via HTMX) -->
    <div id="edit-modal-container"></div>

    <script>
        // ... (existing scripts)
        // Tab switching logic removed for flattened layout

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
@extends('layouts.app')

@section('content')
    <div class="space-y-8">
        <div>
            <h1 class="text-2xl font-bold text-slate-800">Dashboard</h1>
            <p class="text-slate-500 text-sm">Overview of operations, history, and archives.</p>
        </div>

        <!-- Summary Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <h3 class="text-slate-500 text-sm font-medium uppercase">Active Jobs</h3>
                <p class="text-3xl font-bold text-slate-800 mt-2">12</p>
                <p class="text-xs text-slate-400 mt-1">Placeholder</p>
            </div>
            <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <h3 class="text-slate-500 text-sm font-medium uppercase">Total Clients</h3>
                <p class="text-3xl font-bold text-slate-800 mt-2">24</p>
                <p class="text-xs text-slate-400 mt-1">Placeholder</p>
            </div>
            <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <h3 class="text-slate-500 text-sm font-medium uppercase">Pending Reports</h3>
                <p class="text-3xl font-bold text-slate-800 mt-2">5</p>
                <p class="text-xs text-slate-400 mt-1">Placeholder</p>
            </div>
        </div>

        <!-- History Section -->
        <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
            <div class="p-6 border-b border-slate-100 bg-slate-50">
                <h2 class="text-lg font-semibold text-slate-800">Operation History</h2>
                <p class="text-slate-500 text-xs">Recently completed or updated jobs.</p>
            </div>
            <div class="p-0">
                @if(count($recentJobs) > 0)
                    <table class="min-w-full divide-y divide-slate-200">
                        <thead class="bg-slate-50/50">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                    Job #</th>
                                <th class="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                    Client</th>
                                <th class="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                    Date</th>
                                <th class="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                    Status</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            @foreach($recentJobs as $job)
                                <tr>
                                    <td class="px-6 py-4 text-sm text-slate-900 font-medium">{{ $job->id }}</td>
                                    <td class="px-6 py-4 text-sm text-slate-600">{{ $job->client->client_name }}</td>
                                    <td class="px-6 py-4 text-sm text-slate-500">{{ $job->updated_at->format('d/m/Y') }}</td>
                                    <td class="px-6 py-4">
                                        <span
                                            class="px-2 py-1 text-[10px] font-bold uppercase rounded-full bg-green-100 text-green-700">Completed</span>
                                    </td>
                                </tr>
                            @endforeach
                        </tbody>
                    </table>
                @else
                    <div class="p-12 text-center">
                        <p class="text-slate-400 italic text-sm">No recent operations found.</p>
                    </div>
                @endif
            </div>
        </div>

        <!-- Archive Section -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <!-- Archived Clients -->
            <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
                <div class="p-6 border-b border-slate-100 bg-slate-50/50">
                    <h2 class="text-sm font-bold text-slate-800 uppercase tracking-wider">Archived Clients</h2>
                </div>
                <div class="max-h-[300px] overflow-y-auto">
                    @if($archivedClients->count() > 0)
                        <table class="min-w-full divide-y divide-slate-200">
                            <tbody class="divide-y divide-slate-100">
                                @foreach($archivedClients as $client)
                                    <tr class="hover:bg-slate-50 transition-colors">
                                        <td class="px-6 py-4 text-sm text-slate-600 font-medium">{{ $client->client_name }}</td>
                                        <td class="px-6 py-4 text-right">
                                            <a href="{{ route('admin.manage', ['client_name' => $client->client_name]) }}"
                                                class="text-blue-600 hover:text-blue-800 text-xs font-semibold">View</a>
                                        </td>
                                    </tr>
                                @endforeach
                            </tbody>
                        </table>
                    @else
                        <div class="p-8 text-center bg-slate-50/30">
                            <p class="text-slate-400 italic text-sm">No archived clients.</p>
                        </div>
                    @endif
                </div>
            </div>

            <!-- Archived Sites -->
            <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
                <div class="p-6 border-b border-slate-100 bg-slate-50/50">
                    <h2 class="text-sm font-bold text-slate-800 uppercase tracking-wider">Archived Sites</h2>
                </div>
                <div class="max-h-[300px] overflow-y-auto">
                    @if($archivedSites->count() > 0)
                        <table class="min-w-full divide-y divide-slate-200">
                            <tbody class="divide-y divide-slate-100">
                                @foreach($archivedSites as $site)
                                    <tr class="hover:bg-slate-50 transition-colors">
                                        <td class="px-6 py-4">
                                            <div class="text-sm text-slate-600 font-medium">{{ $site->site_name }}</div>
                                            <div class="text-[10px] text-slate-400 font-semibold uppercase">{{ $site->client_name }}
                                            </div>
                                        </td>
                                        <td class="px-6 py-4 text-right">
                                            <a href="{{ route('admin.manage', ['client_name' => $site->client_name]) }}"
                                                class="text-blue-600 hover:text-blue-800 text-xs font-semibold">View</a>
                                        </td>
                                    </tr>
                                @endforeach
                            </tbody>
                        </table>
                    @else
                        <div class="p-8 text-center bg-slate-50/30">
                            <p class="text-slate-400 italic text-sm">No archived sites.</p>
                        </div>
                    @endif
                </div>
            </div>
        </div>
    </div>
@endsection
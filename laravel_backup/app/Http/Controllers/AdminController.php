<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\Client;
use App\Models\ClientSite;
use App\Models\User;

class AdminController extends Controller
{
    // Main View
    public function manageLists(Request $request)
    {
        // Get all filters for initial load
        $clients = Client::orderBy('client_name')->get();
        // For brands, we fetch distinct brand names from ClientSite
        $brands = ClientSite::select('brand_name')->distinct()->whereNotNull('brand_name')->orderBy('brand_name')->get();

        return view('admin.manage_lists', [
            'clients' => $clients,
            'brands' => $brands
        ]);
    }

    // Clients Table (Filtered)
    public function getClientsTable(Request $request)
    {
        $query = Client::query();

        if ($request->filled('client_name')) {
            $query->where('client_name', $request->client_name);
        }

        if ($request->filled('brand_name')) {
            // Find clients who have a site with this brand
            $brand = $request->brand_name;
            $query->whereHas('sites', function ($q) use ($brand) {
                $q->where('brand_name', $brand);
            });
            // Note: Since we didn't define 'sites' relation in the minimal Model yet, 
            // we can use join or raw implementation if relations aren't set up.
            // Let's assume simpler approach if relation missing:
            /*
            $clientNames = ClientSite::where('brand_name', $brand)->pluck('client_name');
            $query->whereIn('client_name', $clientNames);
            */
        }

        if ($request->filled('site_id')) {
            $site = ClientSite::find($request->site_id);
            if ($site) {
                $query->where('client_name', $site->client_name);
            }
        }

        $clients = $query->orderBy('client_name')->get();

        // Count sites logic (simplified for now, usually eager loaded)
        // We'll pass raw count in view or model accessor

        return view('partials.clients_table_rows', compact('clients'));
    }

    // Sites Table (Filtered)
    public function getSitesTable(Request $request)
    {
        $query = ClientSite::query();

        if ($request->filled('client_name')) {
            $query->where('client_name', $request->client_name);
        }

        if ($request->filled('brand_name')) {
            $query->where('brand_name', $request->brand_name);
        }

        if (!$request->boolean('show_archived')) {
            $query->where('archived', false);
        }

        $sites = $query->orderBy('site_name')->get();

        return view('partials.sites_table_rows', compact('sites'));
    }

    // Sites Lookup (Dependent Dropdown)
    public function getSitesLookup(Request $request)
    {
        $query = ClientSite::where('archived', false);

        if ($request->filled('client_name')) {
            $query->where('client_name', $request->client_name);
        }

        if ($request->filled('brand_name')) {
            $query->where('brand_name', $request->brand_name);
        }

        $sites = $query->orderBy('site_name')->get();

        // Return HTML options
        $html = '<option value="">All Sites</option>'; // or "Select a Site"
        foreach ($sites as $site) {
            $html .= '<option value="' . $site->id . '">' . $site->site_name . '</option>';
        }
        return response($html);
    }

    // Clients Lookup (Filtered by Brand)
    public function getClientsLookup(Request $request)
    {
        $query = Client::query();

        if ($request->filled('brand_name')) {
            $brand = $request->brand_name;
            // Manual join logic since we kept models simple
            $clientNames = ClientSite::where('brand_name', $brand)->pluck('client_name')->unique();
            $query->whereIn('client_name', $clientNames);
        }

        $clients = $query->orderBy('client_name')->get();

        $html = '<option value="">All Clients</option>';
        foreach ($clients as $client) {
            $html .= '<option value="' . $client->client_name . '">' . $client->client_name . '</option>';
        }
        return response($html);
    }
}

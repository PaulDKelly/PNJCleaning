<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\AuthController;
use App\Http\Controllers\AdminController;

Route::get('/', function () {
    return redirect()->route('login');
});

// Authentication
Route::get('/login', [AuthController::class, 'showLogin'])->name('login');
Route::post('/login', [AuthController::class, 'login']);
Route::post('/logout', [AuthController::class, 'logout'])->name('logout');

// Admin Panel (Protected)
Route::middleware(['auth'])->prefix('admin')->group(function () {

    // Manage Lists (Primary View)
    Route::get('/manage', [AdminController::class, 'manageLists'])->name('admin.manage');

    // HTMX Partials & Table Endpoints
    Route::get('/manage/clients-table', [AdminController::class, 'getClientsTable'])->name('admin.clients.table');
    Route::get('/manage/sites-table', [AdminController::class, 'getSitesTable'])->name('admin.sites.table');

    // Lookups (Filtered Dropdowns)
    Route::get('/sites-lookup', [AdminController::class, 'getSitesLookup'])->name('admin.sites.lookup');
    Route::get('/clients-lookup', [AdminController::class, 'getClientsLookup'])->name('admin.clients.lookup');

    // Bulk Actions
    Route::post('/manage/sites/bulk-archive', [AdminController::class, 'bulkArchiveSites']);

    // Other routes can be added here...
});

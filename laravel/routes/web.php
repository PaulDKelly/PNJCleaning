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

    // CRUD Actions
    Route::post('/clients', [AdminController::class, 'storeClient'])->name('admin.clients.store');
    Route::get('/clients/{id}/edit', [AdminController::class, 'editClient'])->name('admin.clients.edit');
    Route::put('/clients/{id}', [AdminController::class, 'updateClient'])->name('admin.clients.update');

    Route::post('/sites', [AdminController::class, 'storeSite'])->name('admin.sites.store');
    Route::get('/sites/{id}/edit', [AdminController::class, 'editSite'])->name('admin.sites.edit');
    Route::put('/sites/{id}', [AdminController::class, 'updateSite'])->name('admin.sites.update');

    // Bulk Actions
    Route::post('/manage/sites/bulk-archive', [AdminController::class, 'bulkArchiveSites']);

    // Other routes
    Route::get('/test', function () {
        return view('admin.test');
    });

    // Sidebar Pages
    Route::get('/dashboard', [AdminController::class, 'dashboard'])->name('dashboard');
    Route::get('/engineer/diary', [AdminController::class, 'engineerDiary'])->name('engineer.diary');
    Route::get('/job-allocation', [AdminController::class, 'jobAllocation'])->name('job.allocation');
    Route::get('/admin/reports', [AdminController::class, 'reports'])->name('admin.reports');
    Route::get('/admin/portal-preview', [AdminController::class, 'portalPreview'])->name('admin.portal.preview');
    Route::get('/extraction-report', [AdminController::class, 'reports'])->name('reports.extraction'); // Alias for now
});

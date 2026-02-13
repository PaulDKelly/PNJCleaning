<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PNJ Cleaning - Admin</title>

    <!-- Pure Tailwind - No External DaisyUI Dependency -->
    <script src="/vendor/tailwind.js"></script>
    <script src="/vendor/htmx.js"></script>
    <script src="/vendor/hyperscript.js"></script>

    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        primary: '#2563eb', // blue-600
                        secondary: '#db2777', // pink-600
                    }
                }
            }
        }
    </script>

    <meta name="csrf-token" content="{{ csrf_token() }}">
</head>

<body class="bg-slate-50 min-h-screen font-sans flex flex-col md:flex-row">

    <!-- Sidebar (Desktop) -->
    <aside class="hidden md:flex flex-col w-80 bg-slate-900 h-screen sticky top-0 shadow-2xl z-50">
        <div class="px-6 py-10 border-b border-slate-800">
            <h1 class="text-2xl font-bold text-white tracking-tight">PNJ <span class="text-blue-500">Cleaning</span>
            </h1>
            <p class="text-slate-500 text-xs mt-1 uppercase tracking-widest font-semibold italic">Management System</p>
        </div>

        <nav class="flex-1 px-4 py-6 overflow-y-auto space-y-1">
            <a href="{{ route('dashboard') }}"
                class="flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 text-slate-400 hover:bg-slate-800 hover:text-white">
                <span class="font-medium">Dashboard</span>
            </a>

            <a href="{{ route('engineer.diary') }}"
                class="flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 text-slate-400 hover:bg-slate-800 hover:text-white">
                <span class="font-medium">My Jobs Queue</span>
            </a>

            <a href="{{ route('job.allocation') }}"
                class="flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 text-slate-400 hover:bg-slate-800 hover:text-white">
                <span class="font-medium">Job Allocation</span>
            </a>

            <div class="pt-4 pb-1">
                <p class="px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Administration</p>
            </div>

            <a href="{{ route('admin.reports') }}"
                class="flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 text-slate-400 hover:bg-slate-800 hover:text-white">
                <span class="font-medium">Client Reports</span>
            </a>

            <a href="{{ route('admin.manage') }}"
                class="flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 {{ request()->routeIs('admin.manage') ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20' : 'text-slate-400 hover:bg-slate-800 hover:text-white' }}">
                <span class="font-medium">Administrators Panel</span>
            </a>

            <a href="{{ route('admin.portal.preview') }}"
                class="flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 text-slate-400 hover:bg-slate-800 hover:text-white">
                <span class="font-medium">Client Portal Experience</span>
            </a>
        </nav>

        <div class="p-6 bg-slate-950/50 border-t border-slate-800">
            <div class="flex items-center space-x-3 mb-6 p-3 bg-slate-800/30 rounded-2xl border border-slate-700/50">
                <div class="h-10 w-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold">
                    {{ substr(Auth::user()->email ?? 'U', 0, 1) }}
                </div>
                <div class="overflow-hidden">
                    <p class="font-bold text-white truncate text-sm">{{ Auth::user()->email ?? 'Guest' }}</p>
                    <p class="text-slate-500 text-xs truncate">Administrator</p>
                </div>
            </div>
            @auth
                <form action="{{ route('logout') }}" method="POST">
                    @csrf
                    <button type="submit"
                        class="w-full py-2 px-4 border border-red-500/30 text-red-400 hover:bg-red-500/10 rounded-xl text-sm font-medium transition-colors">Logout</button>
                </form>
            @endauth
        </div>
    </aside>

    <!-- Mobile Header -->
    <header class="md:hidden bg-slate-900 text-white p-4 flex justify-between items-center sticky top-0 z-50">
        <h1 class="text-xl font-bold">PNJ <span class="text-blue-500">Cleaning</span></h1>
        <!-- Simple Mobile Menu Toggle could be added here -->
    </header>

    <!-- Main Content -->
    <main class="flex-1 w-full min-h-screen overflow-x-hidden">
        <div class="p-6 lg:p-10 container mx-auto max-w-7xl">
            @yield('content')
        </div>
    </main>

    <script>
        // Global HTMX setup for CSRF
        document.body.addEventListener('htmx:configRequest', function (evt) {
            evt.detail.headers['X-CSRF-TOKEN'] = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        });
    </script>
</body>

</html>
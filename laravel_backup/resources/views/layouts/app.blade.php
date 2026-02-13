<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PNJ Cleaning - Admin</title>
    <!-- Tailwind + DaisyUI CDN (for simplicity, or use local build) -->
    <link href="https://cdn.jsdelivr.net/npm/daisyui@3.1.0/dist/full.css" rel="stylesheet" type="text/css" />
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/htmx.org@1.9.2"></script>
    <script src="https://unpkg.com/hyperscript.org@0.9.9"></script>
    <meta name="csrf-token" content="{{ csrf_token() }}">
</head>

<body class="bg-slate-50 min-h-screen text-slate-600 font-sans">

    <!-- Navbar -->
    <div class="navbar bg-white border-b border-slate-200 sticky top-0 z-50 px-4 md:px-8">
        <div class="flex-1">
            <a href="/admin/manage" class="btn btn-ghost normal-case text-xl text-primary font-bold tracking-tight">PNJ
                Cleaning</a>
        </div>
        <div class="flex-none gap-4">
            <span class="text-sm font-medium text-slate-500 hidden md:block">{{ Auth::user()->email ?? 'Guest' }}</span>
            @auth
                <form action="{{ route('logout') }}" method="POST">
                    @csrf
                    <button type="submit" class="btn btn-sm btn-ghost">Logout</button>
                </form>
            @endauth
        </div>
    </div>

    <!-- Content -->
    <main class="container mx-auto px-4 py-8 max-w-7xl">
        @yield('content')
    </main>

    <script>
        // Global HTMX setup for CSRF
        document.body.addEventListener('htmx:configRequest', function (evt) {
            evt.detail.headers['X-CSRF-TOKEN'] = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        });
    </script>
</body>

</html>
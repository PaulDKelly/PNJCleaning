@extends('layouts.app')

@section('content')
    <div class="space-y-6">
        <h1 class="text-2xl font-bold text-slate-800">Test Page</h1>
        <p class="text-slate-500">If you see this, the layout and Tailwind are working.</p>

        <div class="w-full bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
            <h2 class="text-xl font-semibold mb-4 text-blue-600">Tailwind Box</h2>
            <button class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition">Test Button</button>
        </div>
    </div>
@endsection